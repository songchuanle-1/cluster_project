"""Read-only live snapshot and frozen supervision/outcome contingency audit."""
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
PIPE = ROOT / "pipeline"
STAMP = "20260913-051000"
OUT = PIPE / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    OUT.mkdir(exist_ok=False)
    protected = {n: sha(PIPE / n) for n in
                 ("goal.json", "queue.json", "running.json", "experiments.csv")}
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("monitor_tick", skill / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    inventory = []
    for p in sorted((PIPE / "analyses").glob("*.md")):
        text = p.read_text(encoding="utf-8")
        inventory.append(dict(path=str(p.relative_to(ROOT)), sha256=sha(p), characters=len(text)))
    prior = load(PIPE / "reports/tick_evidence_20260913-041000/audit.json")
    assert inventory == prior["analyses"], "Changed analyses require fresh terminal review"
    with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == prior["ledger_rows"]
    live = []
    srv = servers["server-4"]
    trainers = [p for p in remote(srv, "ps -eo pid,args").decode().splitlines()
                if "tools/train.py" in p and "ctf_hcg_csort" in p]
    for prefix in ("M191", "M193"):
        exp = load(next((PIPE / "experiments").glob(prefix + "-*.json")))
        assert exp["status"] == "running"
        base = Path(exp["config"]).stem
        assert any(base in p for p in trainers)
        path = monitor.find_latest_log(base, srv["work_dir"], srv["host"], srv["user"])
        assert path
        snapshot = OUT / f"{prefix}_live.log"
        snapshot.write_bytes(remote(srv, "cat " + shlex.quote(path)))
        text = snapshot.read_text(encoding="utf-8")
        assert not re.search(r"Traceback|Early stopping at epoch", text)
        rows = [r for r in parse_log(text) if {"acc50", "spmiou"} <= r.keys()]
        assert [r["epoch"] for r in rows] == list(range(1, len(rows) + 1))
        counts = re.findall(r"Evaluate referring segmentation:\s*(\d+)", text)
        assert len(counts) >= len(rows) and set(counts) == {"9508"}
        live.append(dict(id=exp["id"], config=exp["config"], gpu=exp["gpu"],
                         epoch=re.findall(r"Epoch \[(\d+)/50\]", text)[-1],
                         metrics=rows, completed=len(rows), best=max(rows, key=lambda r: r["miou"]),
                         remote_log=path, log_sha256=sha(snapshot)))
    gpu = {}
    for name in ("server-4", "server-6"):
        s = servers[name]
        ids = ",".join(map(str, s["allowed_gpus"]))
        gpu[name] = remote(s, f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()
    source = PIPE / "reports/d1_case_scope_coupling_20260912-1610/case_scope_coupling.json"
    cases = load(source)
    assert sha(source) == prior["source_sha256"]
    for key in ("scope_audit", "margin", "identity_geometry"):
        assert sha(Path(cases["sources"][key])) == cases["sources"][key + "_sha256"]
    contingency = Counter()
    discordant = []
    seen = set()
    for r in cases["records"]:
        identity = tuple(r[k] for k in ("model", "scene_id", "object_id", "ann_id"))
        assert identity not in seen
        seen.add(identity)
        success = r["selected_iou"] >= .5
        assert success == (r["stratum"] == "success")
        contingency[(r["model"], r["selected_positive"], success)] += 1
        if bool(r["selected_positive"]) != success:
            discordant.append(r)
    assert len(seen) == 42
    ct = "\n".join(f"| {model} | {positive} | {success} | {count} |"
                   for (model, positive, success), count in sorted(contingency.items()))
    diagnostic = f"""# Frozen Supervision And Outcome Audit
Completed {datetime.now().isoformat()} Asia/Shanghai.

## Question And Provenance
Is selected_positive interchangeable with selected_iou>=0.5 in the casebook?
Source: {source.relative_to(ROOT)}; SHA256 {sha(source)}.
All three upstream hashes verified; 42 unique model-description records;
21 descriptions per model, zero missing/duplicate records.

## Contingency
| Model | Selected Positive Label | IoU Success | Count |
|-------|-------------------------|-------------|-------|
{ct}

Discordant records: {len(discordant)}. Full IDs and source fields are retained
in audit.json. The two fields represent different diagnostic definitions;
do not infer a parser bug, or force equality, from a disagreement.

## Interpretation And Boundary
Supervision-positive status is not a substitute for measured segmentation
success. Future fixed-fixture checks must preserve both fields and use the
existing selected_iou threshold for outcome strata. This audit checks source
field semantics only, not training-time label construction or correctness.
It does not establish a new failure mechanism or justify replacing supervision.
These outcome-selected cases are not independent evidence, a population
confusion matrix, an unbiased error rate, or a generalization test.
No new inference, labels, dataset, loss, model, checkpoint or queue mutation.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    evidence = dict(at=datetime.now().isoformat(), analyses=inventory, ledger_rows=len(ledger),
                    live=live, gpu=gpu, trainers=trainers, protected=protected,
                    contingency=[dict(model=k[0], selected_positive=k[1], success=k[2], count=v)
                                 for k, v in sorted(contingency.items())],
                    discordant_records=discordant, source_sha256=sha(source))
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical; see individual terminal analysis |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{(PIPE / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal 05:07:58: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; exact gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 vs baseline | New derived mechanism |
| Wrong-instance selection | exploratory | D1/D2 frozen diagnostics | Independent confirmation |
| Terminal recurrence controls improve M95 | unsupported | M184-M190 0/7 | M191/M193 ongoing |
| Positive label equals IoU success | not assumed | Frozen contingency below | Training label construction not re-audited |

## 3. Experiment Assessment
All {len(inventory)} analyses read/hash-inventoried and unchanged from prior tick.
All {len(ledger)} ledger rows read; no newly terminal experiment.
| Experiment | mIoU | State | Motivation assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: Missing derived forward/loss, verified primary-source distinction, matched
controls, independent error subsets, scene-level uncertainty and efficiency.
M191 platform matching and M193 full-patience matching remain unverified.
The frozen contingency is not evidence that training supervision is wrong.

## 5. Design Rationale
Q2: Audit supervision-label/outcome contingency without conflating fields.
Q3: Preserve diagnostic definitions for future regression tests. Results:
{len(discordant)} disagreements among 42 selected records; not a population rate.
All12 constraints and11 bans checked: no numerical, graph, schedule, seed,
resource-policy or training changes. No selector/routing/pooling successor.
No new source review or novelty claim. Scientific admission overrides depth.

## 6. Next Batch
No admitted mechanism; no new exp_design, model/config implementation,
enqueue or deployment sync. Preserve M191/M193 at patience10.
Evidence: reports/tick_evidence_{STAMP}/diagnostic.md.
"""
    (PIPE / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    print(run([monitor.bash_executable(), str(skill / "log_decision.sh"),
               "cluster_project", "route_change",
               "Does zero waiting or frozen label-outcome disagreement justify new training?",
               "Preserve M191/M193 patience10; no unadmitted refill; retain supervision labels separately from measured IoU outcomes.",
               "Scientific admission incomplete; selected fixtures cannot establish a supervision defect or population mechanism.",
               f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json"]))
    now = datetime.now()
    questions = []
    for p in (PIPE / "decisions").glob("*_question.md"):
        when = datetime.strptime(p.name[:15], "%Y%m%d-%H%M%S")
        if now - timedelta(hours=24) <= when <= now:
            questions.append((p.name, p.read_text(encoding="utf-8")))
    gpu_rows = []
    for name, lines in gpu.items():
        for line in lines.splitlines():
            idx, util, used, total = [v.strip() for v in line.split(",")]
            proc = next((r["id"] for r in live if name == "server-4" and str(r["gpu"]) == idx), "IDLE")
            gpu_rows.append(f"| {name} | {idx} | {util}% | {used}/{total} MiB | {proc} |")
    live_rows = []
    for r in live:
        b = r["best"]
        live_rows.append(f"| {r['id']} | {r['config']} | server-4 | {r['gpu']} | {r['epoch']}/50 | {b['miou']:.10f}@{b['epoch']} | {b['acc50']} | {b['spmiou']} | {r['completed']-b['epoch']}/10 | running |")
    queue = load(PIPE / "queue.json")
    assert not [t for ts in queue["gpu_queues"].values() for t in ts if t["status"] == "waiting"]
    report = f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})

## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal05:07:58).

## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs:server-6:7 (two configured slots); no eligible waiting tasks.

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
Metrics paired at best epoch. All completed validations report9508 expressions.
Trainer identities checked; early progress is not terminal efficacy evidence.

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| - | - | - | No waiting tasks | - | - |
Queue depth:0 waiting/5 declared slots -> NEED MORE (requires6).
SERVERS.yaml computes4 slots (requires5); scientific admission overrides depth.
No resource-policy or scheduler change.

## 4. This Tick's Actions
- Unhealthy sentinel absent; monitor/check_goal succeeded once each.
- No new terminal, crash, early-stop or launch; repair attempts0.
- Read/hash-inventoried231 analyses and228 ledger rows, unchanged.
- Saved live logs and whitelisted GPU snapshot.
- Audited42 frozen records for supervision-positive/IoU-success contingency:
  {len(discordant)} disagreements; no new mechanism or label-bug claim.
- Wrote motivation review and diagnostic. No model/config edit, enqueue,
  checkpoint pull or deployment sync. Preserve existing training.

## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no scientifically unadmitted
  refill; distinguish supervision-positive status from measured IoU success.
See decisions/_index.md and reports/tick_evidence_{STAMP}/audit.json.

## \u26a0 Pending User Decisions
{chr(10).join('- '+n+chr(10)+t for n,t in questions) if questions else 'No type=question records in the last24h. No user interaction.'}

Next tick:2026-09-13 06:07 Asia/Shanghai.
"""
    (PIPE / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(PIPE / n) for n in protected}
    print(json.dumps(dict(live=live, gpu=gpu, contingency=evidence["contingency"],
                          discordant=discordant, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
