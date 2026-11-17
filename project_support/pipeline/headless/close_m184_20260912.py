"""Reconcile M184 only after explicit, hash-verified terminal evidence."""
import copy
import csv
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

from close_m185_20260912 import parse_log, run
import yaml


ROOT = Path("D:/project/cluster_project")
SKILL = ROOT.parent / ".claude/skills/songcl_research_pipeline"
EID = "M184-CTF-HCG-CSORT-MQST-TR"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqst_tr"
REL_LOG = f"{BASE}/20260910_001153/20260910_001153.log"
LOG = ROOT / "Checkpoints/server-6" / REL_LOG
ANALYSIS = ROOT / f"pipeline/analyses/{EID}_done_earlystop_20260912-171500.md"
EVIDENCE = ROOT / "pipeline/reports/m184_transition_20260912.json"
EXPECTED_HASH = "b615b2f6dcacb15a2233bf48842988566a4bcdfda57932293c0d4ff1f6434c6d"


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location("monitor_m184", SKILL / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    srv = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-6"]
    target = f"{srv['user']}@{srv['host']}"
    remote_log = f"{srv['work_dir']}/{REL_LOG}"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", target]
    text = run(ssh + [f"cat {remote_log}"], timeout=120)
    digest = run(ssh + [f"sha256sum {remote_log}"]).split()[0]
    assert digest == EXPECTED_HASH
    rows = parse_log(text)
    assert [r["epoch"] for r in rows] == list(range(1, 26))
    best = max(rows, key=lambda r: r["miou"])
    assert best == {"epoch": 15, "miou": 0.48762595653533936, "acc50": 0.538, "spmiou": 0.451}
    assert all(r["miou"] < best["miou"] for r in rows[15:])
    assert text.rstrip().endswith(
        "Early stopping at epoch 25: no improvement for 10 epochs (best=0.4876)"
    )
    LOG.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["scp", "-o", "BatchMode=yes", f"{target}:{remote_log}", str(LOG)],
        check=True, capture_output=True, timeout=120,
    )
    assert hashlib.sha256(LOG.read_bytes()).hexdigest() == digest
    start = text.splitlines()[0].split(" - ")[0]
    end = text.splitlines()[-1].split(" - ")[0]
    duration = datetime.strptime(end, "%Y-%m-%d %H:%M:%S,%f") - datetime.strptime(
        start, "%Y-%m-%d %H:%M:%S,%f"
    )
    final = rows[-1]
    analysis = f"""================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: {EID} | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: {EID}
  - Config: configs/Quard/ctf_hcg_csort_mqst_tr/{BASE}.yaml
  - Server: server-6 | GPU: 7
  - Registry launch: 2026-09-10T08:09:05 (Asia/Shanghai).
  - Logger start: {start}; finish: {end}; duration: {duration}.
    Server-6 reports UTC, so logger finish corresponds to 2026-09-12
    16:35:18 Asia/Shanghai; do not mix logger and local naive timestamps.
  - State: done_earlystop; explicit marker, absent process, 25 validations.
  - Archive: Checkpoints/server-6/{REL_LOG}
  - Remote/local SHA256: {digest}

## 2. Best Metrics
  | Metric | Value | @ Epoch |
  |--------|-------|---------|
  | mIoU | {best['miou']} | 15 |
  | Acc@50 | 0.538 | 15 |
  | spmIOU | 0.451 | 15 |

## 3. Convergence Summary
  - Best first reached at epoch 15; epochs 16-25 all failed to improve.
  - Final epoch 25 mIoU={final['miou']}, Acc@50=0.525, spmIOU=0.433.
  - Ten post-best validations; normal trainer patience=10 stop, no monitor kill.
  - Initial improvement followed by a fluctuating/declining plateau.
  - Exact log-derived best epoch is 15, not the live parser's progress counter.

## 4. Comparison
  - Baseline model_base1 0.4894491136074066:
    delta={best['miou'] - 0.4894491136074066:+.10f}.
  - Champion M95 0.5024607181549072:
    delta={best['miou'] - 0.5024607181549072:+.10f}.
  - Target 0.5100: delta={best['miou'] - 0.51:+.10f}.
  - M185-MQPP-TR 0.4884226322174072:
    delta={best['miou'] - 0.4884226322174072:+.10f}; different topology,
    not a matched causal comparison.
  - M179-MQST parent never trained after >10G admission failure.
    No parent accuracy exists; recurrence-edge effect cannot be isolated.
  - M184 admission: 9.845647916G; resource eligibility is not efficacy.

## 5. Conclusion
  - Conclusion: failed to improve baseline or champion in this single-seed run.
  - The preserved MQST terminal-readout control does not retain M95's gain.
    It supplies no evidence for a new mechanism or automatic successor.
  - Close this variant without numerical rescue/retry. Preserve M191 then M193
    on server-4 and preserve live M189/M190.
  - Aggregate validation bests are exploratory; no independent test or
    mechanistic causal conclusion follows from this comparison.

## 6. Crash Info
  - Not crashed. Model repair attempts: 0. No checkpoint pulled or modified.
================================================================================
"""
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Pipeline writer active; refusing mutation")
    try:
        queue = monitor.load_queue(str(ROOT))
        before = copy.deepcopy(monitor.load_running(str(ROOT)))
        original = monitor.load_experiment(str(ROOT), EID)
        assert original["status"] == "running"
        assert before["server-6"]["7"] == [EID]
        assert not ANALYSIS.exists()
        tasks = [t for t in queue["gpu_queues"]["server-6"] if t["id"] == EID]
        assert len(tasks) == 1 and tasks[0]["status"] == "running"
        protected_queue = copy.deepcopy(queue["gpu_queues"]["server-4"])
        processes = monitor.find_running_processes(srv["host"], srv["user"], srv["remote_code_root"])
        assert not any(Path(cfg).stem == BASE for cfg in processes)
        with (ROOT / "pipeline/experiments.csv").open(encoding="utf-8", newline="") as stream:
            assert not any(row["id"] == EID for row in csv.DictReader(stream))
        print(run([
            monitor.bash_executable(), str(SKILL / "log_decision.sh"),
            "cluster_project", "other",
            "M184 has explicit normal early stop at epoch25; finalize during deathwatch grace?",
            "Archive M184 done_earlystop; release only its server-6 GPU7 slot; preserve server-4 FIFO and trainers.",
            "25 contiguous validations; best .48762595653533936 at15; ten stale; process absent; remote/local hash verified. No repair or successor.",
            str(ANALYSIS),
        ]))
        ANALYSIS.write_text(analysis, encoding="utf-8")
        monitor.pull_log = lambda *args: str(LOG)
        monitor.write_analysis_md = lambda *args: str(ANALYSIS)
        events = []
        monitor.finalize_task(
            str(ROOT), queue, "server-6", srv["host"], srv["user"], tasks[0],
            BASE, "done_earlystop", best["miou"], "25/50", "7", remote_log, events,
        )
        exp = monitor.load_experiment(str(ROOT), EID)
        assert exp["history"][:len(original["history"])] == original["history"]
        exp.update(
            best_miou_exact=best["miou"], best_epoch=15, best_acc50=0.538,
            best_spmiou=0.451, validations_completed=25, no_improve_final=10,
            ended_at_remote=end, log_sha256=digest, analysis=str(ANALYSIS),
            terminal_evidence="Explicit marker;25 contiguous validations;absent process;matching log hashes",
        )
        monitor.save_experiment(str(ROOT), exp)
        dw = monitor.load_deathwatch(str(ROOT))
        dw.get("server-6", {}).pop(BASE, None)
        monitor.save_deathwatch(str(ROOT), dw)
        after = monitor.load_running(str(ROOT))
        assert "server-6" not in after and after["server-4"] == before["server-4"]
        assert monitor.load_queue(str(ROOT))["gpu_queues"]["server-4"] == protected_queue
        evidence = dict(
            verified_at=datetime.now().isoformat(), best=best, final=final,
            validations=rows, log_sha256=digest, running=after, events=events,
        )
        EVIDENCE.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        monitor.daily_report(str(ROOT), events)
        print(json.dumps(evidence, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
