"""Synchronous CPU confirmation and original-data preparation receipts."""
import json
import shlex
from ops import guard,run,save,OUT,STAGE

guard()
files=['confirm_counterexample.py','train_geometry_cpu.py']
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*[str(OUT/f) for f in files],'songcl@192.168.1.115:'+STAGE+'/'])
save('confirmation_upload.json',dict(returncode=upload.returncode,stdout=upload.stdout,stderr=upload.stderr));assert upload.returncode==0
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && export CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 && python -B '+shlex.quote(STAGE+'/confirm_counterexample.py')+' && python -B '+shlex.quote(STAGE+'/train_geometry_cpu.py')
execution=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],420)
save('confirmation_execution.json',dict(returncode=execution.returncode,stdout=execution.stdout,stderr=execution.stderr,cuda_visible_devices=''))
print(execution.stdout)
if execution.returncode:print(execution.stderr)
for filename in ('counterexample_confirmation.json','train_geometry_cpu_result.json'):
    fetched=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/'+filename,str(OUT/filename)])
    save(filename+'.fetch.json',dict(returncode=fetched.returncode,stdout=fetched.stdout,stderr=fetched.stderr))
    assert fetched.returncode==0,fetched.stderr
result=json.loads((OUT/'train_geometry_cpu_result.json').read_text())
for scene in result['scenes']:
    filename=scene['geometry_file']
    fetched=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/'+filename,str(OUT/filename)])
    assert fetched.returncode==0,fetched.stderr
print(json.dumps({'execution_returncode':execution.returncode,'CPU_scenes':len(result['scenes']),'native_membership_tests':result['native_fine_membership']}))
