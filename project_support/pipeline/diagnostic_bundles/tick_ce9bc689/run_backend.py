"""One preregistered M95 backend observation, no algorithm forcing."""
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
label='backend_m95_'+a.replicate
local=OUT/label
local.mkdir(exist_ok=False)
shutil.copyfile(OLD/'native_m95/native_runtime.py',local/'native_runtime.py')
shutil.copyfile(OUT/'native_backend.py',local/'native_backend.py')
manifest=copy.deepcopy(tick.load(OLD/'models.json')['m95'])
control=tick.load(OUT/'sparse_m95_1/native_sparse_result.json')
stage=STAGE+'/'+label
manifest.update(stage=stage,candidate_id=CID,backend_preregistration=evidence(OUT/'backend_observation_prereg.md'),
    control_source={'path':STAGE+'/sparse_m95_1/control_bundle.npz','sha256':control['control_bundle_sha256'],
        'weight_sha256':control['layer_weight_sha256'],**{k:control['native_input_metadata'][k] for k in ('spatial_shape','batch_size')}})
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','native_backend.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
    'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'backend_observation_prereg.md',local/'native_manifest.json',local/'native_backend.py'],stage='validation',
    next_action='Observe actual chosen M95SparseConv descriptors in two frozen processes without cache/backendchanges;retain unresolved cause,not admission.')
save(label+'_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
upload=run(['scp',*SSH,*[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')],'songcl@'+HOST+':'+stage+'/'])
assert upload.returncode==0,upload.stderr
guard(340)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(stage+'/native_backend.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh',*SSH,'songcl@'+HOST,shlex.join(['bash','-lc',command])],min(1000,int(remaining)-120))
save(label+'_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,
    'finished_at':datetime.now(timezone.utc).isoformat()})
fetch=run(['scp',*SSH,'songcl@'+HOST+':'+stage+'/native_backend_result.json',str(local/'native_backend_result.json')])
assert fetch.returncode==0,response.stderr
r=tick.load(local/'native_backend_result.json')
advance([local/'native_backend_result.json',OUT/(label+'_execution.json')],
    gate_result=label+(' read-only measurement PASS;kernel causality not established.' if r['passed'] else ' measurement FAILED retained;no gate relaxation.'))
print({k:v for k,v in r.items() if k not in ('before','after')})
