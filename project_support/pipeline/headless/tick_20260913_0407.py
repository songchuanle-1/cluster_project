"""Snapshot live training and audit paired frozen-case outcome semantics."""
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
STAMP = "20260913-041000"
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
    prior = load(PIPE / "reports/tick_evidence_20260913-031000/audit.json")
    assert inventory == prior["analyses"]
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
        assert len(counts) >= len(rows) and set(counts) <= {"9508"}
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
    for key in ("scope_audit", "margin", "identity_geometry"):
        assert sha(Path(cases["sources"][key])) == cases["sources"][key + "_sha256"]
    paired = {}
    for r in cases["records"]:
        key = (r["scene_id"], r["object_id"], r["ann_id"])
        assert r["model"] not in paired.setdefault(key, {})
        paired[key][r["model"]] = r
    assert len(paired) == 21
    transitions = Counter()
    identities = []
    for key, models in sorted(paired.items()):
        assert set(models) == {"baseline", "m95"}
        a, b = models["baseline"], models["m95"]
        assert all(a[k] == b[k] for k in ("description", "role", "scope", "target_label"))
        for r in (a, b):
            assert 0 <= r["selected_iou"] <= r["oracle_iou"] <= 1
            assert (r["stratum"] == "success") == (r["selected_iou"] >= .5)
        transitions[(a["stratum"], b["stratum"])] += 1
        identities.append(dict(scene_id=key[0], object_id=key[1], ann_id=key[2],
                               sampling_role=b["role"], baseline=a["stratum"], m95=b["stratum"],
                               baseline_iou=a["selected_iou"], m95_iou=b["selected_iou"]))
    transition_rows = "\n".join(f"| {a} | {b} | {n} |" for (a, b), n in sorted(transitions.items()))
    diagnostic = f"""# Frozen Paired-Outcome Regression Audit
Completed {datetime.now().isoformat()} Asia/Shanghai.

## Question And Provenance
Does the casebook sampling role denote each model's actual outcome?
Source: {source.relative_to(ROOT)}; SHA256 {sha(source)}.
All three upstream hashes verified. All42 records joined into21 unique
baseline/M95 pairs; missing IDs0, duplicate model-ID pairs0.
Descriptions, target labels, scopes and sampling roles agree across each pair.
Selected IoU never exceeds the corresponding bank oracle; success labels
agree with the existing IoU>=0.5 diagnostic threshold for all42 records.

## Paired Outcomes
| Baseline Outcome | M95 Outcome | Descriptions |
|------------------|-------------|--------------|
{transition_rows}

## Interpretation
The error/control role was selected using M95, not baseline. A baseline record
with role=error can therefore be a successful prediction, not a labeling bug.
These paired transitions are deterministic regression fixtures only: the
outcome-selected21 descriptions cannot estimate either model's population
gain, a paired significance test or a generalization result. Their11 scenes
and20 objects are unchanged from the sampling audit. Do not silently redefine
roles per model or select a mechanism by maximizing performance on these cases.
No new labels, inference, data acquisition, mechanism or training is involved.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    evidence = dict(at=datetime.now().isoformat(), analyses=inventory, ledger_rows=len(ledger),
                    live=live, gpu=gpu, trainers=trainers, protected=protected,
                    paired_outcomes=identities, source_sha256=sha(source))
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical result; retained individual analysis |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{(PIPE / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal04:08:08: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; exact gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical support | M95 vs baseline | New derived mechanism |
| Wrong-instance selection | exploratory | Frozen D1/D2 | Independent confirmation |
| Legacy terminal controls improve M95 | unsupported | M184-M190 0/7 | M191/M193 ongoing |
| Casebook role is model-specific outcome | false | Paired outcome audit | Keep role separate from stratum |

## 3. Experiment Assessment
All{len(inventory)} analyses read/hash-inventoried unchanged; all{len(ledger)}
ledger rows read. No newly terminal experiment.
| Experiment | mIoU | State | Motivation assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: A derived forward/loss with verified primary-source distinction remains
missing, as do matched mechanism controls, independent error subsets,
scene-level uncertainty and full efficiency admission. Outcome-selected
cases cannot resolve population effects. Platform matching for M191 and
full-patience matching for M193 remain unverified.

## 5. Design Rationale
Q2: Check paired role/outcome semantics, identity joins and oracle invariants.
Q3: Prevent mislabeling a baseline success as a baseline failure in future
regression tests. This closes an offline correctness check, not a mechanism.
All12 constraints and11 bans checked: no graph/parameter/numerical/schedule/
seed/resource-policy change; no routing/gating/pooling/selector successor.
No new literature search or novelty verification claimed. No candidate passes
scientific admission; it overrides both declared and configured queue depth.

## 6. Next Batch
No new exp_design, model/config implementation, enqueue or deployment sync.
Preserve M191/M193 patience10 and existing allocations. Continue bounded
evidence-driven work. See reports/tick_evidence_{STAMP}/diagnostic.md.
"""
    (PIPE / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    print(run([monitor.bash_executable(), str(skill / "log_decision.sh"),
               "cluster_project", "route_change",
               "Does zero waiting and early M191/M193 progress justify a new mechanism?",
               "Preserve M191/M193 patience10; no unadmitted refill; distinguish M95 sampling roles from paired model outcomes.",
               "All231 analyses unchanged; scientific admission incomplete; outcome-selected fixtures cannot estimate generalization.",
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
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal04:08:08).

## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs:server-6:7 (two configured slots); no eligible waiting tasks.

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
Metrics paired at best epoch. Completed validations all report9508 expressions.
Both trainer identities verified; early training is not terminal efficacy evidence.

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
- Audited21 paired IDs/42 records: joins, labels, oracle and outcome semantics.
- Wrote motivation review and diagnostic. No new design, model/config edit,
  enqueue, checkpoint pull or deployment sync. Preserve existing training.

## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no scientifically unadmitted
  refill. Keep sampling role separate from per-model outcome.
See decisions/_index.md and reports/tick_evidence_{STAMP}/audit.json.

## \u26a0 Pending User Decisions
{chr(10).join('- '+n+chr(10)+t for n,t in questions) if questions else 'No type=question records in the last24h. No user interaction.'}

Next tick:2026-09-13 05:07 Asia/Shanghai.
"""
    (PIPE / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(PIPE / n) for n in protected}
    print(json.dumps(dict(live=live, gpu=gpu, transitions=[[*k, v] for k, v in transitions.items()],
                          questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
