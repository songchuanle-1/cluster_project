"""Enqueue the single admitted CPS experiment without changing active owners."""
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path("D:/project/cluster_project")
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cps"
ID = "M195-CTF-HCG-CSORT-CPS"
DECISION = "20260914-172420_next_batch.md"


def main():
    spec = importlib.util.spec_from_file_location(
        "monitor", "D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    head = subprocess.check_output(["git", "-C", str(ROOT / "Cluster"), "rev-parse", "HEAD"], text=True).strip()
    assert head.startswith("1584fe9")
    for host, code in (
        ("songcl@192.168.1.137", "/data/songcl/Project/Cluster_project/Cluster"),
        ("songcl@100.64.3.28", "/data3/songcl/Project/Cluster_project/Cluster"),
    ):
        actual = subprocess.check_output(["ssh", host, f"git -C {code} rev-parse HEAD"], text=True).strip()
        assert actual == head
        clean = subprocess.check_output(
            ["ssh", host, f"git -C {code} diff --name-only -- framework/model/Quard_model/{BASE} configs/Quard/ctf_hcg_csort_cps"],
            text=True).strip()
        assert not clean, clean
    parity = json.loads((ROOT / "pipeline/reports/cps_parity_ddp_20260914.json").read_text())
    assert parity["inference_criterion_independent"]
    assert (ROOT / "pipeline/decisions" / DECISION).is_file()
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Pipeline lock busy; no queue mutation")
    try:
        queue = monitor.load_queue(str(ROOT))
        owners = monitor.load_running(str(ROOT))
        all_tasks = [t for group in queue["gpu_queues"].values() for t in group]
        assert not any(t["id"] == ID for t in all_tasks)
        assert sum(t["status"] in ("running", "claiming", "waiting") for t in all_tasks) < 4
        task = dict(
            id=ID, config=f"configs/Quard/ctf_hcg_csort_cps/{BASE}.yaml",
            status="waiting", gpu=None, depends_on=[], patience=10,
            label="M195 Common-Seed Paired Switching",
            measured_flops_g=9.762532428,
            validation_report="pipeline/reports/cps_admission_20260914-1725.md",
            design="pipeline/designs/exp_design_20260914-1705.md",
            code_commit=head,
            note="Independent M95; training-only cross-expression shared-physical-seed conditional assignment. Inherited indi weight and schedule; no efficacy claim. Decision172420; synced both servers.")
        queue["gpu_queues"]["server-4"].append(task)
        now = datetime.now().isoformat(timespec="seconds")
        monitor.save_experiment(str(ROOT), {**task, "server": "server-4", "created_at": now,
                                           "history": [{"ts": now, "action": "enqueued", "decision": DECISION}]})
        monitor.save_queue(str(ROOT), queue)
        assert monitor.load_running(str(ROOT)) == owners
        print(json.dumps(task, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
