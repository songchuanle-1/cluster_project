"""Read-only native validation/checkpoint audit under this foreground lease."""
import argparse, ast, hashlib, json, math, os, subprocess, sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='c19e28c6d7a342eaa625e8b1fd17bd75'
CID='m95-hierarchical-mask-feature-path-audit'
DIAG='m202-native-validation-checkpoint-evidence-audit'
EXP='M202-HDS'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1'
REL='pipeline/diagnostic_bundles/hds_evidence_c19e28c6'
BUNDLE=ROOT/REL
PLAN='pipeline/designs/exp_design_20261016_hier_support_admitted.md'
OPTIONS=['-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','-o','PasswordAuthentication=no']
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0,str(SKILL))
import foreground_tick as tick, pipeline_monitor as monitor, closure
def now():return datetime.now(timezone.utc).isoformat()
def guard():
    o=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert o['token']==TOKEN and o['thread_id']==os.environ['CODEX_THREAD_ID']
    assert o['deadline_at']=='2026-10-16T11:09:30.674701+00:00'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o['deadline_at'])
    return o
def save(p,value):
    guard();p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tick.save(p,value)
def ev(p):return {'path':p,'sha256':tick.digest(ROOT/p)}
def add(c,*paths):
    for p in paths:
        if ev(p) not in c.setdefault('evidence',[]):c['evidence'].append(ev(p))
def remote(program,timeout=90):
    r=subprocess.run(['ssh',*OPTIONS,'server-4','/home/songcl/.conda/envs/project_cluster/bin/python -B -'],input=program.encode('utf-8'),capture_output=True,timeout=timeout)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-2500:])
    return json.loads(r.stdout.decode('utf-8'))
def prepare():
    guard();assert tick.digest(ROOT/PLAN)=='e03b138638da520f1a873e81e2ee501a2f3b18bc5545c98aed9fc9c4127f1fca'
    assert tick.digest(ROOT/'pipeline/goal.json')=='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
    prereg={'recorded_at':now(),'hypothesis':'Native current-run validation and checkpoint artifacts preserve enough identity, best/patience, model/optimizer/scheduler state for the frozen evaluation and native end-of-epoch resume; absent fields are evidence gaps, not zeros or efficacy failures.','matched_control':'Frozen evaluation plan plus actual native saver/resume source; positive schema fixture versus one-required-field-deleted controls. Compare completed native metrics to stable checkpoint meta without rerunning prediction or changing training.','tests':['Strict host/GPU UUID/PID/flock and increasing native progress','Parse only this run native scalar validation records and current artifacts','Read only stable current-run checkpoint on CPU and inspect resume fields against actual provider','AST audit native persistence sinks for per-expression/scene-level evaluation readiness','Positive/negative schema fixtures detect missing state/scene identity'],'no_authorized_change':'No training restart/stop, code/config/environment/goal/scheduler modification, extra GPU allocation, model revision or effect-based selection. Checkpoint tensor arrays stay remote, no GPU deserialization.','plan':ev(PLAN),'scope':'Operational/scientific-evidence readiness diagnosis; not a new model or queue variant.'}
    save(BUNDLE/'prereg.json',prereg)
    work=tick.load(ROOT/'pipeline/research_work.json');assert not any(c['id']==DIAG for c in work['candidates'])
    work['candidates'].append({'id':DIAG,'stage':'diagnosis','research_role':'evaluation_and_resume_evidence_diagnostic','parent_candidate_id':CID,'linked_experiment_id':EXP,'hypothesis':prereg['hypothesis'],'matched_control':prereg['matched_control'],'next_action':'Execute bounded current-run checkpoint/schema/source audit and actual native continuity; no duplicate model/queue item.','evidence':[ev(REL+'/prereg.json')]})
    save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'prepared':True,'diagnostic':DIAG,'new_model':False}))
