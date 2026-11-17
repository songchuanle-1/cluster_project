"""Freeze a replay manifest and synchronously validate all non-GPU assets."""
import json
import shlex
from ops import guard,save,run,evidence,OUT,ROOT,STAGE,NAME,REMOTE_ROOT

guard()
files=['native_runtime.py','native_diagnostic.py','neighbor_content.py']
for file in files+['cpu_prepare.py']:
    compile((OUT/file).read_text(),str(OUT/file),'exec')
assets=json.loads((OUT/'frozen_assets.json').read_text())
cohort=json.loads((OUT/'asset_metadata_result.json').read_text())['cohort']
manifest={'schema_version':1,'candidate_id':'fle-self-neighbor-content-separation','root':REMOTE_ROOT,'stage':STAGE,'name':NAME,
    'assets':assets,'cohort':cohort,'tolerance':1e-6,'seed':1999,'optimizer_steps':0,'new_training':False,
    'diagnostic_files':{name:evidence(OUT/name)['sha256'] for name in files},
    'execution':'Not authorized by this manifest alone;fresh owning foreground tick lease,live idle pinned GPU0 and all three lifetime locks required',
    'diagnostic_batch_size':1,'diagnostic_workers':0,'native_training_config':'unchanged batch2/workers4',
    'scientific_status':'pending_native_early_checkpoint_mechanism_test_not_efficacy_or_novelty',
    'self_preservation':'hold exact self term;within-leaf nonself reassignment matched per head norm;strict identity and suffix replay1e-6',
    'source_impact':'no changes to running package,configuration,checkpoint or optimizer'}
assert not (OUT/'native_manifest.json').exists()
save('native_manifest.json',manifest)
guard()
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*[str(OUT/n) for n in files+['cpu_prepare.py','native_manifest.json']],
    'songcl@192.168.1.115:'+STAGE+'/'],60)
save('native_upload.json',{'returncode':upload.returncode,'stdout':upload.stdout,'stderr':upload.stderr})
assert upload.returncode==0
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 python -B '+shlex.quote(STAGE+'/cpu_prepare.py')
guard()
execution=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],240)
save('native_cpu_preparation_execution.json',{'returncode':execution.returncode,'stdout':execution.stdout,'stderr':execution.stderr,'cuda_visible_devices':''})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/cpu_prepare_result.json',str(OUT/'cpu_prepare_result.json')],60)
save('native_cpu_preparation_fetch.json',{'returncode':fetch.returncode,'stdout':fetch.stdout,'stderr':fetch.stderr})
assert fetch.returncode==0
result=json.loads((OUT/'cpu_prepare_result.json').read_text())
print(json.dumps({'passed':result['passed'],'cpu_batches':len(result['batches']),'native_forwards':result['native_forwards'],
    'cuda_initialized':result.get('cuda_initialized'),'checkpoint_meta':result.get('checkpoint_meta'),'error':result.get('error'),'returncode':execution.returncode}))
