#!/usr/bin/env python3
"""研究目标检查器 — 判定项目是否达成 goal.json 中定义的目标。

用法:
    python3 check_goal.py <project>
    python3 check_goal.py <project> --json    # JSON 输出（供 cron 消费）

退出码:
    0 = 目标未达成
    1 = GOAL_REACHED（全部达成）
    2 = goal.json 不存在（无目标定义）
    3 = 部分达成
"""

import json, csv, os, sys, re
from datetime import datetime
# Windows UTF-8 兼容
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import builtins as _builtins_mod
_orig_open = _builtins_mod.open
def _patched_open(file, mode='r', *args, **kwargs):
    if 'encoding' not in kwargs and 'b' not in mode:
        kwargs['encoding'] = 'utf-8'
    return _orig_open(file, mode, *args, **kwargs)
_builtins_mod.open = _patched_open

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "/home/songcl/3dres/project")


def load_goal(project_dir):
    gp = os.path.join(project_dir, "pipeline", "goal.json")
    if not os.path.exists(gp):
        return None
    with open(gp) as f:
        return json.load(f)


def load_experiments_csv(project_dir):
    cp = os.path.join(project_dir, "pipeline", "experiments.csv")
    if not os.path.exists(cp):
        return []
    rows = []
    with open(cp, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        legacy_monitor = ("finished_at", "id", "config", "server", "gpu",
                          "state", "best_miou", "epochs", "log_local")
        for values in reader:
            if not values:
                continue
            # Older monitor versions appended their nine-column rows to
            # project-owned CSVs without honoring the existing header.
            if (len(values) == len(legacy_monitor)
                    and header != list(legacy_monitor)
                    and re.fullmatch(r"\d{4}-\d{2}-\d{2} .*", values[0])):
                row = dict(zip(legacy_monitor, values))
            elif len(values) == len(header):
                row = dict(zip(header, values))
            else:
                continue
            rows.append(row)
    return rows


def load_analyses(project_dir):
    ad = os.path.join(project_dir, "pipeline", "analyses")
    if not os.path.isdir(ad):
        return {}
    analyses = {}
    for fname in sorted(os.listdir(ad)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(ad, fname)
        with open(fpath) as f:
            text = f.read()
        info = _parse_analysis(text, fname)
        if info:
            analyses[info.get("id", fname)] = info
    return analyses


def _parse_analysis(text, fname):
    info = {"file": fname}
    m = re.search(r"Experiment:\s*(\S+)\s*\|", text)
    if m:
        info["id"] = m.group(1).strip()
    m = re.search(r"State:\s*(\S+)", text)
    if m:
        info["state"] = m.group(1).strip()
    m = re.search(r"mIoU\s*\|\s*([\d.]+)", text)
    if m:
        info["miou"] = float(m.group(1))
    m = re.search(r"Acc@50\s*\|\s*([\d.]+)", text)
    if m:
        info["acc50"] = float(m.group(1))
    m = re.search(r"spmIOU\s*\|\s*([\d.]+)", text)
    if m:
        info["spmiou"] = float(m.group(1))
    m = re.search(r"结论:\s*\[([^\]]+)\]", text)
    if m:
        info["conclusion"] = m.group(1).strip()
    m = re.search(r"vs baseline.*?:\s*γ\s*=\s*([+-]?\d+\.\d+)", text)
    if m:
        info["gamma_vs_baseline"] = float(m.group(1))
    return info


def _get_exp_field(exp, *keys):
    """Get first matching field from experiment dict, supporting multiple naming conventions."""
    for k in keys:
        v = exp.get(k, "")
        if v not in ("", None):
            return v
    return ""

def metric_field_candidates(metric_name):
    """Return CSV field aliases for the goal metric."""
    normalized = str(metric_name or "miou").strip().lower().replace("@", "").replace("-", "_")
    if normalized in ("accuracy", "acc", "acc50"):
        return ("accuracy", "best_accuracy", "best_metric", "best_val_iou", "best_miou", "best_spmiou")
    return ("best_miou", "best_val_iou", "best_metric", "best_spmiou", "accuracy")


def frozen_reference_champion(experiments, goal):
    """Use an explicitly frozen benchmark anchor when a project defines one."""
    frozen = goal.get("frozen_reference", {})
    experiment_id = frozen.get("experiment_id")
    champion_method = frozen.get("champion_method")
    if not experiment_id or not champion_method:
        return None

    metric_fields = metric_field_candidates(goal.get("metric", {}).get("name", "miou"))
    for exp in experiments:
        if _get_exp_field(exp, "experiment_id", "id", "exp_id") != experiment_id:
            continue
        if exp.get("method") != champion_method:
            continue
        if _get_exp_field(exp, "state", "status") not in ("done_complete", "done_earlystop"):
            continue
        try:
            metric_value = float(_get_exp_field(exp, *metric_fields))
        except (ValueError, TypeError):
            continue
        return {
            "id": experiment_id,
            "config": frozen.get("config", "frozen benchmark"),
            "miou": metric_value,
            "epochs": "frozen",
            "state": _get_exp_field(exp, "state", "status"),
            "source": "frozen_reference",
        }
    return None


def find_champion(experiments, analyses, metric_name="miou"):
    best = None
    best_miou = -1
    metric_fields = metric_field_candidates(metric_name)
    for exp in experiments:
        # Support both "state" (legacy) and "status" (multiview/vla conventions)
        state = _get_exp_field(exp, "state", "status")
        if state not in ("done_complete", "done_earlystop", "stopped_unknown"):
            continue
        try:
            miou = float(_get_exp_field(exp, *metric_fields) or "0")
        except (ValueError, TypeError):
            miou = 0
        if miou > best_miou:
            best_miou = miou
            best = {
                "id": _get_exp_field(exp, "id", "exp_id") or "?",
                "config": exp.get("config", "?"),
                "miou": miou,
                "epochs": exp.get("epochs", "?"),
                "state": state,
                "source": "experiments.csv",
            }
    for aid, info in analyses.items():
        if "miou" not in info:
            continue
        state = info.get("state", "")
        if state not in ("done_complete", "done_earlystop", "stopped_unknown"):
            continue
        if info["miou"] > best_miou:
            best_miou = info["miou"]
            best = {
                "id": info.get("id", aid),
                "config": "?",
                "miou": info["miou"],
                "epochs": "?",
                "state": state,
                "source": f"analyses/{info.get('file', '?')}",
            }
    return best


def check_ablation_coverage(ablations, experiments, analyses, goal):
    required = goal.get("evidence_chain", {}).get("ablations_required", [])
    explicit = goal.get("evidence_chain", {}).get("ablation_experiments", {})
    results = {}
    for dim in required:
        if dim in explicit and explicit[dim]:
            exp_ids = explicit[dim]
            covered = any(
                e.get("id") in exp_ids and e.get("state", "") in ("done_complete", "done_earlystop")
                for e in experiments
            )
            if not covered:
                covered = any(
                    aid in exp_ids and a.get("state", "") in ("done_complete", "done_earlystop")
                    for aid, a in analyses.items()
                )
            results[dim] = {"covered": covered, "method": "explicit", "experiments": exp_ids if covered else []}
        else:
            keywords = dim.lower().replace("_", " ").split()
            matches = []
            for e in experiments:
                eid = (e.get("id", "") + " " + e.get("config", "")).lower()
                if any(kw in eid for kw in keywords):
                    if e.get("state", "") in ("done_complete", "done_earlystop"):
                        matches.append(e.get("id", "?"))
            if not matches:
                for aid, a in analyses.items():
                    if a.get("state", "") not in ("done_complete", "done_earlystop"):
                        continue
                    a_text = (aid + " " + a.get("id", "")).lower()
                    if any(kw in a_text for kw in keywords):
                        matches.append(aid)
            results[dim] = {"covered": len(matches) > 0, "method": "keyword", "experiments": matches}
    return results


def check_multi_seed(experiments, analyses, goal):
    if not goal.get("evidence_chain", {}).get("multi_seed_stability", False):
        return {"required": False, "covered": True, "note": "not required"}

    champion = frozen_reference_champion(experiments, goal) or find_champion(
        experiments, analyses, goal.get("metric", {}).get("name", "miou")
    )
    if not champion:
        return {"required": True, "covered": False, "note": "no champion found"}

    champ_config = champion.get("config", "")
    base = os.path.splitext(os.path.basename(champ_config))[0]

    variants = []
    for e in experiments:
        if e.get("state", "") not in ("done_complete", "done_earlystop"):
            continue
        e_base = os.path.splitext(os.path.basename(e.get("config", "")))[0]
        if e_base == base:
            variants.append(e.get("id", "?"))
    for e in experiments:
        if e.get("state", "") not in ("done_complete", "done_earlystop"):
            continue
        cfg = e.get("config", "")
        if "seed" in cfg.lower() and base in cfg:
            variants.append(e.get("id", "?"))
    variants = list(set(variants))
    covered = len(variants) >= 2
    return {
        "required": True, "covered": covered,
        "champion_config": champ_config, "seed_variants": variants,
        "note": f"{len(variants)} seed variant(s), need ≥2" if not covered else f"{len(variants)} seed variants ✓",
    }


def check_baseline(experiments, analyses, goal):
    if not goal.get("evidence_chain", {}).get("baseline_reproduced", False):
        return {"required": False, "covered": True, "note": "not required"}

    baseline_id = goal.get("evidence_chain", {}).get("baseline_experiment_id", None)
    if baseline_id:
        covered = any(
            _get_exp_field(e, "id", "exp_id") == baseline_id and
            _get_exp_field(e, "state", "status") in ("done_complete", "done_earlystop")
            for e in experiments
        )
        return {"required": True, "covered": covered, "baseline_experiments": [baseline_id] if covered else [],
                "note": "" if covered else f"baseline '{baseline_id}' not found or not complete"}

    baseline_exps = []
    for e in experiments:
        eid = (e.get("id", "") + " " + e.get("config", "")).lower()
        if "baseline" in eid or e.get("id", "").endswith("base"):
            if e.get("state", "") in ("done_complete", "done_earlystop"):
                baseline_exps.append(e.get("id", "?"))
    covered = len(baseline_exps) > 0
    return {"required": True, "covered": covered, "baseline_experiments": baseline_exps,
            "note": "" if covered else "specify 'baseline_experiment_id' in goal.json"}


def check_champion_vs_sota(experiments, analyses, goal):
    if not goal.get("evidence_chain", {}).get("champion_vs_sota", False):
        return {"required": False, "covered": True, "note": "not required"}
    sota_exps = []
    for e in experiments:
        eid = (e.get("id", "") + " " + e.get("config", "")).lower()
        if any(kw in eid for kw in ("sota", "external", "benchmark")):
            if e.get("state", "") in ("done_complete", "done_earlystop"):
                sota_exps.append(e.get("id", "?"))
    covered = len(sota_exps) > 0
    return {"required": True, "covered": covered, "experiments": sota_exps,
            "note": "" if covered else "no SOTA comparison experiment found"}


def check_story_completeness(goal, champion, baseline_check, experiments):
    """Phase 2: 检查论文故事线是否闭环。不强求特定模块。"""
    story = {}
    
    # Motivation: do we have a baseline to compare against?
    story["motivation"] = "covered" if baseline_check["covered"] else "partial"
    
    # Method: do we have a champion?
    story["method"] = "covered" if champion else "missing"
    
    # Gap: champion vs baseline improvement
    if champion and baseline_check.get("baseline_miou"):
        gamma = champion["miou"] - baseline_check["baseline_miou"]
        story["gap"] = f"covered (γ={gamma:+.4f})" if gamma > 0 else "missing (no improvement)"
    elif champion:
        story["gap"] = "partial (baseline metric unknown)"
    else:
        story["gap"] = "missing"
    
    # Ablation: are there any ablation experiments at all?
    ablation_count = sum(1 for e in experiments 
                         if e.get("state", "") in ("done_complete", "done_earlystop")
                         and ("ablation" in (e.get("id","") + e.get("config","")).lower()
                              or "noroute" in e.get("id","").lower()
                              or "nomask" in e.get("id","").lower()))
    # Also check for any experiment that looks like a "removed component" test
    removal_count = sum(1 for e in experiments
                        if e.get("state", "") in ("done_complete", "done_earlystop")
                        and any(kw in e.get("id","").lower() 
                               for kw in ("no", "ablation", "remove", "without", "baseline")))
    total_ablations = max(ablation_count, removal_count)
    if total_ablations >= 3:
        story["ablation"] = "covered"
    elif total_ablations >= 1:
        story["ablation"] = "partial"
    else:
        story["ablation"] = "missing"
    
    # Stability: multi-seed?
    seed_count = len(set(e.get("id","") for e in experiments 
                        if "seed" in (e.get("id","") + e.get("config","")).lower()
                        and e.get("state", "") in ("done_complete", "done_earlystop")))
    story["stability"] = "covered" if seed_count >= 2 else ("partial" if seed_count >= 1 else "missing")
    
    # Generalization & Limitation are typically missing unless explicitly tested
    story["generalization"] = "missing"
    story["limitation"] = "missing"
    
    return story


def format_report(goal, champion, phase1_reached, baseline_check, experiments):
    """生成人类可读的报告"""
    lines = []
    lines.append("=" * 80)
    lines.append(f"  Goal Check Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append(f"  Target: {goal.get('description', goal.get('metric', {}).get('name', '?'))}")
    lines.append("")

    target = goal.get("metric", {}).get("target", 0)
    metric_name = goal.get("metric", {}).get("name", "mIoU")

    # Phase 1: Metric
    lines.append("## Phase 1: Metric Target")
    lines.append(f"  Target: {metric_name} ≥ {target:.4f}")
    if champion:
        gap = target - champion["miou"]
        if phase1_reached:
            lines.append(f"  [✓] Champion: {champion['id']} — {metric_name}={champion['miou']:.4f} (target met, exceeded by {-gap:+.4f})")
        else:
            lines.append(f"  [✗] Champion: {champion['id']} — {metric_name}={champion['miou']:.4f} (gap to target: {gap:+.4f})")
        lines.append(f"       Epochs: {champion['epochs']}, State: {champion['state']}")
    else:
        lines.append(f"  [✗] No champion found (no completed experiments)")
    lines.append(f"  Phase 1: {'PHASE1_REACHED ✓' if phase1_reached else 'NOT YET — continue exploring ✗'}")
    lines.append("")

    # Baseline info
    if baseline_check.get("covered"):
        lines.append("## Baseline")
        if baseline_check.get("baseline_miou") is not None:
            lines.append(f"  Baseline: {baseline_check.get('baseline_id','?')} — mIoU={baseline_check['baseline_miou']:.4f}")
            if champion:
                lines.append(f"  Champion vs Baseline: γ = {champion['miou'] - baseline_check['baseline_miou']:+.4f}")
        lines.append("")

    # Phase 2: only relevant if Phase 1 reached
    if phase1_reached:
        lines.append("## Phase 2: Story Verification")
        lines.append("  (champion 已达标，检查论文故事是否闭环)")
        lines.append("")
        
        story = check_story_completeness(goal, champion, baseline_check, experiments)
        story_elements = [
            ("motivation", "Motivation (为什么需要这个方法)"),
            ("method", "Method (我们的方法是什么)"),
            ("gap", "Gap (champion vs baseline 提升)"),
            ("ablation", "Ablation (核心设计是否必要)"),
            ("stability", "Stability (多seed稳定性)"),
            ("generalization", "Generalization (跨setting泛化)"),
            ("limitation", "Limitation (失败案例分析)"),
        ]
        
        covered_count = 0
        total_count = 0
        for key, label in story_elements:
            status = story.get(key, "missing")
            icon = {"covered": "✓", "partial": "◐", "missing": "✗"}.get(status, "?")
            lines.append(f"  [{icon}] {label}: {status}")
            if status in ("covered", "partial"):
                covered_count += 1
            total_count += 1
        
        lines.append("")
        story_complete = covered_count >= 5  # 5/7 elements at least partial
        lines.append(f"  Story: {'COMPLETE ✓' if story_complete else 'INCOMPLETE ✗'} ({covered_count}/{total_count} elements covered)")
        lines.append(f"  Phase 2: {'COMPLETE — 可以开始写论文' if story_complete else '需要补充消融/seed实验'}")
        lines.append("")
        
        if not story_complete:
            lines.append("  Suggested next steps:")
            if story.get("ablation") in ("missing", "partial"):
                lines.append("    - 设计消融实验验证 champion 核心设计选择")
            if story.get("stability") in ("missing", "partial"):
                lines.append("    - 跑 champion 的多 seed 稳定性验证")
        lines.append("")
        
        all_complete = story_complete
    else:
        all_complete = False
        lines.append("## Phase 2: Story Verification")
        lines.append("  (等待 Phase 1 达标后启动)")
        lines.append("")

    # Overall
    lines.append("## Overall")
    if phase1_reached and all_complete:
        lines.append(f"  GOAL_REACHED ✓ — champion {metric_name}={champion['miou']:.4f} ≥ {target:.4f}, 故事闭环")
    elif phase1_reached:
        lines.append(f"  PHASE1_REACHED — champion 达标，Phase 2 进行中")
    else:
        if champion:
            lines.append(f"  Phase 1: champion={champion['miou']:.4f}, target={target:.4f}, gap={target - champion['miou']:+.4f}")
        else:
            lines.append(f"  Phase 1: no champion yet")
    lines.append("=" * 80)
    
    return "\n".join(lines), phase1_reached, all_complete if phase1_reached else False


def main():
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <project> [--json]")
        sys.exit(2)

    project = sys.argv[1]
    json_out = "--json" in sys.argv

    project_dir = os.path.join(PROJECT_ROOT, project)
    if not os.path.isdir(project_dir):
        print(f"错误: 项目目录不存在: {project_dir}")
        sys.exit(2)

    goal = load_goal(project_dir)
    if goal is None:
        if json_out:
            print(json.dumps({"phase": "no_goal", "message": "pipeline/goal.json not found"}))
        else:
            print("pipeline/goal.json 不存在 — 无目标定义，流水线自由探索模式。")
        sys.exit(2)

    experiments = load_experiments_csv(project_dir)
    analyses = load_analyses(project_dir)

    metric_name = goal.get("metric", {}).get("name", "miou")
    champion = frozen_reference_champion(experiments, goal) or find_champion(
        experiments, analyses, metric_name
    )
    target = goal.get("metric", {}).get("target", 0)
    phase1_reached = champion is not None and champion["miou"] >= target

    # Baseline check
    baseline_id = goal.get("baseline_experiment_id", "")
    baseline_check = {"covered": False, "baseline_id": baseline_id}
    for e in experiments:
        # 兼容 id / exp_id 两种列名 (cluster 用 id, multiview 用 exp_id)
        if _get_exp_field(e, "experiment_id", "id", "exp_id") == baseline_id and \
                _get_exp_field(e, "state", "status") in ("done_complete", "done_earlystop"):
            frozen = goal.get("frozen_reference", {})
            if frozen.get("baseline_method") and e.get("method") != frozen["baseline_method"]:
                continue
            baseline_check["covered"] = True
            try:
                baseline_check["baseline_miou"] = float(
                    _get_exp_field(e, *metric_field_candidates(metric_name)) or 0)
            except (ValueError, TypeError):
                pass
            break

    report, p1, p2 = format_report(goal, champion, phase1_reached, baseline_check, experiments)

    if json_out:
        result = {
            "phase": "phase1_reached" if phase1_reached else "phase1",
            "champion": champion,
            "metric_ok": phase1_reached,
            "target": target,
            "baseline": baseline_check,
        }
        if phase1_reached:
            story = check_story_completeness(goal, champion, baseline_check, experiments)
            result["story"] = story
            result["status"] = "goal_reached" if p2 else "phase2_in_progress"
        else:
            result["status"] = "phase1"
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(report)

    if phase1_reached and p2:
        sys.exit(1)  # GOAL_REACHED
    elif phase1_reached:
        sys.exit(4)  # PHASE1_REACHED, Phase 2 in progress
    else:
        sys.exit(0)  # Phase 1 not yet reached


if __name__ == "__main__":
    main()
