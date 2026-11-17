"""Finalize only the independently verified M191 normal stop, under pipeline lock."""
import copy
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex

import yaml

from run_d1_head_20260911 import run, sha
from close_m185_20260912 import parse_log

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/source_head_interference_20260913-1938"
EID = "M191-CTF-HCG-CSORT-MQSD-TR"
ANALYSIS = P / f"analyses/{EID}_done_earlystop_20260913-1953.md"


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("monitor", skill / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    srv = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
    live = json.loads((OUT / "live.json").read_text())["live"][0]
    assert live["id"] == EID and live["early_stop"] and not live["trainer_present"]
    remote_log = live["remote_log"]
    host = f"{srv['user']}@{srv['host']}"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
    raw = run(ssh + ["cat " + shlex.quote(remote_log)])
    digest = run(ssh + ["sha256sum " + shlex.quote(remote_log)]).decode().split()[0]
    text = raw.decode()
    rows = parse_log(text)
    assert [r["epoch"] for r in rows] == list(range(1, 26))
    assert re.findall(r"Evaluate referring segmentation:\s*(\d+)", text) == ["9508"] * 25
    best = max(rows, key=lambda r: r["miou"])
    assert best == dict(epoch=15, miou=.4917144179344177, acc50=.541, spmiou=.457)
    assert all(r["miou"] < best["miou"] for r in rows[15:])
    assert text.rstrip().endswith("Early stopping at epoch 25: no improvement for 10 epochs (best=0.4917)")
    log = ROOT / "Checkpoints/server-4" / Path(remote_log).relative_to(srv["work_dir"])
    log.parent.mkdir(parents=True, exist_ok=True)
    run(["scp", "-q", f"{host}:{remote_log}", str(log)])
    assert sha(log) == digest
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None, "Concurrent writer owns lock"
    try:
        queue = monitor.load_queue(str(ROOT))
        running = monitor.load_running(str(ROOT))
        tasks = {t["id"]: t for g in queue["gpu_queues"].values() for t in g}
        assert tasks[EID]["status"] == "running"
        assert running["server-4"]["1"] == EID
        other = copy.deepcopy(running["server-4"]["0"])
        original = monitor.load_experiment(str(ROOT), EID)
        other_exp_path = P / f"experiments/{other}.json"
        other_sha = sha(other_exp_path)
        processes = run(ssh + ["ps -eo pid,args"]).decode()
        base = Path(original["config"]).stem
        assert not any(base in line and "tools/train.py" in line for line in processes.splitlines())
        run([monitor.bash_executable(), str(skill / "log_decision.sh"),
             "cluster_project", "other",
             "M191 completed 25 validations and normal patience10 stop; reconcile?",
             "Archive M191 done_earlystop and release only its server-4 GPU1 registry slot; preserve M193.",
             "Exact best .4917144179344177 at15; ten stale, explicit stop19:50:38, no process, raw archive hash verified.",
             str(ANALYSIS)])
        monitor.pull_log = lambda *args: str(log)
        monitor.write_analysis_md = lambda *args: str(ANALYSIS)
        events = []
        monitor.finalize_task(str(ROOT), queue, "server-4", srv["host"], srv["user"],
            tasks[EID], base, "done_earlystop", best["miou"], "25/50", "1", remote_log, events)
        exp = monitor.load_experiment(str(ROOT), EID)
        assert exp["history"][:len(original["history"])] == original["history"]
        exp.update(best_miou_exact=best["miou"], best_epoch=15, best_acc50=.541,
            best_spmiou=.457, validations_completed=25, no_improve_final=10,
            ended_at_remote="2026-09-13 19:50:38.085", log_sha256=digest, analysis=str(ANALYSIS),
            terminal_evidence="Explicit normal stop, 25 contiguous9508 validations, absent process, raw archive hash verified.")
        monitor.save_experiment(str(ROOT), exp)
        watch = monitor.load_deathwatch(str(ROOT))
        watch.get("server-4", {}).pop(base, None)
        monitor.save_deathwatch(str(ROOT), watch)
        after = monitor.load_running(str(ROOT))
        assert after["server-4"] == {"0": other} and sha(other_exp_path) == other_sha
        evidence = dict(at=datetime.now().isoformat(), best=best, final=rows[-1],
                        validations=rows, remote_log=remote_log, archive=str(log),
                        log_sha256=digest, running=after, events=events)
        (OUT / "m191_closure.json").write_text(json.dumps(evidence, indent=2))
        print(json.dumps({k:v for k,v in evidence.items() if k != "validations"}, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
