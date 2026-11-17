"""Capture real post-launch state and advance only verified native training."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import closure
import foreground_tick
import pipeline_monitor


def main():
    token = "e3d3340fabdd45bb9fc636e57be24156"
    owner = foreground_tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == token and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    queue = pipeline_monitor.load_queue(str(ROOT))
    tasks = [row for row in queue["gpu_queues"]["server-6"]
             if row["id"] in ("M198-PDC", "M199-BEI")]
    assert len(tasks) == 2
    assert all(row["status"] == "running" and row["launch_verified"] and
               row["launch_verification"] == "training_progress" for row in tasks)
    records = []
    for row in tasks:
        text = pipeline_monitor.ssh("100.64.3.28", "songcl",
            f"if kill -0 {int(row['pid'])} 2>/dev/null; then tail -c 24000 "
            f"{shlex.quote(row['log'])}; else echo __DEAD__; fi")
        assert "__DEAD__" not in text and not any(
            marker in text for marker in ("Traceback", "CUDA out of memory", "RuntimeError"))
        observed_steps = sorted(set(closure.steps(text)))
        assert len(observed_steps) >= 2
        records.append({
            "id": row["id"], "pid": row["pid"], "config": row["config"], "log": row["log"],
            "launched": row["launched"], "server": "server-6", "gpu": 7,
            "launch_verified": True, "observed_native_steps": observed_steps[-4:],
            "log_tail_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "code_commit": row["code_commit"]})
    gpu = pipeline_monitor.ssh("100.64.3.28", "songcl",
        "nvidia-smi -i 7 --query-gpu=timestamp,uuid,utilization.gpu,memory.used,memory.total "
        "--format=csv,noheader,nounits")
    processes = pipeline_monitor.ssh("100.64.3.28", "songcl",
        "nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader,nounits")
    gpu_uuid = gpu.split(",")[1].strip()
    gpu_processes = [line for line in processes.splitlines() if line.startswith(gpu_uuid)]
    assert {int(line.split(",")[1]) for line in gpu_processes} == {row["pid"] for row in tasks}
    record = {
        "contract": "bei_postlaunch_verified_v1",
        "timestamp": datetime.now().astimezone().isoformat(), "token": token,
        "experiments": records, "gpu7_csv": gpu, "gpu7_process_csv": gpu_processes,
        "local_code_commit": closure.git(ROOT / "Cluster", "rev-parse", "HEAD"),
        "remote_code_commit": pipeline_monitor.ssh(
            "100.64.3.28", "songcl",
            "git -C /data3/songcl/Project/Cluster_project/Cluster rev-parse HEAD").strip(),
        "active_authorized_slots": 2, "capacity": 2,
        "trained_efficacy_known": False}
    assert record["local_code_commit"] == record["remote_code_commit"]
    path = "pipeline/reports/bei_launch_verified_20261009-1047.json"
    with (ROOT / path).open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
    work = foreground_tick.load(ROOT / "pipeline/research_work.json")
    candidate = next(row for row in work["candidates"]
                     if row["id"] == "m95-native-mask-boundary-incidence")
    candidate.update(
        stage="training", next_action="Monitor M199 native training and apply the frozen VAL/subgroup/Pareto plan; no efficacy claim until actual results.",
        latest_progress="Gated launch verified increasing native steps on server6 GPU7; both slots occupied. Trained efficacy unknown.")
    candidate["evidence"].append({
        "path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()})
    work.pop("design_cycle", None)
    foreground_tick.save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
