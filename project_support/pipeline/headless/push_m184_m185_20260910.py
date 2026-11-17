"""Locked, admission-gated manual dispatch without the legacy reset/clean sync."""
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess

import yaml

ROOT = Path("D:/project/cluster_project")
REPORT = ROOT / "pipeline/reports/h100_admission_20260910-0803"
HEAD = "971d65d55a9e7f341db2c170266efac28e65b2eb"
IDS = ("M184-CTF-HCG-CSORT-MQST-TR", "M185-CTF-HCG-CSORT-MQPP-TR")
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=90, **kwargs).stdout


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location(
        "manual_monitor", ROOT.parent / ".claude/skills/songcl_research_pipeline/pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-6"]
    assert srv["allowed_gpus"] == [7] and srv["max_tasks_per_gpu"] == 2
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
           f"{srv['user']}@{srv['host']}"]
    remote = srv["remote_code_root"]
    q = shlex.quote
    resources = json.loads((REPORT / "resource_audit.json").read_text())
    assert [Path(r["config"]).stem for r in resources] == [
        BASE, BASE + "_mqst_tr", BASE + "_mqpp_tr"]
    for row in resources:
        assert (row["batch_size"], row["warmup"], row["repeat"]) == (1, 20, 100)
        assert row["flops"] <= 10e9
        assert row["peak_allocated_mb"] <= 1.15 * resources[0]["peak_allocated_mb"]
    for suffix in ("mqst", "mqpp"):
        tests = json.loads((REPORT / f"{BASE}_{suffix}_tr_tests.json").read_text())
        assert tests["passed"]
        assert tests["decoder_events"] == [
            "decoder0", "decoder1", "decoder2", "decoder3", "decoder4", "refiner", "decoder5"]
    assert run(["git", "-C", str(ROOT / "Cluster"), "rev-parse", "HEAD"]).strip() == HEAD
    assert not run(["git", "-C", str(ROOT / "Cluster"), "status", "--porcelain"]).strip()

    def code_matches(*_args):
        return run(ssh + [f"git -C {q(remote)} rev-parse HEAD"]).strip() == HEAD

    assert code_matches()
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Pipeline writer active; no migration or launch attempted")
    try:
        queue = monitor.load_queue(str(ROOT))
        tasks = {t["id"]: t for group in queue["gpu_queues"].values() for t in group}
        if all(tasks[i]["status"] == "running" for i in IDS):
            print("Both already running; no duplicate launch")
            return
        assert all(tasks[i]["status"] == "waiting" for i in IDS)
        assert all(not tasks[i].get("dispatch_hold") and not tasks[i].get("depends_on") for i in IDS)
        waiting = [t["id"] for t in queue["gpu_queues"]["server-4"] if t["status"] == "waiting"]
        assert waiting[:2] == list(IDS)
        assert not any(t["status"] in ("waiting", "running", "claiming")
                       for t in queue["gpu_queues"]["server-6"])
        assert not monitor.load_running(str(ROOT)).get("server-6")
        assert not monitor.find_running_processes(srv["host"], srv["user"], remote)
        gpu = run(ssh + ["nvidia-smi -i 7 --query-gpu=utilization.gpu,memory.used,memory.total "
                         "--format=csv,noheader,nounits"]).strip()
        util, used, total = map(int, gpu.split(","))
        assert util < 10 and used < 1000 and total - used > 40000, gpu
        configs = {tasks[i]["config"]: yaml.safe_load(
            (ROOT / "Cluster" / tasks[i]["config"]).read_text()) for i in IDS}
        for cfg in configs.values():
            assert cfg["train"]["seed"] == 1999 and cfg["train"]["epochs"] == 50
            assert cfg["lr_scheduler"]["max_iters"] == 70
        local = servers["local"]
        payload = {"configs": configs, "root": remote, "report": str(Path(remote).parent).replace("\\", "/")
                   + "/pipeline/reports/h100_admission_20260910-0803",
                   "old_data": local["data_root"], "new_data": srv["data_root"],
                   "old_work": local["work_dir"], "new_work": srv["work_dir"]}
        # Parse YAML and change deployment paths only, never model or schedule values.
        adapt = """
import copy, json, pathlib, sys, yaml
p = json.loads(sys.argv[1])
for name, expected in p["configs"].items():
    path = pathlib.Path(p["root"]) / name
    before = path.read_bytes()
    current = yaml.safe_load(before)
    changed = copy.deepcopy(expected)
    changed["work_dir"] = p["new_work"]
    changed["train"]["pretrain"] = p["new_data"].rstrip("/") + "/sp_unet_backbone.pth"
    for split in changed["data"].values():
        split["data_root"] = p["new_data"]
    changed["model"]["data_root"] = p["new_data"]
    assert current == expected or current == changed, name
    assert pathlib.Path(changed["train"]["pretrain"]).is_file()
    assert pathlib.Path(p["new_data"], "scanrefer").is_dir()
    assert pathlib.Path(p["new_work"]).is_dir()
    if current != changed:
        backup = pathlib.Path(p["report"]) / (path.name + ".before")
        if not backup.exists():
            backup.write_bytes(before)
        path.write_text(yaml.safe_dump(changed, sort_keys=False))
    assert yaml.safe_load(path.read_text()) == changed
    print("deployment_paths_verified", name)
"""
        print(run(ssh + [f"{q(srv['conda_source'].replace('/etc/profile.d/conda.sh', '/envs/project_cluster/bin/python'))} "
                         f"-c {q(adapt)} {q(json.dumps(payload))}"]))
        now = datetime.now().isoformat(timespec="seconds")
        monitor.log_decision(
            str(ROOT), "manual", "User requested immediate experiment dispatch.",
            "Migrate FIFO M184 and M185 to server-6 GPU7, two slots; launch after H100 admission.",
            "Explicit user push; CUDA tests and matched <=10G resource audit passed. "
            "Only deployment paths adapted; safe ff-only sync already verified; no external overlay.",
            str(REPORT / "resource_audit.json"))
        for exp_id in IDS:
            task = tasks[exp_id]
            queue["gpu_queues"]["server-4"].remove(task)
            task["gpu"] = 7
            task["admission_report"] = "pipeline/reports/h100_admission_20260910-0803/resource_audit.json"
            queue["gpu_queues"]["server-6"].append(task)
            exp = monitor.load_experiment(str(ROOT), exp_id)
            exp.update(server="server-6", gpu="7", admission_report=task["admission_report"])
            exp.setdefault("history", []).append({
                "ts": now, "action": "manual_placement", "from_server": "server-4",
                "server": "server-6", "gpu": "7", "reason": "User requested push; H100 admission passed"})
            monitor.save_experiment(str(ROOT), exp)
        monitor.save_queue(str(ROOT), queue)
        launched = {}

        def launch(_project, server_name, config, gpu_ids):
            assert server_name == "server-6" and str(gpu_ids) == "7"
            assert config in configs and code_matches()
            assert config not in monitor.find_running_processes(srv["host"], srv["user"], remote)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = Path(config).stem
            stdout = f"{remote}/logs/train_{name}_{stamp}.log"
            command = f"""
set -e
cd {q(remote)}
source {q(srv["conda_source"])}
conda activate {q(srv["conda_env"])}
export PYTHONPATH={q(remote)}:{q(remote + "/framework/lib")}:${{PYTHONPATH:-}}
export LD_LIBRARY_PATH=$(python -c 'import torch,os;print(os.path.dirname(torch.__file__))')/lib:$(find ${{CONDA_PREFIX}}/lib/python*/site-packages/nvidia/cuda_runtime/lib -maxdepth 0 2>/dev/null):${{LD_LIBRARY_PATH:-}}
mkdir -p logs
nohup python tools/train.py {q(config)} --gpu_ids 7 --num_gpus 1 > {q(stdout)} 2>&1 < /dev/null &
pid=$!
printf '%s\\n' "$pid" > {q(remote + "/logs/.pid_" + name)}
echo "TRAIN_PID=$pid"
sleep 5
kill -0 "$pid"
"""
            out = run(ssh + [command])
            print(out)
            pid = next(int(line.split("=")[1]) for line in out.splitlines() if line.startswith("TRAIN_PID="))
            launched[config] = {"pid": pid, "stdout_log": stdout}
            return True

        monitor.check_code_sync = code_matches
        monitor.launch_training = launch
        events = []
        monitor._process_queue(queue, "server-6", srv["host"], srv["user"], str(ROOT),
                               set(), {"7"}, events, max_tasks_per_gpu=2)
        processes = monitor.find_running_processes(srv["host"], srv["user"], remote)
        for exp_id in IDS:
            task = tasks[exp_id]
            assert task["status"] == "running", task
            cfg = task["config"]
            assert str(processes[cfg][0]) == str(launched[cfg]["pid"])
            assert str(processes[cfg][2]) == "7"
            exp = monitor.load_experiment(str(ROOT), exp_id)
            exp.update(launched[cfg])
            monitor.save_experiment(str(ROOT), exp)
        evidence = {"verified_at": datetime.now().isoformat(), "launches": launched,
                    "events": events, "running": monitor.load_running(str(ROOT))}
        (REPORT / "dispatch.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps(evidence, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
