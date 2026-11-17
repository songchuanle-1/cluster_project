"""One-shot, evidence-gated M186 completion and M188 FIFO dispatch."""
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
SKILL = ROOT.parent / ".claude/skills/songcl_research_pipeline"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
OLD, NEW = "M186-CTF-HCG-CSORT-MQHT-TR", "M188-CTF-HCG-CSORT-MQB-TR"
HEAD = "05335bdd15d83d106d410e03498b0c38dc9ad414"
DIGEST = "f1227f1c8efa52aac4cd170ee136701ff707b63d0bdefa27e1bc2741e7337623"
RELLOG = f"{BASE}_mqht_tr/20260910_082710/20260910_082710.log"
LOG = ROOT / "Checkpoints/server-4" / RELLOG
ANALYSIS = ROOT / f"pipeline/analyses/{OLD}_done_earlystop_20260911-031100.md"
EVIDENCE = ROOT / "pipeline/reports/m186_m188_transition_20260911.json"


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="strict", check=True, timeout=90).stdout


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location("scoped_monitor", SKILL / "pipeline_monitor.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    def decision(project, kind, question, action, basis="", evidence=""):
        return run([m.bash_executable(), str(SKILL / "log_decision.sh"),
                    "cluster_project", kind, question, action, basis, evidence])

    m.log_decision = decision
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
           f"{srv['user']}@{srv['host']}"]
    remote, q = srv["remote_code_root"], shlex.quote
    remote_log = srv["work_dir"] + "/" + RELLOG
    assert hashlib.sha256(LOG.read_bytes()).hexdigest() == DIGEST
    assert run(ssh + [f"sha256sum {q(remote_log)}"]).split()[0] == DIGEST
    rows, epoch = [], None
    text = LOG.read_text(encoding="utf-8")
    for line in text.splitlines():
        training = re.search(r"Epoch \[(\d+)/50\]", line)
        if training:
            epoch = int(training[1])
        exact = re.search(r"\bmIoU : ([0-9.]+)", line)
        if exact:
            rows.append(dict(epoch=epoch, miou=float(exact[1])))
        elif rows:
            acc = re.search(r"\bmIOU:.*?Acc_50: ([0-9.]+)", line)
            spm = re.search(r"\bspmIOU: ([0-9.]+)", line)
            if acc:
                rows[-1]["acc50"] = float(acc[1].rstrip("."))
            if spm:
                rows[-1]["spmiou"] = float(spm[1].rstrip("."))
    assert [r["epoch"] for r in rows] == list(range(1, 28))
    best = max(rows, key=lambda r: r["miou"])
    assert best == dict(epoch=17, miou=.49449968338012695, acc50=.548, spmiou=.459)
    assert all(r["miou"] < best["miou"] for r in rows[17:])
    assert text.rstrip().endswith(
        "Early stopping at epoch 27: no improvement for 10 epochs (best=0.4945)")
    assert ANALYSIS.is_file()
    lock = m.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Another pipeline writer is active")
    try:
        queue = m.load_queue(str(ROOT))
        before = copy.deepcopy(m.load_running(str(ROOT)))
        tasks = {t["id"]: t for group in queue["gpu_queues"].values() for t in group}
        processes = m.find_running_processes(srv["host"], srv["user"], remote)
        assert not any(Path(c).stem == BASE + "_mqht_tr" for c in processes)
        assert any(str(p[0]) == "2863721" and str(p[2]) == "1" for p in processes.values())
        task = tasks[NEW]
        if task["status"] == "running":
            assert task["config"] in processes and OLD not in tasks
            print("Already dispatched; no duplicate launch")
            return
        assert task["status"] == "waiting" and not task.get("dispatch_hold") and not task.get("depends_on")
        assert next(t for t in queue["gpu_queues"]["server-4"] if t["status"] == "waiting")["id"] == NEW
        assert not any(str(p[2]) == "0" for p in processes.values())
        assert srv["allowed_gpus"] == [0, 1] and srv.get("max_tasks_per_gpu", 1) == 1
        assert before["server-4"].get("0") in (None, OLD)
        cfg, name = task["config"], Path(task["config"]).stem
        resource_dir = ROOT / "pipeline/reports/m188_validation_20260909-1218"
        resource = json.loads((resource_dir / "resource_audit.json").read_text())
        row = next(r for r in resource if r["config"] == cfg)
        assert row["flops"] == 9832737324 and row["peak_allocated_mb"] <= resource[0]["peak_allocated_mb"] * 1.15
        assert (row["batch_size"], row["warmup"], row["repeat"]) == (1, 20, 100)
        assert json.loads((resource_dir / f"{name}_tests.json").read_text())["passed"]
        expected = yaml.safe_load((ROOT / "Cluster" / cfg).read_text())
        original_yaml = copy.deepcopy(expected)
        expected["work_dir"] = srv["work_dir"]
        deployed = yaml.safe_load(run(ssh + [f"cat {q(remote + '/' + cfg)}"]))
        if deployed == original_yaml:
            decision(str(ROOT), "other", "M188 deployment work_dir still points at old host path; repair?",
                     "Apply one-line server-4-only work_dir deployment patch before launch.",
                     "First helper attempt stopped before any queue change or launch; all other YAML fields match.",
                     "pipeline/bugfixes/bugfix_20260911-031400.md")
            patch = ROOT / "pipeline/headless/m188_server4_workdir_20260911.patch"
            remote_patch = "/tmp/cluster_m188_server4_workdir_20260911.patch"
            run(["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                 str(patch), f"{srv['user']}@{srv['host']}:{remote_patch}"])
            run(ssh + [f"git -C {q(remote)} apply --check {q(remote_patch)}"])
            run(ssh + [f"git -C {q(remote)} apply {q(remote_patch)}"])
        assert yaml.safe_load(run(ssh + [f"cat {q(remote + '/' + cfg)}"])) == expected
        assert expected["data"]["val"]["data_root"] == srv["data_root"]
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
        ledger = list(csv.DictReader((ROOT / "pipeline/experiments.csv").open(encoding="utf-8-sig")))
        events = []
        if OLD in tasks:
            assert tasks[OLD]["status"] == "running"
            assert not any(r["id"] == OLD for r in ledger)
            original = m.load_experiment(str(ROOT), OLD)
            decision(str(ROOT), "other", "M186 normal stop verified at27; finalize?",
                     "Archive M186 done_earlystop and release only server-4GPU0.",
                     "Best.4944996834@17;27 contiguous validations;10 stale;PID absent;log hash matches.",
                     str(ANALYSIS))
            m.pull_log = lambda *a: str(LOG)
            m.write_analysis_md = lambda *a: str(ANALYSIS)
            m.finalize_task(str(ROOT), queue, "server-4", srv["host"], srv["user"],
                            tasks[OLD], BASE + "_mqht_tr", "done_earlystop",
                            best["miou"], "27/50", "0", remote_log, events)
            exp = m.load_experiment(str(ROOT), OLD)
            assert exp["history"][:len(original["history"])] == original["history"]
            assert exp["launched"] == original["launched"]
            exp.update(ended_at_remote="2026-09-11T02:57:54.187",
                       best_miou_exact=best["miou"], best_epoch=17,
                       best_acc50=.548, best_spmiou=.459, validations_completed=27,
                       no_improve_final=10, log_sha256=DIGEST, analysis=str(ANALYSIS),
                       terminal_evidence="Explicit trainer marker and contiguous epochs; no kill")
            m.save_experiment(str(ROOT), exp)
            dw = m.load_deathwatch(str(ROOT))
            dw.get("server-4", {}).pop(BASE + "_mqht_tr", None)
            m.save_deathwatch(str(ROOT), dw)
        else:
            assert len([r for r in ledger if r["id"] == OLD and r["state"] == "done_earlystop"]) == 1
        assert not m.load_running(str(ROOT)).get("server-4", {}).get("0")
        launched = {}
        def launch(project, server, config, gpu):
            assert (server, config, str(gpu)) == ("server-4", cfg, "0")
            assert matches()
            stats = run(ssh + ["nvidia-smi -i 0 --query-gpu=utilization.gpu,memory.used,memory.free "
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
nohup python tools/train.py {q(cfg)} --gpu_ids 0 --num_gpus 1 > {q(stdout)} 2>&1 < /dev/null &
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
        decision(str(ROOT), "queue_push", "GPU0 free after M186 normal stop; dispatch FIFO?",
                 "Launch admitted legacy M188 on server-4GPU0 with non-destructive launcher.",
                 "Verified deployment YAML,seed1999,50/70,9.832737324G,CUDA tests,all HEADs; preserve other3 trainers.",
                 str(resource_dir / "resource_audit.json"))
        m.check_code_sync, m.launch_training = matches, launch
        m._process_queue(queue, "server-4", srv["host"], srv["user"], str(ROOT),
                         {"1"}, {"0"}, events, max_tasks_per_gpu=1)
        processes = m.find_running_processes(srv["host"], srv["user"], remote)
        assert task["status"] == "running"
        assert (str(processes[cfg][0]), str(processes[cfg][2])) == (str(launched["pid"]), "0")
        after = m.load_running(str(ROOT))
        assert after["server-4"] == {"0": NEW, "1": before["server-4"]["1"]}
        assert after["server-6"] == before["server-6"]
        exp = m.load_experiment(str(ROOT), NEW)
        exp.update(launched)
        m.save_experiment(str(ROOT), exp)
        evidence = dict(verified_at=datetime.now().isoformat(), terminal=best,
                        validations=rows, log_sha256=DIGEST, launches={NEW: launched},
                        running=after, events=events)
        EVIDENCE.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        m.daily_report(str(ROOT), events)
        print(json.dumps(evidence, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