def observe():
    guard();q=monitor.load_queue(str(ROOT));t=next(t for t in q['gpu_queues']['server-4'] if t['id']==EXP)
    assert t['pid']==216566 and t['gpu']=='0'
    code=f"""
import os,json,pathlib,re,subprocess,time
from datetime import datetime,timezone
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
pid={t['pid']};p=pathlib.Path('/proc')/str(pid);log=pathlib.Path({t['log']!r})
text=log.read_text(errors='replace');assert log.stat().st_size<30*1024*1024
train=[list(map(int,r)) for r in re.findall(r'Train\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)]
val=[list(map(int,r)) for r in re.findall(r'Val\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)]
metrics=[float(x) for x in re.findall(r'mIoU\\s*:\\s*([0-9]+(?:\\.[0-9]+)?(?:e[-+]?\\d+)?)',text)]
base=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints')/{NAME!r}
runs=[r for r in base.glob('20261016_1734*') if r.is_dir()]
assert len(runs)==1,runs
run=runs[0]
native_logs=[]
for f in run.glob('*.log'):
    content=f.read_text(errors='replace')
    native_logs.append(dict(path=str(f),size=f.stat().st_size,miou=[float(x) for x in re.findall(r'mIoU\\s*:\\s*([0-9]+(?:\\.[0-9]+)?(?:e[-+]?\\d+)?)',content)],evaluate_counts=[int(x) for x in re.findall(r'Evaluate referring segmentation:\\s*(\\d+)',content)],save_lines=[line for line in content.splitlines() if 'save ' in line.lower()][-6:]))
contexts=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader,nounits'],text=True)
own=[row for row in contexts.splitlines() if int(row.split(',')[0])==pid]
locks=[]
if p.exists():
    for fd in (p/'fd').iterdir():
        try:target=os.readlink(fd)
        except OSError:continue
        if 'cluster_project_gpu0_' in target and target.endswith('.lock'):locks.append(target)
files=[dict(name=f.name,path=str(f),size=f.stat().st_size,mtime=f.stat().st_mtime) for f in run.iterdir() if f.is_file()]
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),pid=pid,alive=p.exists(),native_train_last=train[-8:],native_val_last=val[-8:],console_miou=metrics,native_logs=native_logs,checkpoint_run=str(run),files=files,own_contexts=own,locks=locks,crash_markers=[m for m in ('Traceback','CUDA out of memory','RuntimeError') if m in text],gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip())))
"""
    result=remote(code);assert 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in result['gpu']
    result['log']=t['log'];save(BUNDLE/'current_native_observation.json',result)
    print(json.dumps(result))
def checkpoint():
    guard();observation=tick.load(BUNDLE/'current_native_observation.json')
    run=observation['checkpoint_run'];candidates=[f for f in observation['files'] if f['name']=='last.pth']
    if not candidates:
        save(BUNDLE/'checkpoint_audit.json',{'observed_at':now(),'status':'not_yet_available','run':run,'evidence':ev(REL+'/current_native_observation.json'),'continuation_readiness':'unknown; no destructive intervention or fake complete state'});print('checkpoint_not_yet_available');return
    target=candidates[0]['path']
    code=f"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
import hashlib,inspect,json,pathlib,sys,time,torch,gorilla
from datetime import datetime,timezone
p=pathlib.Path({target!r});assert p.parent.resolve()==pathlib.Path({run!r}).resolve() and p.name=='last.pth'
before=p.stat();assert time.time()-before.st_mtime>15,'Checkpoint currently writing/recent; defer, never read partial data.'
state=torch.load(p,map_location='cpu',weights_only=False)
meta=state.get('meta',{{}})
serialized={{k:{{'type':type(v).__name__,'entries':len(v) if hasattr(v,'__len__') else None,'keys':list(v)[:20] if isinstance(v,dict) and k!='model' else None}} for k,v in state.items()}}
meta_scalars={{k:v for k,v in meta.items() if isinstance(v,(str,int,float,bool,type(None)))}}
optimizer=state.get('optimizer',{{}});scheduler=state.get('lr_scheduler',state.get('scheduler',{{}}))
model=state.get('model',state.get('state_dict',{{}}))
checks=dict(model_tensors=bool(model),optimizer_states=bool(optimizer.get('state')),optimizer_param_groups=bool(optimizer.get('param_groups')),scheduler_state=bool(scheduler),epoch=isinstance(meta.get('epoch'),int),best_miou=isinstance(meta.get('best_miou'),(int,float)),patience_state=isinstance(meta.get('epochs_no_improve'),int))
h=hashlib.sha256()
with p.open('rb') as f:
    for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
