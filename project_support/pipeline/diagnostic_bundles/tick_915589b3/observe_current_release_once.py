"""Default NOP. Fresh-owner read-only current-stage/process/lock reconciliation."""
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
OWNER = {"token": "915589b3154c4c3c99b1db658f610a1f", "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-09T01:12:12.491733+00:00", "deadline_at": "2026-11-09T02:12:12.491733+00:00",
    "context_sha256": "dada34d7594e909fafb5912692a196a80a7f11a55681e45cb7b1736039e08e5e",
    "pending_sha256": "d5e94794b90053aff865886bb78f0d94483538397354b954968aa5e13566ffd7"}
PROGRAM = r"""
from datetime import datetime,timezone
from pathlib import Path
import fcntl,hashlib,json,os,socket,stat,subprocess
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
assert datetime.now(timezone.utc)<datetime.fromisoformat('2026-11-09T02:12:12.491733+00:00')
root=Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')
stages=[Path('/data/songcl/Project/Cluster_project/pipeline/rvec_915589b3_gpu0'),Path('/data/songcl/Project/Cluster_project/pipeline/rvec_915589b3b_gpu0')]
workers=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  if proc.stat().st_uid!=1001:continue
  argv=[v.decode(errors='replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v]
  joined='\0'.join(argv)
  matches=[str(stage) for stage in stages if str(stage) in joined and ('worker.py' in joined or 'runpy' in joined)]
  trainer=(proc/'cwd').resolve()==root and 'tools/train.py' in argv
  if matches or trainer:
   fields=(proc/'stat').read_text().rsplit(')',1)[1].split()
   workers.append({'pid':int(proc.name),'state':fields[0],'start_ticks':fields[19],
    'stages':matches,'same_root_native_trainer':trainer,'argv_bounded':[a[:800] for a in argv[:8]]})
 except (OSError,RuntimeError):pass
locks=[]
for kind,inode in [('training',92537152),('diagnostic',92537153),('exclusive',92537154)]:
 path='/tmp/cluster_project_gpu0_'+kind+'.lock'
 item={'kind':kind,'path':path,'expected_device':66308,'expected_inode':inode,'recreated':False}
 try:
  fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
  with os.fdopen(fd,'r+b') as stream:
   opened,named=os.fstat(stream.fileno()),os.lstat(path)
   item.update(device=opened.st_dev,inode=opened.st_ino,regular=stat.S_ISREG(opened.st_mode),
    original_inode_matches=(opened.st_dev,opened.st_ino)==(66308,inode) and (named.st_dev,named.st_ino)==(66308,inode))
   if item['original_inode_matches'] and item['regular']:
    try:
     fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);item['nonblocking_available']=True
     fcntl.flock(stream,fcntl.LOCK_UN)
    except BlockingIOError:item['nonblocking_available']=False
 except OSError as error:item.update(error_type=type(error).__name__,error=str(error))
 locks.append(item)
results=[]
for stage in stages:
 row={'stage':str(stage),'exists':stage.exists(),'results':[]}
 if stage.exists():
  for name in ('smoke_candidate_result.json','resources_candidate_result.json','smoke_champion_result.json','resources_champion_result.json'):
   path=stage/name
   if not path.is_file():continue
   raw=path.read_bytes();data=json.loads(raw)
   summary={k:data.get(k) for k in ('execution_completed','optimizer_steps','native_loss_forwards','native_criterion_backwards','error_type','native_gate_failure')}
   summary.update(name=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),error=str(data.get('error',''))[:1500])
   common=data.get('original_common_initialization_comparison')
   if common is not None:summary['common_init']={k:common.get(k) for k in ('passed','same_names','same_shapes','same_dtypes','candidate_tensor_count','reference_tensor_count','candidate_sha256','reference_sha256')}
   row['results'].append(summary)
 results.append(row)
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
head=subprocess.check_output(['/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(root),'rev-parse','HEAD'],text=True,env=env,timeout=15).strip()
assert head=='0747f6acec1c61018ec99acf2efa5329c9b3523c'
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.free,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'runtime_HEAD':head,
 'stage_processes_or_native_trainers':workers,'original_locks':locks,'stages':results,'gpu0':gpu,
 'signals_sent':False,'remote_files_written':False,'GPU_compute_started':False}))
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_GPU_OR_MUTATION"}))
        return
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text(encoding="utf8"))
    assert {key: owner[key] for key in OWNER} == OWNER
    assert datetime.now(timezone.utc) < datetime.fromisoformat(OWNER["deadline_at"])
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == OWNER[key]
    intent, actual = HERE / "post_native_reconciliation_intent.json", HERE / "post_native_reconciliation_actual.json"
    assert not intent.exists() and not actual.exists(), "Existing or uncertain observation; never replay"
    save(intent, {"owner": OWNER, "producer_sha256": sha(__file__),
        "remote_program_sha256": hashlib.sha256(PROGRAM.encode()).hexdigest(),
        "read_only": True, "no_signals_or_remote_writes": True, "no_replay": True})
    record = {"owner": OWNER, "producer_sha256": sha(__file__), "intent_sha256": sha(intent), "certainty": "uncertain"}
    process = subprocess.Popen(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
        "-o", "ConnectTimeout=8", "songcl@192.168.1.115", "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(PROGRAM)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf8", errors="replace")
    record["local_ssh_pid"] = process.pid
    try:
        stdout, stderr = process.communicate(timeout=40)
    except subprocess.TimeoutExpired:
        record["reason"] = "Read-only reconciliation uncertain; no signal or replay"
        save(actual, record)
        raise SystemExit(75)
    record.update(certainty="terminal", returncode=process.returncode, stderr=stderr)
    try:
        record["observation"] = json.loads(stdout)
    except json.JSONDecodeError:
        record["stdout"] = stdout
    save(actual, record)
    assert process.returncode == 0 and "observation" in record
    print(json.dumps({"path": str(actual), "sha256": sha(actual), "observation": record["observation"]}))


if __name__ == "__main__":
    main()
