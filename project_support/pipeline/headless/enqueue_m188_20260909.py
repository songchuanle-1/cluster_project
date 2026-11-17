"""Apply measured M188 admission and the logged M183 metadata repair."""
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import subprocess

import yaml


ROOT = Path("D:/project/cluster_project")
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
NAME = BASE + "_mqb_tr"
EXP_ID = "M188-CTF-HCG-CSORT-MQB-TR"
HEAD = "971d65d55a9e7f341db2c170266efac28e65b2eb"
REPORT = "pipeline/reports/m188_validation_20260909-1218"
DECISION = "20260909-122323_next_batch.md"
REPAIR = "20260909-122335_other.md"


def main():
    source = ROOT.parent / ".claude/skills/songcl_research_pipeline/pipeline_monitor.py"
    spec = importlib.util.spec_from_file_location("enqueue_monitor", source)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    assert subprocess.check_output(
        ["git", "-C", str(ROOT / "Cluster"), "rev-parse", "HEAD"],
        text=True).strip() == HEAD
    servers = monitor.load_servers(str(ROOT))
    for name in ("server-4", "server-6"):
        server = servers[name]
        assert monitor.ssh(server["host"], server["user"],
                           f"git -C {server['remote_code_root']} rev-parse HEAD").strip() == HEAD
    resources = json.loads((ROOT / REPORT / "resource_audit.json").read_text())
    baseline, candidate = resources
    assert Path(baseline["config"]).stem == BASE
    assert Path(candidate["config"]).stem == NAME
    assert candidate["flops"] <= 10e9
    assert candidate["peak_allocated_mb"] <= 1.15 * baseline["peak_allocated_mb"]
    for row in resources:
        assert (row["batch_size"], row["warmup"], row["repeat"]) == (1, 20, 100)
    tests = json.loads((ROOT / REPORT / f"{NAME}_tests.json").read_text())
    assert tests["passed"] and tests["decoder_events"] == [
        "decoder0", "decoder1", "decoder2", "decoder3", "decoder4", "refiner", "decoder5"]
    assert tests["mask_selection_gradient"] == "absent by hard argmax design"
    config = ROOT / "Cluster" / candidate["config"]
    parent = ROOT / "Cluster/configs/Quard/ctf_hcg_csort_mqb" / f"{BASE}_mqb.yaml"
    assert yaml.safe_load(config.read_text()) == yaml.safe_load(parent.read_text())
    assert len(list((ROOT / "Cluster/configs").rglob(config.name))) == 1
    for decision in (DECISION, REPAIR):
        assert (ROOT / "pipeline/decisions" / decision).is_file()
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Pipeline lock busy; no files changed")
    try:
        queue = monitor.load_queue(str(ROOT))
        ownership = monitor.load_running(str(ROOT))
        watched = ("running.json", "goal.json", "experiments.csv")
        before = {name: (ROOT / "pipeline" / name).read_bytes() for name in watched}
        now = datetime.now().isoformat(timespec="seconds")
        hqi_id = "M183-CTF-HCG-CSORT-HQI"
        hqi = monitor.load_experiment(str(ROOT), hqi_id)
        hqi_task = next(t for t in queue["gpu_queues"]["server-4"] if t["id"] == hqi_id)
        assert hqi_task["status"] == hqi["status"] == "running"
        assert ownership["server-4"]["1"] == hqi_id
        assert any(h.get("action") == "launched" and h.get("gpu") == "1"
                   for h in hqi["history"])
        server = servers["server-4"]
        processes = monitor.find_running_processes(
            server["host"], server["user"], server["remote_code_root"])
        process = processes[hqi["config"]]
        assert str(process[0]) == "2939408" and str(process[2]) == "1"
        if hqi.get("gpu") != "1":
            assert hqi.get("gpu") is None
            hqi.update(server="server-4", gpu="1")
            hqi["history"].append({
                "ts": now, "action": "placement_metadata_reconciled", "gpu": "1",
                "decision": REPAIR, "source": "running.json; launch history; live PID2939408"})
            monitor.save_experiment(str(ROOT), hqi)
            print("M183 actual GPU metadata repaired; prior history retained")
        tasks = queue["gpu_queues"]["server-4"]
        if any(t["id"] == EXP_ID for t in tasks):
            assert monitor.load_experiment(str(ROOT), EXP_ID) is not None
            print("M188 already enqueued; no duplicate")
            return
        waiting = [t for group in queue["gpu_queues"].values()
                   for t in group if t["status"] == "waiting"]
        assert [t["id"].split("-")[0] for t in waiting] == ["M184", "M185", "M186", "M187"]
        task = {
            "id": EXP_ID, "config": candidate["config"], "status": "waiting",
            "gpu": None, "depends_on": [],
            "label": "M188 MQB terminal-only dominant ancestor branch structural ablation",
            "note": (
                "Independent M169 copy; remove intermediate query feedback; retain original "
                "fine-argmax ancestor mean before final decoder. Identical numerical YAML. "
                "CUDA ancestry/padding/batch/gradients and exact boundary tests passed; "
                "hard argmax intentionally has no mask gradient. Full-model measured <=10G "
                "and inference allocated peak within1.15x M95; matched20/100 protocol. "
                "Code971d65d synced both servers preserving deployment diffs."),
            "measured_flops_g": candidate["flops_g"],
            "validation_report": f"{REPORT}/resource_audit.json",
            "design": "pipeline/designs/exp_design_20260909-1212.md",
            "code_commit": HEAD,
        }
        record = {
            **task, "server": "server-4", "created_at": now,
            "history": [{"ts": now, "action": "enqueued", "decision": DECISION}],
        }
        existing = monitor.load_experiment(str(ROOT), EXP_ID)
        if existing is not None:
            assert all(existing[key] == value for key, value in task.items())
        else:
            monitor.save_experiment(str(ROOT), record)
        tasks.append(task)
        monitor.save_queue(str(ROOT), queue)
        assert all((ROOT / "pipeline" / name).read_bytes() == data
                   for name, data in before.items())
        assert monitor.load_running(str(ROOT)) == ownership
        waiting.append(task)
        assert len(waiting) == 5 and not any(t.get("dispatch_hold") for t in waiting)
        print("Eligible FIFO", [t["id"] for t in waiting])
        print("Goal/CSV/active ownership unchanged")
    finally:
        lock.close()


if __name__ == "__main__":
    main()
