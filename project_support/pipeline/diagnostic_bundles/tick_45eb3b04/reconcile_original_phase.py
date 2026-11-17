"""Read only the two original job identities, own log tails, and allowed GPUs."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import pathlib,json,subprocess,os,re,time,datetime,hashlib
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
head=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip();assert head=='48fc302c3c02ffef0b241be3593c386b6b65a72e'
out=[]
for t in TASKS:
 p=pathlib.Path('/proc')/str(t['pid']);process={'pid':t['pid'],'present':False}
 try:
  stat=(p/'stat').read_text().rsplit(')',1)[1].split();args=[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x]
  assert stat[19]==t['expected_start'] and args==['python','tools/train.py',t['config'],'--gpu_ids',str(t['gpu']),'--num_gpus','1']
  assert os.readlink(p/'cwd')==root and os.readlink(p/'fd/1')==t['log']
  process.update(present=True,start_ticks=stat[19],state=stat[0],argv=args,cwd=root,fd1=t['log'])
 except FileNotFoundError:process['observation']='Original registered PID not present at read time; no exit reason inferred.'
 actual={n:hashlib.sha256((pathlib.Path(root)/n).read_bytes()).hexdigest() for n in t['model8']};assert actual==t['model8']
 cfgsha=hashlib.sha256((pathlib.Path(root)/t['config']).read_bytes()).hexdigest();assert cfgsha=='77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea'
 log=pathlib.Path(t['log']);size=log.stat().st_size
 with log.open('rb') as f:f.seek(max(0,size-1000000));tail=f.read().decode(errors='replace')
 lines=tail.replace('\r','\n').splitlines();terminal=[x[-1400:] for x in lines if any(k in x for k in ['Traceback','Error:','Early stopping','early stop','Early stop','Best','best','mIoU','Training finished','finished training'])]
 trains=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',tail));vals=list(re.finditer(r'Val\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',tail))
 row=subprocess.check_output(['nvidia-smi','-i',str(t['gpu']),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();assert [x.strip() for x in row.split(',')][:2]==[str(t['gpu']),t['uuid']]
 ctx=subprocess.check_output(['nvidia-smi','-i',str(t['gpu']),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
 out.append({'id':t['id'],'gpu':t['gpu'],'process':process,'admitted_scientific_source':t['code_commit'],'runtime_HEAD':head,'source8':actual,'YAML_sha256':cfgsha,'log':t['log'],'log_bytes':size,'log_age_seconds':time.time()-log.stat().st_mtime,'train_progress':[int(trains[-1][k]) for k in [1,2,3,4]] if trains else None,'val_progress':[int(vals[-1][k]) for k in [1,2,3,4]] if vals else None,'terminal_or_metric_lines':terminal[-35:],'tail_last_lines':lines[-14:],'gpu_inventory':row,'gpu_contexts':ctx})
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'tasks':out,'read_only':True,'signals_sent':False}))
'''
def main():
 owner=guard();q=json.loads((ROOT/'pipeline/queue.json').read_text('utf8'))['gpu_queues']['server-4'];tasks=[]
 specs=[('M213-BFC',0,'56265957',ROOT/'pipeline/diagnostic_bundles/tick_336ca5d7/bfc_execution/native_manifest.json','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),('M212-BCR',1,'51717921',ROOT/'pipeline/diagnostic_bundles/tick_7526f819/bcr_gpu1_execution/native_manifest.json','GPU-7f82edb9-f620-8045-caea-a75232265cd1')]
 for eid,gpu,start,mf,uuid in specs:
  t=next(x for x in q if x['id']==eid);m=json.loads(mf.read_text('utf8'));model8={'framework/model/Quard_model/'+m['candidate_name']+'/'+n:h for n,h in m['candidate_source_hashes'].items()}
  tasks.append({k:t[k] for k in ['id','pid','config','log','code_commit']}|{'gpu':gpu,'expected_start':start,'uuid':uuid,'model8':model8})
 payload='TASKS='+repr(tasks)+'\n'+PROGRAM
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input=payload,capture_output=True,text=True,encoding='utf8',timeout=45)
 guard();out={'owner_token':owner['token'],'command_scope':'Bounded readonly original registered PID and own log tails; no unknown PID lookup or process operation.','returncode':r.returncode,'stderr':r.stderr,'result':json.loads(r.stdout) if r.returncode==0 else None}
 p=HERE/'original_phase_reconciliation.json'
 with p.open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
 assert r.returncode==0,r.stderr[-2000:]
 print(json.dumps({'path':str(p),'sha256':sha(p),'tasks':[{'id':t['id'],'process':t['process'],'train':t['train_progress'],'val':t['val_progress'],'terminal_or_metric_lines':t['terminal_or_metric_lines'][-10:],'tail_last_lines':t['tail_last_lines'][-5:],'gpu_inventory':t['gpu_inventory'],'gpu_contexts':t['gpu_contexts']} for t in out['result']['tasks']]},ensure_ascii=False))
if __name__=='__main__':main()
