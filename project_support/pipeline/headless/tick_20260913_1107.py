"""Capture live runs and audit paired oracle feasibility without scheduler edits."""
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
STAMP = "20260913-111000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    OUT.mkdir(exist_ok=False)
    prior = load(P / "reports/tick_evidence_20260913-101000/audit.json")
    protected = {n: sha(P / n) for n in prior["protected"]}
    assert protected == prior["protected"]
    inventory = []
    for path in sorted((P / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                              characters=len(text)))
    assert inventory == prior["analyses"]
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
    pp = ap.with_name("protocol.json")
    protocol = load(pp)
    assert sha(ap) == prior["assignment_sha256"]
    assert load(ap)["protocol_sha256"] == sha(pp) == prior["protocol_sha256"]
    for rel, digest in protocol["source_hashes"].items():
        assert sha(ROOT / "Cluster" / rel) == digest
    banks = {}
    for model, digest in protocol["summary_hashes"].items():
        path = P / f"reports/d1_expansion_20260911-0715/{model}/summary.json"
        assert sha(path) == digest
        rows = load(path)["rows"]
        keys = [tuple(str(r[k]) for k in ("scene_id", "object_id", "ann_id")) for r in rows]
        assert len(set(keys)) == len(rows) == 284
        banks[model] = dict(zip(keys, rows))
        for row in rows:
            assert row["oracle_iou"] == max(row["candidate_ious"])
            assert 0 <= row["selected_iou"] <= row["oracle_iou"] <= 1
    assert banks["baseline"].keys() == banks["m95"].keys()
    contingency, strata, manifest = Counter(), {}, []
    for key in sorted(banks["baseline"]):
        b, m = banks["baseline"][key], banks["m95"][key]
        label = f"baseline_{int(b['oracle_iou'] > .5)}_m95_{int(m['oracle_iou'] > .5)}"
        contingency[label] += 1
        counts = strata.setdefault(label, Counter())
        counts["records"] += 1
        counts["baseline_success"] += b["selected_iou"] > .5
        counts["m95_success"] += m["selected_iou"] > .5
        manifest.append(dict(id=list(key), stratum=label,
                             baseline_oracle=b["oracle_iou"], m95_oracle=m["oracle_iou"],
                             baseline_selected=b["selected_iou"], m95_selected=m["selected_iou"]))
    assert sum(contingency.values()) == 284
    scene_counts = Counter(k[0] for k in banks["baseline"])
    assert len(scene_counts) == 71 and set(scene_counts.values()) == {4}
    result = dict(contingency=dict(contingency), strata=strata, scene_counts=scene_counts)
    evidence = dict(at=datetime.now().isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu,
                    assignment_sha256=sha(ap), protocol_sha256=sha(pp),
                    summary_hashes=protocol["summary_hashes"], result=result, manifest=manifest)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    diagnostic = f"""# Paired Oracle Feasibility Audit
Completed {datetime.now().isoformat()} Asia/Shanghai.

## Question And Protocol
Does each frozen candidate bank contain any mask with IoU strictly greater
than .5 for the same description? This is a coverage diagnostic, not a selector
intervention. Join all 284 unique description IDs across 71 scenes, four each.
No missing or duplicate IDs. Verify assignment/protocol, five code hashes and
both upstream summary hashes. Verify oracle against actual candidate maxima.
Threshold .5 is inherited from prior success diagnostics, not optimized here.

## Results
```json
{json.dumps(result, indent=2)}
```
The paired per-description stratum manifest and raw IoUs are in audit.json.
Strata report selected-mask success separately from oracle feasibility.

## Interpretation And Limits
Both-feasible failures establish that at least one usable candidate exists in
each respective bank; they do not hold masks fixed between models. Oracle
feasibility does not imply a deployable selector can recover the target.
This selected validation bank is not a population sample, independent test,
or matched causal intervention. No significance, full-validation metric,
supervision defect, new mechanism, or novelty claim is inferred.
No new model is scientifically admitted by this audit.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical; terminal analysis authoritative |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal 11:08:08: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 versus baseline | New derived mechanism |
| Wrong-instance selection | exploratory | D1/D2 diagnostics | Causal intervention |
| Terminal controls beat M95 | unsupported | M184-M190 0/7 | M191/M193 live |
| Paired oracle feasibility | audited | 284 identities and candidate maxima | Fixed-bank intervention |

## 3. Experiment Assessment
Read all {len(inventory)} analyses; hashes unchanged. All {len(ledger)} ledger rows
unchanged; no new terminal requiring analysis.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: Derived forward/loss, verified primary-source-distinct novelty, matched
controls, predefined error subsets, scene uncertainty, robustness and efficiency
remain incomplete. The frozen banks do not isolate selector effects.
M191 parent platform differs; M193 parent has truncated patience.

## 5. Design Rationale
Q2: Audit paired oracle feasibility without new training or changing masks.
Q3: Separate joint candidate availability from selected-mask success.
All 12 constraints and 11 bans reviewed; no hyperparameter/schedule/seed change,
renamed selector or successor admitted. No literature verification this tick.
Scientific admission overrides depth; this is not a global pipeline pause.

## 6. Next Batch
No qualified candidate: no new exp_design, implementation, enqueue or sync.
Preserve M191/M193 patience10 and deployments; continue evidence-led work.
Evidence: reports/tick_evidence_{STAMP}/diagnostic.md.
"""
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Does paired oracle feasibility permit refill at zero waiting?",
                    "Preserve M191/M193 patience10; no unadmitted refill or selector successors.",
                    "Joint candidate availability does not isolate selector effects; derived novel mechanism and matched controls remain incomplete.",
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
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal11:08:08).

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
- No new terminal, crash, launch or early-stop; training repair attempts0.
- Read/hash-inventoried{len(inventory)} analyses and{len(ledger)} ledger rows; unchanged.
- Archived live logs and whitelisted GPU snapshot.
- Audited284 paired oracle-feasibility strata; verified upstream hashes.
- No model/config edits, checkpoint pull, enqueue or code sync.

## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no unadmitted refill or successors.
  See decisions/_index.md and this tick's review/audit.

## \u26a0 Pending User Decisions
{chr(10).join(questions) if questions else 'No type=question records in last24h. No user interaction.'}

Next tick:2026-09-13 12:07 Asia/Shanghai.
"""
    (P / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=[{k:v for k,v in r.items() if k != "metrics"} for r in live],
                          gpu=gpu, result=result, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
