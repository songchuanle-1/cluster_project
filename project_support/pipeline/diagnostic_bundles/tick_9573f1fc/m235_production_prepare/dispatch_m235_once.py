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
EXPECTED_OWNER = {'token': '9573f1fc8cad435fb47660949b563298', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-10T11:34:11.138562+00:00', 'deadline_at': '2026-11-10T12:34:11.138562+00:00', 'context_sha256': '963ebc596263bcce708d1b19a7a4eac472136dbe68ac348d242d38ddc5e2151e', 'pending_sha256': '3809a1ef5963b17c4df04c3870d57c65b50cd273631eb1f2ab25b8f6b8284857'}
TOKEN = '9573f1fc8cad435fb47660949b563298'
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
SOURCE = 'b1e639b3ceb14bb5c65d9f81a084d41c834b951c'
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


ACTIVE_ARGS = None

def guard():
    return packet_guard(ACTIVE_ARGS, pointer=True, minimum=100)[0]


from packet_runtime import guard as packet_guard, arguments, require_arguments, actual_production
from source_resolver import scoped, verify
EXEC = TICK / "m235_dispatch_execution"
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
    pin = "test \"$(hostname)\" = dl04-MS-7E06 && test \"$(id -u)\" = 1001 && "
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no", "songcl@192.168.1.115", pin + actual],
        capture_output=True, text=True, encoding="utf8", errors="replace", timeout=timeout,
    )
    number = len(CALLS)
    stdout = EXEC / f"m235_dispatch_ssh_{number:02d}.stdout"
    stderr = EXEC / f"m235_dispatch_ssh_{number:02d}.stderr"
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
    arguments(parser)
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_QUEUE_OR_LAUNCH"}))
        return
    global ACTIVE_ARGS
    require_arguments(args)
    ACTIVE_ARGS = args
    owner = guard()
    EXEC.mkdir(exist_ok=True)
    assert not (EXEC / "m235_dispatch_intent.json").exists(), "Existing intent: reconcile, never replay"
    review = Path(args.production_review)
    production_path = Path(args.production_result)
    production = actual_production(production_path, review, args.production_review_sha256)
    import yaml
    raw = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf8"))["servers"]["server-4"]
    assert raw["remote_code_root"] == RUNTIME
    assert sha(ROOT / "SERVERS.yaml") == read(HERE / "baseline.json")["SERVERS_sha256"]
    assert production["shim"]=="/data/songcl/Project/Cluster_project/pipeline/runtime/sinc_path_prod_9573f1fc/conda_source.sh"
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
        assert len(eligible) == 1 and eligible[0]["id"] == "M235-SINC"
        assert not [t for ts in queue["gpu_queues"].values() for t in ts if t.get("status") in ("running", "claiming")]
        task = eligible[0]
        assert task["code_commit"] == SOURCE and not task.get("resume_authorized") and not task.get("resume_from")
        closure.admission(ROOT, task)
        verify()
        server = monitor.load_servers(str(ROOT))["server-4"]
        original_ssh = monitor.ssh
        monitor.ssh = ssh
        try:
            program = r'''
from pathlib import Path
from datetime import datetime,timezone
import os,json,subprocess,hashlib,fcntl,stat
assert os.getuid()==1001
root=Path(P["root"])
assert subprocess.check_output(["git","--no-optional-locks","-C",str(root),"rev-parse","HEAD"],text=True).strip()==P["source"]
for relative,expected in P["files"].items():
 assert hashlib.sha256((Path(P["stage"])/relative).read_bytes()).hexdigest()==expected
assert not Path(P["marker"]).exists()
assert hashlib.sha256((root/P["config"]).read_bytes()).hexdigest() in (P["source_config_sha256"],P["config_sha256"])
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
 path=Path(item["path"]);fd=os.open(str(path),os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  a,b=os.fstat(fd),os.lstat(path)
  assert stat.S_ISREG(a.st_mode) and stat.S_ISREG(b.st_mode)
  assert (a.st_dev,a.st_ino)==(b.st_dev,b.st_ino)==(item["dev"],item["ino"])
  fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  c=os.lstat(path);assert (c.st_dev,c.st_ino)==(item["dev"],item["ino"])
 finally:os.close(fd)
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
                      "source_config_sha256": "d479b53c7874d2515f91af32acdf908a884c91ebb24bcec42d53d12c39c74369",
                      "locks": production["binding"]["lock_files"]}
            observation = json.loads(ssh(server["host"], server["user"],
                "/usr/bin/python3 -B -c " + shlex.quote("P=" + repr(params) + "\n" + program)))
            save(EXEC / "m235_prelaunch_actual_resources.json", observation)
            # Canonical monitor/closure retain admission, source, live memory,
            # concurrency and progress gates. The exact existence probe above
            # is read-only; no process signal is sent.
            save(EXEC / "m235_dispatch_intent.json", {
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "owner": {k: owner[k] for k in ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")},
                "source": SOURCE, "runtime_root": RUNTIME, "task": task,
                "production_result_sha256": sha(production_path),
                "production_review_sha256": sha(review),
                "no_replay": True,
            })
            events = []
            with scoped(monitor, production_shim=production["shim"]):
                monitor._process_queue(
                    queue, "server-4", server["host"], server["user"], str(ROOT), set(), {"0"}, events,
                    max_tasks_per_gpu=1, allow_external_overlay=True, task_memory_mb=20000,
                    remote_code_root=RUNTIME, current_tasks=0, max_tasks_total=1,
                )
        finally:
            monitor.ssh = original_ssh
        current = read(ROOT / "pipeline/queue.json")
        actual = next(t for t in current["gpu_queues"]["server-4"] if t["id"] == "M235-SINC")
        save(EXEC / "m235_dispatch_result.json", {
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
