"""Exactly one existing canonical FIFO GPU0 dispatch; uncertain requests are never replayed."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,csv,hashlib,io,json,os,shlex,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from anchor import ROOT,guard,sha,EXPECTED
import elc_evidence as evidence
HERE=evidence.TICK;SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
EXP='M225-ELC';CID='hierarchy-undirected-edge-state-line-graph-composition';COMMIT=evidence.COMMIT
UUID='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c';CALLS=[]
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v,new=False):
 guard();p=Path(p)
 if new:
  with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 else:
  tmp=Path(str(p)+'.a6e82f44.dispatch.tmp')
  with tmp.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  guard();os.replace(tmp,p)
def protected():
 b=read(HERE/'post_sfc_dispatch_baseline.json');git=lambda *a:subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
 assert git('rev-parse','HEAD').decode().strip()==COMMIT
 assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and not git('diff','--cached','--name-only','-z')
 for p,h in b['files'].items():assert sha(ROOT/'Cluster'/p)==h
 for p,h in read(HERE/'elc_root_ff_result.json')['source_paths'].items():assert sha(ROOT/'Cluster'/p)==h
def protected_others():
 p=HERE/'elc_before_admission_lifecycle.json';assert sha(p)==evidence.read(HERE/'elc_summary_outputs.json')['lifecycle_baseline']['sha256']
 b=read(p);q=read(ROOT/'pipeline/queue.json')
 for server in q['gpu_queues']:q['gpu_queues'][server]=[t for t in q['gpu_queues'][server] if t.get('id')!=EXP]
 assert q==b['queue'],'Nontarget queue/global fields changed'
 run=read(ROOT/'pipeline/running.json')
 for server in list(run):
  run[server]={g:e for g,e in run[server].items() if e!=EXP}
  if server not in b['running'] and not run[server]:run.pop(server)
 assert run==b['running'],'Nontarget running assignments changed'
 rows=list(csv.DictReader(io.StringIO((ROOT/'pipeline/experiments.csv').read_text(encoding='utf-8-sig'))))
 assert [r for r in rows if r.get('id')!=EXP]==b['csv_rows'],'Nontarget CSV rows changed'
 for rel,h in b['protected_ledgers'].items():
  if rel not in ['queue.json','running.json','experiments.csv']:assert sha(ROOT/'pipeline'/rel)==h,rel
 candidates=read(ROOT/'pipeline/research_work.json')['candidates'];assert {c['id'] for c in candidates}==set(b['candidate_digests'])
 for c in candidates:
  if c['id']!=CID:assert hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==b['candidate_digests'][c['id']],c['id']
def strict_ssh(host,user,command,timeout=8):
 guard();assert (host,user)==('192.168.1.115','songcl')
 inventory='nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null'
 if command==inventory:command=command.replace('nvidia-smi ','nvidia-smi -i 0 ',1)
 elif 'nvidia-smi' in command:raise RuntimeError('Unexpected canonical GPU query shape; refuse rather than query another card')
 launch='proc=subprocess.Popen(' in command and 'tools/train.py' in command
 if 'Popen' in command and 'tools/train.py' in command:assert launch
 remote_guard="import socket;assert socket.gethostname()=='dl04-MS-7E06'"
 if launch:
  assert command.count('proc=subprocess.Popen(')==1 and not any(x['canonical_native_launch_request'] for x in CALLS)
  deadline='assert __import__("datetime").datetime.now(__import__("datetime").timezone.utc)<__import__("datetime").datetime.fromisoformat("'+EXPECTED['deadline_at']+'"); '
  command=command.replace('proc=subprocess.Popen(',deadline+'proc=subprocess.Popen(',1)
  remote_guard='''import socket,subprocess,fcntl,os,sys
assert socket.gethostname()=='dl04-MS-7E06'
handles=[]
try:
 for kind in ('training','diagnostic','exclusive'):
  f=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().split(',')
 assert row[0].strip()=='0' and row[1].strip()==GPU_UUID and int(row[2])<1024 and int(row[3])<10
 assert not subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONFAULTHANDLER']='1'
 result=subprocess.run(['/bin/bash','-lc',COMMAND],env=env,capture_output=True,text=True,timeout=120)
 sys.stdout.write(result.stdout);sys.stderr.write(result.stderr)
 if result.returncode:raise SystemExit(result.returncode)
finally:
 for handle in handles:handle.close()
'''.replace('GPU_UUID',repr(UUID)).replace('COMMAND',repr(command))
 checked='export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(remote_guard)
 if not launch:checked+=' && '+command
 args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',user+'@'+host,checked]
 run=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=max(timeout,150))
 CALLS.append({'recorded_at':datetime.now(timezone.utc).isoformat(),'command':args,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'canonical_native_launch_request':launch,'physical_gpu':0,'gpu_uuid':UUID})
 save(HERE/'elc_dispatch_transport_calls.json',CALLS)
 if run.returncode:raise RuntimeError('Pinned SSH failed; preserve original uncertainty, never blind retry: '+run.stderr[-1500:])
 return run.stdout.strip()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');args=ap.parse_args()
 if not args.execute_root:print('DRAFT_READ_ONLY_NO_DISPATCH');return
 evidence.require_execution();evidence.reviewed()
 guard();assert not any((HERE/n).exists() for n in ['elc_dispatch_request.json','elc_dispatch_result.json','elc_dispatch_transport_calls.json'])
 assert sha(HERE/'elc_actual_four_result_review.json')==evidence.review_ref()['sha256']
 for e in [evidence.independent_ref()]:assert sha(ROOT/e['path'])==e['sha256'] and read(ROOT/e['path'])['material_concerns']==[]
 protected();protected_others();sys.path.insert(0,str(SKILL));import pipeline_monitor as mon;import closure
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 original_ssh=mon.ssh;original_git_ssh=os.environ.get('GIT_SSH_COMMAND')
 try:
  guard();server=mon.load_servers(str(ROOT))['server-4']
  assert server['host']=='192.168.1.115' and server['user']=='songcl' and server['expected_hostname']=='dl04-MS-7E06' and server['allowed_gpus']==[0,1] and server['max_tasks_per_gpu']==1 and server['dispatch_enabled'] is True
  queue=mon.load_queue(str(ROOT));tasks=queue['gpu_queues']['server-4'];target=[t for t in tasks if t.get('id')==EXP];assert len(target)==1
  task=target[0];assert task['status']=='waiting' and task['code_commit']==COMMIT and str(task['gpu'])=='0' and not task.get('pid') and not task.get('dispatch_hold') and not task.get('resume_from')
  assert not task.get('launch_verified') and task.get('launch_verification')!='pending_progress' and task.get('dispatch_phase') not in ['launch_requested','progress_pending']
  assert [t['id'] for t in tasks if t.get('status')=='waiting' and not t.get('dispatch_hold')]==[EXP]
  # Preserve original nonselected GPU1 SFC work; only the selected physical GPU0 must be free.
  reserved=[]
  for other in tasks:
   hold=other.get('dispatch_hold','');uncertain=isinstance(hold,str) and hold.startswith(('Interrupted claim;','Launch uncertain;','Process observed'))
   if other.get('status') in ('running','claiming') or (other.get('status')=='waiting' and (other.get('launch_verification')=='pending_progress' or uncertain)):
    gpu=other.get('gpu');assert (type(gpu) is int and gpu in (0,1)) or (type(gpu) is str and gpu in ('0','1'))
    assert int(gpu)!=0,'Selected GPU0 has canonical active/uncertain assignment';reserved.append(other)
  running=mon.load_running(str(ROOT)).get('server-4',{})
  for key,value in running.items():
   assert (type(key) is int and key in (0,1)) or (type(key) is str and key in ('0','1')),'Unknown running GPU assignment'
  assert not running.get('0') and not running.get(0),'Selected GPU0 has registered running assignment'
  existing_tasks=max(len(reserved),sum(bool(v) for v in running.values()))
  closure.admission(ROOT,task);closure.validate_foreground_dispatch_budget(ROOT,queue,task)
  mon.ssh=strict_ssh;os.environ['GIT_SSH_COMMAND']='ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8'
  guard();protected();protected_others();save(HERE/'elc_dispatch_request.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'id':EXP,'code_commit':COMMIT,'operation':'one_existing_canonical_FIFO_GPU0_dispatch','physical_gpu':0,'gpu_uuid':UUID},new=True)
  events=[]
  mon._process_queue(queue,'server-4',server['host'],server['user'],str(ROOT),set(),{'0'},events,max_tasks_per_gpu=1,allow_external_overlay=False,remote_code_root=server['remote_code_root'],current_tasks=existing_tasks,max_tasks_total=existing_tasks+1)
  after=mon.load_queue(str(ROOT));final=next(t for t in after['gpu_queues']['server-4'] if t.get('id')==EXP)
  assert str(final['gpu'])=='0';verified=final['status']=='running' and final.get('launch_verified') is True and final.get('launch_verification')=='training_progress'
  protected();protected_others();work=read(ROOT/'pipeline/research_work.json');candidate=next(c for c in work['candidates'] if c['id']==CID)
  candidate.update(stage='training' if verified else 'deployment',training_status='running' if verified else final['status'],next_action=('Monitor exact original ELC PID/log on server4 GPU0; canonical increasing native progress verified, efficacy UNKNOWN. Unselected-card replay prohibited and all other holds retained.' if verified else 'Preserve original claim/request/PID/log/receipt; reconcile exact original attempt, no blind retry/cold fallback/signal/other-card launch.'))
  exp=mon.load_experiment(str(ROOT),EXP)
  if exp is not None:exp['training_status']='running' if verified else final['status'];guard();mon.save_experiment(str(ROOT),exp)
  work['updated_at']=datetime.now(timezone.utc).isoformat();save(ROOT/'pipeline/research_work.json',work);protected_others()
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':EXPECTED['token'],'canonical_dispatch_invoked_once':True,'events':events,'task_after':final,'running_after':mon.load_running(str(ROOT)),'verified_native_progress':verified,'physical_gpu':0,'gpu_uuid':UUID,'signals_sent':False,'blind_relaunch_performed':False,'protected_other_tasks_and_terminal_receipts_unchanged':True,'transport_calls':ref(HERE/'elc_dispatch_transport_calls.json') if (HERE/'elc_dispatch_transport_calls.json').exists() else None}
  save(HERE/'elc_dispatch_result.json',result,new=True)
  print(json.dumps({'id':EXP,'status':final['status'],'launch_verified':final.get('launch_verified'),'pid':final.get('pid'),'log':final.get('log'),'physical_gpu':0,'evidence':ref(HERE/'elc_dispatch_result.json')},ensure_ascii=False))
 finally:
  mon.ssh=original_ssh
  if original_git_ssh is None:os.environ.pop('GIT_SSH_COMMAND',None)
  else:os.environ['GIT_SSH_COMMAND']=original_git_ssh
  lock.close()
if __name__=='__main__':main()
