"""Enqueue the synchronized, measured M193 without touching active ownership."""
from datetime import datetime
import hashlib
import importlib.util
import json
import os
import subprocess

from prepare_flow_20260910 import ROOT, BASE

HEAD = "05335bdd15d83d106d410e03498b0c38dc9ad414"
EXP = "M193-CTF-HCG-CSORT-MQHC-TR"
REPORT = "pipeline/reports/consensus_validation_20260910-1324"


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          check=True, timeout=60).stdout.strip()


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    print(run(["python", str(ROOT / "pipeline/headless/verify_flow_20260910.py"),
               "--suffix", "mqhc"]))
    resources = json.loads((ROOT / REPORT / "resource_audit.json").read_text())
    expected = [f"configs/Quard/ctf_hcg_csort/{BASE}.yaml",
                f"configs/Quard/ctf_hcg_csort_mqhc_tr/{BASE}_mqhc_tr.yaml"]
    assert [r["config"] for r in resources] == expected
    for row in resources:
        assert row["flops"] <= 10e9
        assert row["peak_allocated_mb"] <= 1.15 * resources[0]["peak_allocated_mb"]
        assert (row["batch_size"], row["warmup"], row["repeat"]) == (1, 20, 100)
    test = json.loads((ROOT / REPORT / f"{BASE}_mqhc_tr_tests.json").read_text())
    assert test["passed"] and test["decoder_events"] == [
        "decoder0", "decoder1", "decoder2", "decoder3", "decoder4", "refiner", "decoder5"]
    assert test["resolver"] == f"framework.model.Quard_model.{BASE}_mqhc_tr.network"
    code = ["git", "-C", str(ROOT / "Cluster")]
    assert run(code + ["rev-parse", "HEAD"]) == HEAD
    assert not run(code + ["status", "--porcelain"])
    source = ROOT.parent / ".claude/skills/songcl_research_pipeline/pipeline_monitor.py"
    spec = importlib.util.spec_from_file_location("consensus_monitor", source)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
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
        tasks = [t for group in queue["gpu_queues"].values() for t in group]
        if any(t["id"] == EXP for t in tasks):
            assert monitor.load_experiment(str(ROOT), EXP)["config"] == expected[1]
            print("M193 already present; no duplicate")
            return
        waiting = [t for t in tasks if t["status"] == "waiting"]
        assert [t["id"].split("-")[0] for t in waiting] == ["M188", "M189", "M190", "M191"]
        assert all(not t.get("dispatch_hold") and not t.get("depends_on") for t in waiting)
        assert monitor.load_experiment(str(ROOT), EXP) is None
        before = {name: (ROOT / "pipeline" / name).read_bytes()
                  for name in ("running.json", "goal.json", "experiments.csv")}
        assert hashlib.sha256(before["goal.json"]).hexdigest() == (
            "4fd79c4649d9b2b43f87d9689a4b17a8de3b7568bba6886c7f7075b67b643780")
        print(run(["bash", str(source.with_name("log_decision.sh")), "cluster_project",
                   "next_batch",
                   "M193 CUDA and full-model admission passed; restore waiting4 to5?",
                   "Enqueue M193-MQHC-TR behindM191 on server-4 FIFO, gpu=null; preserve four running jobs.",
                   "Measured9.885821484G and893.871MiB versus M95893.367MiB; exact parent YAML, "
                   "only recurrent graph deletion. Both servers synchronized at05335bd. "
                   "M174 partial patience forbids full causal parent comparison.",
                   f"{REPORT}/resource_audit.json; pipeline/designs/exp_design_20260910-1324.md"]))
        now = datetime.now().isoformat(timespec="seconds")
        task = {
            "id": EXP, "config": expected[1], "status": "waiting",
            "gpu": None, "depends_on": [],
            "label": "M193 MQHC terminal recurrence structural ablation",
            "note": "Independent M174 copy; only four intermediate context edges removed. "
                    "Numerical YAML and consensus formula unchanged. CUDA oracle, gradients, "
                    "padding, isolation, decoder boundary and20/100 admission passed. "
                    "M174 parser-limited evidence is not a matched full-patience control.",
            "measured_flops_g": resources[1]["flops_g"],
            "validation_report": REPORT + "/resource_audit.json",
            "design": "pipeline/designs/exp_design_20260910-1324.md",
            "code_commit": HEAD,
        }
        monitor.save_experiment(str(ROOT), {
            **task, "server": "server-4", "created_at": now,
            "history": [{"ts": now, "action": "enqueued",
                         "decision": "next_batch via log_decision.sh immediately before enqueue"}]})
        queue["gpu_queues"]["server-4"].append(task)
        monitor.save_queue(str(ROOT), queue)
        assert all((ROOT / "pipeline" / name).read_bytes() == data for name, data in before.items())
        final = [t for group in monitor.load_queue(str(ROOT))["gpu_queues"].values()
                 for t in group if t["status"] == "waiting"]
        assert len(final) == 5
        print("Eligible waiting:", [t["id"] for t in final])
    finally:
        lock.close()


if __name__ == "__main__":
    main()
