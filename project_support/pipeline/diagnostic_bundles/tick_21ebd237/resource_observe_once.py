"""Current owner read-only GPU0 resource and launch-state observation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
KEYS = ("token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256")
PROGRAM = r'''
from pathlib import Path
from datetime import datetime,timezone
import os,socket,subprocess,json,fcntl,stat,hashlib
assert socket.gethostname()=="dl04-MS-7E06" and os.getuid()==1001
row=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu","--format=csv,noheader,nounits"],text=True).strip()
v=[s.strip() for s in row.split(",")]
assert v[:2]==["0","GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
contexts=subprocess.check_output(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],text=True).strip()
trainers=[]
for proc in Path("/proc").iterdir():
 if not proc.name.isdigit():continue
 try:
  if proc.stat().st_uid!=os.getuid():continue
  argv=[s.decode(errors="replace") for s in (proc/"cmdline").read_bytes().split(b"\0") if s]
  if not any(s=="tools/train.py" or s.endswith("/tools/train.py") for s in argv):continue
  cwd=os.readlink(proc/"cwd")
  if cwd.startswith("/data/songcl/Project/Cluster_project/"):
   trainers.append({"pid":int(proc.name),"cwd":cwd,"argv":argv})
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
locks=[]
for kind,inode in [("training",92537152),("diagnostic",92537153),("exclusive",92537154)]:
 path=Path("/tmp/cluster_project_gpu0_"+kind+".lock")
 fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  a,b=os.fstat(fd),path.lstat()
  assert stat.S_ISREG(a.st_mode) and stat.S_ISREG(b.st_mode)
  assert (a.st_dev,a.st_ino)==(b.st_dev,b.st_ino)==(66308,inode)
  try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);available=True
  except BlockingIOError:available=False
  locks.append({"kind":kind,"dev":a.st_dev,"ino":a.st_ino,"nonblocking_available":available})
 finally:os.close(fd)
stages={}
for prefix in ("ee6f5eda","21ebd237"):
 root=Path("/data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prod_"+prefix)
 marker=root/"train-consumed.json"
 stages[prefix]={"exists":root.exists(),"marker_exists":marker.exists(),
                 "marker_sha256":hashlib.sha256(marker.read_bytes()).hexdigest() if marker.exists() else None}
print(json.dumps({"observed_at":datetime.now(timezone.utc).isoformat(),
 "hostname":socket.gethostname(),"uid":os.getuid(),"gpu_row":row,
 "free_memory_mib":int(v[3])-int(v[2]),"required_free_memory_mib":20000,
 "memory_budget_satisfied":int(v[3])-int(v[2])>=20000,
 "contexts":contexts,"project_trainers":trainers,"original_locks":locks,
 "production_stages":stages,"read_only":True,"GPU_compute":False,
 "signals_sent":False,"remote_files_written":False}))
'''


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_OR_MUTATION"}))
        return
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    owner = read(HERE / "current_owner_binding.json")
    actual = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: actual[key] for key in KEYS} == owner
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    for name, key in ((".tick_context.json", "context_sha256"),
                      (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    intent, output = HERE / "resource_observe_intent.json", HERE / "resource_actual.json"
    assert not intent.exists() and not output.exists(), "Reconcile without replay."
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
               "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(PROGRAM)]
    save(intent, {"owner": owner, "read_only": True, "script_sha256": sha(__file__),
                  "recorded_at": datetime.now(timezone.utc).isoformat(), "no_replay": True})
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", errors="replace")
    record = {"owner": owner, "certainty": "uncertain", "read_only": True,
              "local_ssh_pid": proc.pid, "script_sha256": sha(__file__)}
    try:
        stdout, stderr = proc.communicate(timeout=35)
        record.update(certainty="terminal", returncode=proc.returncode,
                      stderr=stderr[:2000])
        assert proc.returncode == 0, stderr[:2000]
        assert len(stdout.encode()) < 32768
        record["observation"] = json.loads(stdout)
    except BaseException as error:
        record.update(error_type=type(error).__name__, error=str(error))
        save(output, record)
        raise
    save(output, record)
    observation = record["observation"]
    print(json.dumps({"path": str(output), "sha256": sha(output),
                      "free_memory_mib": observation["free_memory_mib"],
                      "memory_budget_satisfied": observation["memory_budget_satisfied"],
                      "project_trainers": len(observation["project_trainers"]),
                      "original_locks_available": all(
                          item["nonblocking_available"] for item in observation["original_locks"])}))


if __name__ == "__main__":
    main()
