"""Exact full-log archive and canonical normal-terminal finalization only."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,subprocess,sys
from anchor import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='0f02aaa25b1a4f6e9d27cf8da33b8ca1';BASE='56b2a96dc48cc8a88f0f7105527ef448113b1060'
CONFIG='configs/Quard/ctf_hcg_csort_aef/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aef.yaml'
LOG='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aef_20261027_124036.log'
RECEIPT={'path':'pipeline/admissions/M216-AEF.json','sha256':'041074985258a51cf2a5629dcbf19f55fceb42c5255c78251c1fb9cc680ae9a9'}
PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import pathlib,os,sys,json,hashlib,datetime
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
assert not (pathlib.Path('/proc')/'759301').exists()
p=pathlib.Path(LOG);a=p.stat();h=hashlib.sha256();count=0
with p.open('rb') as f:
 while True:
  block=f.read(1024*1024)
  if not block:break
  h.update(block);count+=len(block);sys.stdout.buffer.write(block)
sys.stdout.buffer.flush();b=p.stat();assert (a.st_size,a.st_mtime_ns)==(b.st_size,b.st_mtime_ns) and count==a.st_size
matches=[]
for entry in pathlib.Path('/proc').iterdir():
 if not entry.name.isdigit():continue
 try:
  if entry.stat().st_uid!=os.getuid():continue
  argv=[x.decode() for x in (entry/'cmdline').read_bytes().split(b'\0') if x]
  if CONFIG not in argv or 'tools/train.py' not in argv:continue
  if os.readlink(entry/'cwd')!=root:continue
  matches.append({'pid':int(entry.name),'argv':argv,'fd1':os.readlink(entry/'fd/1')})
 except (OSError,UnicodeError):pass
assert not (pathlib.Path('/proc')/'759301').exists()
print('AEF_EXACT_ARCHIVE_META='+json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log':str(p),'bytes':count,'sha256':h.hexdigest(),'remote_mtime_ns':b.st_mtime_ns,'original_pid_absent_before_after':True,'same_config_processes':matches,'signals_sent':False,'GPU1_queried':False}),file=sys.stderr)
'''
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def exclusive(p,b):
 with Path(p).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def main():
 assert sys.argv[1:]==['--execute-root'] and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
 owner=guard();assert owner['token']==TOKEN and sha(ROOT/RECEIPT['path'])==RECEIPT['sha256']
 obs=read(HERE/'aef_end_and_slot_observation.json');assert sha(HERE/'aef_end_and_slot_observation.json')=='01ff5497bd7413d238c2e45f002aa5cccfda988eae11d7ac4c6267f3b26fe2ea'
 assert obs['owner']['token']==TOKEN and obs['observation']['process']=={'pid':759301,'exists':False} and obs['observation']['explicit_early_stop_lines']==['Early stopping at epoch 23: no improvement for 10 epochs (best=0.4956)'] and obs['observation']['explicit_exception_lines']==[]
 assert obs['reviewed_CRE_readonly_probe']['idle'] is True
 archive_dir=HERE/'aef_exact_terminal_archive';assert not archive_dir.exists() and not (HERE/'aef_finalize_intent.json').exists(),'Preserve/reconcile partial attempt; never replay'
 archive_dir.mkdir();log=archive_dir/Path(LOG).name
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input=('LOG='+repr(LOG)+'\nCONFIG='+repr(CONFIG)+'\n'+PROGRAM).encode(),capture_output=True,timeout=60)
 assert r.returncode==0,r.stderr.decode('utf8',errors='replace')[-2000:]
 marker=[x.removeprefix('AEF_EXACT_ARCHIVE_META=') for x in r.stderr.decode('utf8',errors='replace').splitlines() if x.startswith('AEF_EXACT_ARCHIVE_META=')];assert len(marker)==1;meta=json.loads(marker[0]);assert meta['log']==LOG and meta['bytes']==len(r.stdout) and meta['sha256']==hashlib.sha256(r.stdout).hexdigest() and meta['original_pid_absent_before_after'] and meta['same_config_processes']==[]
 tail=r.stdout[-1200000:].decode('utf8',errors='replace');assert 'Early stopping at epoch 23: no improvement for 10 epochs (best=0.4956)' in tail and not any(x in tail for x in ['Traceback (most recent call last)','RuntimeError:'])
 exclusive(log,r.stdout);exclusive(archive_dir/'exact_log_evidence.json',encode({'owner_token':TOKEN,'remote':meta,'local':ref(log),'scope':'Exact full original log; PID absent before/after copy and no same-config process under original cwd. No checkpoint/other log/GPU1 read.'}))
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();queue=monitor.load_queue(str(ROOT));matches=[t for rows in queue['gpu_queues'].values() for t in rows if t.get('id')=='M216-AEF'];assert len(matches)==1;task=matches[0]
  assert task['pid']==759301 and task['config']==CONFIG and task['log']==LOG and task['code_commit']==BASE and str(task['gpu'])=='0' and task['status']=='running' and task['admission_receipt']==RECEIPT['path'] and task['launch_verified'] is True and task['launch_verification']=='training_progress'
  running=monitor.load_running(str(ROOT));assert running['server-4']['0']==['M216-AEF'] or running['server-4']['0']=='M216-AEF'
  journal=ROOT/'pipeline/archive_pending'/(hashlib.sha256(b'M216-AEF').hexdigest()+'.json');assert not journal.exists()
  before={'owner_token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),'queue_task':copy.deepcopy(task),'experiment_before':monitor.load_experiment(str(ROOT),'M216-AEF'),'exact_log':ref(log),'exact_log_evidence':ref(archive_dir/'exact_log_evidence.json'),'canonical_action':'finalize_task exact done_earlystop/0.4956/23of50 only; never fake deathwatch or replay uncertain archive'}
  exclusive(HERE/'aef_finalize_intent.json',encode(before));guard()
  original_pull=monitor.pull_log
  def exact_pull(project_dir,host,user,remote_log,cfg_name,state,srv_name=''):
   assert Path(project_dir).resolve()==ROOT.resolve() and (host,user,remote_log,cfg_name,state,srv_name)==('192.168.1.115','songcl',LOG,Path(CONFIG).stem,'done_earlystop','server-4') and sha(log)==meta['sha256'];return str(log)
  monitor.pull_log=exact_pull;events=[]
  try:monitor.finalize_task(str(ROOT),queue,'server-4','192.168.1.115','songcl',task,Path(CONFIG).stem,'done_earlystop',0.4956,'23/50','0',LOG,events)
  finally:monitor.pull_log=original_pull
  exp=monitor.load_experiment(str(ROOT),'M216-AEF');newq=monitor.load_queue(str(ROOT));newrunning=monitor.load_running(str(ROOT))
  assert exp['status']=='done_earlystop' and exp['final_best']=='0.4956' and exp['epochs_final']=='23/50' and exp['code_commit']==BASE and exp['admission_receipt']==RECEIPT['path'] and exp['launch_verified'] is True and exp['log_local']==str(log)
  assert not any(t.get('id')=='M216-AEF' for rows in newq['gpu_queues'].values() for t in rows) and not newrunning.get('server-4',{}).get('0') and not journal.exists()
  exclusive(HERE/'aef_finalize_result.json',encode({'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'status':'CANONICAL_DONE_EARLYSTOP_RECORDED','experiment_id':'M216-AEF','archive_id':exp['archive_id'],'best':'0.4956','epochs':'23/50','exact_full_log':ref(log),'events':events,'source_commit':BASE,'new_training_launches':0,'canonical_pending_absent':True}))
  print(json.dumps({'status':'CANONICAL_DONE_EARLYSTOP_RECORDED','archive_id':exp['archive_id'],'best':'0.4956','epochs':'23/50','full_log_sha256':meta['sha256'],'result':ref(HERE/'aef_finalize_result.json')}))
 finally:lock.close()
if __name__=='__main__':main()
