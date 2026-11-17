"""Exactly two original native M95 provenance captures."""
import argparse
import copy
from datetime import datetime,timezone
import shlex
import shutil
from ops import guard,save,run,ssh,advance,evidence,tick,OUT,OLD,MODELS,TOKEN,THREAD,CID,STAGE,HOST,SSH
p=argparse.ArgumentParser()
p.add_argument('--replicate',choices=['1','2'],required=True)
a=p.parse_args()
owner=guard(380)
label='native_m95_'+a.replicate
local=OUT/label
local.mkdir(exist_ok=False)
for src,dst in [(OLD/'trace_m95_1/native_runtime.py','native_runtime.py'),(OLD/'native_trace.py','trace_template.py'),
    (OUT/'stride_probe.py','stride_probe.py'),(OUT/'native_stride.py','native_stride.py')]:shutil.copyfile(src,local/dst)
manifest=copy.deepcopy(tick.load(MODELS)['m95'])
stage=STAGE+'/'+label
manifest.update(stage=stage,candidate_id=CID,native_stride_preregistration=evidence(OUT/'native_stride_prereg.md'))
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','trace_template.py','stride_probe.py','native_stride.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
    'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'native_stride_prereg.md',local/'native_manifest.json',local/'stride_probe.py',local/'native_stride.py'],stage='validation',
    next_action='Execute only two preregistered actualnative M95calls;compare selecteddescriptor/coordinatecanonical indice tables and fixed-order float64reference;conclude finiteaudit without falseuniquecause.')
save(label+'_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files=[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')]
upload=run(['scp',*SSH,*files,'songcl@'+HOST+':'+stage+'/'])
save(label+'_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr})
assert upload.returncode==0,upload.stderr
guard(340)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(stage+'/native_stride.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh',*SSH,'-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','songcl@'+HOST,
    shlex.join(['bash','-lc',command])],min(1000,int(remaining)-120))
save(label+'_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
collected=[]
for filename in ('native_trace_result.json','native_stride_result.json'):
    fetch=run(['scp',*SSH,'songcl@'+HOST+':'+stage+'/'+filename,str(local/filename)])
    save(label+'_'+filename+'_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
    if fetch.returncode==0:collected.append(local/filename)
assert local/'native_trace_result.json' in collected,response.stderr
r=tick.load(local/'native_trace_result.json')
advance([*collected,OUT/(label+'_execution.json')],gate_result=label+(' nativebackward/capture PASS;not efficacy.' if r['passed'] else ' FAILED;preserve actual fault,no repeatedtrialsuntilmatching.'))
print({k:v for k,v in r.items() if k not in ('before','after')})
if (local/'native_stride_result.json').is_file():
    s=tick.load(local/'native_stride_result.json')
    print({k:v for k,v in s.items() if k!='raw_shapes'})
