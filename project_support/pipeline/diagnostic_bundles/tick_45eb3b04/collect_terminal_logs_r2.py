"""Exact original complete log collection and second stable PID absence proof."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,subprocess
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import pathlib,hashlib,json,subprocess,datetime,time
out=[]
for t in TASKS:
 assert not (pathlib.Path('/proc')/str(t['pid'])).exists()
 p=pathlib.Path(t['log']);a=p.stat();h=hashlib.sha256(p.read_bytes()).hexdigest();b=p.stat()
 assert (a.st_size,a.st_mtime_ns)==(b.st_size,b.st_mtime_ns) and time.time()-b.st_mtime>600
 row=subprocess.check_output(['nvidia-smi','-i',str(t['gpu']),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
 assert [v.strip() for v in row.split(',')][:2]==[str(t['gpu']),t['uuid']]
 ctx=subprocess.check_output(['nvidia-smi','-i',str(t['gpu']),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip();assert not ctx
 out.append({'id':t['id'],'path':str(p),'sha256':h,'bytes':b.st_size,'mtime_ns':b.st_mtime_ns,'log_age_seconds':time.time()-b.st_mtime,'original_pid_absent':True,'gpu_inventory':row,'gpu_contexts':ctx})
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'logs':out,'signals_sent':False}))
'''
def main():
 owner=guard();phase=json.loads((HERE/'original_phase_reconciliation.json').read_text('utf8'));tasks=[]
 for t in phase['result']['tasks']:
  assert t['process']['present'] is False
  tasks.append({'id':t['id'],'pid':t['process']['pid'],'gpu':t['gpu'],'uuid':t['gpu_inventory'].split(',')[1].strip(),'log':t['log']})
 args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -']
 r=subprocess.run(args,input='TASKS='+repr(tasks)+'\n'+PROGRAM,capture_output=True,text=True,encoding='utf8',timeout=60);assert r.returncode==0,r.stderr[-2000:]
 remote=json.loads(r.stdout);results=[]
 for data in remote['logs']:
  task=next(t for t in tasks if t['id']==data['id']);cfg=Path(task['log']).stem.rsplit('_202610',1)[0].removeprefix('train_')
  local=ROOT/'Checkpoints/server_4'/cfg/('native_terminal_'+owner['token'][:8])/Path(task['log']).name
  local.parent.mkdir(parents=True,exist_ok=True);assert not local.exists() or (local.stat().st_size==data['bytes'] and sha(local)==data['sha256'])
  if not local.exists():
   guard();copy=subprocess.run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115:'+task['log'],str(local)],capture_output=True,text=True,encoding='utf8',timeout=90)
   assert copy.returncode==0,copy.stderr[-2000:]
  assert local.stat().st_size==data['bytes'] and sha(local)==data['sha256']
  text=local.read_text('utf8',errors='replace');vals=[float(x) for x in re.findall(r'(?<!sp)mIOU:\s*([0-9]+(?:\.[0-9]+)?)',text)]
  assert vals
  trains=re.findall(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text);train=list(map(int,trains[-1]));best=max(vals)
  if task['id']=='M212-BCR':
   assert 'Early stopping at epoch 27: no improvement for 10 epochs (best=0.4995)' in text and 'Traceback (most recent call last)' not in text
   assert train==[27,50,4686,4686];state='done_earlystop';best=0.4995;epoch='27/50'
  else:
   assert task['id']=='M213-BFC' and train==[20,50,3832,4686]
   assert 'RuntimeError: Caught RuntimeError in DataLoader worker process 0.' in text and 'Please clone() the tensor' in text and 'Early stopping at epoch' not in text
   state='crashed';epoch='20/50'
  results.append({'id':task['id'],'state':state,'best_miou':best,'best_scope':'Native earlystop best exact' if state=='done_earlystop' else 'Max printed completed validation mIOU only; rounded log precision, interrupted train epoch20 excluded.','epochs':epoch,'last_train':train,'validation_count':len(vals),'full_original_native_log':ref(local),'remote':data})
 guard();p=HERE/'full_terminal_log_evidence.json'
 with p.open('x',encoding='utf8') as f:json.dump({'owner_token':owner['token'],'recorded_at':datetime.now(timezone.utc).isoformat(),'remote_observation':remote,'results':results,'signals_sent':False,'checkpoint_bodies_read':False},f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'evidence':ref(p),'results':[{'id':x['id'],'state':x['state'],'best':x['best_miou'],'epochs':x['epochs'],'log_bytes':x['remote']['bytes'],'log_sha256':x['remote']['sha256']} for x in results]}))
if __name__=='__main__':main()
