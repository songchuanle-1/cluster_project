"""One exact prespecified failure measurement, never retry-until-PASS."""
import copy
from datetime import datetime,timezone
import shlex
import shutil
from ops import guard,save,run,ssh,advance,evidence,tick,OUT,OLD,TOKEN,THREAD,STAGE,HOST,SSH
RID='hierarchical-nonlocal-channel-rank-audit'
owner=guard(380)
label='channel_failure'
local=OUT/label
local.mkdir(exist_ok=False)
for src,dst in [(OLD/'trace_m95_1/native_runtime.py','native_runtime.py'),(OUT/'native_channel_null.py','channel_template.py'),(OUT/'native_channel_failure.py','native_channel_failure.py')]:shutil.copyfile(src,local/dst)
manifest=copy.deepcopy(tick.load(OUT/'channel_null/native_manifest.json'))
stage=STAGE+'/'+label
manifest.update(stage=stage,failure_preregistration=evidence(OUT/'channel_failure_prereg.md'))
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','channel_template.py','native_channel_failure.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'channel_failure_prereg.md',local/'native_manifest.json',local/'native_channel_failure.py'],candidate_id=RID,
    next_action='Measure only fixed failingreadout0/last,keep exact1e-6 scientificgate and original failure;save float32cast/meanrounding residuals,no repeatedmatching.')
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
r=run(['scp',*SSH,*[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')],'songcl@'+HOST+':'+stage+'/'])
assert r.returncode==0,r.stderr
guard(340)
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_channel_failure.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
r=run(['ssh',*SSH,'songcl@'+HOST,shlex.join(['bash','-lc',command])],min(450,int(remaining)-120))
save(label+'_execution.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
f=run(['scp',*SSH,'songcl@'+HOST+':'+stage+'/native_channel_failure_result.json',str(local/'native_channel_failure_result.json')])
assert f.returncode==0,r.stderr
v=tick.load(local/'native_channel_failure_result.json')
advance([local/'native_channel_failure_result.json',OUT/(label+'_execution.json')],candidate_id=RID,
    failure_scope='inconclusive',gate_result='Original nullgate FAILED retained;one fixed-readout diagnostic recorded strict result '+str(v.get('strict_null_gate_passed','UNKNOWN'))+';not efficacy/admission or revision of originalfailure.')
print({k:v for k,v in v.items() if k not in ('before','after')})
