"""Archive the explicitly completed M177 run without advancing deathwatch."""
import ast
import csv
from datetime import datetime
import importlib.util
from pathlib import Path
import re
import subprocess


ROOT = Path("D:/project/cluster_project")
ID = "M177-CTF-HCG-CSORT-MQBC"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqbc"
LOG = ROOT / "Checkpoints/server-4" / NAME / "20260908_010850/20260908_010850.log"
REMOTE = f"/data/songcl/Project/Cluster_project/Cluster_checkpoints/{NAME}/20260908_010850/20260908_010850.log"


def main():
    source = Path("D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")
    spec = importlib.util.spec_from_file_location("monitor_m177", source)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Another monitor owns the pipeline lock")
    try:
        queue = monitor.load_queue(str(ROOT))
        matches = [t for t in queue["gpu_queues"]["server-4"] if t["id"] == ID]
        if not matches:
            assert monitor.load_experiment(str(ROOT), ID)["status"] == "done_earlystop"
            print("M177 already reconciled")
            return
        task = matches[0]
        assert task["status"] == "running"
        process = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
             "songcl@192.168.1.137", "ps -eo pid,args"],
            capture_output=True, text=True, encoding="utf-8", check=True, timeout=20)
        assert not any(NAME in line and "tools/train.py" in line
                       for line in process.stdout.splitlines())
        text = LOG.read_text(encoding="utf-8")
        assert text.rstrip().endswith(
            "Early stopping at epoch 27: no improvement for 10 epochs (best=0.4963)")
        vals = [float(v) for v in re.findall(r"mIoU : ([0-9.]+)", text)]
        assert len(vals) == 27 and vals.index(max(vals)) + 1 == 17
        with (ROOT / "pipeline/experiments.csv").open(encoding="utf-8") as stream:
            assert not any(row["id"] == ID and row["state"] == "done_earlystop"
                           for row in csv.DictReader(stream))
        before = monitor.load_running(str(ROOT))
        assert before["server-4"]["0"] == "M178-CTF-HCG-CSORT-MQTD"
        # Reuse the verified local copy; the generic writer uses wrong metric labels.
        monitor.pull_log = lambda *args: str(LOG)
        monitor.write_analysis_md = lambda *args: str(
            ROOT / f"pipeline/analyses/{ID}_done_earlystop_20260908-181400.md")
        events = []
        monitor.finalize_task(str(ROOT), queue, "server-4", "192.168.1.137",
                              "songcl", task, NAME, "done_earlystop",
                              max(vals), "27/50", "0", REMOTE, events)
        assert monitor.load_running(str(ROOT)) == before
        exp = monitor.load_experiment(str(ROOT), ID)
        exp["ended_at_remote"] = "2026-09-08T17:21:15"
        exp["best_miou_exact"] = max(vals)
        exp["best_epoch"] = 17
        exp["terminal_evidence"] = "Explicit trainer early-stop marker; 10 real validations"
        monitor.save_experiment(str(ROOT), exp)
        deathwatch = monitor.load_deathwatch(str(ROOT))
        deathwatch.get("server-4", {}).pop(NAME, None)
        monitor.save_deathwatch(str(ROOT), deathwatch)
        monitor.daily_report(str(ROOT), events)
        print("\n".join(events))
        print("M178 slot retained; M177 exact best", max(vals))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
