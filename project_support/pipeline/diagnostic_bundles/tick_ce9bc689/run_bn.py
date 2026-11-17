"""Single preregistered FLE original native cotangent + BN permutation probe."""
import copy
from datetime import datetime,timezone
import shlex
import shutil
from ops import guard,save,run,ssh,advance,evidence,tick,OUT,OLD,TOKEN,THREAD,CID,STAGE,HOST,SSH

owner=guard(380)
label='bn_fle'
local=OUT/label
local.mkdir(exist_ok=False)
for src,dst in [(OLD/'native_m95/native_runtime.py','native_runtime.py'),(OUT/'native_trace.py','trace_template.py'),
    (OUT/'native_bn.py','native_bn.py'),(OUT/'bn_probe.py','bn_probe.py')]:shutil.copyfile(src,local/dst)
manifest=copy.deepcopy(tick.load(OLD/'models.json')['fle'])
stage=STAGE+'/'+label
dependencies=ssh('''from pathlib import Path
import hashlib,json
root=Path('''+repr(STAGE)+''')
sources=[]
for i in (1,2):
    path=root/('aligned_fle_'+str(i))
    values={}
    for name in ('trace_events.json','trace_arrays.npz'):
        h=hashlib.sha256()
        with (path/name).open('rb') as f:
            for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
        values[name]=h.hexdigest()
    sources.append({'path':str(path),'hashes':values})
print(json.dumps(sources))''')
manifest.update(stage=stage,candidate_id=CID,comparison_sources=dependencies,
    bn_preregistration=evidence(OUT/'bn_permutation_prereg.md'))
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','trace_template.py','native_bn.py','bn_probe.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
    'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'bn_permutation_prereg.md',local/'native_manifest.json',local/'native_bn.py',local/'bn_probe.py'],stage='validation',
    next_action='Run one original FLE nativecotangent capture then A/A/B row-only BNcontrols;preserve original1e-6 and report exact identity/nulls.')
save(label+'_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files=[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')]
upload=run(['scp',*SSH,*files,'songcl@'+HOST+':'+stage+'/'])
assert upload.returncode==0,upload.stderr
guard(340)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(stage+'/native_bn.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh',*SSH,'-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','songcl@'+HOST,
    shlex.join(['bash','-lc',command])],min(1000,int(remaining)-120))
save(label+'_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,
    'finished_at':datetime.now(timezone.utc).isoformat()})
for filename in ('native_trace_result.json','bn_probe_result.json'):
    fetch=run(['scp',*SSH,'songcl@'+HOST+':'+stage+'/'+filename,str(local/filename)])
    save(label+'_'+filename+'_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
    assert fetch.returncode==0,response.stderr
r=tick.load(local/'native_trace_result.json')
probe=tick.load(local/'bn_probe_result.json')
advance([local/'native_trace_result.json',local/'bn_probe_result.json',OUT/(label+'_execution.json')],
    gate_result='FLEroworder causalcontrol '+('PASS;actual stats recorded,not efficacy.' if probe['passed'] else 'FAILED;keep actual discrepancy without tolerancechange.'))
print(probe)
print({'native_passed':r['passed'],'native_forwards':r['native_forwards'],'native_backwards':r['native_backwards']})
