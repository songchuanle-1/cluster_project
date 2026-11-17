"""Read-only exact BEC process/own-log evidence plus reviewed physical0 probe."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,subprocess,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import pathlib,subprocess,os,re,json,hashlib,datetime,time
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1')
head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip();assert head==TASK['code_commit']=='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
source={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in TASK['model8']};assert source==TASK['model8']
cfg=hashlib.sha256((root/TASK['config']).read_bytes()).hexdigest();assert cfg=='77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea'
p=pathlib.Path('/proc')/str(TASK['pid']);process={'pid':TASK['pid'],'exists':p.exists()}
if p.exists():
 try:
  stat=(p/'stat').read_text().rsplit(')',1)[1].split();args=[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x]
  process.update(state=stat[0],start_ticks=stat[19],argv=args,cwd=os.readlink(p/'cwd'),fd1=os.readlink(p/'fd/1'))
 except OSError as e:process['read_error']=str(e)
log=pathlib.Path(TASK['log']);size=log.stat().st_size
with log.open('rb') as f:f.seek(max(0,size-1200000));tail=f.read().decode('utf8',errors='replace')
lines=tail.replace('\r','\n').splitlines()
semantic=[x[-1600:] for x in lines if re.search(r'early.stop|best|valid|miou|mIoU|Traceback|RuntimeError|Error:|finish|complete|patience',x,re.I)][-50:]
matches=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',tail))
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'runtime_HEAD':head,'source_model8':source,'deployed_config_sha256':cfg,'process':process,'exact_log':str(log),'log_bytes':size,'log_age_seconds':time.time()-log.stat().st_mtime,'semantic_tail':semantic,'last_TRAIN_progress':[int(matches[-1][i]) for i in [1,2,3,4]] if matches else None,'explicit_early_stop_lines':[x for x in semantic if re.search(r'early.stop',x,re.I)],'explicit_exception_lines':[x for x in semantic if re.search(r'Traceback|RuntimeError|Error:',x)],'GPU1_queried':False,'signals_sent':False,'checkpoint_read':False,'read_only':True}))
'''
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 owner=guard();queue=json.loads((ROOT/'pipeline/queue.json').read_text('utf8'));task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M215-BEC')
 assert task['pid']==1558071 and task['code_commit']=='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563' and str(task['gpu'])=='0'
 m=json.loads((HERE.parent/'tick_94f8ddb8/bec_r1_execution/native_manifest.json').read_text('utf8'));model8={'framework/model/Quard_model/'+m['candidate_name']+'/'+n:h for n,h in m['candidate_source_hashes'].items()};assert len(model8)==8
 t={k:task[k] for k in ['pid','config','log','code_commit']};t['model8']=model8
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input='TASK='+repr(t)+'\n'+PROGRAM,capture_output=True,text=True,encoding='utf8',timeout=40);assert r.returncode==0,r.stderr[-2000:]
 observation=json.loads(r.stdout);guard()
 adapter_path=HERE.parent/'tick_05f6addd/aef_operational_prepare/adapter.py';spec=importlib.util.spec_from_file_location('existing_aef_probe',adapter_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 probe=module.Adapter().probe(0);guard()
 out={'owner_token':owner['token'],'recorded_at':datetime.now(timezone.utc).isoformat(),'observation':observation,'reviewed_AEF_readonly_probe':probe,'scope':'Exact original BEC process/log/source and permitted physical0 occupation/lock probe only; no lifecycle mutation or native computation.'}
 p=HERE/'bec_end_and_slot_observation.json'
 with p.open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({'path':str(p),'sha256':sha(p),'process':observation['process'],'last_TRAIN_progress':observation['last_TRAIN_progress'],'early_stop_lines':observation['explicit_early_stop_lines'],'exceptions':observation['explicit_exception_lines'],'slot':probe},ensure_ascii=False))
if __name__=='__main__':main()
