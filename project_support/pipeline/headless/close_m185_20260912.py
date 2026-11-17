"""Evidence-gated M185 normal early-stop reconciliation."""
import copy
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

import yaml


ROOT = Path("D:/project/cluster_project")
SKILL = ROOT.parent / ".claude/skills/songcl_research_pipeline"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
EID = "M185-CTF-HCG-CSORT-MQPP-TR"
REL_LOG = f"{BASE}_mqpp_tr/20260910_001203/20260910_001203.log"
LOG = ROOT / "Checkpoints/server-6" / REL_LOG
ANALYSIS = ROOT / "pipeline/analyses/M185-CTF-HCG-CSORT-MQPP-TR_done_earlystop_20260912-161500.md"
EVIDENCE = ROOT / "pipeline/reports/m185_transition_20260912.json"
BEST_MIOU = 0.4884226322174072
BEST_EPOCH = 13
FINAL_EPOCH = 23
NO_IMPROVE = 10
FLOPS = 9.845844524


def run(args, timeout=90):
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=True,
        timeout=timeout,
    ).stdout


def parse_log(text):
    rows = []
    epoch = None
    for line in text.splitlines():
        training = re.search(r"Epoch \[(\d+)/50\]", line)
        if training:
            epoch = int(training[1])
        exact = re.search(r"\bmIoU : ([0-9.]+)", line)
        if exact:
            rows.append({"epoch": epoch, "miou": float(exact[1])})
            continue
        if not rows:
            continue
        acc = re.search(r"\bmIOU:.*?\bAcc_50: ([0-9.]+)", line)
        spm = re.search(r"\bspmIOU: ([0-9.]+)", line)
        if acc:
            rows[-1]["acc50"] = float(acc[1].rstrip("."))
        if spm:
            rows[-1]["spmiou"] = float(spm[1].rstrip("."))
    return rows


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location(
        "scoped_monitor", SKILL / "pipeline_monitor.py"
    )
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)

    def decision(project_dir, kind, question, action, basis="", evidence=""):
        return run([
            monitor.bash_executable(),
            str(SKILL / "log_decision.sh"),
            "cluster_project",
            kind,
            question,
            action,
            basis,
            evidence,
        ])

    monitor.log_decision = decision
    servers = yaml.safe_load(
        (ROOT / "SERVERS.yaml").read_text(encoding="utf-8")
    )["servers"]
    srv = servers["server-6"]
    ssh = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        f"{srv['user']}@{srv['host']}",
    ]
    remote_log = f"{srv['work_dir']}/{REL_LOG}"
    quoted_log = shlex.quote(remote_log)

    remote_text = run(ssh + [f"cat {quoted_log}"], timeout=120)
    digest = run(ssh + [f"sha256sum {quoted_log}"], timeout=30).split()[0]
    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    rows = parse_log(remote_text)
    assert [row["epoch"] for row in rows] == list(range(1, FINAL_EPOCH + 1))
    best = max(rows, key=lambda row: row["miou"])
    assert best == {
        "epoch": BEST_EPOCH,
        "miou": BEST_MIOU,
        "acc50": 0.539,
        "spmiou": 0.453,
    }
    assert all(row["miou"] < BEST_MIOU for row in rows[BEST_EPOCH:])
    assert remote_text.rstrip().endswith(
        "Early stopping at epoch 23: no improvement for 10 epochs (best=0.4884)"
    )
    assert not ANALYSIS.exists(), ANALYSIS

    LOG.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "scp",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=10",
            f"{srv['user']}@{srv['host']}:{remote_log}",
            str(LOG),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert hashlib.sha256(LOG.read_bytes()).hexdigest() == digest

    start = remote_text.splitlines()[0].split(" - ")[0]
    end = remote_text.splitlines()[-1].split(" - ")[0]
    start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S,%f")
    end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M:%S,%f")
    duration = end_dt - start_dt
    final = rows[-1]

    analysis = f"""================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: {EID} | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: {EID}
  - Config: configs/Quard/ctf_hcg_csort_mqpp_tr/{BASE}_mqpp_tr.yaml
  - Server: server-6 | GPU: 7
  - Registry launch: 2026-09-10T08:09:15; logger start/end: {start} / {end}.
  - Logger duration: {duration}. Server-6 clock offset is not mixed with the
    local wall clock.
  - Archive: Checkpoints/server-6/{REL_LOG}
  - SHA256 remote/local: {digest}
  - State: done_earlystop, explicit normal trainer early-stop marker and absent
    project process.

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | {best['miou']} | {best['epoch']} |
  | Acc@50   | {best['acc50']:.3f} | {best['epoch']} |
  | spmIOU   | {best['spmiou']:.3f} | {best['epoch']} |

## 3. Convergence Summary
  - Best first reached at epoch {best['epoch']}.
  - Epochs {best['epoch'] + 1}..{FINAL_EPOCH} provide {NO_IMPROVE} genuine
    post-best validations.
  - Final epoch {FINAL_EPOCH}: mIoU={final['miou']}, Acc@50={final['acc50']:.3f},
    spmIOU={final['spmiou']:.3f}.
  - Shape: rapid early rise, then a shallow fluctuating plateau below the best.
  - Explicit marker: Early stopping at epoch {FINAL_EPOCH}: no improvement for
    {NO_IMPROVE} epochs (best=0.4884).

## 4. Comparison
  - vs baseline model_base1 0.4894491136: {best['miou'] - 0.4894491136:+.10f}.
  - vs champion M95-CTF-HCG-CSORT 0.5024607181549072:
    {best['miou'] - 0.5024607181549072:+.10f}.
  - vs target 0.5100: {best['miou'] - 0.5100:+.10f}.
  - vs M188-MQB-TR 0.4916: {best['miou'] - 0.4916:+.10f}, but M185 and M188
    are terminal-readout ablations of different parent topologies; the
    descriptive gap does not isolate one causal edge.
  - Admission measurement: {FLOPS:.9f}G <= 10G.

## 5. Conclusion
  - Conclusion: failed as a mechanism claim.
  - Interpretation: MQPP terminal readout remained below both baseline and
    champion. This single-seed normal stop supplies no champion-level gain and
    does not explain the parent-path weakness.
  - Guidance: close this tested variant without numerical rescue, automatic
    rerun, or successor variant. Preserve FIFO M191-MQSD-TR then M193-MQHC-TR.

## 6. Crash Info
  - Not crashed. Explicit trainer early-stop marker, contiguous validations,
    process absence, and remote/local log hash agree.
  - Model auto-fix attempts: 0. Checkpoint remains remote.

================================================================================
"""
    ANALYSIS.write_text(analysis, encoding="utf-8")

    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Another pipeline writer is active")
    try:
        queue = monitor.load_queue(str(ROOT))
        before = copy.deepcopy(monitor.load_running(str(ROOT)))
        tasks = {
            task["id"]: task
            for group in queue["gpu_queues"].values()
            for task in group
        }
        processes = monitor.find_running_processes(
            srv["host"], srv["user"], srv["remote_code_root"]
        )
        assert not any(Path(command).stem == BASE + "_mqpp_tr"
                       for command in processes)
        assert tasks[EID]["status"] == "running"
        assert before["server-6"]["7"] == [
            "M184-CTF-HCG-CSORT-MQST-TR",
            EID,
        ]

        decision(
            str(ROOT),
            "other",
            "M185 normal early stop verified at epoch 23; finalize terminal state?",
            "Archive M185 done_earlystop and release only its server-6 GPU7 slot.",
            "Best .4884226322174072 @13; 23 contiguous validations; 10 stale; "
            "process absent; remote/local log hash matches.",
            str(ANALYSIS),
        )

        original = monitor.load_experiment(str(ROOT), EID)
        events = []
        monitor.pull_log = lambda *args: str(LOG)
        monitor.write_analysis_md = lambda *args: str(ANALYSIS)
        monitor.finalize_task(
            str(ROOT),
            queue,
            "server-6",
            srv["host"],
            srv["user"],
            tasks[EID],
            BASE + "_mqpp_tr",
            "done_earlystop",
            best["miou"],
            f"{FINAL_EPOCH}/50",
            "7",
            remote_log,
            events,
        )
        exp = monitor.load_experiment(str(ROOT), EID)
        assert exp["history"][:len(original["history"])] == original["history"]
        exp.update(
            final_best=f"{best['miou']:.4f}",
            best_miou_exact=best["miou"],
            best_epoch=best["epoch"],
            best_acc50=best["acc50"],
            best_spmiou=best["spmiou"],
            validations_completed=FINAL_EPOCH,
            no_improve_final=NO_IMPROVE,
            epochs_final=f"{FINAL_EPOCH}/50",
            ended_at_remote=end,
            log_local=str(LOG),
            log_sha256=digest,
            analysis=str(ANALYSIS),
            measured_flops_g=FLOPS,
            terminal_evidence=(
                "Explicit trainer marker, 23 contiguous validations, absent "
                "process, and matching remote/local hash"
            ),
        )
        monitor.save_experiment(str(ROOT), exp)
        deathwatch = monitor.load_deathwatch(str(ROOT))
        deathwatch.get("server-6", {}).pop(BASE + "_mqpp_tr", None)
        monitor.save_deathwatch(str(ROOT), deathwatch)

        after = monitor.load_running(str(ROOT))
        assert after["server-6"]["7"] == ["M184-CTF-HCG-CSORT-MQST-TR"]
        assert EID not in {
            task["id"]
            for task in monitor.load_queue(str(ROOT))["gpu_queues"]["server-6"]
        }
        events.append(
            f"[{BASE}_mqpp_tr] terminal early stop at epoch {FINAL_EPOCH}; "
            "server-6 GPU7 slot released"
        )
        evidence = {
            "verified_at": datetime.now().isoformat(),
            "terminal": best,
            "final": final,
            "validations": rows,
            "log_sha256": digest,
            "running": after,
            "events": events,
        }
        EVIDENCE.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        monitor.daily_report(str(ROOT), events)
        print(json.dumps(evidence, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
