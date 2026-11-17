"""Read-only two-sample observation after the single canonical BFC launch."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,time
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import pathlib,os,json,subprocess,re,time,hashlib,datetime
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
head=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip();assert head=='48fc302c3c02ffef0b241be3593c386b6b65a72e'
out=[]
for t in TASKS:
 p=pathlib.Path('/proc')/str(t['pid']);s=(p/'stat').read_text().rsplit(')',1)[1].split();args=[v.decode() for v in (p/'cmdline').read_bytes().split(b'\0') if v]
 assert s[0] not in ['Z','X','x'] and args==['python','tools/train.py',t['config'],'--gpu_ids',str(t['gpu']),'--num_gpus','1']
 assert os.readlink(p/'cwd')==root and os.readlink(p/'fd/1')==t['log']
 if t['id']=='M212-BCR':assert s[19]=='51717921' and t['pid']==1215422
 if t['id']=='M213-BFC':assert s[19]=='56265957' and t['pid']==219369
 actual={name:hashlib.sha256((pathlib.Path(root)/name).read_bytes()).hexdigest() for name in t['model8']};assert actual==t['model8']
 configsha=hashlib.sha256((pathlib.Path(root)/t['config']).read_bytes()).hexdigest();assert configsha=='77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea'
 log=pathlib.Path(t['log'])
 with log.open('rb') as f:f.seek(max(0,log.stat().st_size-600000));tail=f.read().decode(errors='replace')
 trains=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',tail));vals=list(re.finditer(r'Val\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',tail));assert trains
 row=subprocess.check_output(['nvidia-smi','-i',str(t['gpu']),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();assert [v.strip() for v in row.split(',')][:2]==[str(t['gpu']),t['uuid']]
 ctx=subprocess.check_output(['nvidia-smi','-i',str(t['gpu']),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip();assert any(line.split(',')[0].strip()==str(t['pid']) for line in ctx.splitlines())
 errors=[v[-600:] for v in tail.replace('\r','\n').splitlines() if any(k in v for k in ['Traceback','AttributeError','RuntimeError','Early stopping'])];assert not errors
 out.append({'id':t['id'],'pid':t['pid'],'start_ticks':s[19],'state':s[0],'gpu':t['gpu'],'uuid':t['uuid'],'argv':args,'cwd':root,'fd1':t['log'],'runtime_HEAD':head,'admitted_scientific_source':t['code_commit'],'actual_model8_hashes':actual,'deployed_config_sha256':configsha,'train_progress':[int(trains[-1][k]) for k in [1,2,3,4]],'val_progress':[int(vals[-1][k]) for k in [1,2,3,4]] if vals else None,'log_bytes':log.stat().st_size,'log_age_seconds':time.time()-log.stat().st_mtime,'gpu_inventory':row,'gpu_contexts':ctx,'errors':errors,'read_only':True,'signals_sent':False})
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tasks':out}))
'''
def main():
 owner=guard();q=read(ROOT/'pipeline/queue.json')['gpu_queues']['server-4'];tasks=[]
 specs=[('M213-BFC',0,ROOT/'pipeline/diagnostic_bundles/tick_336ca5d7/bfc_execution/native_manifest.json','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),('M212-BCR',1,ROOT/'pipeline/diagnostic_bundles/tick_7526f819/bcr_gpu1_execution/native_manifest.json','GPU-7f82edb9-f620-8045-caea-a75232265cd1')]
 for eid,gpu,mf,uuid in specs:
  t=next(t for t in q if t['id']==eid);assert t['status']=='running' and t['launch_verified'] is True and str(t['gpu'])==str(gpu)
  manifest=read(mf);model8={'framework/model/Quard_model/'+manifest['candidate_name']+'/'+name:value for name,value in manifest['candidate_source_hashes'].items()};assert len(model8)==8 and all(sha(ROOT/'Cluster'/name)==value for name,value in model8.items())
  tasks.append({k:t[k] for k in ['id','pid','config','log','code_commit']}|{'gpu':gpu,'uuid':uuid,'model8':model8})
 samples=[];payload='TASKS='+repr(tasks)+'\n'+PROGRAM
 for i in range(2):
  if i:time.sleep(3)
  guard();run=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input=payload,capture_output=True,text=True,encoding='utf8',timeout=40)
  assert run.returncode==0,run.stderr[-2000:];samples.append(json.loads(run.stdout))
 summary=[]
 for a,b in zip(samples[0]['tasks'],samples[1]['tasks']):
  assert a['pid']==b['pid'] and a['start_ticks']==b['start_ticks'] and a['argv']==b['argv']
  growth=(b['train_progress'][0],b['train_progress'][2])>(a['train_progress'][0],a['train_progress'][2])
  summary.append({'id':a['id'],'pid':a['pid'],'start_ticks':a['start_ticks'],'progress':[a['train_progress'],b['train_progress']],'native_TRAIN_growth':growth})
 assert summary[0]['native_TRAIN_growth'],'Original BFC launch progress needs read-only phase reconciliation, never replay'
 guard();out={'owner_token':owner['token'],'observations':samples,'summary':summary,'BCR_original_source11a_and_model8_YAML_process_preserved':True,'BFC_tested_admitted_and_runtime_source48fc':True,'historical_manifests_scope':'Read-only exact model/source provenance, never reused execution leases','no_migration_restart_or_signals':True,'M206':'PAUSED_NOT_OBSERVED_ON_GPU_NOT_RESUMED'}
 p=HERE/'active_runs_progress_observation.json'
 with p.open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'path':str(p),'sha256':sha(p),'summary':summary},ensure_ascii=False))
if __name__=='__main__':main()
