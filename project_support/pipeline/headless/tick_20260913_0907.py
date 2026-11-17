"""Capture live progress and descriptive scene-level paired outcome counts."""
import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex

import yaml
from close_m185_20260912 import parse_log, run
from verify_control_archives_20260912 import remote, sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
STAMP = "20260913-091000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    OUT.mkdir(exist_ok=False)
    protected = {n: sha(P / n) for n in
                 ("goal.json", "queue.json", "running.json", "experiments.csv")}
    prior_path = P / "reports/tick_evidence_20260913-081000/audit.json"
    prior = load(prior_path)
    inventory = []
    for path in sorted((P / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                              characters=len(text)))
    assert inventory == prior["analyses"], "Changed terminal analyses need review"
    with (P / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == prior["ledger_rows"]
    assert protected == prior["protected"], "Changed registry needs reconciliation"
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
    protocol_path = ap.with_name("protocol.json")
    assignment, protocol = load(ap), load(protocol_path)
    assert sha(ap) == prior["assignment_sha256"]
    assert assignment["protocol_sha256"] == sha(protocol_path)
    for rel, digest in protocol["source_hashes"].items():
        assert sha(ROOT / "Cluster" / rel) == digest
    banks = {}
    for model, digest in protocol["summary_hashes"].items():
        path = P / f"reports/d1_expansion_20260911-0715/{model}/summary.json"
        assert sha(path) == digest
        rows = load(path)["rows"]
        banks[model] = {tuple(str(r[k]) for k in ("scene_id", "object_id", "ann_id")): r for r in rows}
        assert len(banks[model]) == len(rows) == 284
    assert banks["baseline"].keys() == banks["m95"].keys()
    scene_rows = defaultdict(list)
    for pair in prior["pairs"]:
        key = tuple(pair[k] for k in ("scene_id", "object_id", "ann_id"))
        for model in ("baseline", "m95"):
            assert pair[f"{model}_iou"] == banks[model][key]["selected_iou"]
            assert pair[f"{model}_success"] == (pair[f"{model}_iou"] > .5)
        scene_rows[pair["scene_id"]].append(pair)
    assert sum(map(len, scene_rows.values())) == 284
    assert len({(r["scene_id"], r["object_id"], r["ann_id"]) for r in prior["pairs"]}) == 284
    scenes = []
    for scene, rows in sorted(scene_rows.items()):
        assert len(rows) == 4
        gained = sum(not r["baseline_success"] and r["m95_success"] for r in rows)
        lost = sum(r["baseline_success"] and not r["m95_success"] for r in rows)
        scenes.append(dict(scene_id=scene, records=4, gained=gained, lost=lost,
                           net_success=gained-lost,
                           mean_iou_delta=sum(r["m95_iou"]-r["baseline_iou"] for r in rows)/4))
    result = dict(pairs=284, scenes=len(scenes),
                  scenes_with_gain=sum(r["gained"] > 0 for r in scenes),
                  scenes_with_loss=sum(r["lost"] > 0 for r in scenes),
                  scenes_with_both=sum(r["gained"] > 0 and r["lost"] > 0 for r in scenes),
                  net_success_histogram=dict(Counter(r["net_success"] for r in scenes)),
                  total_gains=sum(r["gained"] for r in scenes),
                  total_losses=sum(r["lost"] for r in scenes))
    assert result["total_gains"] == 17 and result["total_losses"] == 30
    diagnostic = f"""# Frozen Bank Scene Outcome Audit
Completed {datetime.now().isoformat()} Asia/Shanghai.

## Question And Protocol
Are the previously counted 17 success gains and 30 losses concentrated in the
same scenes? Use all 284 paired descriptions in the frozen expansion bank,
four per scene, with unchanged IoU>.5 threshold. Recheck both source summaries,
assignment/protocol and five source-code hashes. No training or new sampling.
Full 71-scene manifest and upstream audit hash are in audit.json.

## Results
```json
{json.dumps(result, indent=2)}
```

## Interpretation And Limits
Gain/loss scene counts overlap: a scene can contain both kinds of transition.
Net success zero can mean no transitions or cancelling transitions.
These are descriptive counts for a selected validation diagnostic bank only.
No population confidence interval, independent generalization estimate or
causal mechanism is established. Do not substitute this bank for full-validation
champion metrics or combine it with original D1 or the 42-record casebook.
Scene grouping prevents treating descriptions as independent evidence but
does not repair selection bias. Core mechanism admission remains incomplete.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    evidence = dict(at=datetime.now().isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu,
                    assignment_sha256=sha(ap), upstream_audit_sha256=sha(prior_path),
                    result=result, scenes=scenes)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical evidence; terminal analysis authoritative |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal 09:07:59: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 vs baseline | Derived new mechanism |
| Wrong-instance selection | exploratory | D1/D2 frozen banks | Independent confirmation |
| Terminal controls improve M95 | unsupported | M184-M190 0/7 | M191/M193 live |
| Paired outcomes vary by scene | described | This tick's 71-scene manifest | Sampling bias and causality |

## 3. Experiment Assessment
All {len(inventory)} analyses read and hash-unchanged; all {len(ledger)} ledger
rows read. No new terminal experiment needing another result analysis.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: Derived forward/loss, verified primary-source novelty, matched controls,
predefined error subsets, scene uncertainty, robustness and efficiency remain
incomplete. M191 parent platform differs; M193 parent patience is truncated.
Stale running labels in goal findings do not override live registries.

## 5. Design Rationale
Q2: Group paired gains/losses by scene to check whether aggregate transitions
hide within-scene cancellation. Q3: Improve descriptive diagnostic scope, not
claim a mechanism or generalized effect. All12 constraints/11 bans reviewed:
no schedule/seed/value/resource changes, banned selector or renamed mechanism.
No literature or novelty claim added. Scientific admission overrides refill.

## 6. Next Batch
No admitted candidate, hence no exp_design/implementation/enqueue/code sync.
Preserve existing M191/M193 patience10; no automatic legacy successors.
Evidence: reports/tick_evidence_{STAMP}/diagnostic.md.
"""
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Do scene-grouped frozen-bank gains/losses justify refill with zero waiting?",
                    "Preserve M191/M193 patience10; no unadmitted refill or legacy successors.",
                    "Scene grouping is descriptive only; derived novel mechanism and matched controls remain incomplete.",
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
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal09:07:59).

## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs:server-6:7 (two configured slots); no eligible waiting task.

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
Metrics paired at best completed epoch; every completed validation reports9508.

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
- Grouped284 paired outcomes into71 scenes; recorded gains/losses and cancellation.
- No model/config edits, checkpoint pull, enqueue or code sync.

## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no unadmitted refill or successors.
  See decisions/_index.md and this tick's review/audit.

## \u26a0 Pending User Decisions
{chr(10).join(questions) if questions else 'No type=question records in last24h. No user interaction.'}

Next tick:2026-09-13 10:07 Asia/Shanghai.
"""
    (P / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=live, gpu=gpu, result=result, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
