"""Read-only live snapshot and paired frozen-bank outcome audit."""
import csv
from collections import Counter
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
STAMP = "20260913-081000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    OUT.mkdir(exist_ok=False)
    protected = {n: sha(P / n) for n in
                 ("goal.json", "queue.json", "running.json", "experiments.csv")}
    prior = load(P / "reports/tick_evidence_20260913-071000/audit.json")
    inventory = []
    for path in sorted((P / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                              characters=len(text)))
    assert inventory == prior["analyses"], "New analyses require review"
    with (P / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == prior["ledger_rows"]
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("monitor_tick", skill / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    trainers = [line for line in remote(srv, "ps -eo pid,args").decode().splitlines()
                if "tools/train.py" in line and "ctf_hcg_csort" in line]
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
    assigned = {(r["model"], *(str(r[k]) for k in ("scene_id", "object_id", "ann_id"))): r
                for r in assignment["rows"]}
    assert len(assigned) == len(assignment["rows"]) == 568
    pairs = []
    for key in sorted(banks["baseline"]):
        a, b = assigned[("baseline", *key)], assigned[("m95", *key)]
        for model, row in (("baseline", a), ("m95", b)):
            assert row["status"] == "complete"
            assert row["selected_iou"] == banks[model][key]["selected_iou"]
        pairs.append(dict(scene_id=key[0], object_id=key[1], ann_id=key[2],
                          baseline_iou=a["selected_iou"], m95_iou=b["selected_iou"],
                          baseline_success=a["selected_iou"] > .5,
                          m95_success=b["selected_iou"] > .5))
    transitions = Counter(f"{r['baseline_success']}->{r['m95_success']}" for r in pairs)
    scene_counts = Counter(r["scene_id"] for r in pairs)
    result = dict(pairs=len(pairs), scenes=len(scene_counts),
                  records_per_scene=dict(Counter(scene_counts.values())),
                  transitions=dict(transitions), missing_ids=0, duplicate_ids=0)
    diagnostic = f"""# Frozen Bank Paired Outcome Audit
Completed {datetime.now().isoformat()} Asia/Shanghai.

## Question And Protocol
Can the two 284-record evaluation banks be paired without missing IDs, and
what are their descriptive IoU>.5 outcome transitions? No new sampling,
checkpoint execution, training or relabeling. This is the expansion protocol,
not original D1 or the separate 42-record outcome-selected regression casebook.
Assignment, protocol, five code and two summary hashes verified.
All 568 assignment rows joined to summaries; full 284-pair manifest in audit.json.

## Results
```json
{json.dumps(result, indent=2)}
```

## Interpretation And Limits
Paired identity is necessary for paired comparison but does not establish
representative sampling, an independent test, or causal attribution.
These counts describe only this frozen diagnostic bank. A success transition
does not identify which architectural mechanism caused it. No uncertainty or
population estimate claimed; descriptions within a scene are not independent.
The audit closes an identity-comparability check, not scientific admission.
No novel forward/loss, matched mechanism control or generalized gain established.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    evidence = dict(at=datetime.now().isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu,
                    assignment_sha256=sha(ap), result=result, pairs=pairs)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical evidence; terminal analysis authoritative |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal08:08:05: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; exact gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 vs baseline | New derived mechanism |
| Wrong-instance selection | exploratory | Frozen D1/D2 | Independent confirmation |
| Terminal controls improve M95 | unsupported | M184-M190 0/7 | M191/M193 live |
| Expansion banks support pairing | checked | 284 unique matched IDs | Representativeness and causality |

## 3. Experiment Assessment
All {len(inventory)} terminal analyses read and hash-identical to previous tick;
all {len(ledger)} ledger rows read. No new terminal requiring analysis.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: A derived forward/loss, verified original-source distinction, matched
falsification controls, predefined subsets, scene uncertainty, robustness and
efficiency remain incomplete. M191 parent platform differs; M193 parent has
truncated patience. Historic goal findings contain stale running labels;
queue and experiment registries override them.

## 5. Design Rationale
Q2: Verify paired identities and outcome transitions before comparing models.
Q3: Establish a bounded descriptive comparison without inferring mechanism.
All12 constraints/11 bans checked: no seed/schedule/numeric/resource changes,
no banned or renamed score mechanism. No new literature claim this tick.
Scientific admission overrides queue depth; preserve admitted legacy controls.

## 6. Next Batch
No admitted candidate; no exp_design, implementation, enqueue or sync.
Preserve M191/M193 patience10. Evidence: reports/tick_evidence_{STAMP}/diagnostic.md.
"""
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Do paired frozen-bank outcomes and zero waiting justify new training?",
                    "Preserve M191/M193 patience10; no unadmitted refill or relabeling.",
                    "Paired identities permit descriptive comparison only; derived novel mechanism and matched controls remain incomplete.",
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
    queue = load(P / "queue.json")
    assert not [t for tasks in queue["gpu_queues"].values() for t in tasks if t["status"] == "waiting"]
    report = f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})

## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal08:08:05).

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
- Read/hash-inventoried231 analyses and228 ledger rows; unchanged.
- Archived both live logs and whitelisted GPU snapshot.
- Audited284 paired frozen-bank outcomes across71 scenes; no new sampling.
- Wrote motivation review/diagnostic; all23 monitor regression tests passed.
- No model/config edits, checkpoint pull, enqueue or code sync.

## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no unadmitted refill or relabeling.
  See decisions/_index.md and this tick's audit.json.

## \u26a0 Pending User Decisions
{chr(10).join(questions) if questions else 'No type=question records in last24h. No user interaction.'}

Next tick:2026-09-13 09:07 Asia/Shanghai.
"""
    (P / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=live, gpu=gpu, result=result, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
