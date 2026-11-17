"""Archive the verified M189 terminal and record the current tick."""
import copy
import csv
from datetime import datetime, timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess

import yaml
from close_m185_20260912 import parse_log, run

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
SKILL = ROOT.parent / ".claude/skills/songcl_research_pipeline"
STAMP = "20260913-001200"
EID = "M189-CTF-HCG-CSORT-MQBC-TR"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqbc_tr"
REL = f"{BASE}/20260912_030730/20260912_030730.log"
BASELINE = 0.4894491136074066
CHAMPION = 0.5024607181549072


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location("monitor_tick", SKILL / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    target = f"{srv['user']}@{srv['host']}"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", target]
    remote_log = f"{srv['work_dir']}/{REL}"
    log = ROOT / "Checkpoints/server-4" / REL
    log.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["scp", "-o", "BatchMode=yes", f"{target}:{remote_log}", str(log)],
                   check=True, capture_output=True, timeout=120)
    digest = run(ssh + [f"sha256sum {remote_log}"]).split()[0]
    assert sha(log) == digest == "88dd6356aecbaa571640a369733596c475ea42a5dd8fa09ded69c7f582b73ed3"
    text = log.read_text(encoding="utf-8")
    rows = parse_log(text)
    assert [r["epoch"] for r in rows] == list(range(1, 30))
    assert re.findall(r"Evaluate referring segmentation:\s*(\d+)", text) == ["9508"] * 29
    best = max(rows, key=lambda r: r["miou"])
    assert best["epoch"] == 19 and best["miou"] == 0.49086183309555054
    assert text.rstrip().endswith("Early stopping at epoch 29: no improvement for 10 epochs (best=0.4909)")
    end = text.splitlines()[-1].split(" - ")[0]
    analysis = PIPE / f"analyses/{EID}_done_earlystop_{STAMP}.md"
    analysis_text = f"""================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: {EID} | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: {EID}
- Config: configs/Quard/ctf_hcg_csort_mqbc_tr/{BASE}.yaml
- Server: server-4 | GPU: 1
- Started (logger): {text.splitlines()[0].split(' - ')[0]}
- Finished (logger): {end}; local registry launch: 2026-09-12T03:07:33.
- State: done_earlystop. Explicit trainer marker; no surviving matching process.
- Archive: {log.relative_to(ROOT)}; SHA256 remote/local: {digest}.
- Duration: approximately 20h53m from logger start to finish.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | {best['miou']} | 19 |
| Acc@50 | {best['acc50']} | 19 |
| spmIOU | {best['spmiou']} | 19 |

## 3. Convergence Summary
- Best first reached at19; ten subsequent validations did not improve.
- Final epoch29: mIoU={rows[-1]['miou']}, Acc@50={rows[-1]['acc50']}, spmIOU={rows[-1]['spmiou']}.
- All29 contiguous validations report9508 expressions. No crash or monitor kill.
- Initial improvement followed by a fluctuating lower plateau.

## 4. Comparison
- Baseline {BASELINE}: delta={best['miou']-BASELINE:+.10f}.
- M95 {CHAMPION}: delta={best['miou']-CHAMPION:+.10f}.
- M177 parent .4962787926197052@17/27: delta={best['miou']-.4962787926197052:+.10f}.
- M1899.845844524G is eligible under10G; parent exceeds10G and is historical only.
- Source audit reports recurrence-only change, unchanged numerical YAML.
  Single seed, unverified environment matching and unequal realized horizons
  prevent a causal or statistically reliable conclusion.
- Prior common27-epoch comparison gives the same best delta; parent raw log
  provenance: reports/control_provenance_20260912-201000/audit.json.

## 5. Conclusion
- Failed to improve champion or parent; small +.0014127 vs baseline is below
  the .002 branch threshold. Close without retry or successor.
- Six completed preserved terminal controls M184-M189 now have0/6 above M95.
  This supplies legacy evidence, not an independently novel mechanism.
- Preserve M190/M191 trainers and remaining M193 FIFO. No test-set claim.

## 6. Crash Info
- Not crashed; repair attempts0. Checkpoints remain remote.
================================================================================
"""
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None, "Another pipeline writer is active"
    try:
        queue = monitor.load_queue(str(ROOT))
        before = copy.deepcopy(monitor.load_running(str(ROOT)))
        original = monitor.load_experiment(str(ROOT), EID)
        assert original["status"] == "running"
        assert before["server-4"]["1"] == "M191-CTF-HCG-CSORT-MQSD-TR"
        tasks = [t for t in queue["gpu_queues"]["server-4"] if t["id"] == EID]
        assert len(tasks) == 1
        expected = copy.deepcopy(queue)
        expected["gpu_queues"]["server-4"] = [t for t in expected["gpu_queues"]["server-4"] if t["id"] != EID]
        processes = monitor.find_running_processes(srv["host"], srv["user"], srv["remote_code_root"])
        assert not any(Path(cfg).stem == BASE for cfg in processes)
        with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as stream:
            assert not any(r["id"] == EID for r in csv.DictReader(stream))
        print(run([monitor.bash_executable(), str(SKILL / "log_decision.sh"), "cluster_project", "other",
                   "M189 ended normally at29 while GPU1 already belongs to M191; reconcile?",
                   "Archive M189 done_earlystop; preserve M191 GPU1 and M190 GPU0 mappings.",
                   "29 contiguous validations; best .4908618331 at19; ten stale; absent process; matching SHA256.",
                   str(analysis)]))
        analysis.write_text(analysis_text, encoding="utf-8")
        monitor.pull_log = lambda *args: str(log)
        monitor.write_analysis_md = lambda *args: str(analysis)
        events = []
        monitor.finalize_task(str(ROOT), queue, "server-4", srv["host"], srv["user"],
                              tasks[0], BASE, "done_earlystop", best["miou"], "29/50",
                              "1", remote_log, events)
        exp = monitor.load_experiment(str(ROOT), EID)
        assert exp["history"][:len(original["history"])] == original["history"]
        exp.update(best_miou_exact=best["miou"], best_epoch=19, best_acc50=best["acc50"],
                   best_spmiou=best["spmiou"], validations_completed=29, no_improve_final=10,
                   ended_at_remote=end, log_sha256=digest, analysis=str(analysis))
        monitor.save_experiment(str(ROOT), exp)
        dw = monitor.load_deathwatch(str(ROOT))
        dw.get("server-4", {}).pop(BASE, None)
        monitor.save_deathwatch(str(ROOT), dw)
        assert monitor.load_running(str(ROOT)) == before
        assert monitor.load_queue(str(ROOT)) == expected
        monitor.daily_report(str(ROOT), events)
    finally:
        lock.close()
    protected = {n: sha(PIPE / n) for n in ("goal.json", "queue.json", "running.json", "experiments.csv")}
    inventory = []
    for path in sorted((PIPE / "analyses").glob("*.md")):
        content = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), characters=len(content)))
    with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    out = PIPE / f"reports/tick_evidence_{STAMP}"
    out.mkdir(exist_ok=False)
    live = []
    for prefix in ("M190", "M191"):
        exp = load(next((PIPE / "experiments").glob(f"{prefix}-*.json")))
        base = Path(exp["config"]).stem
        remote = monitor.find_latest_log(base, srv["work_dir"], srv["host"], srv["user"])
        assert remote
        content = run(ssh + [f"cat {remote}"], timeout=120)
        (out / f"{prefix}_live.log").write_text(content, encoding="utf-8")
        metrics = [r for r in parse_log(content) if {"miou", "acc50", "spmiou"} <= r.keys()]
        assert "Traceback" not in content and "Early stopping at epoch" not in content
        live.append(dict(id=exp["id"], config=exp["config"], gpu=exp["gpu"],
                         epoch=(re.findall(r"Epoch \[(\d+)/50\]", content) or ["initializing"])[-1],
                         best=max(metrics, key=lambda r:r["miou"]) if metrics else None,
                         completed=len(metrics)))
    gpu = {}
    for name in ("server-4", "server-6"):
        s = servers[name]
        ids = ",".join(map(str, s["allowed_gpus"]))
        gpu[name] = run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                         f"{s['user']}@{s['host']}", f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"]).strip()
    evidence = dict(at=datetime.now().isoformat(), terminal=dict(id=EID, best=best, metrics=rows,
                    log_sha256=digest), live=live, gpu=gpu, analyses=inventory, ledger_rows=len(ledger),
                    protected=protected)
    (out / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    goal = (PIPE / "goal.json").read_text(encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical evidence; retain route analysis |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}

## 1. Goal
```json
{goal}
```
check_goal00:08:46: Phase1 NOT YET; target .5100; ledger champion .5020;
exact champion {CHAMPION}; exact gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context gain | historical support | M95 above baseline | Novel mechanism |
| Wrong-instance selection | exploratory support | Frozen D1/D2 | Independent confirmation |
| Terminal controls exceed M95 | unsupported | M184-M1890/6 | M190/M191 live; M193 waiting |
| Shared-anchor fixed errors | unsupported | Prior0/21 applicability | Do not reopen without evidence |

## 3. Experiment Assessment
All{len(inventory)} analyses read and hash-inventoried; all{len(ledger)} ledger rows read.
| Experiment | mIoU | State | Motivation assessment |
|------------|------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: Novel derived forward/loss, primary-source distinction, scene uncertainty,
robustness and independent validation remain incomplete. M189 does not
restore M95 performance. Source-level recurrence isolation does not establish
environment matching. M190 also changes padding; M191 has a platform mismatch.

## 5. Design Rationale
Q2: Close M189 using exact paired metrics and29 full-denominator validations.
Q3: Adds a completed legacy control without inventing new efficacy or novelty.
All12 constraints and11 bans reviewed. No new numerical or structural training
candidate passes scientific admission. No tuning, schedule, seed, attention,
resource or deployment changes. Scientific admission overrides1/5 queue depth.

## 6. Next Batch
No new design, implementation, enqueue or model sync. M191 was dispatched by
the monitor from the preserved FIFO after matching code commit05335bdd.
Preserve M190/M191 and waiting M193. No automatic successor.
Evidence: reports/tick_evidence_{STAMP}/audit.json.
"""
    (PIPE / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    print(run([monitor.bash_executable(), str(SKILL / "log_decision.sh"), "cluster_project", "route_change",
               "M189 terminal best .4908618331 leaves six controls below M95 and1/5 waiting; refill?",
               "Close M189 without successor; preserve M190/M191 and waiting M193; admit no new mechanism.",
               "Scientific admission overrides depth; exact parent delta -.0054169595; no novel derived mechanism.",
               f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json"]))
    now = datetime.now()
    questions = []
    for path in (PIPE / "decisions").glob("*_question.md"):
        when = datetime.strptime(path.name[:15], "%Y%m%d-%H%M%S")
        if now - timedelta(hours=24) <= when <= now:
            questions.append((path.name, path.read_text(encoding="utf-8")))
    gpu_rows = []
    for name, lines in gpu.items():
        for line in lines.splitlines():
            index, util, used, total = [v.strip() for v in line.split(",")]
            process = next((r["id"] for r in live if name == "server-4" and str(r["gpu"]) == index), "IDLE")
            gpu_rows.append(f"| {name} | {index} | {util}% | {used}/{total} MiB | {process} |")
    live_rows = []
    for r in live:
        b = r["best"]
        vals = f"{b['miou']:.10f} | {b['acc50']} | {b['spmiou']} | {r['completed']-b['epoch']}/10" if b else "n/a | n/a | n/a | 0/10"
        live_rows.append(f"| {r['id']} | {r['config']} | server-4 | {r['gpu']} | {r['epoch']}/50 | {vals} | running |")
    queue = load(PIPE / "queue.json")
    waiting = [(s,t) for s,ts in queue["gpu_queues"].items() for t in ts if t["status"]=="waiting"]
    assert [t["id"] for _,t in waiting] == ["M193-CTF-HCG-CSORT-MQHC-TR"]
    queue_rows = "\n".join(f"| {i} | {t['id']} | {t['config']} | waiting | none | {s} |" for i,(s,t) in enumerate(waiting,1))
    report = f"""================================================================================
  Research Pipeline Report - cluster_project
  {now:%Y-%m-%d %H:%M:%S} (tick #{STAMP})
================================================================================

## 0. Goal Status
Target: mIoU >= .5100 | Champion: M95 .5020 (exact .5024607182)
Gap: +.0080 ledger / +.0075392818 exact | Phase:1 NOT YET.

## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs: server-6:7 (two configured slots). No server-6 waiting task.

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
M189 is terminal, not a third running task; stale deathwatch cleared.

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
{queue_rows}
Queue depth:1 waiting /5 declared capacity -> NEED MORE (requires6).
SERVERS.yaml configured capacity4; discrepancy retained, not silently edited.
Scientific admission takes priority over depth; no migration.

## 4. This Tick's Actions
- Unhealthy sentinel absent; required monitor and check_goal completed once.
- Monitor dispatched original M191 to GPU1; local/remote commit05335bdd matched.
- Hash-verified M189 normal early stop29/best19; exact best .4908618331.
- Archived log, six-section analysis, registry and ledger; preserved history,
  M191 GPU1 and M190 GPU0 identities, and remaining FIFO.
- Read/hash-inventoried{len(inventory)} analyses and loaded{len(ledger)} ledger rows.
- Completed full-goal motivation review. No new model/config/sync/repair.
- Old summary cleanup by filename timestamp, >24h only; durable memory updated.

## 5. Decisions Made
- Monitor queue_push: launch original M191 on server-4 GPU1.
- other: finalize only M189 with exact terminal evidence; preserve M191 mapping.
- route_change: no successor or unadmitted refill; preserve M190/M191/M193.
See pipeline/decisions/_index.md and reviews/motivation_review_{STAMP}.md.

## \u26a0 Pending User Decisions
{chr(10).join('- '+name+chr(10)+text for name,text in questions) if questions else 'No type=question records in the last24h.'}

================================================================================
  Next tick: 2026-09-13 01:07
================================================================================
"""
    (PIPE / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(PIPE / n) for n in protected}
    print(json.dumps(dict(live=live, gpu=gpu, analyses=len(inventory), ledger_rows=len(ledger),
                          questions=len(questions), report=f"summary_{STAMP}.md"), indent=2))


if __name__ == "__main__":
    main()
