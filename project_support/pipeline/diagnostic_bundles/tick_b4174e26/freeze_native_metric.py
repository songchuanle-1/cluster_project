"""Freeze exact original-data geometry and a future native audit runner."""
import json
import shlex
from ops import guard,save,evidence,OUT,STAGE,run

guard()
compile((OUT/'native_metric.py').read_text(),str(OUT/'native_metric.py'),'exec')
base=json.loads((OUT/'manifest.json').read_text())
data=json.loads((OUT/'train_geometry_cpu_result.json').read_text())
assert data['execution_passed'] and len(data['scenes'])==8 and data['cuda_initialized'] is False
manifest={k:base[k] for k in ('root','name','source_hashes','config_path','config_sha256','annotation_path','annotation_sha256','dataset_source_sha256')}
manifest.update(schema_version=1,candidate_id='fle-fixed-membership-metric-geometry-audit',
    runner_sha256=evidence(OUT/'native_metric.py')['sha256'],
    geometry=[{k:row[k] for k in ('scene','geometry_file','geometry_sha256','group_index','expressions','superpoints')} for row in data['scenes']],
    limitation='Synthetic feature probes;exact native GPUscatter/FPS/fine kernel only,no checkpoint loading,no trained mask/effect measurement',
    controls='Original fine memberships held fixed for all seven preregistered geometric transforms;1e-6 unchanged',
    execution='Fresh foreground owning lease required;live pinned idle authorized GPU0 and three lifetime locks before any Torch/CUDA')
assert not (OUT/'native_metric_manifest.json').exists()
save('native_metric_manifest.json',manifest)
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(OUT/'native_metric.py'),str(OUT/'native_metric_manifest.json'),'songcl@192.168.1.115:'+STAGE+'/'])
save('native_metric_upload.json',dict(returncode=upload.returncode,stdout=upload.stdout,stderr=upload.stderr));assert upload.returncode==0
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && CUDA_VISIBLE_DEVICES= python -B '+shlex.quote(STAGE+'/native_metric.py')+' --prepare-check'
execution=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])])
save('native_metric_prepare_execution.json',dict(returncode=execution.returncode,stdout=execution.stdout,stderr=execution.stderr))
fetched=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/native_metric_prepare_result.json',str(OUT/'native_metric_prepare_result.json')])
assert fetched.returncode==0,fetched.stderr
result=json.loads((OUT/'native_metric_prepare_result.json').read_text())
assert execution.returncode==0 and result['passed'] and result['torch_imported'] is False
print(json.dumps(result))
