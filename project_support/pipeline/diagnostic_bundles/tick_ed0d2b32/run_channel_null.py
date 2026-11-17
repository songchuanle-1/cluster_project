"""Single frozen-prefix nativeinterface follow-up, without a training loop."""
import copy
from datetime import datetime,timezone
import shlex
import shutil
from ops import guard,save,run,ssh,advance,evidence,tick,OUT,OLD,MODELS,TOKEN,THREAD,STAGE,HOST,SSH
RID='hierarchical-nonlocal-channel-rank-audit'
owner=guard(380)
label='channel_null'
local=OUT/label
local.mkdir(exist_ok=False)
for src,dst in [(OLD/'trace_m95_1/native_runtime.py','native_runtime.py'),(OUT/'native_channel_null.py','native_channel_null.py')]:shutil.copyfile(src,local/dst)
manifest=copy.deepcopy(tick.load(MODELS)['m95'])
stage=STAGE+'/'+label
prefix=STAGE+'/rank_m95/rank_prefix.npz'
digest=ssh('from pathlib import Path\nimport hashlib,json\nprint(json.dumps({"sha256":hashlib.sha256(Path('+repr(prefix)+').read_bytes()).hexdigest()}))')
manifest.update(stage=stage,candidate_id=RID,channel_null_preregistration=evidence(OUT/'channel_null_prereg.md'),prefix_source={'path':prefix,'sha256':digest['sha256']})
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','native_channel_null.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'channel_null_prereg.md',local/'native_manifest.json',local/'native_channel_null.py'],candidate_id=RID,
    next_action='Single savedprefix nativeinterface null/row/owncoarse controls with fixed24readouts and original tolerances;linear surrogate not native taskloss.')
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
r=run(['scp',*SSH,*[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')],'songcl@'+HOST+':'+stage+'/'])
assert r.returncode==0,r.stderr
guard(340)
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_channel_null.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
r=run(['ssh',*SSH,'songcl@'+HOST,shlex.join(['bash','-lc',command])],min(600,int(remaining)-120))
save(label+'_execution.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
f=run(['scp',*SSH,'songcl@'+HOST+':'+stage+'/native_channel_null_result.json',str(local/'native_channel_null_result.json')])
assert f.returncode==0,r.stderr
v=tick.load(local/'native_channel_null_result.json')
advance([local/'native_channel_null_result.json',OUT/(label+'_execution.json')],candidate_id=RID,gate_result='Native channel-null follow-up '+('PASS;conditional informationconstraint only,not efficacy/admission.' if v['passed'] else 'FAILED actualcontrol retained;do not relax1e-6/1e-12.'))
print({k:v for k,v in v.items() if k not in ('before','after','records')})
