"""Read only the admitted BEC0 original process, own log, source and GPU0."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,time
from anchor_bfc_packet import guard as _base_guard

def guard():
 _base_guard()
 return json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import pathlib,subprocess,os,re,json,hashlib,time,datetime
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
head=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip();assert head==TASK['code_commit']=='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
p=pathlib.Path('/proc')/str(TASK['pid']);stat=(p/'stat').read_text().rsplit(')',1)[1].split();args=[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x]
assert stat[0] not in ('Z','X','x') and args==['python','tools/train.py',TASK['config'],'--gpu_ids','0','--num_gpus','1']
assert os.readlink(p/'cwd')==root and os.readlink(p/'fd/1')==TASK['log']
source={n:hashlib.sha256((pathlib.Path(root)/n).read_bytes()).hexdigest() for n in TASK['model8']};assert source==TASK['model8']
cfgsha=hashlib.sha256((pathlib.Path(root)/TASK['config']).read_bytes()).hexdigest();assert cfgsha=='77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea'
log=pathlib.Path(TASK['log']);size=log.stat().st_size
with log.open('rb') as f:f.seek(max(0,size-500000));tail=f.read().decode(errors='replace')
matches=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',tail));assert matches
errors=[line[-800:] for line in tail.replace('\r','\n').splitlines() if any(s in line for s in ['Traceback','RuntimeError','AttributeError','Early stopping'])];assert not errors
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();assert [v.strip() for v in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip();assert any(line.split(',')[0].strip()==str(TASK['pid']) for line in contexts.splitlines())
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'id':'M215-BEC','pid':TASK['pid'],'start_ticks':stat[19],'state':stat[0],'argv':args,'cwd':root,'fd1':TASK['log'],'runtime_HEAD':head,'actual_model8_hashes':source,'deployed_config_sha256':cfgsha,'train_progress':[int(matches[-1][k]) for k in [1,2,3,4]],'log_bytes':size,'log_age_seconds':time.time()-log.stat().st_mtime,'gpu_inventory':gpu,'gpu_contexts':contexts,'errors':errors,'read_only':True,'GPU1_queried':False,'identity_attribution_attempted':False,'signals_sent':False}))
'''
def main():
 owner=guard();q=json.loads((ROOT/'pipeline/queue.json').read_text('utf8'));t=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M215-BEC')
 assert t['status']=='running' and t['launch_verified'] is True and t['launch_verification']=='training_progress' and str(t['gpu'])=='0'
 manifest=json.loads((HERE.parent/'tick_94f8ddb8/bec_r1_execution/native_manifest.json').read_text('utf8'));model8={'framework/model/Quard_model/'+manifest['candidate_name']+'/'+n:v for n,v in manifest['candidate_source_hashes'].items()}
 assert len(model8)==8 and all(sha(ROOT/'Cluster'/n)==v for n,v in model8.items())
 task={k:t[k] for k in ['pid','config','log','code_commit']};task['model8']=model8;samples=[]
 for i in range(2):
  if i:time.sleep(3)
  guard();r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input='TASK='+repr(task)+'\n'+PROGRAM,capture_output=True,text=True,encoding='utf8',timeout=40);assert r.returncode==0,r.stderr[-2200:];samples.append(json.loads(r.stdout))
 a,b=samples;assert a['pid']==b['pid'] and a['start_ticks']==b['start_ticks'] and a['argv']==b['argv']
 growth=(b['train_progress'][0],b['train_progress'][2])>(a['train_progress'][0],a['train_progress'][2]);assert growth
 guard();out={'owner_token':owner['token'],'observations':samples,'native_TRAIN_growth':growth,'original_BEC_launch_preserved':True,'queue_launch_verified':True,'dispatch_phase_field_scope':'Canonical retained progress_pending but launch_verified=true and independent actual TRAIN growth. No replay or lifecycle mutation.','admission_receipt':t['admission_receipt'],'GPU_scope':'server4 physical0 only; no GPU1 query or computation.','new_training_by_observer':False}
 p=HERE/'bec_training_progress_observation.json'
 with p.open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'path':str(p),'sha256':sha(p),'pid':t['pid'],'start_ticks':b['start_ticks'],'progress':[a['train_progress'],b['train_progress']],'native_TRAIN_growth':growth,'GPU0_contexts':b['gpu_contexts']},ensure_ascii=False))
if __name__=='__main__':main()
