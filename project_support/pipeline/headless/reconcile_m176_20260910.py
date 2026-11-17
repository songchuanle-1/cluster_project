"""Reconcile M176's explicit normal early stop while retaining shared ownership."""
import copy
import csv
import hashlib
import importlib.util
from pathlib import Path
import re
import subprocess


ROOT = Path("D:/project/cluster_project")
ID = "M176-CTF-HCG-CSORT-MQSD"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqsd"
LOG = ROOT / "Checkpoints/server-6" / NAME / "20260907_015118/20260907_015118.log"
REMOTE = f"/data3/songcl/Project/Cluster_project/Cluster_checkpoints/{NAME}/20260907_015118/20260907_015118.log"
ANALYSIS = ROOT / f"pipeline/analyses/{ID}_done_earlystop_20260910-001300.md"
DIGEST = "87ca41800632e9425913a7b8d66a37e04d12e77b0a13e4f129dcfad2f89c7888"


def main():
    source = Path("D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")
    spec = importlib.util.spec_from_file_location("monitor_m176", source)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Another monitor owns the pipeline lock")
    try:
        queue = monitor.load_queue(str(ROOT))
        tasks = [t for t in queue["gpu_queues"]["server-6"] if t["id"] == ID]
        with (ROOT / "pipeline/experiments.csv").open(encoding="utf-8") as stream:
            ledger = [r for r in csv.DictReader(stream) if r["id"] == ID]
        if not tasks:
            assert monitor.load_experiment(str(ROOT), ID)["status"] == "done_earlystop"
            assert len(ledger) == 1 and ledger[0]["state"] == "done_earlystop"
            assert ANALYSIS.is_file()
            print("M176 already reconciled; no changes")
            return
        assert len(tasks) == 1 and tasks[0]["status"] == "running"
        assert not ledger
        assert ANALYSIS.is_file()
        assert hashlib.sha256(LOG.read_bytes()).hexdigest() == DIGEST
        text = LOG.read_text(encoding="utf-8")
        assert text.rstrip().endswith(
            "Early stopping at epoch 24: no improvement for 10 epochs (best=0.4936)")
        vals = [float(v) for v in re.findall(r"\bmIoU : ([0-9.]+)", text)]
        assert len(vals) == 24 and vals.index(max(vals)) + 1 == 14
        assert max(vals) == 0.4935617446899414
        assert all(v < max(vals) for v in vals[14:])
        assert vals[-1] == 0.48384666442871094
        process = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
             "songcl@100.64.3.28", "ps -eo pid,args"],
            capture_output=True, text=True, encoding="utf-8", check=True, timeout=20)
        assert not any(NAME in line and "tools/train.py" in line
                       for line in process.stdout.splitlines())
        assert any("2791032" in line and "tools/train.py" in line and
                   "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhf.yaml" in line
                   for line in process.stdout.splitlines())
        before = monitor.load_running(str(ROOT))
        assert before["server-6"]["7"] == ["M175-CTF-HCG-CSORT-MQHF", ID]
        expected = copy.deepcopy(before)
        expected["server-6"]["7"].remove(ID)
        original = monitor.load_experiment(str(ROOT), ID)
        assert original["gpu"] == "7" and original["launched"] == "2026-09-07T09:48:32"
        history = copy.deepcopy(original["history"])
        # The generic analysis writer uses unpaired maxima; use the verified analysis.
        monitor.pull_log = lambda *args: str(LOG)
        monitor.write_analysis_md = lambda *args: str(ANALYSIS)
        events = []
        monitor.finalize_task(str(ROOT), queue, "server-6", "100.64.3.28",
                              "songcl", tasks[0], NAME, "done_earlystop",
                              max(vals), "24/50", "7", REMOTE, events)
        assert monitor.load_running(str(ROOT)) == expected
        exp = monitor.load_experiment(str(ROOT), ID)
        assert exp["history"][:len(history)] == history
        assert exp["launched"] == original["launched"]
        exp.update(
            ended_at_remote="2026-09-09T14:48:51.019",
            remote_clock_note="Server-6 UTC logger; host has about +2m48s clock offset.",
            best_miou_exact=max(vals), best_epoch=14,
            best_acc50=0.541, best_spmiou=0.456,
            validations_completed=24, no_improve_final=10,
            measured_flops_g=10.378977708, resource_eligible=False,
            terminal_evidence="Explicit trainer early-stop marker; ten real post-best validations",
            log_sha256=DIGEST, analysis=str(ANALYSIS))
        monitor.save_experiment(str(ROOT), exp)
        deathwatch = monitor.load_deathwatch(str(ROOT))
        deathwatch.get("server-6", {}).pop(NAME, None)
        monitor.save_deathwatch(str(ROOT), deathwatch)
        monitor.daily_report(str(ROOT), events)
        print("\n".join(events))
        print("M175 shared-slot ownership retained; launch history unchanged")
    finally:
        lock.close()


if __name__ == "__main__":
    main()
