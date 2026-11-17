"""Admit only the three measured, synchronized terminal-recurrence ablations."""
from datetime import datetime
import importlib.util
import json
import os
import subprocess

from prepare_reserve_20260910 import ROOT, BASE, SUFFIXES
from verify_reserve_20260910 import main as verify_static

REPORT = "pipeline/reports/reserve_validation_20260910-1113"
HEAD = "b171bd6d3487948f294f5994eda613d0aa052713"


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    verify_static()
    resources = json.loads((ROOT / REPORT / "resource_audit.json").read_text())
    assert [r["config"].split("/")[-1] for r in resources] == [
        BASE + ".yaml", *[BASE + "_" + s + "_tr.yaml" for s in SUFFIXES]]
    for row in resources:
        assert row["flops"] <= 10e9
        assert row["peak_allocated_mb"] <= 1.15 * resources[0]["peak_allocated_mb"]
        assert (row["batch_size"], row["warmup"], row["repeat"]) == (1, 20, 100)
    for suffix in SUFFIXES:
        test = json.loads((ROOT / REPORT / f"{BASE}_{suffix}_tr_tests.json").read_text())
        assert test["passed"] and test["decoder_events"] == [
            "decoder0", "decoder1", "decoder2", "decoder3", "decoder4", "refiner", "decoder5"]
    source = ROOT.parent / ".claude/skills/songcl_research_pipeline/pipeline_monitor.py"
    spec = importlib.util.spec_from_file_location("reserve_monitor", source)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    assert subprocess.check_output(["git", "-C", str(ROOT / "Cluster"), "rev-parse", "HEAD"],
                                   text=True).strip() == HEAD
    servers = monitor.load_servers(str(ROOT))
    for name in ("server-4", "server-6"):
        srv = servers[name]
        assert monitor.ssh(srv["host"], srv["user"],
                           f"git -C {srv['remote_code_root']} rev-parse HEAD").strip() == HEAD
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Pipeline writer active; no queue changes")
    try:
        queue = monitor.load_queue(str(ROOT))
        watched = ("running.json", "goal.json", "experiments.csv")
        before = {f: (ROOT / "pipeline" / f).read_bytes() for f in watched}
        waiting = [t for group in queue["gpu_queues"].values()
                   for t in group if t["status"] == "waiting"]
        ids = [f"M{i}-CTF-HCG-CSORT-{s.upper()}-TR" for i, s in zip(range(189, 192), SUFFIXES)]
        existing = {t["id"] for t in waiting}
        if all(i in existing for i in ids):
            print("Already enqueued; no duplicate")
            return
        assert not any(i in existing for i in ids)
        assert [t["id"].split("-")[0] for t in waiting] == ["M187", "M188"]
        decision_text = monitor.log_decision(
            str(ROOT), "next_batch", "Three terminal recurrence ablations passed measured resource admission.",
            "Enqueue M189 MQBC-TR, M190 MQTD-TR, M191 MQSD-TR behind M187/M188; waiting2->5.",
            "No numeric tuning; scalar/CUDA/decoder tests passed; all<=10G and within15% "
            "matched inference allocation. Independent code synced both servers preserving deployments.",
            f"{REPORT}/resource_audit.json; pipeline/designs/exp_design_20260910-1113.md")
        now = datetime.now().isoformat(timespec="seconds")
        for exp_id, suffix, row in zip(ids, SUFFIXES, resources[1:]):
            assert monitor.load_experiment(str(ROOT), exp_id) is None
            task = {
                "id": exp_id, "config": row["config"], "status": "waiting",
                "gpu": None, "depends_on": [],
                "label": f"{exp_id} terminal recurrence structural ablation",
                "note": "Independent parent copy; only intermediate feedback removed. Original "
                "score formula and numerical YAML retained. CUDA oracle/gradients/padding/"
                "isolation/decoder-boundary tests and matched20/100 full-model resource audit passed. "
                "M190 includes established real-cluster padding correctness fix. No training launched.",
                "measured_flops_g": row["flops_g"], "validation_report": REPORT + "/resource_audit.json",
                "design": "pipeline/designs/exp_design_20260910-1113.md", "code_commit": HEAD,
            }
            monitor.save_experiment(str(ROOT), {
                **task, "server": "server-4", "created_at": now,
                "history": [{"ts": now, "action": "enqueued",
                             "decision": "next_batch logged immediately before enqueue"}]})
            queue["gpu_queues"]["server-4"].append(task)
        monitor.save_queue(str(ROOT), queue)
        assert all((ROOT / "pipeline" / f).read_bytes() == data for f, data in before.items())
        final = [t for group in queue["gpu_queues"].values()
                 for t in group if t["status"] == "waiting"]
        assert len(final) == 5 and not any(t.get("dispatch_hold") for t in final)
        print("Eligible reserve", [t["id"] for t in final])
    finally:
        lock.close()


if __name__ == "__main__":
    main()