after=p.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Checkpoint changed while reading; discard interpretation.'
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),path=str(p),sha256=h.hexdigest(),bytes=after.st_size,checkpoint_mtime=after.st_mtime,meta=meta_scalars,top_keys=list(state),serialized_summary=serialized,checks=checks,cpu_only=not torch.cuda.is_initialized(),model_state_entries=len(model),optimizer_state_entries=len(optimizer.get('state',{{}})),scheduler_keys=list(scheduler) if isinstance(scheduler,dict) else None,saver_source=inspect.getsource(gorilla.save_checkpoint),resume_source=inspect.getsource(gorilla.resume),scope='Metadata/state presence audit only; no new native resume execution and no assertion of exact stochastic mid-epoch replay.')))
"""
    result=remote(code,timeout=180);assert result['cpu_only'];save(BUNDLE/'checkpoint_audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('saver_source','resume_source','serialized_summary')}))
def scalar_review():
    guard();original=tick.load(BUNDLE/'checkpoint_audit.json');target=original['path']
    code=f"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
import hashlib,json,math,numbers,pathlib,torch
from datetime import datetime,timezone
p=pathlib.Path({target!r});before=p.stat();assert before.st_size=={original['bytes']} and before.st_mtime=={original['checkpoint_mtime']!r}
state=torch.load(p,map_location='cpu',weights_only=False);meta=state['meta'];value=meta.get('best_miou')
review=dict(meta_key_present='best_miou' in meta,native_type=type(value).__module__+'.'+type(value).__name__,is_real=isinstance(value,numbers.Real),finite=bool(math.isfinite(float(value))) if isinstance(value,numbers.Real) else False,value=float(value) if isinstance(value,numbers.Real) else None,epoch=int(meta['epoch']),epochs_no_improve=int(meta['epochs_no_improve']))
after=p.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
train=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/tools/train.py')
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),review=review,cpu_only=not torch.cuda.is_initialized(),checkpoint_unchanged_from_hashed_initial_audit=True,train_source_sha256=hashlib.sha256(train.read_bytes()).hexdigest())))
"""
    result=remote(code,timeout=120);assert result['cpu_only']
    result['initial_inspection']=ev(REL+'/checkpoint_audit.json')
    result['explanation']='Initial metadata serializer accepted only built-in int/float and omitted native numpy.float32. Preserve initial false flag; assess the existing scalar against numbers.Real and finiteness, not a scientific threshold change.'
    save(BUNDLE/'checkpoint_scalar_type_review.json',result);print(json.dumps(result))
