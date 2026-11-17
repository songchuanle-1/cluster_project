"""Root-only canonical one-shot dispatch; default NOP; preserve uncertain launches."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
DRAFT_EXECUTION_DISABLED = False
EXPECTED_OWNER = {'token': '8a3431facc69449d9cbb681e512733aa', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-08T17:12:25.818193+00:00', 'deadline_at': '2026-11-08T18:12:25.818193+00:00', 'context_sha256': '17d3570ccf2b9677ea549d0757a5615a23f8d370950789ff485f59cc821814c9', 'pending_sha256': '5ac1360d2e0a47c22aa15d5e24144abb7cfd41f5ee33467a735bce1e6101ba06'}
TOKEN = '8a3431facc69449d9cbb681e512733aa'
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
SOURCE = '0747f6acec1c61018ec99acf2efa5329c9b3523c'
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
GPU_UUID = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
SKILL = "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard():
    assert not DRAFT_EXECUTION_DISABLED, "Disabled NSD dispatch template; separate reviewed root activation required"
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD == os.environ["CODEX_THREAD_ID"]
    assert {k:owner[k] for k in EXPECTED_OWNER}==EXPECTED_OWNER
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 100
    for name, field in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[field]
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    return owner


CALLS = []


def ssh(host, user, command, timeout=100):
    guard()
    assert (host, user) == ("192.168.1.115", "songcl")
    probe = re.fullmatch(r"if kill -0 ([0-9]+) 2>/dev/null; then tail -c 24000 (.+); else echo __DEAD__; fi", command)
    actual = command
    if probe:
        pid = int(probe[1])
        logfile = shlex.split(probe[2])
        assert len(logfile) == 1 and logfile[0].startswith(RUNTIME + "/logs/")
        program = (
            "from pathlib import Path;import os,sys;"
            f"p=Path('/proc/{pid}');f=Path({logfile[0]!r});"
            "alive=p.is_dir() and (p/'stat').read_text().split(')')[-1].split()[0]!='Z';"
            "sys.stdout.write('__DEAD__') if not alive else None;"
            "h=f.open('rb') if alive and f.is_file() else None;"
            "h.seek(max(0,f.stat().st_size-24000)) if h else None;"
            "sys.stdout.write(h.read(24000).decode('utf8',errors='replace')) if h else None"
        )
        actual = "/usr/bin/python3 -B -c " + shlex.quote(program)
    else:
        assert not re.search(r"\b(kill|pkill|killall|reboot|shutdown)\b", command)
    pin = "test \"$(hostname)\" = dl04-MS-7E06 && "
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "songcl@192.168.1.115", pin + actual],
        capture_output=True, text=True, encoding="utf8", errors="replace", timeout=timeout,
    )
    number = len(CALLS)
    stdout = HERE / f"nde_dispatch_ssh_{number:02d}.stdout"
    stderr = HERE / f"nde_dispatch_ssh_{number:02d}.stderr"
    with stdout.open("x", encoding="utf8") as stream:
        stream.write(result.stdout)
    with stderr.open("x", encoding="utf8") as stream:
        stream.write(result.stderr)
    CALLS.append({"ordinal": number, "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
                  "returncode": result.returncode, "read_only_proc_replaced_existence_probe": bool(probe),
                  "stdout": {"path": stdout.relative_to(ROOT).as_posix(), "sha256": sha(stdout)},
                  "stderr": {"path": stderr.relative_to(ROOT).as_posix(), "sha256": sha(stderr)}})
    assert result.returncode == 0, result.stderr[-1000:]
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--production-result")
    parser.add_argument("--production-review")
    parser.add_argument("--production-review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_QUEUE_OR_LAUNCH"}))
        return
    owner = guard()
    assert not (HERE / "nde_dispatch_intent.json").exists(), "Existing intent: reconcile, never replay"
    review = Path(args.production_review)
    assert sha(review) == args.production_review_sha256
    review_data = read(review)
    assert review_data["passed"] is True
    production_path = Path(args.production_result)
    assert review_data["production_result_sha256"] == sha(production_path)
    production = read(production_path)
    assert production["kind"] == "PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED"
    assert production["owner"] == EXPECTED_OWNER
    assert production["binding"]["runtime_root"] == RUNTIME and production["binding"]["source_commit"] == SOURCE
    assert production["training_launch_or_GPU_use"] is False and production["one_shot_consumed"] is False
    import yaml
    raw = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf8"))["servers"]["server-4"]
    assert raw["remote_code_root"] == RUNTIME and raw["conda_source"] == production["shim"]
    assert production["shim"]=="/data/songcl/Project/Cluster_project/pipeline/runtime/nde_path_prod_8a3431fa/conda_source.sh"
    assert raw["allowed_gpus"] == [0] and raw["max_tasks_per_gpu"] == 1
    assert raw["allow_external_overlay"] is True and raw["task_memory_mb"] == 20000
    assert raw["expected_hostname"] == "dl04-MS-7E06"
    assert str(raw["expected_gpu_uuids"].get("0", raw["expected_gpu_uuids"].get(0))) == GPU_UUID
    sys.path.insert(0, SKILL)
    import closure
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        queue = monitor.load_queue(str(ROOT))
        eligible = [t for ts in queue["gpu_queues"].values() for t in ts
                    if t.get("status") == "waiting" and not t.get("dispatch_hold")]
        assert len(eligible) == 1 and eligible[0]["id"] == "M233-NDE"
        assert not [t for ts in queue["gpu_queues"].values() for t in ts if t.get("status") in ("running", "claiming")]
        task = eligible[0]
        assert task["code_commit"] == SOURCE and not task.get("resume_authorized") and not task.get("resume_from")
        closure.admission(ROOT, task)
        before = TICK / "protected_assets_before.json"
        assert all(sha(ROOT / "Cluster" / p) == value for p, value in read(before)["files"].items())
        server = monitor.load_servers(str(ROOT))["server-4"]
        original_ssh = monitor.ssh
        monitor.ssh = ssh
        try:
            program = r'''
from pathlib import Path
from datetime import datetime,timezone
import os,json,subprocess,hashlib,fcntl
assert os.getuid()==1001
root=Path(P["root"])
assert subprocess.check_output(["git","--no-optional-locks","-C",str(root),"rev-parse","HEAD"],text=True).strip()==P["source"]
for relative,expected in P["files"].items():
 assert hashlib.sha256((Path(P["stage"])/relative).read_bytes()).hexdigest()==expected
assert not Path(P["marker"]).exists()
assert hashlib.sha256((root/P["config"]).read_bytes()).hexdigest()==P["config_sha256"]
row=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu","--format=csv,noheader,nounits"],text=True).strip()
v=[s.strip() for s in row.split(",")]
assert v[:2]==["0",P["uuid"]]
assert int(v[3])-int(v[2])>=20000
contexts=subprocess.check_output(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],text=True).strip()
trainers=[]
for proc in Path("/proc").iterdir():
 if not proc.name.isdigit():continue
 try:
  if proc.stat().st_uid!=os.getuid():continue
  argv=[s.decode(errors="replace") for s in (proc/"cmdline").read_bytes().split(b"\0") if s]
  if not any(arg=="tools/train.py" or arg.endswith("/tools/train.py") for arg in argv):continue
  cwd=os.readlink(proc/"cwd")
  if cwd.startswith("/data/songcl/Project/Cluster_project/"):trainers.append({"pid":int(proc.name),"argv":argv,"cwd":cwd})
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
assert not trainers,"Actual project trainer exists; reconcile"
for item in P["locks"]:
 path=Path(item["path"]);s=path.stat()
 assert (s.st_dev,s.st_ino)==(item["dev"],item["ino"])
 with path.open("r+b") as handle:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
print(json.dumps({"observed_at":datetime.now(timezone.utc).isoformat(),"gpu_row":row,
 "free_memory_mib":int(v[3])-int(v[2]),"contexts":contexts,"project_trainers":trainers,
 "three_original_inodes_available":True,"all_production_bytes_verified":True,
 "overlay_authorized":True,"exclusive_performance_claimed":False,"signals_sent":False}))
'''
            params = {"root": RUNTIME, "source": SOURCE, "uuid": GPU_UUID,
                      "stage": production["binding"]["stage"], "files": production["files"],
                      "marker": production["binding"]["one_shot_marker"],
                      "config": task["config"],
                      "config_sha256": production["binding"]["runtime_config_sha256"],
                      "locks": production["binding"]["lock_files"]}
            observation = json.loads(ssh(server["host"], server["user"],
                "/usr/bin/python3 -B -c " + shlex.quote("P=" + repr(params) + "\n" + program)))
            save(HERE / "nde_prelaunch_actual_resources.json", observation)
            # Canonical monitor/closure retain admission, source, live memory,
            # concurrency and progress gates. The exact existence probe above
            # is read-only; no process signal is sent.
            save(HERE / "nde_dispatch_intent.json", {
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "owner": {k: owner[k] for k in ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")},
                "source": SOURCE, "runtime_root": RUNTIME, "task": task,
                "production_result_sha256": sha(production_path),
                "production_review_sha256": sha(review),
                "no_replay": True,
            })
            events = []
            monitor._process_queue(
                queue, "server-4", server["host"], server["user"], str(ROOT), set(), {"0"}, events,
                max_tasks_per_gpu=1, allow_external_overlay=True, task_memory_mb=20000,
                remote_code_root=RUNTIME, current_tasks=0, max_tasks_total=1,
            )
        finally:
            monitor.ssh = original_ssh
        current = read(ROOT / "pipeline/queue.json")
        actual = next(t for t in current["gpu_queues"]["server-4"] if t["id"] == "M233-NDE")
        save(HERE / "nde_dispatch_result.json", {
            "recorded_at": datetime.now(timezone.utc).isoformat(), "owner_token": TOKEN,
            "task": actual, "canonical_events": events, "ssh_calls": CALLS,
            "signals_sent": False, "launch_verified": actual.get("launch_verified") is True,
        })
        print(json.dumps({"id": actual["id"], "status": actual["status"],
                          "pid": actual.get("pid"), "launch_verified": actual.get("launch_verified"),
                          "log": actual.get("log"), "dispatch_hold": actual.get("dispatch_hold")}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
