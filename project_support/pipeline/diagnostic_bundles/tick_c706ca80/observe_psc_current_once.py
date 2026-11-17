"""Default NOP. Root-only read-only PSC postlaunch audit; no signals/retries."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "c706ca805df642f3b7d41f51206ed921"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_psc_20261106"
SOURCE = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
CONFIG = "configs/Quard/ctf_hcg_csort_psc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psc.yaml"
GPU_UUID = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert os.environ.get("CODEX_THREAD_ID") == THREAD and sys.dont_write_bytecode
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    for name, key in ((".tick_context.json", "context_sha256"),
                      (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    return {key: owner[key] for key in ("token", "thread_id", "generated_at",
                                       "deadline_at", "context_sha256", "pending_sha256")}


REMOTE = r'''
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,socket,stat,subprocess,time
assert socket.gethostname()=="dl04-MS-7E06" and os.getuid()==os.geteuid()==1001
assert datetime.now(timezone.utc)<datetime.fromisoformat(P["owner"]["deadline_at"])
pid=P["pid"];proc=Path("/proc")/str(pid);binding=P["binding"];root=Path(binding["runtime_root"])
assert binding["kind"]=="production" and root==Path("/data/songcl/Project/Cluster_project/Cluster_psc_20261106")
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def execute(argv):
 process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:out,err=process.communicate(timeout=10)
 except subprocess.TimeoutExpired:raise RuntimeError("CPU observation uncertain PID "+str(process.pid)+"; no signal/retry")
 assert process.returncode==0,err[-600:]
 return out.strip()
def process_stat():
 assert proc.stat().st_uid==1001
 fields=(proc/"stat").read_text().rsplit(")",1)[1].split()
 assert fields[0] not in ("Z","X")
 return {"state":fields[0],"starttime_ticks":fields[19]}
first=process_stat()
if P["expected_starttime"] is not None:assert first["starttime_ticks"]==str(P["expected_starttime"])
argv=[part.decode() for part in (proc/"cmdline").read_bytes().split(b"\0") if part]
assert argv[1:]==binding["argv"] and Path(argv[0]).resolve()==Path(binding["python_realpath"])
assert os.readlink(proc/"cwd")==str(root)
assert Path(os.readlink(proc/"exe")).resolve()==Path(binding["python_realpath"])
git_env={"PATH":"/usr/bin:/bin","GIT_OPTIONAL_LOCKS":"0","GIT_CONFIG_NOSYSTEM":"1",
         "GIT_CONFIG_SYSTEM":"/dev/null","GIT_CONFIG_GLOBAL":"/dev/null","LANG":"C"}
head=subprocess.check_output(["/usr/bin/git","--no-optional-locks","-c","core.fsmonitor=false",
                             "-C",str(root),"rev-parse","HEAD"],env=git_env,text=True).strip()
assert head==P["source"]
for relative,expected in binding["source_files"].items():assert sha(root/relative)==expected
assert sha(root/binding["argv"][1])==binding["runtime_config_sha256"]
for relative,expected in P["production_files"].items():
 assert sha(Path(binding["stage"])/relative)==expected
marker_path=Path(binding["one_shot_marker"]);metadata=os.lstat(marker_path)
assert stat.S_ISREG(metadata.st_mode) and metadata.st_uid==1001 and metadata.st_nlink==1
marker=json.loads(marker_path.read_text())
for key,expected in {"pid":pid,"uid":1001,"argv":binding["argv"],"runtime_root":str(root),
                     "source_commit":P["source"],"activation_receipt_sha256":binding["activation_receipt_sha256"],
                     "lock_inodes":binding["lock_files"]}.items():assert marker[key]==expected
wanted={(item["dev"],item["ino"]):item for item in binding["lock_files"]}
assert len(wanted)==3
for item in wanted.values():
 metadata=os.lstat(item["path"])
 assert stat.S_ISREG(metadata.st_mode) and metadata.st_uid==1001
 assert (metadata.st_dev,metadata.st_ino)==(item["dev"],item["ino"])
fds=[]
for filename in (proc/"fd").iterdir():
 try:
  metadata=filename.stat();key=(metadata.st_dev,metadata.st_ino)
  if key not in wanted:continue
  info=(proc/"fdinfo"/filename.name).read_text()
  flags=int(re.search(r"(?m)^flags:\s*([0-7]+)$",info)[1],8)
  assert not flags&os.O_CLOEXEC
  fds.append({"fd":int(filename.name),"path":wanted[key]["path"],"dev":key[0],"ino":key[1],"cloexec":False})
 except FileNotFoundError:pass
assert len(fds)==3 and {(item["dev"],item["ino"]) for item in fds}==set(wanted)
kernel=[]
for line in Path("/proc/locks").read_text().splitlines():
 parts=line.split()
 if len(parts)<8 or parts[1:4]!=["FLOCK","ADVISORY","WRITE"] or parts[4]!=str(pid):continue
 major,minor,inode=parts[5].split(":")
 for dev,ino in wanted:
  if (int(major,16),int(minor,16),int(inode))==(os.major(dev),os.minor(dev),ino):kernel.append(line)
assert len(kernel)==3
log=Path(P["log"]);assert log.is_relative_to(root/"logs") and log.resolve().is_relative_to(root/"logs")
def progress():
 metadata=log.stat();assert metadata.st_uid==1001
 with log.open("rb") as handle:
  handle.seek(max(0,metadata.st_size-24000));raw=handle.read(24000)
 text=raw.decode("utf-8",errors="replace")
 pattern=r"Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+|Epoch:\s*\[(\d+)\]\s*\[\s*(\d+)/\d+\]"
 steps=[tuple(int(value) for value in match if value) for match in re.findall(pattern,text)]
 return {"file_bytes":metadata.st_size,"tail_bytes":len(raw),"tail_sha256":hashlib.sha256(raw).hexdigest(),
         "native_pairs_last4":steps[-4:],"native_distinct_pairs":len(set(steps)),
         "native_max_pair":max(steps) if steps else None,
         "errors":[name for name in ("Traceback","CUDA out of memory","RuntimeError") if name in text]}
budget=16*1024*1024;log_size=log.stat().st_size
with log.open("rb") as handle:
 handle.seek(max(0,log_size-budget));metric_bytes=handle.read(budget)
metric_text=metric_bytes.decode("utf8",errors="replace")
validations=[float(x) for x in re.findall(r"mIoU : ([0-9.eE+-]+)",metric_text)]
best_value=None;noimp=0
for value in validations:
 if best_value is None or value>best_value:best_value=value;noimp=0
 else:noimp+=1
validation_summary={"scan_budget_bytes":budget,"scanned_bytes":len(metric_bytes),"log_bytes":log_size,
 "full_log_scanned":log_size<=budget,"complete_validation_record_count_in_scope":len(validations),
 "native_logged_values":validations,"native_logged_best_rounded":best_value,"no_improvement_in_scope":noimp,
 "exact_checkpoint_best_evaluated":False,"terminal_training_result":False}
progress0=progress();time.sleep(3);progress1=progress();last=process_stat()
assert first["starttime_ticks"]==last["starttime_ticks"]
assert not progress1["errors"]
native_observed=progress1["native_distinct_pairs"]>=2 and progress1["native_max_pair"][1]>0
gpu=execute(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu","--format=csv,noheader,nounits"])
gpu_values=[value.strip() for value in gpu.split(",")]
assert gpu_values[:2]==["0",P["uuid"]]
contexts=execute(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"])
context_rows=[line.split(",") for line in contexts.splitlines() if line.strip()]
assert any(row[0].strip()==str(pid) for row in context_rows)
assert datetime.now(timezone.utc)<datetime.fromisoformat(P["owner"]["deadline_at"])
print(json.dumps({"recorded_at":datetime.now(timezone.utc).isoformat(),"identity_locks_source_passed":True,
 "pid":pid,"process_start":first,"process_end":last,"expected_starttime_bound":P["expected_starttime"] is not None,
 "argv":argv,"cwd":str(root),"source_commit":head,"marker_sha256":sha(marker_path),
 "three_retained_FDs":fds,"three_kernel_FLOCK_same_PID":kernel,
 "native_validation_summary":validation_summary,"native_progress_first":progress0,"native_progress_second":progress1,"native_progress_observed":native_observed,
 "progress_increased_between_observations":bool(progress0["native_max_pair"] and progress1["native_max_pair"] and progress1["native_max_pair"]>progress0["native_max_pair"]),
 "physical_gpu_row":gpu,"contexts":[[item.strip() for item in row] for row in context_rows],
 "read_only":True,"signals_GPU_model_or_training_invocation":False}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--production-result")
    parser.add_argument("--production-result-sha256")
    parser.add_argument("--expected-starttime")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_OR_MUTATION"}))
        return
    owner = guard()
    result_path = HERE / "psc_postlaunch_observation.json"
    assert not result_path.exists(), "Existing observation: preserve; never overwrite/replay"
    production_path = Path(args.production_result).resolve()
    assert production_path.is_relative_to(ROOT) and sha(production_path) == args.production_result_sha256
    production = read(production_path)
    binding = production["binding"]
    assert production["kind"] == "PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED"
    assert binding["kind"] == "production" and binding["runtime_root"] == RUNTIME and binding["source_commit"] == SOURCE
    queue = read(ROOT / "pipeline/queue.json")
    tasks = [task for group in queue["gpu_queues"].values() for task in group if task.get("id") == "M231-PSC"]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["status"] in ("running", "claiming") and task["server"] == "server-4"
    assert str(task["gpu"]) == "0" and task["code_commit"] == SOURCE and task["config"] == CONFIG
    pid = int(task["pid"])
    assert pid > 1 and task["log"].startswith(RUNTIME + "/logs/")
    start = args.expected_starttime or task.get("starttime") or task.get("pid_starttime")
    params = {"owner": owner, "pid": pid, "expected_starttime": start,
              "binding": binding, "production_files": production["files"],
              "source": SOURCE, "log": task["log"], "uuid": GPU_UUID}
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
               "/usr/bin/python3 -I -B -c " + shlex.quote("P=" + repr(params) + "\n" + REMOTE)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", errors="replace")
    try:
        stdout, stderr = process.communicate(timeout=45)
    except subprocess.TimeoutExpired:
        value = {"certainty": "uncertain", "owner": owner, "local_ssh_pid": process.pid,
                 "target_pid": pid, "read_only": True, "no_signal_or_replay": True}
    else:
        value = {"certainty": "terminal", "owner": owner, "returncode": process.returncode,
                 "queue_snapshot": {key: task.get(key) for key in
                                    ("id", "status", "pid", "log", "launch_verified")},
                 "production_result_sha256": sha(production_path)}
        if process.returncode == 0:
            value["observation"] = json.loads(stdout)
        else:
            value.update(observation_passed=False, target_pid=pid,
                         stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
                         stderr_last_line=stderr.strip().splitlines()[-1][-240:] if stderr.strip() else "")
        guard()
    with result_path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"path": str(result_path), "sha256": sha(result_path),
                      "certainty": value["certainty"]}))


if __name__ == "__main__":
    main()
