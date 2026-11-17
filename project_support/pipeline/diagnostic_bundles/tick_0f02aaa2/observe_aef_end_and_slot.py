"""Reconcile only the exact original AEF process/log/source and permitted GPU0."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,subprocess,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import pathlib,subprocess,os,re,json,hashlib,datetime,time
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1')
head=subprocess.check_output(['git','--no-optional-locks','-C',str(root),'rev-parse','HEAD'],text=True).strip()
assert head==TASK['code_commit']=='56b2a96dc48cc8a88f0f7105527ef448113b1060'
source={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in TASK['model8']};assert source==TASK['model8']
cfg=hashlib.sha256((root/TASK['config']).read_bytes()).hexdigest();assert cfg=='77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea'
p=pathlib.Path('/proc')/str(TASK['pid']);process={'pid':TASK['pid'],'exists':p.exists()}
if p.exists():
 try:
  stat=(p/'stat').read_text().rsplit(')',1)[1].split();args=[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x]
  process.update(state=stat[0],start_ticks=stat[19],argv=args,cwd=os.readlink(p/'cwd'))
 except OSError as e:process['read_error']=str(e)
log=pathlib.Path(TASK['log']);size=log.stat().st_size
with log.open('rb') as f:f.seek(max(0,size-1200000));tail=f.read().decode('utf8',errors='replace')
lines=tail.replace('\r','\n').splitlines()
semantic=[x[-1600:] for x in lines if re.search(r'early.stop|best|valid|miou|mIoU|Traceback|RuntimeError|Error:|finish|complete|patience',x,re.I)][-50:]
matches=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',tail))
metric_lines=[]
for name in TASK['native_logger_paths']:
 assert name.startswith('/data/songcl/Project/Cluster_project/Cluster_checkpoints/'+pathlib.Path(TASK['config']).stem+'/') and name.endswith('.log')
 with open(name,errors='replace') as f:
  for line in f:
   if 'mIoU :' in line or 'resume start_epoch:' in line:metric_lines.append(line.strip())
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'runtime_HEAD':head,'source_model8':source,'deployed_config_sha256':cfg,'process':process,'exact_log':str(log),'log_bytes':size,'log_age_seconds':time.time()-log.stat().st_mtime,'semantic_tail':semantic,'last_TRAIN_progress':[int(matches[-1][i]) for i in [1,2,3,4]] if matches else None,'explicit_early_stop_lines':[x for x in semantic if re.search(r'early.stop',x,re.I)],'explicit_exception_lines':[x for x in semantic if re.search(r'Traceback|RuntimeError|Error:',x)],'native_logger_paths':TASK['native_logger_paths'],'metric_lines':metric_lines,'GPU1_queried':False,'signals_sent':False,'checkpoint_body_read':False,'read_only':True}))
'''
def main():
    guard();q=json.loads((ROOT/'pipeline/queue.json').read_text('utf8'));task=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M216-AEF')
    assert task['pid']==759301 and task['code_commit']=='56b2a96dc48cc8a88f0f7105527ef448113b1060' and str(task['gpu'])=='0'
    original=json.loads((ROOT/'pipeline/diagnostic_bundles/tick_458bf62f/aef_root_ff_result.json').read_text('utf8'))
    model8={n:h for n,h in original['source_paths'].items() if n.endswith('.py')};assert len(model8)==8
    old=json.loads((ROOT/'pipeline/diagnostic_bundles/tick_c7a49040/aef_training_progress_observation.json').read_text('utf8'))
    t={k:task[k] for k in ['pid','config','log','code_commit']};t['model8']=model8;t['native_logger_paths']=old['observation']['native_logger_paths'];assert len(t['native_logger_paths'])==1
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input='TASK='+repr(t)+'\n'+PROGRAM,capture_output=True,text=True,encoding='utf8',timeout=40)
    assert r.returncode==0,r.stderr[-2000:]
    observation=json.loads(r.stdout);guard()
    op=ROOT/'pipeline/diagnostic_bundles/tick_d08825b5/cre_compatible_tooling/adapter.py'
    spec=importlib.util.spec_from_file_location('existing_cre_readonly_probe',op);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    probe=m.Adapter().probe(0);guard()
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    values,best,missed=mon.parse_native_lineage('\n'.join(observation['metric_lines']),resumed=False)
    out={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'observation':observation,'reviewed_CRE_readonly_probe':probe,'precise_native_validation':{'values':values,'best':best,'no_improve':missed},'failed_initial_live_observer':{'path':(HERE/'aef_training_progress_observation.json').relative_to(ROOT).as_posix(),'sha256':sha(HERE/'aef_training_progress_observation.json')},'scope':'Reconcile exact original AEF end and physical0 only; no signal, lifecycle mutation or GPU computation.'}
    with (HERE/'aef_end_and_slot_observation.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'sha256':sha(HERE/'aef_end_and_slot_observation.json'),'process':observation['process'],'last_TRAIN_progress':observation['last_TRAIN_progress'],'early_stop_lines':observation['explicit_early_stop_lines'],'exceptions':observation['explicit_exception_lines'],'precise_native_validation':out['precise_native_validation'],'slot':probe},ensure_ascii=False))
if __name__=='__main__':main()
