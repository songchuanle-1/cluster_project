"""Bounded read-only observation of the exact existing HVD trainer and locks."""
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
TOKEN = "20c15273b622479495bada469c5f3c99"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
LABEL = sys.argv[1]
assert LABEL in ("before", "after", "final")
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"] == THREAD
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
owner = {k: owner[k] for k in (
    "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256",
)}
program = r'''
from pathlib import Path
from datetime import datetime,timezone
import os,json,socket,subprocess,re,time
assert socket.gethostname()=='dl04-MS-7E06'
pid=2829477
root='/data/songcl/Project/Cluster_project/Cluster_hvd_20261106'
source='d20eb221eff6584b67d4e9b5673559d0e1cb735b'
log=root+'/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd_20261106_195228.log'
argv=['python','tools/train.py','configs/Quard/ctf_hcg_csort_hvd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd.yaml','--gpu_ids','0','--num_gpus','1']
proc=Path('/proc')/str(pid)
def identity():
 text=(proc/'stat').read_text();fields=text[text.rfind(')')+2:].split()
 assert fields[19]=='158248846' and fields[0] not in ('Z','X')
 assert proc.stat().st_uid==os.getuid()==1001
 assert os.readlink(proc/'cwd')==root and os.readlink(proc/'fd/1')==log
 assert [v.decode() for v in (proc/'cmdline').read_bytes().split(b'\0') if v]==argv
identity()
actual_source=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip()
assert actual_source==source
def log_sample():
 p=Path(log)
 with p.open('rb') as f:
  f.seek(max(0,p.stat().st_size-24576));raw=f.read(24576)
 text=raw.decode('utf8',errors='replace')
 clean=re.sub(r'\x1b\[[0-9;]*[a-zA-Z]','',text)
 train=re.findall(r'(?:Train|Epoch|epoch)\s*[:\[]?\s*(\d+)[^\r\n]{0,180}?(\d+)/4686',clean)
 phases=re.findall(r'(Train|Val)\[(\d+)/(\d+)\][^\r\n]{0,240}?(\d+)/(\d+)',clean)
 if not train:
  steps=re.findall(r'(\d+)/4686',clean)
  epochs=re.findall(r'(?:Epoch|epoch)\D{0,5}(\d+)',clean)
  train=[(epochs[-1] if epochs else None,steps[-1])] if steps else []
 return {'observed_at':datetime.now(timezone.utc).isoformat(),'log_size':p.stat().st_size,
  'bytes_read':len(raw),'last_native_train':train[-1] if train else None,
  'last_native_phase_progress':phases[-1] if phases else None,
  'fatal_error_markers':[x for x in ('Traceback (most recent call last)','CUDA out of memory','RuntimeError:','FloatingPointError') if x in clean]}
first=log_sample();time.sleep(1.5);second=log_sample();identity()
with Path(log).open('rb') as f:
 f.seek(max(0,Path(log).stat().st_size-2097152));metadata_bytes=f.read(2097152)
metadata=metadata_bytes.decode('utf8',errors='replace')
validation_lines=re.findall(r'(?mi)^[^\r\n]*\bmIOU\s*:\s*[^\r\n]+',metadata)
metadata_summary={'bytes_read':len(metadata_bytes),
 'recent_validation_lines':[line[-350:] for line in validation_lines[-3:]],
 'validation_scalar_precision':'Native printed phase metrics only; not terminal checkpoint exact best.',
 'early_stop_markers':re.findall(r'Early stopping at epoch \d+[^\r\n]*',metadata)[-2:]}
table=Path('/proc/locks').read_text().splitlines();locks=[]
for kind in ('training','diagnostic','exclusive'):
 path=Path('/tmp/cluster_project_gpu0_'+kind+'.lock');st=path.stat()
 key='%02x:%02x:%d'%(os.major(st.st_dev),os.minor(st.st_dev),st.st_ino)
 rows=[row for row in table if len(row.split())>5 and row.split()[5]==key]
 locks.append({'kind':kind,'path':str(path),'inode':st.st_ino,'device_major':os.major(st.st_dev),
  'device_minor':os.minor(st.st_dev),'kernel_entries':rows})
stages={}
for name in ('m230_12e364dc','m230_20c15273'):
 stage=Path('/data/songcl/Project/Cluster_project/pipeline/cooperative_guards')/name
 stages[name]={'exists':stage.exists()}
 if stage.exists():
  for filename in ('spawn.json','state.json'):
   if (stage/filename).exists():
    stages[name][filename]=json.loads((stage/filename).read_text())
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),
 'pid':pid,'starttime':'158248846','uid':1001,'runtime_root':root,'source_commit':actual_source,
 'argv':argv,'log':log,'samples':[first,second],'metadata_summary':metadata_summary,'locks':locks,'stages':stages,
 'read_only':True,'signals_sent':False,'training_launches':0}))
'''
command = [
    "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
    "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
    "PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c " + shlex.quote(program),
]
out = subprocess.run(command, capture_output=True, text=True, encoding="utf8", timeout=30)
observation = json.loads(out.stdout) if out.returncode == 0 else None
result = {"owner": owner, "command": command, "returncode": out.returncode,
          "stderr": out.stderr, "observation": observation}
target = HERE / ("hvd_live_" + LABEL + ".json")
with target.open("x", encoding="utf8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write("\n")
assert out.returncode == 0, out.stderr[-1500:]
print(json.dumps({
    "pid": observation["pid"], "starttime": observation["starttime"],
    "samples": observation["samples"],
    "metadata_summary": observation["metadata_summary"],
    "lock_owners": {x["kind"]: x["kernel_entries"] for x in observation["locks"]},
    "stage_exists": {k: v["exists"] for k, v in observation["stages"].items()},
    "path": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
}))
