"""Read-only exact M234 process/source/producer/terminal reconciliation."""
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
OLD = ROOT / "pipeline/diagnostic_bundles/tick_21ebd237"
KEYS = ("token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256")
PROGRAM = r'''
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,socket,stat,subprocess,sys,fcntl
P=json.load(sys.stdin)
assert socket.gethostname()=="dl04-MS-7E06" and os.getuid()==os.geteuid()==1001
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def checked(path,digest):
 path=Path(path);st=path.lstat()
 assert stat.S_ISREG(st.st_mode) and st.st_uid==1001 and not stat.S_ISLNK(st.st_mode)
 assert sha(path)==digest
 return path
root=Path(P["runtime_root"])
assert str(root)=="/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
env={k:v for k,v in os.environ.items() if not k.startswith("GIT_")};env["GIT_OPTIONAL_LOCKS"]="0"
head=subprocess.check_output(["git","--no-optional-locks","-C",str(root),"rev-parse","HEAD"],env=env,text=True,timeout=10).strip()
assert head==P["source_commit"]=="d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
binding=json.loads(checked(P["binding_path"],P["binding_sha256"]).read_text())
assert binding["source_commit"]==head and binding["runtime_root"]==str(root)
checked(binding["entry"],P["entry_sha256"]);checked(P["core_path"],P["core_sha256"])
for relative,digest in binding["source_files"].items():
 path=(root/relative).resolve();assert path.is_relative_to(root);checked(path,digest)
checked(root/binding["argv"][1],binding["runtime_config_sha256"])
marker=json.loads(checked(binding["one_shot_marker"],P["marker_sha256"]).read_text())
assert marker["pid"]==P["pid"] and marker["source_commit"]==head and marker["runtime_root"]==str(root)
proc=Path("/proc")/str(P["pid"])
process={"pid":P["pid"],"expected_start_ticks":str(P["start_ticks"]),"exists":proc.exists()}
if proc.exists():
 fields=(proc/"stat").read_text().rsplit(")",1)[1].split()
 process.update(state=fields[0],actual_start_ticks=fields[19],same_identity=fields[19]==str(P["start_ticks"]))
 process["alive"]=process["same_identity"] and fields[0] not in ("Z","X")
else:process.update(alive=False,same_identity=None)
def bounded(path):
 path=Path(path);size=path.stat().st_size
 with path.open("rb") as stream:offset=max(0,size-131072);stream.seek(offset);raw=stream.read(131072)
 text=raw.decode("utf-8",errors="replace")
 pattern=r"Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+|Epoch:\s*\[(\d+)\]\s*\[\s*(\d+)/\d+\]"
 native=[tuple(int(v) for v in match if v) for match in re.findall(pattern,text)]
 error={key:key in text for key in ("Traceback","CUDA out of memory","RuntimeError","Segmentation fault","TypeError")}
 pos=text.rfind("Traceback")
 excerpt=text[pos:pos+5000] if pos>=0 else None
 validations=[float(v) for v in re.findall(r"\bmIoU :\s*([0-9.eE+-]+)",text)]
 return {"path":str(path),"size":size,"offset":offset,"bytes_read":len(raw),
  "tail_sha256":hashlib.sha256(raw).hexdigest(),"latest_native_step":native[-1] if native else None,
  "native_steps_last5":native[-5:],"exact_validations_in_bounded_tail":validations,
  "complete_log_observed":offset==0,"error_markers":error,"error_excerpt":excerpt,
  "terminal_markers":{key:key in text for key in ("Early stopping","Training finished","Training completed")}}
logs={"registered_stdout":bounded(P["log"]),"actual_native_logger":bounded(P["actual_native_logger"])}
work=Path(P["actual_work_dir"])
assert work.is_relative_to(Path("/data/songcl/Project/Cluster_project/Cluster_checkpoints"))
checkpoints=[]
for name in ("best.pth","last.pth"):
 path=work/name
 if path.is_file():
  st=path.stat();checkpoints.append({"path":str(path),"bytes":st.st_size,"mtime_ns":st.st_mtime_ns})
locks=[]
for kind,inode in (("training",92537152),("diagnostic",92537153),("exclusive",92537154)):
 path=Path("/tmp/cluster_project_gpu0_"+kind+".lock");fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  a,b=os.fstat(fd),path.lstat();assert (a.st_dev,a.st_ino)==(b.st_dev,b.st_ino)==(66308,inode)
  try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);available=True
  except BlockingIOError:available=False
  locks.append({"kind":kind,"dev":a.st_dev,"ino":a.st_ino,"available":available})
 finally:os.close(fd)
row=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu","--format=csv,noheader,nounits"],text=True,timeout=10).strip()
values=[v.strip() for v in row.split(",")]
assert values[:2]==["0","GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
trainers=[]
for other in Path("/proc").iterdir():
 if not other.name.isdigit():continue
 try:
  if other.stat().st_uid!=1001:continue
  argv=[v.decode(errors="replace") for v in (other/"cmdline").read_bytes().split(b"\0") if v]
  if not any(v=="tools/train.py" or v.endswith("/tools/train.py") for v in argv):continue
  cwd=os.readlink(other/"cwd")
  if cwd.startswith("/data/songcl/Project/Cluster_project/"):trainers.append({"pid":int(other.name),"cwd":cwd,"argv":argv})
 except (OSError,FileNotFoundError,ProcessLookupError):pass
print(json.dumps({"observed_at":datetime.now(timezone.utc).isoformat(),"hostname":socket.gethostname(),
 "uid":os.getuid(),"source_commit":head,"runtime_root":str(root),"source_and_producer_verified":True,
 "process":process,"project_trainers":trainers,"logs":logs,"checkpoint_metadata_only":checkpoints,
 "original_locks":locks,"gpu0":row,"free_memory_mib":int(values[3])-int(values[2]),
 "marker_consumed":True,"marker_sha256":P["marker_sha256"],
 "original_launch_owner_retained":True,"read_only":True,"GPU_compute":False,
 "signals_sent":False,"remote_files_written":False,"checkpoint_content_loaded":False}))
'''


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {key: owner[key] for key in KEYS}
    assert owner["token"] == "342a6a92a2c645fdb64f7806feec102f"
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    for name, key in ((".tick_context.json", "context_sha256"),
                      (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    return owner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_OR_MUTATION"}))
        return
    owner = guard()
    proof_path = OLD / "dispatch_proof_execution/dispatch_proof.json"
    assert sha(proof_path) == "805bec8e842e12f0e81262e6a1d5a6c3b19e321ec48d5c3358de8efaa0bd0b66"
    proof = read(proof_path)
    assert proof["owner"]["token"] == "21ebd23722904fa3ac93d7330cbb58c1"
    past = ROOT / "pipeline/diagnostic_bundles/tick_6d1f5659/native_summary.actual.json"
    assert sha(past) == "2cb7ed25c431b85f021824393fc6066bbf5d2ec62a82a04daafdde02505cfedf"
    native = read(past)["observation"]
    params = dict(proof, actual_native_logger=native["native_logger_discovered_from_live_open_fd"],
                  actual_work_dir=native["actual_work_dir"])
    binding, intent, output = (HERE / name for name in
                               ("current_reconcile_binding.json", "reconcile.intent.json", "reconcile.actual.json"))
    assert not binding.exists() and not intent.exists() and not output.exists(), "Reconcile without replay."
    save(binding, {"owner": owner, "historical_launch_owner": proof["owner"],
                   "historical_dispatch_proof_sha256": sha(proof_path),
                   "historical_native_discovery_sha256": sha(past),
                   "new_launch_or_renewal": False, "read_only": True})
    save(intent, {"owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "script_sha256": sha(__file__), "binding_sha256": sha(binding),
                  "read_only": True, "no_replay": True})
    process = subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
         "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(PROGRAM)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace")
    result = {"owner": owner, "certainty": "uncertain", "local_ssh_pid": process.pid,
              "kind": "CURRENT_EXACT_EXISTING_TRAINER_TERMINAL_AND_RESOURCE_RECONCILIATION",
              "read_only": True, "historical_launch_owner_preserved": True}
    try:
        stdout, stderr = process.communicate(json.dumps(params), timeout=40)
        result.update(certainty="terminal", returncode=process.returncode, stderr=stderr[:2000])
        assert process.returncode == 0, stderr[:2000]
        assert len(stdout.encode()) < 32768
        result["observation"] = json.loads(stdout)
        guard()
        result["passed"] = True
    except BaseException as error:
        result.update(passed=False, error_type=type(error).__name__, error=str(error))
        save(output, result)
        raise
    save(output, result)
    value = result["observation"]
    stdout_log = value["logs"]["registered_stdout"]
    print(json.dumps({"path": str(output), "sha256": sha(output),
                      "process": value["process"], "project_trainers": value["project_trainers"],
                      "latest_native_step": stdout_log["latest_native_step"],
                      "error_markers": stdout_log["error_markers"],
                      "error_excerpt": stdout_log["error_excerpt"],
                      "checkpoint_metadata": value["checkpoint_metadata_only"],
                      "free_memory_mib": value["free_memory_mib"],
                      "signals_sent": value["signals_sent"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
