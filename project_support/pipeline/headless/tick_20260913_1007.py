"""Read-only live capture and frozen-bank error-budget identity audit."""
import csv
from collections import defaultdict
from datetime import datetime, timedelta
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex

import yaml
from close_m185_20260912 import parse_log, run
from verify_control_archives_20260912 import remote, sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
STAMP = "20260913-101000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    OUT.mkdir(exist_ok=False)
    protected = {n: sha(P / n) for n in
                 ("goal.json", "queue.json", "running.json", "experiments.csv")}
    prior = load(P / "reports/tick_evidence_20260913-091000/audit.json")
    inventory = []
    for path in sorted((P / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                              characters=len(text)))
    assert inventory == prior["analyses"]
    assert protected == prior["protected"]
    with (P / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == prior["ledger_rows"]
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("monitor_tick", skill / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    trainers = [s for s in remote(srv, "ps -eo pid,args").decode().splitlines()
                if "tools/train.py" in s and "ctf_hcg_csort" in s]
    live, gpu = [], {}
    for prefix in ("M191", "M193"):
        exp = load(next((P / "experiments").glob(prefix + "-*.json")))
        assert exp["status"] == "running"
        base = Path(exp["config"]).stem
        assert any(base in line for line in trainers)
        path = monitor.find_latest_log(base, srv["work_dir"], srv["host"], srv["user"])
        assert path
        snapshot = OUT / f"{prefix}_live.log"
        snapshot.write_bytes(remote(srv, "cat " + shlex.quote(path)))
        text = snapshot.read_text(encoding="utf-8")
        assert not re.search(r"Traceback|Early stopping at epoch", text)
        parsed = parse_log(text)
        rows = [r for r in parsed if {"acc50", "spmiou"} <= r.keys()]
        assert [r["epoch"] for r in rows] == list(range(1, len(rows) + 1))
        counts = re.findall(r"Evaluate referring segmentation:\s*(\d+)", text)
        assert len(counts) >= len(rows) and set(counts) == {"9508"}
        live.append(dict(id=exp["id"], config=exp["config"], gpu=exp["gpu"],
                         epoch=int(re.findall(r"Epoch \[(\d+)/50\]", text)[-1]),
                         completed=len(rows), metrics=rows, best=max(rows, key=lambda r:r["miou"]),
                         unpaired_rows=len(parsed)-len(rows), remote_log=path,
                         log_sha256=sha(snapshot)))
    for name in ("server-4", "server-6"):
        s = servers[name]
        ids = ",".join(map(str, s["allowed_gpus"]))
        gpu[name] = remote(s, f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()

    ap = P / "reports/d1_assignment_20260911-1113/assignment.json"
    pp = ap.with_name("protocol.json")
    protocol = load(pp)
    assert sha(ap) == prior["assignment_sha256"]
    assert load(ap)["protocol_sha256"] == sha(pp)
    for rel, digest in protocol["source_hashes"].items():
        assert sha(ROOT / "Cluster" / rel) == digest
    banks, results, scenes = {}, {}, {}
    for model, digest in protocol["summary_hashes"].items():
        path = P / f"reports/d1_expansion_20260911-0715/{model}/summary.json"
        assert sha(path) == digest
        rows = load(path)["rows"]
        keys = [tuple(str(r[k]) for k in ("scene_id", "object_id", "ann_id")) for r in rows]
        assert len(set(keys)) == len(rows) == 284
        banks[model] = dict(zip(keys, rows))
        grouped = defaultdict(list)
        for row in rows:
            selected, oracle = row["selected_iou"], row["oracle_iou"]
            candidates = row["candidate_ious"]
            assert len(candidates) == row["candidate_count"] == 128
            assert all(math.isfinite(v) and 0 <= v <= 1 for v in candidates)
            assert selected == candidates[row["selected_index"]]
            assert oracle == candidates[row["oracle_index"]] == max(candidates)
            assert 0 <= selected <= oracle <= 1
            assert math.isclose(row["bank_limitation"], 1-oracle, abs_tol=1e-12)
            assert math.isclose(row["selection_gap"], oracle-selected, abs_tol=1e-12)
            assert math.isclose(1-selected, row["bank_limitation"]+row["selection_gap"], abs_tol=1e-12)
            grouped[row["scene_id"]].append(row)
        assert len(grouped) == 71 and all(len(v) == 4 for v in grouped.values())
        def aggregate(rs):
            return dict(records=len(rs),
                        mean_selected_iou=sum(r["selected_iou"] for r in rs)/len(rs),
                        mean_oracle_iou=sum(r["oracle_iou"] for r in rs)/len(rs),
                        mean_bank_limitation=sum(r["bank_limitation"] for r in rs)/len(rs),
                        mean_selection_gap=sum(r["selection_gap"] for r in rs)/len(rs),
                        success=sum(r["selected_iou"] > .5 for r in rs),
                        recoverable=sum(r["selected_iou"] <= .5 < r["oracle_iou"] for r in rs),
                        bank_limited=sum(r["oracle_iou"] <= .5 for r in rs))
        results[model] = aggregate(rows)
        scenes[model] = {k: aggregate(v) for k, v in sorted(grouped.items())}
        assert sum(results[model][k] for k in ("success", "recoverable", "bank_limited")) == 284
    assert banks["baseline"].keys() == banks["m95"].keys()
    delta = {k: results["m95"][k]-results["baseline"][k]
             for k in ("mean_selected_iou", "mean_oracle_iou", "mean_selection_gap")}
    assert math.isclose(delta["mean_selected_iou"],
                        delta["mean_oracle_iou"]-delta["mean_selection_gap"], abs_tol=1e-12)
    evidence = dict(at=datetime.now().isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu,
                    assignment_sha256=sha(ap), protocol_sha256=sha(pp),
                    summary_hashes=protocol["summary_hashes"], result=results,
                    delta=delta, scenes=scenes,
                    ids=[list(k) for k in sorted(banks["baseline"])])
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    diagnostic = f"""# Frozen Bank Error Budget Audit
Completed {datetime.now().isoformat()} Asia/Shanghai.

## Question And Protocol
Check whether stored bank limitation and selection gap exactly reconstruct
selected-mask error. All 284 paired descriptions, 71 scenes with four each,
128 candidate IoUs per model-description; no missing or duplicate identities.
Both summary hashes, assignment/protocol and five source-code hashes verified.
All 568 selected/oracle indices checked against their actual candidate arrays.

## Results
```json
{json.dumps(dict(models=results, m95_minus_baseline=delta), indent=2)}
```
Every record satisfies:
1-selected = (1-oracle) + (oracle-selected).
The paired mean identity is delta_selected = delta_oracle - delta_selection_gap.
The full scene aggregates and paired ID manifest are in audit.json.

## Interpretation And Limits
This is an arithmetic decomposition, not a causal allocation of model error.
The two models have different candidate masks, so selection-gap differences
do not isolate the selector. Oracle uses labels and is not deployable.
These are selected validation-bank results, not full-validation metrics,
independent generalization evidence or historical training-target verification.
No population interval is inferred from this selected bank. Do not mix with
original D1 or the 42-record outcome-selected casebook. No training admission.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical; terminal analysis authoritative |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal 10:08:09: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 versus baseline | New derived mechanism |
| Wrong-instance selection | exploratory | D1/D2 diagnostics | Causal intervention |
| Terminal controls beat M95 | unsupported | M184-M190 0/7 | M191/M193 live |
| Error budget fields are correct | verified on frozen bank | 568 candidate-array checks | Not causal attribution |

## 3. Experiment Assessment
Read all {len(inventory)} analyses, hash-unchanged from prior tick; all
{len(ledger)} ledger rows unchanged. No new terminal analysis required.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: Derived forward/loss, primary-source-distinct novelty, matched controls,
predefined error subsets, scene uncertainty, robustness and efficiency remain
incomplete. M191 parent platform differs; M193 parent has truncated patience.
Goal findings' old running labels are historical, not current scheduler state.

## 5. Design Rationale
Q2: Verify exact candidate coverage/selection decomposition before attributing
errors to a mechanism. Q3: Establish arithmetic correctness and denominators,
not a new mechanism. All12 constraints/11 bans reviewed; no schedule/seed/value
changes, banned variants or relabeling. No new literature verification claimed.
Scientific admission takes precedence over depth. Existing controls preserved.

## 6. Next Batch
No scientifically admitted candidate; no new exp_design, implementation,
enqueue or sync. Preserve M191/M193 patience10 and original deployments.
Evidence: reports/tick_evidence_{STAMP}/diagnostic.md.
"""
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Does a verified frozen-bank error budget justify refill at zero waiting?",
                    "Preserve M191/M193 patience10; no unadmitted refill or selector successors.",
                    "Arithmetic decomposition does not isolate selection causality; novel derived mechanism and matched controls remain incomplete.",
                    f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json"])
    now = datetime.now()
    questions = []
    for path in (P / "decisions").glob("*_question.md"):
        when = datetime.strptime(path.name[:15], "%Y%m%d-%H%M%S")
        if now-timedelta(hours=24) <= when <= now:
            questions.append(path.name + "\n" + path.read_text(encoding="utf-8"))
    gpu_rows, live_rows = [], []
    for name, lines in gpu.items():
        for line in lines.splitlines():
            idx, util, used, total = [v.strip() for v in line.split(",")]
            proc = next((r["id"] for r in live if name == "server-4" and str(r["gpu"]) == idx), "IDLE")
            gpu_rows.append(f"| {name} | {idx} | {util}% | {used}/{total} MiB | {proc} |")
    for r in live:
        b = r["best"]
        live_rows.append(f"| {r['id']} | {r['config']} | server-4 | {r['gpu']} | {r['epoch']}/50 | {b['miou']:.10f}@{b['epoch']} | {b['acc50']} | {b['spmiou']} | {r['completed']-b['epoch']}/10 | running |")
    assert not [t for tasks in load(P / "queue.json")["gpu_queues"].values() for t in tasks if t["status"] == "waiting"]
    report = f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})

## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal10:08:09).

## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs:server-6:7 (two configured slots); no eligible waiting task.

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
Metrics paired at best completed epoch; each completed validation reports9508.

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| - | - | - | No waiting tasks | - | - |
Queue depth:0 waiting/5 declared slots -> NEED MORE (requires6).
SERVERS.yaml capacity4 (requires5); scientific admission overrides refill.
No scheduler or capacity change.

## 4. This Tick's Actions
- Unhealthy sentinel absent; monitor/check_goal succeeded once each.
- No new terminal, crash, launch or early-stop; repair attempts0.
- Read/hash-inventoried{len(inventory)} analyses and{len(ledger)} ledger rows; unchanged.
- Archived live logs and whitelisted GPU snapshot.
- Verified568 candidate arrays and exact error-budget identities;71-scene aggregates.
- No model/config edits, checkpoint pull, enqueue or code sync.

## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no unadmitted refill or successors.
  See decisions/_index.md and this tick's review/audit.

## \u26a0 Pending User Decisions
{chr(10).join(questions) if questions else 'No type=question records in last24h. No user interaction.'}

Next tick:2026-09-13 11:07 Asia/Shanghai.
"""
    (P / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=live, gpu=gpu, result=results, delta=delta, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
