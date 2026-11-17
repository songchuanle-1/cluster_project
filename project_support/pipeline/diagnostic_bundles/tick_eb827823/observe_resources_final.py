"""Read current physical GPU0 resources and existing cooperative lock state."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
LABEL = sys.argv[1]
assert LABEL == "before_finish"
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == "eb827823f30543d8aa8609643034f996"
assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
    assert hashlib.sha256((ROOT / "pipeline/headless" / name).read_bytes()).hexdigest() == owner[key]
program = r'''
from pathlib import Path
from datetime import datetime,timezone
import socket,subprocess,json,os,fcntl
assert socket.gethostname()=='dl04-MS-7E06'
root=Path('/data/songcl/Project/Cluster_project/Cluster_psc_20261106')
commit=subprocess.check_output(['git','--no-optional-locks','-C',str(root),'rev-parse','HEAD'],text=True).strip()
assert commit=='0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d'
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
values=[x.strip() for x in row.split(',')]
assert values[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
used,total,util=int(values[2]),int(values[3]),int(values[4])
raw=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
contexts=[]
for line in raw.splitlines():
 if line.strip():
  fields=[x.strip() for x in line.split(',')];contexts.append({'pid':int(fields[0]),'used_memory_mib':fields[1]})
locks=[]
for kind in ('training','diagnostic','exclusive'):
 p=Path('/tmp/cluster_project_gpu0_'+kind+'.lock');info=p.stat()
 with p.open('r+b') as handle:
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);available=True
  except BlockingIOError:available=False
 locks.append({'kind':kind,'inode':info.st_ino,'available':available})
project=[]
for directory in Path('/proc').iterdir():
 if not directory.name.isdigit():continue
 try:
  if directory.stat().st_uid!=os.getuid():continue
  argv=[x.decode(errors='replace') for x in (directory/'cmdline').read_bytes().split(b'\0') if x]
  if not any(arg=='tools/train.py' or arg.endswith('/tools/train.py') for arg in argv):continue
  cwd=os.readlink(directory/'cwd')
  if cwd.startswith('/data/songcl/Project/Cluster_project/'):
   text=(directory/'stat').read_text()
   project.append({'pid':int(directory.name),'starttime':text[text.rfind(')')+2:].split()[19],'cwd':cwd,'argv':argv})
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),
 'runtime_root':str(root),'runtime_source':commit,'physical_gpu':0,'gpu_uuid':values[1],
 'memory_used_mib':used,'memory_total_mib':total,'memory_free_mib':total-used,
 'utilization_percent':util,'external_or_other_contexts':contexts,'project_trainers':project,
 'locks':locks,'usable_under_authorized_overlay':total-used>=20000 and not project and all(x['available'] for x in locks),
 'exclusive_performance_claimed':False,'signals_sent':False,'training_or_GPU_diagnostic_launched':False}))
'''
command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o",
           "ConnectTimeout=8", "songcl@192.168.1.115",
           "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(program)]
out = subprocess.run(command, capture_output=True, text=True, encoding="utf8", timeout=35)
target = HERE / ("resources_" + LABEL + ".json")
record = {
    "owner_provenance_only": {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")},
    "recorded_at": datetime.now(timezone.utc).isoformat(), "command": command,
    "returncode": out.returncode, "stderr": out.stderr,
    "observation": json.loads(out.stdout) if out.returncode == 0 else None,
}
with target.open("x", encoding="utf8") as f:
    json.dump(record, f, ensure_ascii=False, indent=2)
    f.write("\n")
assert out.returncode == 0, out.stderr[-1800:]
print(json.dumps(record["observation"], ensure_ascii=False))
