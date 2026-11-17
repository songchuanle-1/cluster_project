"""Apply the logged, resource-validated reserve replacement under pipeline lock."""
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import subprocess

import yaml


ROOT = Path("D:/project/cluster_project")
REPORT = "pipeline/reports/tr_validation_20260908-1924"
AUDIT = "pipeline/reports/mq_resource_audit_20260908-1912"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
SUFFIXES = ("mqst", "mqpp", "mqht", "mqfc")
HEAD = "cda808cbbf1e87c98e7e3cb9461405856a2e1aba"


def main():
    source = Path("D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")
    spec = importlib.util.spec_from_file_location("enqueue_monitor", source)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    head = subprocess.check_output(
        ["git", "-C", str(ROOT / "Cluster"), "rev-parse", "HEAD"],
        text=True).strip()
    assert head == HEAD
    reports = json.loads((ROOT / REPORT / "resource_audit.json").read_text())
    old_reports = json.loads((ROOT / AUDIT / "resource_audit.json").read_text())
    baseline = reports[0]
    for suffix, resource in zip(SUFFIXES, reports[1:]):
        assert Path(resource["config"]).stem == f"{BASE}_{suffix}_tr"
        assert resource["flops"] <= 10e9
        assert resource["peak_allocated_mb"] <= 1.15 * baseline["peak_allocated_mb"]
        assert (resource["batch_size"], resource["warmup"], resource["repeat"]) == (1, 20, 100)
        tests = json.loads(
            (ROOT / REPORT / f"{BASE}_{suffix}_tr_tests.json").read_text())
        assert tests["passed"] and tests["decoder_events"] == [
            "decoder0", "decoder1", "decoder2", "decoder3", "decoder4",
            "refiner", "decoder5"]
        original = ROOT / "Cluster/configs/Quard" / f"ctf_hcg_csort_{suffix}" / f"{BASE}_{suffix}.yaml"
        new = ROOT / "Cluster" / resource["config"]
        assert yaml.safe_load(original.read_text()) == yaml.safe_load(new.read_text())
        assert len(list((ROOT / "Cluster/configs").rglob(new.name))) == 1
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Another monitor owns the pipeline lock")
    try:
        queue = monitor.load_queue(str(ROOT))
        before = monitor.load_running(str(ROOT))
        tasks = queue["gpu_queues"]["server-4"]
        assert not any(t["id"].startswith(("M184-", "M185-", "M186-", "M187-"))
                       for t in tasks), "Replacement already enqueued"
        now = datetime.now().isoformat(timespec="seconds")
        for offset, suffix in enumerate(SUFFIXES):
            old_id = f"M{179 + offset}-CTF-HCG-CSORT-{suffix.upper()}"
            task = next(t for t in tasks if t["id"] == old_id)
            assert task["status"] == "waiting" and task.get("dispatch_hold")
            assert not task.get("launched")
            task.update(status="withdrawn", finished_at=now,
                        measured_flops_g=old_reports[offset + 1]["flops_g"],
                        validation_report=f"{AUDIT}/resource_audit.json")
            task["note"] += (
                "; withdrawn_resource 2026-09-08: measured >10G, never trained; "
                "decision191559/193039; replaced by independent terminal-readout ID.")
            record = monitor.load_experiment(str(ROOT), old_id) or {
                "id": old_id, "config": task["config"], "server": "server-4",
                "gpu": None, "history": []}
            record.update(status="withdrawn", finished_at=now,
                          reason="Measured FLOPs exceed10G; never trained",
                          measured_flops_g=task["measured_flops_g"],
                          validation_report=task["validation_report"])
            record["history"].append({"ts": now, "action": "withdrawn_resource",
                                      "decision": "20260908-193039_next_batch.md"})
            monitor.save_experiment(str(ROOT), record)
            new_id = f"M{184 + offset}-CTF-HCG-CSORT-{suffix.upper()}-TR"
            new_task = {
                "id": new_id, "config": reports[offset + 1]["config"],
                "status": "waiting", "gpu": None, "depends_on": [],
                "label": f"M{184 + offset} {suffix.upper()} terminal-readout structural ablation",
                "note": (
                    "Independent original topology with intermediate feedback removed; "
                    "one context read before final decoder; identical numerical config. "
                    "CUDA topology/padding/batch-isolation/gradients and exact boundary "
                    "hooks passed after padding repair1. Full-model measured <=10G. "
                    "Codecda808c synced both servers preserving deployment diffs."),
                "measured_flops_g": reports[offset + 1]["flops_g"],
                "validation_report": f"{REPORT}/resource_audit.json",
                "design": "pipeline/designs/exp_design_20260908-1917.md",
                "code_commit": HEAD,
            }
            tasks.append(new_task)
            monitor.save_experiment(str(ROOT), {
                **new_task, "server": "server-4", "created_at": now,
                "history": [{"ts": now, "action": "enqueued",
                             "decision": "20260908-193039_next_batch.md"}]})
        monitor.save_queue(str(ROOT), queue)
        assert monitor.load_running(str(ROOT)) == before
        waiting = [t for group in queue["gpu_queues"].values()
                   for t in group if t["status"] == "waiting"]
        assert len(waiting) == 5 and not any(t.get("dispatch_hold") for t in waiting)
        print("Withdrawn M179-M182; eligible FIFO", [t["id"] for t in waiting])
        print("Active ownership unchanged", before)
    finally:
        lock.close()


if __name__ == "__main__":
    main()
