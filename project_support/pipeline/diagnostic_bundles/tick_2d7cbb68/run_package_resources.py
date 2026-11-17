"""Sequential exclusive candidate/champion native and standard resource pair."""
import copy
from datetime import datetime,timezone
import shutil
from ops import *
owner=guard(900)
info=tick.load(OUT/'independent_package.json')
name=info['name']
protocol={'preregistered_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
 'tests':'Independent physical package full original native loss/backward on first4frozenTRAINscenes,batch2,workers0and4,seed1999;no optimizer or schedule step. Then unchanged native bs1VALresourcefixture,warmup20repeat100,FVCoreoriginalhandlers,bothcandidateandM95.',
 'readouts':'Every existing coarseFFN/norm tensor has finite nonzero native loss gradients;actual new attention weights carry finite nonzero loss gradients;CSORT remains active;strict parameter-state names and original requires_grad flags match.',
 'pairing':'Compare resources only with identical input hashes/parameter counts and standard handlers;native loss comparisons across processes are not exact task pairing.',
 'rules':'Default10G,relative15%memory policy unchanged;no optimizer-state peak or trained efficacy claim. Native+resources alone do not pass diagnosis or authorize training.',
 'production_changes':False,'new_training':False,'revision':'Same one-key-connection revision1;no new realization or tuning'}
save('package_resource_protocol.json',protocol)
label='independent_package'
local=OUT/label
local.mkdir(exist_ok=False)
package=Path(info['source_path'])
shutil.copytree(package,local/name)
shutil.copyfile(ROOT/info['candidate_config']['path'],local/(name+'.yaml'))
shutil.copyfile(OUT/'native_package_resources.py',local/'native_package_resources.py')
shutil.copyfile(ROOT/'pipeline/diagnostic_bundles/tick_ce9bc689/trace_m95_1/native_runtime.py',local/'native_runtime.py')
manifest=copy.deepcopy(tick.load(OUT/'native_coarse/native_manifest.json'))
stage=STAGE+'/'+label
manifest.update(stage=stage,candidate_name=name,resource_protocol=evidence(OUT/'package_resource_protocol.json'))
files=[p for p in local.rglob('*') if p.is_file()]
manifest['diagnostic_files']={p.relative_to(local).as_posix():tick.digest(p) for p in files}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'package_resource_protocol.json',local/'native_manifest.json',OUT/'native_package_resources.py',OUT/'run_package_resources.py'],
 next_action='Run independent candidate/champion full backward and unchanged-standard resources;keep diagnosis/efficacy/admission pending')
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
sc=run(['scp',*SSH,'-r',*[str(p) for p in local.iterdir()],'songcl@192.168.1.115:'+stage+'/'])
assert sc.returncode==0,sc.stderr
summaries=[]
for target in ('champion','candidate'):
    guard(600)
    command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_package_resources.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')+' --target '+target
    remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
    result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(1000,int(remaining)-180))
    save('package_'+target+'_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
    output='native_package_'+target+'_result.json'
    pull=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/'+output,str(local/output)])
    assert pull.returncode==0,pull.stderr
    value=tick.load(local/output)
    advance([local/output,OUT/('package_'+target+'_execution.json')],gate_result='Independent '+target+' full native/resource execution='+str(value.get('execution_completed'))+';diagnosis/efficacy/admission remain unpassed')
    summaries.append({k:value.get(k) for k in ('target','execution_completed','error_type','error','native_train_forwards','native_train_backwards','native_predict_calls','parameters','profile','median_ms','p90_ms','peak_allocated_bytes')})
    if not value.get('execution_completed'):break
print(json.dumps(summaries,ensure_ascii=False))
