"""Read-only live and fixed-case sampling audit, with tick documentation."""
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
STAMP = "20260913-031000"
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
    prior = load(PIPE / "reports/tick_evidence_20260913-021200/audit.json")
    assert inventory == prior["analyses"]
    with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == prior["ledger_rows"]
    live = []
    srv = servers["server-4"]
    processes = remote(srv, "ps -eo pid,args").decode()
    trainers = [p for p in processes.splitlines() if "tools/train.py" in p and "ctf_hcg_csort" in p]
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
        best = max(rows, key=lambda r: r["miou"]) if rows else None
        live.append(dict(id=exp["id"], config=exp["config"], gpu=exp["gpu"],
                         epoch=re.findall(r"Epoch \[(\d+)/50\]", text)[-1],
                         metrics=rows, completed=len(rows), best=best,
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
    records = [r for r in cases["records"] if r["model"] == "m95"]
    ids = [(r["scene_id"], r["object_id"], r["ann_id"]) for r in records]
    assert len(records) == len(set(ids)) == 21
    baseline_ids = {(r["scene_id"], r["object_id"], r["ann_id"])
                    for r in cases["records"] if r["model"] == "baseline"}
    assert set(ids) == baseline_ids
    scene_rows = []
    for scene in sorted({r["scene_id"] for r in records}):
        subset = [r for r in records if r["scene_id"] == scene]
        scene_rows.append(dict(scene=scene, errors=sum(r["role"] == "error" for r in subset),
                               controls=sum(r["role"] == "control" for r in subset),
                               objects=len({r["object_id"] for r in subset})))
    counts = Counter((r["scene_id"], r["object_id"]) for r in records)
    diag = dict(source=str(source.relative_to(ROOT)), source_sha256=sha(source),
                descriptions=len(records), scenes=len(scene_rows), objects=len(counts),
                repeated_objects=[dict(scene=k[0], object=k[1], descriptions=v)
                                  for k, v in sorted(counts.items()) if v > 1],
                scenes_with_both_roles=sum(r["errors"] > 0 and r["controls"] > 0 for r in scene_rows),
                scene_rows=scene_rows, sample_ids=ids, missing_ids=0)
    table = "\n".join(f"| {r['scene']} | {r['errors']} | {r['controls']} | {r['objects']} |" for r in scene_rows)
    diagnostic = f"""# Fixed Casebook Sampling Audit
Completed {datetime.now().isoformat()} Asia/Shanghai.

## Source And Denominator
Source: {diag['source']}; SHA256: {diag['source_sha256']}.
All three upstream source hashes verified. Baseline/M95 expression IDs match:
21 unique descriptions each, 42 total records, zero missing IDs.
The 21 descriptions cover {diag['scenes']} scenes and {diag['objects']} scene-object pairs.
Only {diag['scenes_with_both_roles']} scenes contain both selected errors and controls.
Repeated objects: {json.dumps(diag['repeated_objects'])}.
Full IDs are in audit.json; no new cases, labels, inference or training.

## Scene Coverage
| Scene | Selected Errors | Selected Controls | Distinct Objects |
|-------|-----------------|-------------------|------------------|
{table}

## Interpretation And Admission
The earlier 12/12 recoverable-error and 9/9 successful-control contrast is
outcome-selected, not an estimate of a population failure rate. Description
counts are not independent scene counts. Scene grouping cannot undo selection
bias, and a bootstrap on this casebook would not establish generalization.
Use these cases for deterministic regression tests only; select any evaluation
subset by outcome-independent criteria before mechanism testing. No novel
forward/loss follows from this coverage check. Mechanism admission remains
incomplete; no new selector, reranker, shared-anchor mechanism or successor.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    evidence = dict(at=datetime.now().isoformat(), analyses=inventory, ledger_rows=len(ledger),
                    live=live, gpu=gpu, trainers=trainers, sampling=diag, protected=protected)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    goal = (PIPE / "goal.json").read_text(encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical evidence; individual analysis retained |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{goal.strip()}
```
check_goal03:07:53: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical support | M95 vs baseline | Novel derived mechanism |
| Wrong-instance selection | exploratory | Frozen D1/D2 | Outcome-independent confirmation |
| Legacy terminal controls improve M95 | unsupported | M184-M190 0/7 | M191/M193 ongoing |
| Casebook generalizes | unestablished | Outcome-selected 21 descriptions | Independent sampling |

## 3. Experiment Assessment
All {len(inventory)} terminal analyses read/hash-inventoried and unchanged;
all {len(ledger)} ledger rows read. No newly terminal experiment.
| Experiment | mIoU | State | Motivation assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: Novel derived forward/loss, primary-source distinction, matched controls,
outcome-independent error subsets and scene-level uncertainty remain missing.
Casebook covers {diag['scenes']} scenes/{diag['objects']} objects; grouping
does not remove outcome selection. M191 platform matching remains unverified;
M193 parent M174 is not a full-patience control. No early efficacy claim.

## 5. Design Rationale
Q2: Audit frozen-case sampling units and paired identity before any inference.
Q3: Explicit scene coverage and repeated-object inventory strengthen limits,
not mechanism efficacy. No new literature verification claimed.
All12 constraints/11 bans checked: no FLOPs/memory, schedule, seed, graph,
parameter or deployment change; no routing/gating/pooling/numerical successor.
Scientific admission takes priority over queue depth. No candidate passes
admission, hence no exp_design, implementation, enqueue or code sync.

## 6. Next Batch
Preserve M191/M193 patience10. Continue evidence-driven diagnosis and derivation,
not batch expansion. Evidence: reports/tick_evidence_{STAMP}/audit.json and diagnostic.md.
"""
    (PIPE / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision_output = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                          "cluster_project", "route_change",
                          "Does zero waiting capacity justify successors while M191/M193 are early?",
                          "Preserve M191/M193 patience10; no unadmitted refill; record casebook scene coverage.",
                          "Scientific admission overrides depth; selected descriptions are not independent scene-level evidence.",
                          f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json"])
    print(decision_output)
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
        vals = f"{b['miou']:.10f}@{b['epoch']} | {b['acc50']} | {b['spmiou']} | {r['completed']-b['epoch']}/10" if b else "n/a | n/a | n/a | 0/10"
        live_rows.append(f"| {r['id']} | {r['config']} | server-4 | {r['gpu']} | {r['epoch']}/50 | {vals} | running |")
    queue = load(PIPE / "queue.json")
    assert not [t for ts in queue["gpu_queues"].values() for t in ts if t["status"] == "waiting"]
    report = f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})

## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal03:07:53).

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
Both trainer identities verified; early training, not terminal efficacy results.

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| - | - | - | No waiting tasks | - | - |
Queue depth:0 waiting/5 declared capacity -> NEED MORE (requires6).
SERVERS.yaml computes4 slots (requires5); both trigger scientific review.
Scientific admission overrides depth; no migration or resource-policy change.

## 4. This Tick's Actions
- Unhealthy sentinel absent; required monitor/check_goal succeeded once.
- No new terminal, launch, early-stop or crash. Repair attempts0.
- Read/hash-inventoried231 analyses;228 ledger rows, unchanged.
- Archived live log snapshots and whitelisted GPU measurements.
- Fixed-case audit:21 paired unique IDs, {diag['scenes']} scenes,
  {diag['objects']} objects; upstream hashes match; missing IDs0.
- Wrote full-goal motivation review and sampling diagnostic. No new design,
  enqueue, model/config edit, checkpoint pull or code synchronization.
- Preserve original running tasks, deployment and scheduler.

## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no scientifically unadmitted
  successor/refill. Outcome-selected descriptions do not establish generalization.
See decisions/_index.md; reviews/motivation_review_{STAMP}.md;
reports/tick_evidence_{STAMP}/audit.json and diagnostic.md.

## \u26a0 Pending User Decisions
{chr(10).join('- '+name+chr(10)+text for name,text in questions) if questions else 'No type=question records in the last24h. No user interaction.'}

Next tick:2026-09-13 04:07 Asia/Shanghai.
"""
    (PIPE / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(PIPE / n) for n in protected}
    print(json.dumps(dict(live=live, gpu=gpu, sampling=diag, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
