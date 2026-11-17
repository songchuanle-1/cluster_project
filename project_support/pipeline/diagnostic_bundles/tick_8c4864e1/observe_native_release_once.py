"""Read-only reconciliation of this tick's diagnostic processes and original locks."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "8c4864e1a36e4f3883b3d301cfc39069"
PROGRAM = r"""
from datetime import datetime,timezone
from pathlib import Path
import fcntl,hashlib,json,os,socket,subprocess
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==1001
root=Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')
stage=Path('/data/songcl/Project/Cluster_project/pipeline/rvec_8c4864e1_gpu0')
processes=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  if proc.stat().st_uid!=1001:continue
  cwd=(proc/'cwd').resolve()
  argv=[a.decode(errors='replace') for a in (proc/'cmdline').read_bytes().split(b'\0') if a]
  if cwd==stage or (cwd==root and 'tools/train.py' in argv):
   processes.append({'pid':int(proc.name),'cwd':str(cwd),'argv':argv[:12]})
 except (OSError,RuntimeError):pass
locks=[]
for kind,inode in [('training',92537152),('diagnostic',92537153),('exclusive',92537154)]:
 path=Path('/tmp/cluster_project_gpu0_'+kind+'.lock')
 assert path.is_file() and not path.is_symlink()
 info=path.stat();descriptor=os.open(path,os.O_RDWR|os.O_NOFOLLOW)
 available=False
 try:
  try:
   fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB);available=True
  except BlockingIOError:pass
  locks.append({'kind':kind,'path':str(path),'device':info.st_dev,'inode':info.st_ino,
    'expected_device':66308,'expected_inode':inode,'original_inode_matches':info.st_dev==66308 and info.st_ino==inode,
    'nonblocking_available':available})
 finally:
  if available:fcntl.flock(descriptor,fcntl.LOCK_UN)
  os.close(descriptor)
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.free,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
results=[]
for name in ('smoke_candidate_result.json','resources_candidate_result.json','resources_champion_result.json'):
 path=stage/name
 if path.is_file():
  raw=path.read_bytes();value=json.loads(raw)
  results.append({'name':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
    'execution_completed':value.get('execution_completed'),'optimizer_steps':value.get('optimizer_steps'),
    'error_type':value.get('error_type'),'error':value.get('error'),
    'common_init_passed':value.get('original_common_initialization_comparison',{}).get('passed')})
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),
 'stage_processes_or_native_trainers':processes,'original_locks':locks,'gpu0':gpu,
 'results':results,'signals_sent':False,'remote_files_written':False,'GPU_compute_started':False}))
"""

assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text(encoding="utf-8"))
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
binding = {k: owner[k] for k in ["token", "thread_id", "generated_at", "deadline_at",
                                "context_sha256", "pending_sha256"]}
result_path = HERE / "native_release_observation.json"
assert not result_path.exists()
process = subprocess.Popen([
    "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
    "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
    "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -",
], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding="utf-8", errors="replace")
record = {"owner": binding, "producer_sha256": hashlib.sha256(PROGRAM.encode()).hexdigest(),
          "recorded_at": datetime.now(timezone.utc).isoformat(), "certainty": "uncertain"}
try:
    stdout, stderr = process.communicate(PROGRAM, timeout=35)
except subprocess.TimeoutExpired:
    record["reason"] = "Read-only reconciliation uncertain; no signals or retry."
else:
    record.update(certainty="terminal", returncode=process.returncode, stderr=stderr)
    try:
        record["observation"] = json.loads(stdout)
    except json.JSONDecodeError:
        record["stdout"] = stdout[:2000]
with result_path.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
assert record.get("returncode") == 0 and "observation" in record
print(json.dumps({"path": str(result_path),
                  "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
                  "observation": record["observation"]}))
