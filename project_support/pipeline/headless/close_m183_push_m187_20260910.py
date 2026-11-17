"""Evidence-gated terminal reconciliation and safe FIFO successor dispatch."""
import copy
import csv
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

import yaml

ROOT = Path("D:/project/cluster_project")
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
OLD = "M183-CTF-HCG-CSORT-HQI"
NEW = "M187-CTF-HCG-CSORT-MQFC-TR"
HEAD = "b171bd6d3487948f294f5994eda613d0aa052713"
DIGEST = "d2fcedfc902e9274687c0f6327c311536b735e97a31d1f3eefc73d421a4cc80e"
RELLOG = f"{BASE}_hqi/20260909_120847/20260909_120847.log"
LOG = ROOT / "Checkpoints/server-4" / RELLOG
ANALYSIS = ROOT / f"pipeline/analyses/{OLD}_done_earlystop_20260910-131000.md"


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="strict", check=True, timeout=90).stdout


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location(
        "scoped_monitor", ROOT.parent / ".claude/skills/songcl_research_pipeline/pipeline_monitor.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
           f"{srv['user']}@{srv['host']}"]
    remote = srv["remote_code_root"]
    q = shlex.quote
    remote_log = srv["work_dir"] + "/" + RELLOG
    assert hashlib.sha256(LOG.read_bytes()).hexdigest() == DIGEST
    assert run(ssh + [f"sha256sum {q(remote_log)}"]).split()[0] == DIGEST
    text = LOG.read_text(encoding="utf-8")
    rows, epoch = [], None
    for line in text.splitlines():
        training = re.search(r"Epoch \[(\d+)/50\]", line)
        if training:
            epoch = int(training[1])
        exact = re.search(r"\bmIoU : ([0-9.]+)", line)
        if exact:
            rows.append({"epoch": epoch, "miou": float(exact[1])})
        elif rows:
            acc = re.search(r"\bmIOU:.*?Acc_50: ([0-9.]+)", line)
            spm = re.search(r"\bspmIOU: ([0-9.]+)", line)
            if acc:
                rows[-1]["acc50"] = float(acc[1].rstrip("."))
            if spm:
                rows[-1]["spmiou"] = float(spm[1].rstrip("."))
    assert [r["epoch"] for r in rows] == list(range(1, 25))
    best = max(rows, key=lambda r: r["miou"])
    assert best == dict(epoch=14, miou=0.49154922366142273, acc50=.545, spmiou=.455)
    assert all(r["miou"] < best["miou"] for r in rows[14:])
    assert text.rstrip().endswith(
        "Early stopping at epoch 24: no improvement for 10 epochs (best=0.4915)")
    assert ANALYSIS.is_file()
    lock = m.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Pipeline writer active; nothing changed")
    try:
        queue = m.load_queue(str(ROOT))
        before = copy.deepcopy(m.load_running(str(ROOT)))
        tasks = {t["id"]: t for group in queue["gpu_queues"].values() for t in group}
        processes = m.find_running_processes(srv["host"], srv["user"], remote)
        assert not any(Path(c).stem == BASE + "_hqi" for c in processes)
        assert any(str(p[0]) == "1982211" for p in processes.values())
        ledger = list(csv.DictReader((ROOT / "pipeline/experiments.csv").open(encoding="utf-8-sig")))
        events = []
        if OLD in tasks:
            assert tasks[OLD]["status"] == "running"
            assert not any(r["id"] == OLD for r in ledger)
            original = m.load_experiment(str(ROOT), OLD)
            m.log_decision(str(ROOT), "other",
                           "M183 has an explicit normal-stop marker and24 exact validations; finalize?",
                           "Archive M183 done_earlystop and release only server-4GPU1 ownership.",
                           "Best.4915492237@14,10 real post-best validations; PID absent; immutable log hash verified. No retry.",
                           str(ANALYSIS))
            m.pull_log = lambda *a: str(LOG)
            m.write_analysis_md = lambda *a: str(ANALYSIS)
            m.finalize_task(str(ROOT), queue, "server-4", srv["host"], srv["user"],
                            tasks[OLD], BASE + "_hqi", "done_earlystop",
                            best["miou"], "24/50", "1", remote_log, events)
            exp = m.load_experiment(str(ROOT), OLD)
            assert exp["history"][:len(original["history"])] == original["history"]
            assert exp["launched"] == original["launched"]
            exp.update(ended_at_remote="2026-09-10T12:40:45.686",
                       best_miou_exact=best["miou"], best_epoch=14,
                       best_acc50=.545, best_spmiou=.455, validations_completed=24,
                       no_improve_final=10, log_sha256=DIGEST, analysis=str(ANALYSIS),
                       terminal_evidence="Explicit trainer marker and contiguous epochs; no kill")
            m.save_experiment(str(ROOT), exp)
            dw = m.load_deathwatch(str(ROOT))
            dw.get("server-4", {}).pop(BASE + "_hqi", None)
            m.save_deathwatch(str(ROOT), dw)
            m.daily_report(str(ROOT), events)
        else:
            assert len([r for r in ledger if r["id"] == OLD and r["state"] == "done_earlystop"]) == 1
        task = tasks[NEW]
        if task["status"] == "claiming":
            assert task["config"] not in processes
            assert not m.load_running(str(ROOT)).get("server-4", {}).get("1")
            exp = m.load_experiment(str(ROOT), NEW)
            assert exp["status"] == "waiting" and not exp.get("launched")
            m.log_decision(str(ROOT), "other", "M187 launcher failed before SSH at missing conda_source; recover claim?",
                           "Restore only M187 claiming to waiting, then retry with full SERVERS.yaml configuration.",
                           "No remote matching process, no running owner and registry still waiting; model was not launched. Helper repair1.",
                           "pipeline/bugfixes/bugfix_20260910-131400.md")
            task["status"] = "waiting"
            m.save_queue(str(ROOT), queue)
        if task["status"] == "running":
            assert task["config"] in processes
            print("Already dispatched; no duplicate launch")
            return
        assert task["status"] == "waiting" and not task.get("dispatch_hold") and not task.get("depends_on")
        assert next(t for t in queue["gpu_queues"]["server-4"] if t["status"] == "waiting")["id"] == NEW
        assert not m.load_running(str(ROOT)).get("server-4", {}).get("1")
        assert not any(str(p[2]) == "1" for p in processes.values())
        assert srv["allowed_gpus"] == [0, 1] and srv.get("max_tasks_per_gpu", 1) == 1
        cfg, name = task["config"], Path(task["config"]).stem
        resource_dir = ROOT / "pipeline/reports/tr_validation_20260908-1924"
        resource = json.loads((resource_dir / "resource_audit.json").read_text())
        row = next(r for r in resource if r["config"] == cfg)
        assert row["flops"] <= 10e9 and row["peak_allocated_mb"] <= resource[0]["peak_allocated_mb"] * 1.15
        assert (row["batch_size"], row["warmup"], row["repeat"]) == (1, 20, 100)
        assert json.loads((resource_dir / f"{name}_tests.json").read_text())["passed"]
        expected = yaml.safe_load((ROOT / "Cluster" / cfg).read_text())
        expected["work_dir"] = srv["work_dir"]
        assert yaml.safe_load(run(ssh + [f"cat {q(remote + '/' + cfg)}"])) == expected
        assert (expected["train"]["seed"], expected["train"]["epochs"],
                expected["lr_scheduler"]["max_iters"]) == (1999, 50, 70)
        assert not run(["git", "-C", str(ROOT / "Cluster"), "status", "--porcelain"]).strip()
        for server in ("server-4", "server-6"):
            s = servers[server]
            assert run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                        f"{s['user']}@{s['host']}", f"git -C {q(s['remote_code_root'])} rev-parse HEAD"]).strip() == HEAD

        def matches(*args):
            return (run(["git", "-C", str(ROOT / "Cluster"), "rev-parse", "HEAD"]).strip()
                    == run(ssh + [f"git -C {q(remote)} rev-parse HEAD"]).strip() == HEAD)

        assert matches()
        launched = {}

        def launch(project, server, config, gpu):
            assert (server, config, str(gpu)) == ("server-4", cfg, "1")
            assert matches()
            stats = run(ssh + ["nvidia-smi -i 1 --query-gpu=utilization.gpu,memory.used,memory.free "
                              "--format=csv,noheader,nounits"]).strip()
            util, used, free = map(int, stats.split(","))
            assert util < 10 and used < 1024 and free > 24000
            assert cfg not in m.find_running_processes(srv["host"], srv["user"], remote)
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
nohup python tools/train.py {q(cfg)} --gpu_ids 1 --num_gpus 1 > {q(stdout)} 2>&1 < /dev/null &
pid=$!
printf '%s\\n' "$pid" > {q(remote + "/logs/.pid_" + name)}
echo "TRAIN_PID=$pid"
sleep 5
kill -0 "$pid"
"""
            out = run(ssh + [command])
            launched.update(pid=int(next(l.split("=")[1] for l in out.splitlines()
                                         if l.startswith("TRAIN_PID="))), stdout_log=stdout)
            return True

        m.log_decision(str(ROOT), "queue_push", "GPU1 free after verified M183 normal stop; dispatch FIFO successor?",
                       "Launch admitted M187-MQFC-TR on server-4GPU1 using scoped non-destructive launcher.",
                       "Same HEAD both servers; measured9.843485228G; CUDA topology tests passed; no external overlay; preserve other3 trainers.",
                       "pipeline/reports/tr_validation_20260908-1924/resource_audit.json")
        m.check_code_sync, m.launch_training = matches, launch
        m._process_queue(queue, "server-4", srv["host"], srv["user"], str(ROOT),
                         {"0"}, {"1"}, events, max_tasks_per_gpu=1)
        processes = m.find_running_processes(srv["host"], srv["user"], remote)
        assert task["status"] == "running"
        assert (str(processes[cfg][0]), str(processes[cfg][2])) == (str(launched["pid"]), "1")
        after = m.load_running(str(ROOT))
        assert after["server-4"] == {"0": before["server-4"]["0"], "1": NEW}
        assert after["server-6"] == before["server-6"]
        exp = m.load_experiment(str(ROOT), NEW)
        exp.update(launched)
        m.save_experiment(str(ROOT), exp)
        evidence = dict(verified_at=datetime.now().isoformat(), terminal=best,
                        validations=rows, log_sha256=DIGEST, launches={NEW: launched},
                        running=after, events=events)
        (ROOT / "pipeline/reports/m183_m187_transition_20260910.json").write_text(
            json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps(evidence, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
