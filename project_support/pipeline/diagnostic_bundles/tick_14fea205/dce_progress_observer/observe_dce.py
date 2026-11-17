"""Future exact original DCE process/log/source readback; no signal or GPU computation."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,shlex,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anchor import guard,ROOT,EXPECTED,sha
HERE=Path(__file__).resolve().parent
REMOTE_ROOT='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
PID=None;EXPECTED_LOG=None;EXPECTED_START_TICKS=None
COMMIT='5c0c211c8ecc9479ecb34dbb8118a95f4b20e391'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--pid',type=int,default=PID);ap.add_argument('--log',default=EXPECTED_LOG);ap.add_argument('--start-ticks',default=EXPECTED_START_TICKS);args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_DISABLED_NO_OBSERVATION');return
 assert type(args.pid) is int and args.pid>0 and isinstance(args.log,str) and args.log.startswith('/data/songcl/Project/Cluster_project/') and isinstance(args.start_ticks,str) and args.start_ticks.isdigit(),'Real canonical original PID/log/start bindings required; None refuses before transport.'
 guard();exp=json.loads((ROOT/'pipeline/experiments/M220-DCE.json').read_text('utf8'));assert exp['pid']==args.pid and exp['code_commit']==COMMIT and exp['status']=='running' and exp['log']==args.log
 original=json.loads((ROOT/'pipeline/diagnostic_bundles/tick_01d9102a/dce_native_prepare/preparation.json').read_text('utf8'));assert original['code_commit']==COMMIT and len(original['source_files'])==9
 payload={'pid':args.pid,'start_ticks':args.start_ticks,'root':REMOTE_ROOT,'commit':COMMIT,'log':exp['log'],'config':exp['config'],'name':Path(exp['config']).stem,'hashes':original['source_files']}
 script='''import socket,os,json,subprocess,hashlib,time,re
from pathlib import Path
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
p=json.loads(PAYLOAD);pid=p['pid'];proc=Path('/proc')/str(pid)
assert proc.exists() and proc.stat().st_uid==os.getuid()
def identity():
 cmd=(proc/'cmdline').read_bytes().replace(b'\\0',b' ').decode();env=dict(v.split(b'=',1) for v in (proc/'environ').read_bytes().split(b'\\0') if b'=' in v)
 assert 'tools/train.py' in cmd and p['config'] in cmd and str((proc/'cwd').resolve())==p['root']
 initial_env=env.get(b'CUDA_VISIBLE_DEVICES');assert initial_env in (None,b'0')
 return {'pid':pid,'argv':cmd,'cwd':str((proc/'cwd').resolve()),'start_ticks':(proc/'stat').read_text().rsplit(') ',1)[1].split()[19],'initial_cuda_environment':initial_env.decode() if initial_env is not None else 'NOT_EXPOSED_IN_INITIAL_PROC_ENVIRONMENT'}
before=identity();assert before['start_ticks']==p['start_ticks'] and str((proc/'fd'/'1').resolve())==p['log'];head=subprocess.check_output(['git','--no-optional-locks','-C',p['root'],'rev-parse','HEAD'],text=True).strip();assert head==p['commit']
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
row=[x.strip() for x in gpu.split(',')];assert row[0]=='0' and row[1]=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert str(pid) in [line.split(',')[0].strip() for line in contexts.splitlines()]
hashes={}
for rel,want in p['hashes'].items():
 actual=hashlib.sha256((Path(p['root'])/rel).read_bytes()).hexdigest();hashes[rel]=actual
 assert actual==(want if rel.endswith('.py') else '77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea')
def sample():
 path=Path(p['log']);size=path.stat().st_size
 with path.open('rb') as f:f.seek(max(0,size-1200000));data=f.read()
 txt=data.decode('utf8',errors='replace');steps=[(int(a),int(b)) for a,b in re.findall(r'Train\\[(\\d+)/\\d+\\]:[^\\r\\n]*?\\|\\s*(\\d+)/\\d+',txt)]
 assert not any(e in txt for e in ['Traceback','CUDA out of memory','RuntimeError'])
 return {'observed_at':datetime.now(timezone.utc).isoformat(),'log_size':size,'tail_sha256':hashlib.sha256(data).hexdigest(),'last_native_step':steps[-1] if steps else None,'max_native_step':max(steps) if steps else None,'tail_exception_seen':False}
a=sample();time.sleep(3);b=sample();after=identity();assert before==after
fd=[]
for f in (proc/'fd').iterdir():
 try:
  target=str(f.resolve())
  if target.endswith('.log') and target.startswith('/data/songcl/Project/Cluster_project/Cluster_checkpoints/'+p['name']+'/'):fd.append(target)
 except (FileNotFoundError,PermissionError):pass
fd=sorted(set(fd));metric_lines=[]
if len(fd)==1:
 with open(fd[0],errors='replace') as f:
  for line in f:
   if 'mIoU :' in line or 'resume start_epoch:' in line:metric_lines.append(line.strip())
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'identity_before':before,'identity_after':after,'runtime_commit':head,'source_hashes':hashes,'samples':[a,b],'native_logger_paths':fd,'metric_lines':metric_lines,'checkpoint_body_read':False,'GPU_queries':'Read-only GPU0 UUID/compute-PID queries only','GPU0':gpu,'GPU0_contexts':contexts,'signals_sent':False}))
'''.replace('PAYLOAD',repr(json.dumps(payload)))
 args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(script)]
 guard();run=subprocess.run(args,capture_output=True,timeout=45)
 record={'owner':EXPECTED,'observed_at':datetime.now(timezone.utc).isoformat(),'command':args,'returncode':run.returncode,'stdout_sha256':hashlib.sha256(run.stdout).hexdigest(),'stderr':run.stderr.decode('utf8',errors='replace')}
 if run.returncode==0:
  record['observation']=json.loads(run.stdout);lines='\n'.join(record['observation']['metric_lines'])
  import sys;sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
  values,best,missed=mon.parse_native_lineage(lines,resumed=False)
  if not values:best=None;missed=None
  record['precise_native_validation']={'values':values,'best':best,'no_improve':missed,'scope':'Exact live original logger mIoU lines only; no checkpoint read, current training incomplete.'}
 guard()
 with (HERE/'dce_training_progress_observation.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
 assert run.returncode==0,record['stderr']
 print(json.dumps({'samples':record['observation']['samples'],'precise_native_validation':record['precise_native_validation'],'source_runtime_original_preserved':True,'sha256':sha(HERE/'dce_training_progress_observation.json')},ensure_ascii=False))
if __name__=='__main__':main()
