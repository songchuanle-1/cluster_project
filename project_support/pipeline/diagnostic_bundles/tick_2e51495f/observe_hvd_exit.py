"""Read bounded original evidence after the exact HVD process disappeared."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import shlex
import subprocess
import hashlib

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == "2e51495f07244023946fc53eec6e6d98"
assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
program = r'''
from pathlib import Path
from datetime import datetime,timezone
import json,os,socket,re,subprocess
assert socket.gethostname()=='dl04-MS-7E06'
root=Path('/data/songcl/Project/Cluster_project/Cluster_hvd_20261106')
log=root/'logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd_20261106_195228.log'
p=Path('/proc/2829477')
proc={'exists':p.exists()}
if p.exists():
 t=(p/'stat').read_text();proc['starttime']=t[t.rfind(')')+2:].split()[19]
st=log.stat()
with log.open('rb') as f:
 f.seek(max(0,st.st_size-2097152));raw=f.read(2097152)
text=raw.decode('utf8',errors='replace')
clean=re.sub(r'\x1b\[[0-9;]*[a-zA-Z]','',text)
phases=re.findall(r'(Train|Val)\[(\d+)/(\d+)\][^\r\n]{0,240}?(\d+)/(\d+)',clean)
lines=[line for line in clean.replace('\r','\n').splitlines() if line.strip()]
markers=[line[-700:] for line in lines if any(x in line for x in ('Traceback (most recent call last)','RuntimeError:','Error:','Killed','killed','out of memory','Early stopping','mIOU:','mIoU :'))][-18:]
stage=Path('/data/songcl/Project/Cluster_project/pipeline/cooperative_guards/m230_20c15273')
state=json.loads((stage/'state.json').read_text())
guardproc=Path('/proc')/str(state['guardian_pid'])
guardian={'exists':guardproc.exists(),'state':state}
if guardproc.exists():
 t=(guardproc/'stat').read_text();guardian['actual_starttime']=t[t.rfind(')')+2:].split()[19]
table=Path('/proc/locks').read_text().splitlines();locks=[]
for kind in ('training','diagnostic','exclusive'):
 path=Path('/tmp/cluster_project_gpu0_'+kind+'.lock');info=path.stat()
 key='%02x:%02x:%d'%(os.major(info.st_dev),os.minor(info.st_dev),info.st_ino)
 rows=[line for line in table if len(line.split())>5 and line.split()[5]==key]
 locks.append({'kind':kind,'inode':info.st_ino,'kernel_entries':rows})
work=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd')
checkpoints=[]
if work.exists():
 for directory in sorted(work.iterdir()):
  if directory.is_dir():
   files=[]
   for name in ('best.pth','last.pth'):
    path=directory/name
    if path.exists():
     s=path.stat();files.append({'path':str(path),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns})
   checkpoints.append({'directory':str(directory),'files':files})
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),
 'trainer':proc,'runtime_source':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
 'log':str(log),'log_size':st.st_size,'log_mtime_ns':st.st_mtime_ns,'bytes_read':len(raw),
 'last_phase':phases[-1] if phases else None,'markers':markers,'bounded_final_lines':lines[-18:],
 'guardian':guardian,'locks':locks,'checkpoints':checkpoints[-2:],
 'read_only':True,'signals_sent':False,'new_training_launches':0}))
'''
command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o",
           "ConnectTimeout=8", "songcl@192.168.1.115",
           "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(program)]
out = subprocess.run(command, capture_output=True, text=True, encoding="utf8", timeout=25)
record = {
    "owner_provenance_only": {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")},
    "actual_command": command, "returncode": out.returncode, "stderr": out.stderr,
    "observation": json.loads(out.stdout) if out.returncode == 0 else None,
}
target = HERE / "hvd_exit_observation.json"
with target.open("x", encoding="utf8") as f:
    json.dump(record, f, ensure_ascii=False, indent=2)
    f.write("\n")
assert out.returncode == 0, out.stderr[-1500:]
observation = record["observation"]
print(json.dumps({k: observation[k] for k in ("observed_at", "trainer", "last_phase", "markers", "locks")}, ensure_ascii=False))
print(json.dumps({"guardian_status": observation["guardian"]["state"]["status"],
                  "released_at": observation["guardian"]["state"].get("released_at"),
                  "bounded_final_lines": observation["bounded_final_lines"][-5:],
                  "evidence_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}, ensure_ascii=False))
