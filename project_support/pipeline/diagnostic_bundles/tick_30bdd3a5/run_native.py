"""Foreground single diagnostic dispatch and receipt; no nested codex or train."""
from gpu1_ops import *
import argparse
p=argparse.ArgumentParser();p.add_argument('label',choices=['scale','expression','scale_fix','expression_fix']);p.add_argument('--pair',type=int,choices=range(4),required=True);args=p.parse_args()
owner,cfg=guard(360)
folder=OUT/args.label;manifest=tick.load(folder/'native_manifest.json');stage=manifest['stage']
entry='native_scale_task.py' if args.label.startswith('scale') else 'native_expression_task.py'
result_name=('native_scale_task_pair_' if args.label.startswith('scale') else 'native_expression_task_pair_')+str(args.pair)+'.json'
receipt_name=args.label+'_pair_'+str(args.pair)
lease={'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(folder/'native_manifest.json'),'physical_gpu':1,'gpu_uuid':UUID,'authorization_sha256':tick.digest(AUTH)}
leasepath=folder/('execution_lease_'+str(args.pair)+'.json');tick.save(leasepath,lease)
remote('from pathlib import Path\nimport json\np=Path('+repr(stage)+');p.mkdir(parents=True,exist_ok=True)\nprint(json.dumps({"stage":str(p),"exists":True}))')
files=[folder/name for name in manifest['diagnostic_files']]+[folder/'native_manifest.json',leasepath]
copy=subprocess.run(['scp',*SSH,*[str(f) for f in files],cfg['user']+'@'+cfg['host']+':'+stage+'/'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
assert copy.returncode==0,copy.stderr[-3000:]
guard(300)
command=shlex.join(['bash','-lc','source '+shlex.quote(cfg['conda_source'])+' && conda activate '+shlex.quote(cfg['conda_env'])+' && cd '+shlex.quote(stage)+' && PYTHONDONTWRITEBYTECODE=1 python -B '+shlex.quote(entry)+' --lease '+shlex.quote(leasepath.name)+' --pair '+str(args.pair)])
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
run=subprocess.run(['ssh',*SSH,cfg['user']+'@'+cfg['host'],command],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=min(600,int(remaining)-100))
save(receipt_name+'_execution.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'returncode':run.returncode,'stdout_tail':run.stdout[-5000:],'stderr_tail':run.stderr[-14000:],'physical_gpu':1,'gpu_uuid':UUID,'manifest':evidence(folder/'native_manifest.json'),'authorization':evidence(AUTH),'entry_byte_identical_to_frozen_plan':not bool(manifest.get('measurement_revision')),'measurement_revision':manifest.get('measurement_revision'),'production_model_config_unchanged':True,'new_training':0})
try:
 result=remote('from pathlib import Path\nimport json\nprint((Path('+repr(stage)+')/'+repr(result_name)+').read_text())')
 save(receipt_name+'_result.json',result)
except Exception as error:
 save(receipt_name+'_missing_result.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'error':str(error),'execution_receipt':evidence(OUT/(receipt_name+'_execution.json'))});raise
cid=manifest['candidate_id']
advance(cid,[OUT/(receipt_name+'_execution.json'),OUT/(receipt_name+'_result.json'),Path(__file__)],gate_result='ActualGPU1nativepairedtaskattemptrecorded;checkexactcontrols/resultbeforeanyscientificinterpretation. NoautomaticPASSornewtraining.')
print(json.dumps({'label':args.label,'pair':args.pair,'returncode':run.returncode,'execution_completed':result.get('execution_completed'),'controls_passed':result.get('controls_passed'),'error_type':result.get('error_type'),'error':result.get('error'),'controls':result.get('controls'),'summary':result.get('summary'),'native_task_mask_replays':result.get('native_task_mask_replays'),'rows':len(result.get('records',[]))},ensure_ascii=True,indent=2))
