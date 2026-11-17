"""One-shot user-directed GPU0 overlay, preserving every existing workload."""
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import shlex

import yaml
from push_m184_m185_20260910 import run, ROOT, HEAD


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location(
        "overlay_monitor", ROOT.parent / ".claude/skills/songcl_research_pipeline/pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    srv = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", f"{srv['user']}@{srv['host']}"]
    remote = srv["remote_code_root"]
    q = shlex.quote
    exp_id = "M186-CTF-HCG-CSORT-MQHT-TR"
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Active pipeline writer; nothing launched")
    try:
        queue = monitor.load_queue(str(ROOT))
        task = next(t for t in queue["gpu_queues"]["server-4"] if t["id"] == exp_id)
        assert task["status"] == "waiting"
        assert next(t for t in queue["gpu_queues"]["server-4"]
                    if t["status"] == "waiting")["id"] == exp_id
        assert not task.get("dispatch_hold") and not task.get("depends_on")
        cfg = task["config"]
        name = Path(cfg).stem
        audit = ROOT / "pipeline/reports/tr_validation_20260908-1924"
        resources = json.loads((audit / "resource_audit.json").read_text())
        row = next(r for r in resources if r["config"] == cfg)
        assert row["flops"] <= 10e9
        assert row["peak_allocated_mb"] <= resources[0]["peak_allocated_mb"] * 1.15
        assert (row["batch_size"], row["warmup"], row["repeat"]) == (1, 20, 100)
        assert json.loads((audit / f"{name}_tests.json").read_text())["passed"]
        before = monitor.load_running(str(ROOT))
        assert not before.get("server-4", {}).get("0")
        processes = monitor.find_running_processes(srv["host"], srv["user"], remote)
        assert not any(str(p[2]) == "0" for p in processes.values())
        assert cfg not in processes
        stats = run(ssh + ["nvidia-smi -i 0 --query-gpu=utilization.gpu,memory.used,memory.free "
                           "--format=csv,noheader,nounits"]).strip()
        util, used, free = map(int, stats.split(","))
        assert util < 10 and free > 24000, stats
        assert 0 in srv["allowed_gpus"]
        local = yaml.safe_load((ROOT / "Cluster" / cfg).read_text())
        actual = yaml.safe_load(run(ssh + [f"cat {q(remote + '/' + cfg)}"]))
        local["work_dir"] = srv["work_dir"]
        assert actual == local, "Unexpected deployment or training configuration difference"
        assert (actual["train"]["seed"], actual["train"]["epochs"],
                actual["lr_scheduler"]["max_iters"]) == (1999, 50, 70)

        def code_matches(*_args):
            return (run(["git", "-C", str(ROOT / "Cluster"), "rev-parse", "HEAD"]).strip()
                    == run(ssh + [f"git -C {q(remote)} rev-parse HEAD"]).strip() == HEAD)

        assert code_matches()
        monitor.log_decision(
            str(ROOT), "manual", "User asks to push on server-4 because sufficient memory remains.",
            "One-shot M186 launch on server-4 GPU0 alongside existing external PID3867104.",
            f"GPU0 {stats}; free>24000MiB with typical project training about20000MiB; "
            "existing M186 server-4 admission passed. Preserve external process and M183. "
            "No persistent global overlay policy change; GPU1 has insufficient remaining memory.",
            "pipeline/reports/tr_validation_20260908-1924/resource_audit.json")
        launched = {}

        def launch(_project, server, config, gpu):
            assert (server, config, str(gpu)) == ("server-4", cfg, "0")
            assert code_matches()
            memory = int(run(ssh + [
                "nvidia-smi -i 0 --query-gpu=memory.free --format=csv,noheader,nounits"]).strip())
            assert memory > 24000
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stdout = f"{remote}/logs/train_{name}_{stamp}.log"
            command = f"""
set -e
cd {q(remote)}
source {q(srv["conda_source"])}
conda activate {q(srv["conda_env"])}
export PYTHONPATH={q(remote)}:{q(remote + "/framework/lib")}:${{PYTHONPATH:-}}
export LD_LIBRARY_PATH=$(python -c 'import torch,os;print(os.path.dirname(torch.__file__))')/lib:$(find ${{CONDA_PREFIX}}/lib/python*/site-packages/nvidia/cuda_runtime/lib -maxdepth 0 2>/dev/null):${{LD_LIBRARY_PATH:-}}
mkdir -p logs
nohup python tools/train.py {q(cfg)} --gpu_ids 0 --num_gpus 1 > {q(stdout)} 2>&1 < /dev/null &
pid=$!
printf '%s\\n' "$pid" > {q(remote + "/logs/.pid_" + name)}
echo "TRAIN_PID=$pid"
sleep 5
kill -0 "$pid"
"""
            output = run(ssh + [command])
            print(output)
            launched.update(pid=int(next(l.split("=")[1] for l in output.splitlines()
                                         if l.startswith("TRAIN_PID="))), stdout_log=stdout)
            return True

        monitor.check_code_sync = code_matches
        monitor.launch_training = launch
        events = []
        monitor._process_queue(queue, "server-4", srv["host"], srv["user"], str(ROOT),
                               {"1"}, {"0"}, events, max_tasks_per_gpu=1,
                               allow_external_overlay=True, task_memory_mb=24000)
        assert task["status"] == "running"
        processes = monitor.find_running_processes(srv["host"], srv["user"], remote)
        assert str(processes[cfg][0]) == str(launched["pid"]) and str(processes[cfg][2]) == "0"
        after = monitor.load_running(str(ROOT))
        assert after["server-4"]["0"] == exp_id
        assert after["server-4"]["1"] == before["server-4"]["1"]
        assert after["server-6"] == before["server-6"]
        exp = monitor.load_experiment(str(ROOT), exp_id)
        exp.update(launched)
        monitor.save_experiment(str(ROOT), exp)
        evidence = {"verified_at": datetime.now().isoformat(), "id": exp_id,
                    **launched, "preflight_gpu0": stats, "events": events, "running": after}
        path = ROOT / "pipeline/reports/dispatch_m186_20260910.json"
        path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps(evidence, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
