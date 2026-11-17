"""One original native rank-diagnosis capture under current guards."""
import copy
from datetime import datetime,timezone
import shlex
import shutil
from ops import guard,save,run,ssh,advance,evidence,tick,OUT,OLD,MODELS,TOKEN,THREAD,STAGE,HOST,SSH
RID='hierarchical-nonlocal-channel-rank-audit'
owner=guard(380)
label='rank_m95'
local=OUT/label
local.mkdir(exist_ok=False)
for src,dst in [(OLD/'trace_m95_1/native_runtime.py','native_runtime.py'),(OLD/'native_trace.py','trace_template.py'),
    (OUT/'rank_probe.py','rank_probe.py'),(OUT/'native_rank.py','native_rank.py')]:shutil.copyfile(src,local/dst)
manifest=copy.deepcopy(tick.load(MODELS)['m95'])
stage=STAGE+'/'+label
manifest.update(stage=stage,candidate_id=RID,rank_preregistration=evidence(OUT/'nonlocal_rank_prereg.md'))
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','trace_template.py','rank_probe.py','native_rank.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
    'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([local/'native_manifest.json',local/'rank_probe.py',local/'native_rank.py'],candidate_id=RID,stage='validation',
    next_action='Execute one fixed original native loss/backward and24tokenVJP controls;exactfullshape replay1e-6;then CPU conditionalrank/nativecotangent analysis.')
save(label+'_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
r=run(['scp',*SSH,*[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')],'songcl@'+HOST+':'+stage+'/'])
assert r.returncode==0,r.stderr
guard(340)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(stage+'/native_rank.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
r=run(['ssh',*SSH,'-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','songcl@'+HOST,
    shlex.join(['bash','-lc',command])],min(1000,int(remaining)-120))
save(label+'_execution.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
paths=[]
for filename in ('native_trace_result.json','native_rank_capture_result.json'):
    f=run(['scp',*SSH,'songcl@'+HOST+':'+stage+'/'+filename,str(local/filename)])
    save(label+'_'+filename+'_fetch.json',{'returncode':f.returncode,'stderr':f.stderr})
    if f.returncode==0:paths.append(local/filename)
assert local/'native_trace_result.json' in paths,r.stderr
result=tick.load(local/'native_trace_result.json')
advance([*paths,OUT/(label+'_execution.json')],candidate_id=RID,
    gate_result='Original native capture '+('PASS,CPUrank/projection pending;not methodadmission.' if result['passed'] else 'FAILED;exactfailure retained,do not loosen nativecontrol.'))
print({k:v for k,v in result.items() if k not in ('before','after')})
if (local/'native_rank_capture_result.json').is_file():
    capture=tick.load(local/'native_rank_capture_result.json')
    print({k:v for k,v in capture.items() if k!='native_token_vjp_controls'})
