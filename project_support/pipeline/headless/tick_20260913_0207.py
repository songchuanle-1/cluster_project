"""Evidence-gated M190 closure and preserved-control tick snapshot."""
import copy
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
PIPE = ROOT / "pipeline"
SKILL = ROOT.parent / ".claude/skills/songcl_research_pipeline"
STAMP = "20260913-021200"
EID = "M190-CTF-HCG-CSORT-MQTD-TR"
BASELINE = 0.4894491136074066
CHAMPION = 0.5024607181549072


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location("monitor_tick", SKILL / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    exp = load(PIPE / "experiments" / f"{EID}.json")
    base = Path(exp["config"]).stem
    rel = f"{base}/20260912_050805/20260912_050805.log"
    remote_log = srv["work_dir"] + "/" + rel
    data = remote(srv, "cat " + shlex.quote(remote_log))
    digest = remote(srv, "sha256sum " + shlex.quote(remote_log)).decode().split()[0]
    log = ROOT / "Checkpoints/server-4" / rel
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_bytes(data)
    assert sha(log) == digest
    text = data.decode("utf-8")
    rows = parse_log(text)
    assert [r["epoch"] for r in rows] == list(range(1, 25))
    assert re.findall(r"Evaluate referring segmentation:\s*(\d+)", text) == ["9508"] * 24
    best = max(rows, key=lambda r: r["miou"])
    assert best == dict(epoch=14, miou=0.4890006184577942, acc50=0.542, spmiou=0.454)
    assert text.rstrip().endswith("Early stopping at epoch 24: no improvement for 10 epochs (best=0.4890)")
    assert all(r["miou"] < best["miou"] for r in rows[14:])
    start, end = [text.splitlines()[i].split(" - ")[0] for i in (0, -1)]
    duration = datetime.strptime(end, "%Y-%m-%d %H:%M:%S,%f") - datetime.strptime(start, "%Y-%m-%d %H:%M:%S,%f")
    parents = load(PIPE / "reports/control_provenance_20260912-201000/audit.json")["parents"]
    parent = next(p for p in parents if p["id"].startswith("M178-"))
    assert sha(ROOT / parent["local_log"]) == parent["sha256"]
    parent_best = parent["best"]["miou"]
    common_delta = best["miou"] - max(r["miou"] for r in parent["metrics"][:24])
    analysis = PIPE / f"analyses/{EID}_done_earlystop_{STAMP}.md"
    assert not analysis.exists()
    analysis_text = f"""# Experiment Result Analysis - cluster_project
Experiment: {EID} | State: done_earlystop

## 1. Basic Info
- ID: {EID}
- Config: {exp['config']}
- Server: server-4 | GPU: 0
- Started (logger): {start}; finished (logger): {end}; duration: {duration}.
- Registry launch: {exp['launched']}. State: done_earlystop.
- Archive: {log.relative_to(ROOT)}; remote/local SHA256: {digest}.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | {best['miou']} | 14 |
| Acc@50 | {best['acc50']} | 14 |
| spmIOU | {best['spmiou']} | 14 |

## 3. Convergence Summary
- Best first reached at14; epochs15-24 are ten strictly lower validations.
- Final epoch24: mIoU={rows[-1]['miou']}, Acc@50={rows[-1]['acc50']}, spmIOU={rows[-1]['spmiou']}.
- All24 contiguous validations report9508 expressions.
- Explicit trainer early-stop marker; normal stop, not monitor kill or crash.

## 4. Comparison
- Baseline {BASELINE}: delta={best['miou']-BASELINE:+.10f}.
- M95 {CHAMPION}: delta={best['miou']-CHAMPION:+.10f}.
- M178 parent {parent_best}: delta={best['miou']-parent_best:+.10f}.
- Common epochs1-24 best delta={common_delta:+.10f}; M178 full run34 epochs.
- M1909.845647916G <=10G; parent >10G, historical comparison only.
- M190 changes BOTH intermediate recurrence and real-cluster padding.
  Neither full-run nor common-horizon difference isolates recurrence.
  Single seed, unverified environment matching and validation reuse remain.
  Counts do not establish identical expression identities/order; no paired
  scene uncertainty, independent confirmation, or test-set claim.

## 5. Conclusion
- Failed to improve baseline, M95 or parent; close without retry or successor.
- Seven completed legacy terminal controls M184-M190 now0/7 above M95.
  Different topologies are not independent seed replications.
- Preserve M191 GPU1 and original M193 now running on GPU0.

## 6. Crash Info
- Not crashed; model repair attempts0. Checkpoints remain remote.
"""

    def decision(kind, question, action, basis, evidence):
        print(run([monitor.bash_executable(), str(SKILL / "log_decision.sh"),
                   "cluster_project", kind, question, action, basis, evidence]))

    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        queue = monitor.load_queue(str(ROOT))
        before = copy.deepcopy(monitor.load_running(str(ROOT)))
        original = monitor.load_experiment(str(ROOT), EID)
        assert original["status"] == "running"
        assert before["server-4"] == {"1": "M191-CTF-HCG-CSORT-MQSD-TR", "0": "M193-CTF-HCG-CSORT-MQHC-TR"}
        tasks = [t for t in queue["gpu_queues"]["server-4"] if t["id"] == EID]
        assert len(tasks) == 1
        expected = copy.deepcopy(queue)
        expected["gpu_queues"]["server-4"] = [t for t in expected["gpu_queues"]["server-4"] if t["id"] != EID]
        processes = monitor.find_running_processes(srv["host"], srv["user"], srv["remote_code_root"])
        assert not any(Path(cfg).stem == base for cfg in processes)
        with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
            assert not any(r["id"] == EID for r in csv.DictReader(f))
        decision("other", "M190 ended normally at24 while GPU0 already belongs to M193; reconcile?",
                 "Archive M190 done_earlystop; preserve M193 GPU0 and M191 GPU1.",
                 "24 contiguous validations; best .4890006185 at14; ten stale; absent process; matching SHA256.", str(analysis))
        analysis.write_text(analysis_text, encoding="utf-8")
        monitor.pull_log = lambda *args: str(log)
        monitor.write_analysis_md = lambda *args: str(analysis)
        events = []
        monitor.finalize_task(str(ROOT), queue, "server-4", srv["host"], srv["user"],
                              tasks[0], base, "done_earlystop", best["miou"], "24/50", "0", remote_log, events)
        final_exp = monitor.load_experiment(str(ROOT), EID)
        assert final_exp["history"][:len(original["history"])] == original["history"]
        final_exp.update(best_miou_exact=best["miou"], best_epoch=14, best_acc50=best["acc50"],
                         best_spmiou=best["spmiou"], validations_completed=24, no_improve_final=10,
                         ended_at_remote=end, log_sha256=digest, analysis=str(analysis))
        monitor.save_experiment(str(ROOT), final_exp)
        dw = monitor.load_deathwatch(str(ROOT))
        dw.get("server-4", {}).pop(base, None)
        monitor.save_deathwatch(str(ROOT), dw)
        assert monitor.load_running(str(ROOT)) == before
        assert monitor.load_queue(str(ROOT)) == expected
        monitor.daily_report(str(ROOT), events)
    finally:
        lock.close()

    protected = {n: sha(PIPE / n) for n in ("goal.json", "queue.json", "running.json", "experiments.csv")}
    out = PIPE / f"reports/tick_evidence_{STAMP}"
    out.mkdir(exist_ok=False)
    inventory = []
    for p in sorted((PIPE / "analyses").glob("*.md")):
        content = p.read_text(encoding="utf-8")
        inventory.append(dict(path=str(p.relative_to(ROOT)), sha256=sha(p), characters=len(content)))
    prior = load(PIPE / "reports/tick_evidence_20260913-011200/audit.json")
    assert [a for a in inventory if a["path"] != str(analysis.relative_to(ROOT))] == prior["analyses"]
    with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == prior["ledger_rows"] + 1
    live = []
    processes = remote(srv, "ps -eo pid,args").decode()
    trainers = [s for s in processes.splitlines() if "tools/train.py" in s and "ctf_hcg_csort" in s]
    for prefix in ("M191", "M193"):
        exp = load(next((PIPE / "experiments").glob(prefix + "-*.json")))
        assert exp["status"] == "running"
        base = Path(exp["config"]).stem
        assert any(base in p for p in trainers)
        path = monitor.find_latest_log(base, srv["work_dir"], srv["host"], srv["user"])
        assert path
        snapshot = out / f"{prefix}_live.log"
        snapshot.write_bytes(remote(srv, "cat " + shlex.quote(path)))
        content = snapshot.read_text(encoding="utf-8")
        assert not re.search(r"Traceback|Early stopping at epoch", content)
        metrics = [r for r in parse_log(content) if {"epoch", "miou", "acc50", "spmiou"} <= r.keys()]
        assert [r["epoch"] for r in metrics] == list(range(1, len(metrics) + 1))
        counts = re.findall(r"Evaluate referring segmentation:\s*(\d+)", content)
        assert len(counts) >= len(metrics) and set(counts) <= {"9508"}
        live.append(dict(id=exp["id"], config=exp["config"], gpu=exp["gpu"], metrics=metrics,
                         epoch=(re.findall(r"Epoch \[(\d+)/50\]", content) or ["initializing"])[-1],
                         best=max(metrics, key=lambda r: r["miou"]) if metrics else None,
                         completed=len(metrics), remote_log=path, log_sha256=sha(snapshot)))
    gpu = {}
    for name in ("server-4", "server-6"):
        s = servers[name]
        ids = ",".join(map(str, s["allowed_gpus"]))
        gpu[name] = remote(s, f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()
    evidence = dict(at=datetime.now().isoformat(), terminal=dict(id=EID, best=best, metrics=rows,
                    log_sha256=digest, parent_delta=best["miou"]-parent_best, common24_best_delta=common_delta),
                    live=live, gpu=gpu, trainers=trainers, analyses=inventory, ledger_rows=len(ledger), protected=protected)
    (out / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical evidence; retain individual route analysis |" for r in ledger)
    goal = (PIPE / "goal.json").read_text(encoding="utf-8")
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{goal.strip()}
```
check_goal02:08:09: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact champion {CHAMPION}; exact gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context gain | historical support | M95 above baseline | Novel mechanism |
| Wrong-instance selection | exploratory | Frozen D1/D2 | Independent confirmation |
| Terminal controls exceed M95 | unsupported | M184-M1900/7 | M191/M193 live |
| Shared-anchor fixed errors | unsupported | Prior0/21 applicability | No reopening evidence |

## 3. Experiment Assessment
All{len(inventory)} analyses read/hash-inventoried; prior230 unchanged.
All{len(ledger)} ledger rows read. Latest M190 exact metrics are in its analysis.
| Experiment | mIoU | State | Motivation assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: Missing novel derived forward/loss, verified primary-source distinction,
matched controls, scene uncertainty and independent validation.
M190 common24 best delta{common_delta:+.10f} does not remove padding confounding.
M191 platform matching and M193 parent's shortened patience remain limitations.

## 5. Design Rationale
Q2: Close M190 from exact paired metrics, full-denominator logs and run identity.
Q3: Adds one completed legacy control; no new efficacy or novelty inference.
All12 constraints and11 bans reviewed. C1-8: no numerical, graph, seed, schedule,
resource or deployment change. C9-12: scientific admission still incomplete.
No candidate is proposed, renamed, or subjected to tuning. Scientific admission
overrides waiting0/declared5 (configured4). No successor to failed old controls.

## 6. Next Batch
No admitted design, implementation, enqueue or model synchronization.
Monitor launched original M193 GPU0 after verifying commit05335bdd.
Preserve live M191/M193 and patience10. Evidence: reports/tick_evidence_{STAMP}/audit.json.
"""
    (PIPE / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision("route_change", "M190 best .4890006185 leaves seven controls below M95 and0/5 waiting; refill?",
             "Close M190 without successor; preserve M191/M193 patience10; admit no new mechanism.",
             "Scientific admission overrides depth; M190-M178 is confounded by padding; no derived novel mechanism.",
             f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json")
    now = datetime.now()
    questions = []
    for p in (PIPE / "decisions").glob("*_question.md"):
        when = datetime.strptime(p.name[:15], "%Y%m%d-%H%M%S")
        if now - timedelta(hours=24) <= when <= now:
            questions.append((p.name, p.read_text(encoding="utf-8")))
    gpu_rows = []
    for name, lines in gpu.items():
        for line in lines.splitlines():
            index, util, used, total = [v.strip() for v in line.split(",")]
            process = next((r["id"] for r in live if name == "server-4" and str(r["gpu"]) == index), "IDLE")
            gpu_rows.append(f"| {name} | {index} | {util}% | {used}/{total} MiB | {process} |")
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
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal02:08:09).

## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs:server-6:7 (two configured slots); no eligible waiting tasks.

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
Metrics paired at best epoch. M190 is terminal, not a third running task.
All completed live validations report9508 expressions; both trainers verified.

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| - | - | - | No waiting tasks | - | - |
Queue depth:0 waiting/5 declared capacity -> NEED MORE (requires6).
SERVERS.yaml computes4 slots (requires5); both trigger scientific review.
Scientific admission overrides queue depth; no migration or filler variants.

## 4. This Tick's Actions
- Unhealthy sentinel absent; required monitor and check_goal completed once.
- Monitor dispatched original M193 GPU0; local/remote commit05335bdd matched.
- Verified M190 normal trainer stop24/best14; exact best .4890006184577942.
- Archived hash-matched log, terminal analysis, registry and ledger; preserved
  history, M193 GPU0/M191 GPU1 identities and queue order; cleared M190 deathwatch.
- Read/hash-inventoried{len(inventory)} analyses and loaded{len(ledger)} ledger rows.
- M190-M178 full/common24 best delta{common_delta:+.10f}; padding confounded.
- Full-goal motivation review written. No new mechanism, design, model/config
  edit, enqueue, code synchronization, checkpoint pull or crash repair.

## 5. Decisions Made
- queue_push: original M193 launched on server-4 GPU0.
- other: finalize only M190; preserve M193 and M191 running mappings.
- route_change: no M190 successor or unadmitted refill; preserve patience10.
See decisions/_index.md; reviews/motivation_review_{STAMP}.md;
reports/tick_evidence_{STAMP}/audit.json.

## \u26a0 Pending User Decisions
{chr(10).join('- '+name+chr(10)+text for name,text in questions) if questions else 'No type=question records in the last24h. No user interaction.'}

Next tick:2026-09-13 03:07 Asia/Shanghai.
"""
    (PIPE / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(PIPE / n) for n in protected}
    print(json.dumps(dict(terminal=evidence["terminal"], live=live, gpu=gpu,
                         analyses=len(inventory), ledger_rows=len(ledger), questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
