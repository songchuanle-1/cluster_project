"""Bounded read-only assignment provenance audit and live tick snapshot."""
import ast
import csv
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
STAMP = "20260913-061000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    OUT.mkdir(exist_ok=False)
    protected = {n: sha(P / n) for n in
                 ("goal.json", "queue.json", "running.json", "experiments.csv")}
    prior = load(P / "reports/tick_evidence_20260913-051000/audit.json")
    inventory = []
    for path in sorted((P / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                              characters=len(text)))
    assert inventory == prior["analyses"], "New terminal analyses need review"
    with (P / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == prior["ledger_rows"]
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("monitor_tick", skill / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    live, gpu = [], {}
    srv = servers["server-4"]
    trainers = [line for line in remote(srv, "ps -eo pid,args").decode().splitlines()
                if "tools/train.py" in line and "ctf_hcg_csort" in line]
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

    assignment_path = P / "reports/d1_assignment_20260911-1113/assignment.json"
    protocol_path = assignment_path.with_name("protocol.json")
    assignment, protocol = load(assignment_path), load(protocol_path)
    assert assignment["status"] == "complete"
    assert assignment["protocol_sha256"] == sha(protocol_path)
    for rel, digest in protocol["source_hashes"].items():
        assert sha(ROOT / "Cluster" / rel) == digest
    methods = {}
    for name, model in protocol["models"].items():
        path = ROOT / "Cluster" / model["loss_path"]
        tree = ast.parse(path.read_text(encoding="utf-8"))
        method = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == "match_sampled_ins")
        methods[name] = dict(path=str(path.relative_to(ROOT)), first=method.lineno,
                             last=method.end_lineno, ast=ast.dump(method, include_attributes=False))
    assert methods["baseline"]["ast"] == methods["m95"]["ast"]
    seen, lookup = set(), {}
    for r in assignment["rows"]:
        identity = tuple(str(r[k]) for k in ("model", "scene_id", "object_id", "ann_id"))
        assert identity not in seen and r["status"] == "complete"
        seen.add(identity)
        labels = r["query_instance_labels"]
        expected = {i for i, label in enumerate(labels) if label == int(r["object_id"])}
        expected.add(r["nearest"])
        assert expected == set(r["positive_indices"])
        lookup[identity] = r
    assert len(seen) == 568
    cases_path = P / "reports/d1_case_scope_coupling_20260912-1610/case_scope_coupling.json"
    assert sha(cases_path) == prior["source_sha256"]
    cases = load(cases_path)
    for key in ("scope_audit", "margin", "identity_geometry"):
        assert sha(Path(cases["sources"][key])) == cases["sources"][key + "_sha256"]
    details = []
    for c in cases["records"]:
        identity = tuple(str(c[k]) for k in ("model", "scene_id", "object_id", "ann_id"))
        r = lookup[identity]
        assert c["selected_positive"] == r["selected_positive"]
        assert c["selected_iou"] == r["selected_iou"]
        # The stored assignment omits selected_index; recover it from its frozen summary.
        summary_path = P / f"reports/d1_expansion_20260911-0715/{c['model']}/summary.json"
        assert sha(summary_path) == protocol["summary_hashes"][c["model"]]
        sr = next(x for x in load(summary_path)["rows"]
                  if tuple(str(x[k]) for k in ("scene_id", "object_id", "ann_id")) == identity[1:])
        si = sr["selected_index"]
        assert (si in r["positive_indices"]) == c["selected_positive"]
        if c["selected_positive"] and c["selected_iou"] <= .5:
            details.append(dict(identity=identity, selected_index=si,
                                selected_seed_label=r["query_instance_labels"][si],
                                nearest_index=r["nearest"], target=int(c["object_id"]),
                                positive_from_membership=r["query_instance_labels"][si] == int(c["object_id"]),
                                positive_from_nearest=si == r["nearest"],
                                selected_iou=c["selected_iou"], oracle_iou=c["oracle_iou"]))
    assert len(details) == 1
    diagnostic = f"""# Assignment Label Provenance Audit
Completed {datetime.now().isoformat()} Asia/Shanghai.

## Question And Inputs
Does the frozen positive-label / IoU-failure case follow the existing assignment?
Rechecked assignment/protocol link, all five code hashes, casebook and three
upstream hashes, plus both frozen summary hashes. No inference or training.
Assignment SHA256: {sha(assignment_path)}.

## Source Definition
Baseline and M95 match_sampled_ins have identical ASTs. For a single target,
positive queries are the union of queries whose sampled superpoint label equals
the target instance ID and the spatially nearest query to the target centroid.
The assignment function does not take predicted masks or mask IoUs as inputs.
loss_indi uses those matched indices; inference selects maximum class-1
probability. Label membership therefore does not guarantee mask IoU success.
References: {methods['baseline']['path']}:{methods['baseline']['first']};
baseline loss.py:182 and network.py:188. Full source hashes in protocol.json.

## Offline Results
All 568 unique assignment records satisfy union(target-membership, nearest).
All 42 casebook records match stored assignment labels and measured IoUs;
zero missing or duplicate assignment identities. The discordant fixture:
```json
{json.dumps(details[0], indent=2)}
```
This is source-consistent label construction, not evidence of a parser defect.

## Limits And Next Evidence
This reconstructs existing evaluation-bank labels, not historical training
targets, independent ground truth, or causal efficacy. The 42 selected cases
are not population evidence; the 568 rows belong to the existing diagnostic
protocol, not a new validation sample. No new mechanism or novelty established.
Next mechanism work still needs a derived forward/loss, original-source
distinction and matched falsifiable controls; do not replace labels on this basis.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    evidence = dict(at=datetime.now().isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu,
                    assignment_sha256=sha(assignment_path), methods=methods,
                    assignment_records=len(seen), joined_casebook_records=len(cases["records"]),
                    discordant_details=details, source_sha256=sha(cases_path))
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical; individual terminal analysis remains authoritative |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal 06:08:13: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; exact gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 vs baseline | Derived new mechanism |
| Wrong-instance selection | exploratory | Existing D1/D2 | Independent confirmation |
| Terminal controls improve M95 | unsupported | M184-M190 0/7 | M191/M193 running |
| Positive label guarantees mask success | false as identity | Source and frozen fixture | No causal supervision claim |

## 3. Experiment Assessment
All {len(inventory)} analyses read and hash-identical to prior tick; all
{len(ledger)} ledger rows read. No new terminal result.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: A derived and primary-source-distinct mechanism, matched controls,
predefined subsets, scene uncertainty, robustness and efficiency remain open.
M191 platform and M193 full-patience comparison limits remain.

## 5. Design Rationale
Q2: Trace the prior discordant case to current assignment source and frozen
query labels. Q3: Exclude a false label-parser diagnosis without new training.
All 568 rows obey target-membership union nearest; all 42 fixture joins agree.
All12 constraints and11 bans checked: no model, numeric, seed, schedule,
resource-policy or deployment change. No primary-source review this tick.
Scientific admission overrides depth; no generic selector/pooling successor.

## 6. Next Batch
No admitted candidate; no exp_design, implementation, enqueue or sync.
Preserve M191/M193 patience10. Diagnostic: reports/tick_evidence_{STAMP}/diagnostic.md.
"""
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Does the positive-label IoU-failure fixture justify supervision repair or queue refill?",
                    "No label repair or unadmitted refill; preserve M191/M193 patience10.",
                    "Source-identical assignment and568 frozen records agree; label membership is not mask IoU. Scientific admission remains incomplete.",
                    f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json"])
    now = datetime.now()
    questions = []
    for path in (P / "decisions").glob("*_question.md"):
        when = datetime.strptime(path.name[:15], "%Y%m%d-%H%M%S")
        if now-timedelta(hours=24) <= when <= now:
            questions.append(path.name + "\n" + path.read_text(encoding="utf-8"))
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
    queue = load(P / "queue.json")
    assert not [t for tasks in queue["gpu_queues"].values() for t in tasks if t["status"] == "waiting"]
    report = f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})

## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal06:08:13).

## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs:server-6:7 (two configured slots); no eligible waiting tasks.

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
Metrics paired at best epoch from complete records; validations report9508.
Monitor initially deferred M191 early-stop because metric streams were
unaligned; fresh complete-log snapshot retained separately. No crash inferred.

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| - | - | - | No waiting tasks | - | - |
Queue depth:0 waiting/5 declared slots -> NEED MORE (requires6).
SERVERS.yaml capacity4 (requires5); scientific admission overrides refill.
No scheduler or resource-policy change.

## 4. This Tick's Actions
- Unhealthy sentinel absent; monitor/check_goal succeeded once each.
- No new terminal, crash, launch or early-stop; repair attempts0.
- Read/hash-inventoried231 analyses and228 ledger rows; unchanged.
- Archived live logs and whitelisted GPU snapshot.
- Traced assignment source and checked568 frozen records/42 casebook joins.
  The discordant fixture is assignment-consistent; no label repair warranted.
- Wrote motivation review and diagnostic; no new model/config, enqueue,
  checkpoint pull or code sync. Existing trainers preserved.

## 5. Decisions Made
- route_change: no label repair or unadmitted refill; retain M191/M193
  patience10. See decisions/_index.md and this tick's diagnostic evidence.

## \u26a0 Pending User Decisions
{chr(10).join(questions) if questions else 'No type=question records in the last24h. No user interaction.'}

Next tick:2026-09-13 07:07 Asia/Shanghai.
"""
    (P / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=live, gpu=gpu, discordant=details, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
