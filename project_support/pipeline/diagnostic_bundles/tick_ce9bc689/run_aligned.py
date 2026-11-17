"""Two additional FLE first-block aligned captures, not architecture variants."""
import argparse
import copy
from datetime import datetime,timezone
import shlex
import shutil
from ops import guard,save,run,ssh,advance,evidence,tick,OUT,OLD,TOKEN,THREAD,CID,STAGE,HOST,SSH

p=argparse.ArgumentParser()
p.add_argument('--replicate',choices=['1','2'],required=True)
a=p.parse_args()
owner=guard(380)
label='aligned_fle_'+a.replicate
local=OUT/label
local.mkdir(exist_ok=False)
for src,dst in [(OLD/'native_m95/native_runtime.py','native_runtime.py'),
    (OUT/'native_trace.py','trace_template.py'),(OUT/'native_aligned.py','native_aligned.py')]:shutil.copyfile(src,local/dst)
manifest=copy.deepcopy(tick.load(OLD/'models.json')['fle'])
stage=STAGE+'/'+label
manifest.update(stage=stage,candidate_id=CID,aligned_preregistration=evidence(OUT/'aligned_block_prereg.md'))
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','trace_template.py','native_aligned.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
    'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'aligned_block_prereg.md',local/'native_manifest.json',local/'native_aligned.py'],stage='validation',
    next_action='Coordinate-align preregistered FLEfirstblock pair;identify actual firstfloatdifference or retain deeper-source unknown,not assume BNcause.')
save(label+'_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files=[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')]
uploaded=run(['scp',*SSH,*files,'songcl@'+HOST+':'+stage+'/'])
save(label+'_upload.json',{'returncode':uploaded.returncode,'stderr':uploaded.stderr})
assert uploaded.returncode==0
guard(340)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(stage+'/native_aligned.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh',*SSH,'-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','songcl@'+HOST,
    shlex.join(['bash','-lc',command])],min(1000,int(remaining)-120))
save(label+'_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,
    'finished_at':datetime.now(timezone.utc).isoformat()})
for filename in ('native_trace_result.json','trace_events.json'):
    fetch=run(['scp',*SSH,'songcl@'+HOST+':'+stage+'/'+filename,str(local/filename)])
    save(label+'_'+filename+'_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
    assert fetch.returncode==0,response.stderr
r=tick.load(local/'native_trace_result.json')
advance([local/'native_trace_result.json',OUT/(label+'_execution.json')],
    gate_result=label+(' PASS coordinate-awarecapture/backward;comparison pending.' if r['passed'] else ' FAILED preserved/no hypothesisrejection.'))
print({k:v for k,v in r.items() if k not in ('before','after')})
