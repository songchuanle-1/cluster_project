"""Frozen native sparse capture and saved-input VJP controls."""
import argparse
import copy
from datetime import datetime,timezone
import shlex
import shutil
from ops import guard,save,run,ssh,advance,evidence,tick,OUT,OLD,TOKEN,THREAD,CID,STAGE,HOST,SSH

p=argparse.ArgumentParser()
p.add_argument('--model',choices=['m95','fle'],required=True)
p.add_argument('--replicate',choices=['1','2'],required=True)
a=p.parse_args()
owner=guard(380)
assert tick.load(OUT/(a.model+'_trace_comparison.json'))['first_difference']['label']=='unet.conv.2'
label='sparse_'+a.model+'_'+a.replicate
local=OUT/label
local.mkdir(exist_ok=False)
shutil.copyfile(OLD/'native_m95/native_runtime.py',local/'native_runtime.py')
shutil.copyfile(OUT/'native_sparse.py',local/'native_sparse.py')
manifest=copy.deepcopy(tick.load(OLD/'models.json')[a.model])
stage=STAGE+'/'+label
manifest.update(stage=stage,candidate_id=CID,sparse_preregistration=evidence(OUT/'sparse_control_prereg.md'))
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','native_sparse.py')}
if a.replicate=='2':
    prior=tick.load(OUT/('sparse_'+a.model+'_1')/'native_sparse_result.json')
    assert prior['passed']
    manifest['control_source']={'path':STAGE+'/sparse_'+a.model+'_1/control_bundle.npz','sha256':prior['control_bundle_sha256']}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
    'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'sparse_control_prereg.md',local/'native_manifest.json',local/'native_sparse.py'],stage='validation',
    next_action='Coordinate-align native sparse outputs;twoexact saved-input/operator-VJP controls per freshprocess;keep gates unchanged.')
save(label+'_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files=[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')]
uploaded=run(['scp',*SSH,*files,'songcl@'+HOST+':'+stage+'/'])
save(label+'_upload.json',{'returncode':uploaded.returncode,'stderr':uploaded.stderr})
assert uploaded.returncode==0
guard(340)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(stage+'/native_sparse.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh',*SSH,'-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','songcl@'+HOST,
    shlex.join(['bash','-lc',command])],min(1000,int(remaining)-120))
save(label+'_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,
    'finished_at':datetime.now(timezone.utc).isoformat()})
fetch=run(['scp',*SSH,'songcl@'+HOST+':'+stage+'/native_sparse_result.json',str(local/'native_sparse_result.json')])
save(label+'_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
assert fetch.returncode==0,response.stderr
r=tick.load(local/'native_sparse_result.json')
advance([local/'native_sparse_result.json',OUT/(label+'_execution.json')],
    gate_result=label+(' PASS operator measurement;not efficacy/admission.' if r['passed'] else ' FAILED;retain specific error/no invented cause.'))
print({k:v for k,v in r.items() if k not in ('before','after')})