def audit():
    guard();ob=tick.load(BUNDLE/'current_native_observation.json');ck=tick.load(BUNDLE/'checkpoint_audit.json');scalar=tick.load(BUNDLE/'checkpoint_scalar_type_review.json')
    actual=scalar['review'];assert actual['meta_key_present'] and actual['is_real'] and actual['finite']
    assert scalar['train_source_sha256']==tick.digest(ROOT/'Cluster/tools/train.py')
    metrics=[v for log in ob['native_logs'] for v in log['miou']]
    assert len(metrics)==1 and abs(actual['value']-metrics[0])<=1e-12
    flags=dict(ck['checks']);flags['best_miou']=True
    assert all(flags.values())
    required=tuple(flags)
    def accepted(checks):return all(checks.get(k) is True for k in required)
    controls=[{'name':'all_native_state_fields','passed':accepted(flags)}]
    for key in required:
        missing=dict(flags);missing.pop(key)
        controls.append({'name':'remove_'+key,'passed':not accepted(missing)})
    import numbers
    def valid_best(v):return isinstance(v,numbers.Real) and math.isfinite(float(v)) and 0<=float(v)<=1
    controls.extend([{'name':'reject_nonfinite_best','passed':not valid_best(float('nan'))}, {'name':'reject_string_best','passed':not valid_best(str(actual['value']))}])
    assert all(c['passed'] for c in controls)
    source=(ROOT/'Cluster/tools/train.py').read_text(encoding='utf-8');tree=ast.parse(source)
    function=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='eval')
    calls=[ast.unparse(n.func) for n in ast.walk(function) if isinstance(n,ast.Call)]
    sinks=[name for name in calls if name in ('torch.save','json.dump','json.dumps','np.save','np.savez','open') or name.endswith(('.write_text','.write_bytes','.to_csv'))]
    returns=[ast.unparse(n.value) for n in ast.walk(function) if isinstance(n,ast.Return)]
    assert not sinks and returns==['miou']
    schema={'native_eval_return':returns,'active_file_export_sinks':sinks,'writer_scalar_calls':calls.count('writer.add_scalar'),'scene_ids_and_ious_accumulated_in_memory':all(name in ast.unparse(function) for name in ('scan_ids','pious')),'per_expression_scene_payload_exported':False,'current_run_files':[f['name'] for f in ob['files']],'checkpoint_top_keys':ck['top_keys'],'train_source_sha256':scalar['train_source_sha256'],'meaning':'Actual eval persists aggregates/TensorBoard scalars, not paired expression/scene arrays. This run alone cannot produce scene-clustered paired intervals; independent scene count, matched M95 predictions, subgroup harm and noise floor remain unmeasured/unknown. Not an efficacy failure.'}
    producer=ck['saver_source'];resume=ck['resume_source']
    assert all(name in producer for name in ('optimizer','scheduler','meta'))
    assert all(name in resume for name in ('optimizer','scheduler','meta'))
    result={'recorded_at':now(),'candidate_id':DIAG,'native_progress_confirmed':ob['alive'] and len(set(tuple(x) for x in ob['native_train_last']))>=2 and len(ob['locks'])==3 and not ob['crash_markers'],'checkpoint_state_fields_passed':flags,'native_best_miou':actual['value'],'native_validation_epoch':actual['epoch'],'native_validation_expression_count':ob['native_logs'][0]['evaluate_counts'],'checkpoint_native_type':actual['native_type'],'checkpoint_sha256':ck['sha256'],'checkpoint_optimizer_states':ck['optimizer_state_entries'],'saver_resume_source_reviewed':True,'actual_resume_executed':False,'schema_controls':controls,'scene_evidence_audit':schema,'limitations':'Only one early validation epoch. Resume-field presence is not an executed resume or exact stochastic replay. Current NVML is not a training peak. No tuning/new model/revision, no active training mutation.','evidence':[ev(REL+'/current_native_observation.json'),ev(REL+'/checkpoint_audit.json'),ev(REL+'/checkpoint_scalar_type_review.json'),ev(PLAN)]}
    assert result['native_progress_confirmed'];save(BUNDLE/'evidence_audit_result.json',result)
    w=tick.load(ROOT/'pipeline/research_work.json');d=next(c for c in w['candidates'] if c['id']==DIAG)
    d.update(stage='complete',failure_scope='inconclusive',result='Checkpoint native state fields present and native metric matches meta; aggregate-only evaluation artifacts cannot establish paired scene uncertainty or trained efficacy.',next_action='Retain audit; monitor frozen training and collect prediction-aligned scene evidence for the already-frozen trained comparison when available. No automatic resume, restart or new variant.')
    add(d,REL+'/evidence_audit_result.json',REL+'/checkpoint_audit.json',REL+'/checkpoint_scalar_type_review.json')
    c=next(c for c in w['candidates'] if c['id']==CID);assert c['stage']=='training'
    add(c,REL+'/evidence_audit_result.json',REL+'/current_native_observation.json')
    c['next_action']='Continue unchanged native training; primary first-epoch VAL mIoU .3337104619 is early evidence, not improvement. Match scene/annotation predictions to frozen reference before intervals/harm claims; no tuning, duplicate launch or automatic restart.'
    held=[c for c in w['candidates'] if c.get('stage')=='blocked' and c.get('blocker_kind')=='human_authorization'];assert len(held)==4
    scope={'recorded_at':now(),'held_ids':[c['id'] for c in held],'reason':'Four auxiliary scope holds remain as authorized. This tick completed first-validation/resume evidence diagnosis without another model admission. No claim of primary route exhaustion or physical GPU blockage.','new_model_variants':0,'new_implementation_revisions':0,'goal_hash_unchanged':tick.digest(ROOT/'pipeline/goal.json')=='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'}
    save(BUNDLE/'scope_disposition.json',scope)
    w['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID,DIAG],'evidence':[ev(REL+'/evidence_audit_result.json'),ev(REL+'/scope_disposition.json')],'resume_condition':'Ongoing primary native validation/checkpoint evidence; auxiliary held work requires explicit human scope authorization. Not GPU exhaustion or a claim all primary routes are exhausted.','scope':'Only remaining four human authorization holds; no unfinished diagnostic abandoned.'}
    save(ROOT/'pipeline/research_work.json',w)
    print(json.dumps({k:v for k,v in result.items() if k not in ('evidence','scene_evidence_audit','schema_controls')}))
    print(json.dumps({'controls_passed':len(controls),'per_scene_persistence':False,'actual_resume_executed':False}))
def closing():
    guard();original=tick.load(BUNDLE/'current_native_observation.json')
    code=f"""
import json,os,pathlib,re,subprocess
from datetime import datetime,timezone
p=pathlib.Path('/proc/216566');f=pathlib.Path({original['log']!r})
with f.open('rb') as s:
    s.seek(0,2);size=s.tell();s.seek(max(0,size-180000));text=s.read().decode(errors='replace')
steps=[list(map(int,row)) for row in re.findall(r'Train\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)]
contexts=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader,nounits'],text=True)
own=[r for r in contexts.splitlines() if int(r.split(',')[0])==216566]
locks=[]
if p.exists():
    for fd in (p/'fd').iterdir():
        try:target=os.readlink(fd)
        except OSError:continue
        if 'cluster_project_gpu0_' in target and target.endswith('.lock'):locks.append(target)
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),alive=p.exists(),pid=216566,steps_last=steps[-8:],own_contexts=own,locks=locks,crash_markers=[m for m in ('Traceback','CUDA out of memory','RuntimeError') if m in text],gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip())))
"""
    result=remote(code);result['confirmed']=result['alive'] and len(set(tuple(s) for s in result['steps_last']))>=2 and not result['crash_markers'] and len(result['locks'])==3 and len(result['own_contexts'])==1 and 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in result['own_contexts'][0]
    assert result['confirmed'];stamp=datetime.now(timezone.utc).strftime('%H%M%S');path=REL+'/continuity_'+stamp+'.json';save(ROOT/path,result)
    w=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in w['candidates'] if c['id']==CID);add(c,path);save(ROOT/'pipeline/research_work.json',w)
    print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','observe','checkpoint','scalar_review','audit','closing'));a=p.parse_args();globals()[a.action]()
