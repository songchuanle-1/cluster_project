"""Owned-tick read-only NVML/process/native-log observation; no torch or job mutation."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/project/cluster_project')
BUNDLE = Path(__file__).resolve().parent
TOKEN = '86e41faaff0b4fa1965a8b90d7636631'
OWNER = '01a159c5-29ab-7a22-ba7f-e79174757253'
assert os.environ.get('CODEX_THREAD_ID') == OWNER
lease = json.loads((ROOT / 'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
assert lease.get('token') == TOKEN
view = json.loads((ROOT / 'pipeline/headless/.tick_model_view.json').read_text(encoding='utf-8'))
assert dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(view['deadline_at'])
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='live_running_resource_check.json')
options = parser.parse_args()
assert Path(options.output).name == options.output and options.output.endswith('.json')
path = BUNDLE/options.output
assert not path.exists(), 'Preserve every previous observation'
payload = r'''
import socket
assert socket.gethostname() == 'dl04-MS-7E06', 'Pinned server-4 hostname mismatch'
import datetime as dt, json, re, subprocess, time
from pathlib import Path
root=Path('/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1')
def command(args):
 return subprocess.check_output(args,text=True,timeout=15).strip()
inventory=command(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
contexts=command(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])
uuids={'0':'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c','1':'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
for row in inventory.splitlines():
 parts=[x.strip() for x in row.split(',')]
 assert uuids[parts[0]] == parts[1]
cases={
 'M207-HAP':(979955,'21613920','0','ctf_hcg_csort_hap','20261022_001959',False),
 'M206-CGCA':(732137,'21298582','1','ctf_hcg_csort_cgca','20261021_232722',True)}
out={'observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'hostname':socket.gethostname(),'inventory':inventory,'contexts':contexts,'experiments':{},'read_only':True,'gpu_computation_started':False}
for name,(pid,start,gpu,mod,stamp,resume) in cases.items():
 proc=Path('/proc')/str(pid)
 item={'pid':pid,'pid_exists':proc.exists(),'gpu':gpu}
 if proc.exists():
  argv=(proc/'cmdline').read_bytes().split(b'\0')[:-1]
  argv=[x.decode() for x in argv]
  actualstart=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
  cfg='configs/Quard/'+mod+'/model_base1_quard2_c2f_enc_lite_posA_l1_'+mod+'.yaml'
  expected=['python','tools/train.py',cfg,'--gpu_ids',gpu,'--num_gpus','1']
  if resume: expected+=['--resume','/data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth']
  assert argv==expected and actualstart==start and (proc/'cwd').resolve()==root, (name,'process identity')
  item.update(starttime=actualstart,exact_argv_cwd_match=True)
 log=root/'logs'/('train_model_base1_quard2_c2f_enc_lite_posA_l1_'+mod+'_'+stamp+'.log')
 with log.open('rb') as fh:
  fh.seek(max(0,log.stat().st_size-4000000))
  tail=fh.read().decode('utf-8',errors='replace')
 progress=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',tail))
 item.update(log=str(log),log_age_seconds=time.time()-log.stat().st_mtime,log_bytes=log.stat().st_size,
  native_progress=[dict(epoch=int(m[1]),epochs=int(m[2]),step=int(m[3]),steps=int(m[4])) for m in progress[-2:]],
  metrics_or_errors=[line for line in tail.splitlines() if line.startswith(('mIOU:','spmIOU:','Early stopping','Traceback','RuntimeError','Best mIoU'))][-12:])
 out['experiments'][name]=item
print(json.dumps(out))
'''
args = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8',
        'songcl@192.168.1.115', '/usr/bin/python3 -B -']
result = subprocess.run(args, input=payload, text=True, encoding='utf-8', capture_output=True, timeout=45)
record = {'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),'tick_token':TOKEN,
          'command':args,'remote_script_sha256':hashlib.sha256(payload.encode()).hexdigest(),
          'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
if result.returncode == 0:
    record['data'] = json.loads(result.stdout)
with path.open('x',encoding='utf-8') as stream:
    json.dump(record,stream,ensure_ascii=False,indent=2)
print(json.dumps({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                 'returncode':result.returncode,'data':record.get('data'),'stderr':result.stderr},ensure_ascii=False))
raise SystemExit(result.returncode)
