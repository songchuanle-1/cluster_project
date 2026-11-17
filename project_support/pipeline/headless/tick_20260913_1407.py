"""Snapshot active jobs and audit leave-one-scene-out frozen-bank sensitivity."""
import csv
from collections import defaultdict
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
STAMP = "20260913-141000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    prior = load(P / "reports/tick_evidence_20260913-121000/audit.json")
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
    OUT.mkdir(exist_ok=False)
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("monitor_tick", skill / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    trainers = [x for x in remote(srv, "ps -eo pid,args").decode().splitlines()
                if "tools/train.py" in x and "ctf_hcg_csort" in x]
    live, gpu, apps = [], {}, {}
    for prefix in ("M191", "M193"):
        exp = load(next((P / "experiments").glob(prefix + "-*.json")))
        assert exp["status"] == "running"
        base = Path(exp["config"]).stem
        assert any(base in x for x in trainers)
        log = monitor.find_latest_log(base, srv["work_dir"], srv["host"], srv["user"])
        assert log
        snapshot = OUT / f"{prefix}_live.log"
        snapshot.write_bytes(remote(srv, "cat " + shlex.quote(log)))
        text = snapshot.read_text(encoding="utf-8")
        assert not re.search(r"Traceback|Early stopping at epoch", text)
        parsed = parse_log(text)
        rows = [r for r in parsed if {"acc50", "spmiou"} <= r.keys()]
        assert len(rows) == len(parsed)
        assert [r["epoch"] for r in rows] == list(range(1, len(rows) + 1))
        counts = re.findall(r"Evaluate referring segmentation:\s*(\d+)", text)
        assert len(counts) >= len(rows) and set(counts) == {"9508"}
        live.append(dict(id=exp["id"], config=exp["config"], gpu=exp["gpu"],
                         epoch=int(re.findall(r"Epoch \[(\d+)/50\]", text)[-1]),
                         completed=len(rows), best=max(rows, key=lambda r: r["miou"]),
                         metrics=rows, remote_log=log, log_sha256=sha(snapshot)))
    for name in ("server-4", "server-6"):
        s = servers[name]
        ids = ",".join(map(str, s["allowed_gpus"]))
        gpu[name] = remote(s, f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()
        apps[name] = remote(s, f"nvidia-smi -i {ids} --query-compute-apps=pid,process_name,used_memory --format=csv,noheader").decode().strip()
    ap = P / "reports/d1_assignment_20260911-1113/assignment.json"
    pp = ap.with_name("protocol.json")
    protocol = load(pp)
    assert sha(ap) == prior["assignment_sha256"]
    assert sha(pp) == prior["protocol_sha256"] == load(ap)["protocol_sha256"]
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
    scenes = defaultdict(list)
    for key, b in banks["baseline"].items():
        m = banks["m95"][key]
        scenes[key[0]].append(dict(id=list(key),
                                  success_delta=int(m["selected_iou"] > .5)-int(b["selected_iou"] > .5),
                                  iou_delta=m["selected_iou"]-b["selected_iou"]))
    assert len(scenes) == 71 and all(len(v) == 4 for v in scenes.values())
    total_success = sum(r["success_delta"] for rows in scenes.values() for r in rows)
    total_iou = sum(r["iou_delta"] for rows in scenes.values() for r in rows)
    omissions = [dict(omitted_scene=s, n=280,
                      success_delta=(total_success-sum(r["success_delta"] for r in rows))/280,
                      iou_delta=(total_iou-sum(r["iou_delta"] for r in rows))/280)
                 for s, rows in sorted(scenes.items())]
    result = dict(pairs=284, scenes=71, full_success_delta=total_success/284,
                  full_iou_delta=total_iou/284,
                  loso_success_range=[min(r["success_delta"] for r in omissions), max(r["success_delta"] for r in omissions)],
                  loso_iou_range=[min(r["iou_delta"] for r in omissions), max(r["iou_delta"] for r in omissions)],
                  nonnegative_success_omissions=sum(r["success_delta"] >= 0 for r in omissions),
                  nonnegative_iou_omissions=sum(r["iou_delta"] >= 0 for r in omissions))
    evidence = dict(at=datetime.now().isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu, apps=apps,
                    assignment_sha256=sha(ap), protocol_sha256=sha(pp),
                    summary_hashes=protocol["summary_hashes"], result=result,
                    manifest=scenes, omissions=omissions)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    diagnostic = f"""# Frozen Bank Leave-One-Scene-Out Sensitivity
## Protocol
All 284 paired descriptions, 71 scenes with four descriptions each; zero missing
or duplicate paired identities. Remove each whole scene once; calculate M95
minus baseline mean selected-IoU and success-rate differences on the remaining
280 descriptions. Success threshold strictly >.5 inherited, not tuned.
Assignment, protocol, five code files and both summaries hash-verified.
No resampling, new sampling, training, or checkpoint evaluation.

## Results
```json
{json.dumps(result, indent=2)}
```
All 71 omissions and the paired 284-description manifest are in audit.json.

## Limits And Decision
This tests whether one scene alone reverses the sign in this selected bank.
The ranges are sensitivity ranges, NOT confidence intervals. They cannot correct
selection bias, represent full validation, prove statistical significance,
establish causality, or support independent generalization. The two models have
different candidate masks, so neither contrast isolates selector quality.
No scientifically admitted new mechanism follows. Preserve running controls.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical; individual terminal analysis authoritative |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}
## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal14:08:08: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; gap .0075392818450928.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 versus baseline | New derived mechanism |
| Wrong-instance selection | exploratory | Frozen D1/D2 | Causal intervention |
| Terminal controls exceed champion | unsupported | M184-M190 0/7 | M191/M193 live |
| A single scene explains bank contrast | sensitivity audited | This tick diagnostic | No population inference |
## 3. Experiment Assessment
Read all {len(inventory)} analyses and {len(ledger)} ledger rows; unchanged hashes.
No new terminal requiring duplicate analysis.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}
## 4. Gap Analysis
Q1: Derivation, primary-source-distinct novelty, matched controls, predefined
error subsets, scene uncertainty, robustness and efficiency remain incomplete.
M191 parent platform differs; M193 parent patience is incomplete. Removing
one scene from an outcome-selected bank cannot repair validation selection bias.
## 5. Design Rationale
Q2: Test a bounded scene-sensitivity question on frozen artifacts without GPU use.
Q3: Quantify whether one scene determines the bank contrast's sign.
All12 constraints/11 bans checked: no new forward/loss proposed, no numerical
sweep, renamed selector or successor admitted; scientific admission overrides
depth. No fresh literature verification or novelty claim this tick.
## 6. Next Batch
No qualified candidate; no exp_design, training implementation, enqueue or sync.
Preserve M191/M193 patience10 and deployments; no global pause.
Evidence: reports/tick_evidence_{STAMP}/diagnostic.md.
"""
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Does leave-one-scene-out bank sensitivity justify new training at zero waiting?",
                    "Preserve M191/M193 patience10; no unadmitted refill; recover missing prior-tick reporting in current report.",
                    "Sensitivity is not causal or generalization evidence; scientific admission remains incomplete; 13:07 Codex failed but fallback reconciled.",
                    f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json; pipeline/headless/tick_20260913-130700.log"])
    now = datetime.now()
    questions = []
    for path in (P / "decisions").glob("*_question.md"):
        when = datetime.strptime(path.name[:15], "%Y%m%d-%H%M%S")
        if now-timedelta(hours=24) <= when <= now:
            questions.append(path.name + "\n" + path.read_text(encoding="utf-8"))
    gpu_rows, live_rows = [], []
    for name, lines in gpu.items():
        for line in lines.splitlines():
            idx, util, used, total = [x.strip() for x in line.split(",")]
            proc = next((r["id"] for r in live if name == "server-4" and str(r["gpu"]) == idx),
                        "External occupancy; no cluster trainer" if int(used) >= 1024 else "IDLE")
            gpu_rows.append(f"| {name} | {idx} | {util}% | {used}/{total} MiB | {proc} |")
    for r in live:
        b = r["best"]
        live_rows.append(f"| {r['id']} | {r['config']} | server-4 | {r['gpu']} | {r['epoch']}/50 | {b['miou']:.10f}@{b['epoch']} | {b['acc50']} | {b['spmiou']} | {r['completed']-b['epoch']}/10 | running |")
    assert not [t for tasks in load(P / "queue.json")["gpu_queues"].values() for t in tasks if t["status"] == "waiting"]
    report = f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})
## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal14:08:08).
## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Physical occupancy and compute-process evidence retained in audit.json.
Free GPUs: see per-GPU utilization/memory and compute-process snapshot; no eligible waiting task.
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
## 4. This Tick's Actions
- Health sentinel absent; monitor14:07 and check_goal14:08 succeeded once each.
- Recovered reporting gap:13:07 Codex stream failed; fallback monitor succeeded.
  No13:07 full report/review exists; this is current evidence, not a backdated tick.
- No new terminal, crash, launch or early-stop; training repair attempts0.
- Read/hash-inventoried{len(inventory)} analyses and{len(ledger)} ledger rows; unchanged.
- Read ten full decisions, both admitted designs, recent designs and bugfixes.
- Archived live logs and whitelisted GPU/compute-process snapshot.
- Completed paired scene-deletion sensitivity audit; no new efficacy claim.
- No model/config edits, checkpoint pull, enqueue, sync or scheduler mutation.
## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no unadmitted refill or successors.
  See decisions/_index.md and this tick's review/audit.
## \u26a0 Pending User Decisions
{chr(10).join(questions) if questions else 'No type=question records in last24h. No user interaction.'}

Next tick:2026-09-13 15:07 Asia/Shanghai.
"""
    (P / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=[{k:v for k,v in r.items() if k != "metrics"} for r in live],
                          gpu=gpu, apps=apps, result=result, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
