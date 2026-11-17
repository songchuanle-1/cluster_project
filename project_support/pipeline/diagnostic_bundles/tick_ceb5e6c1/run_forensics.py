"""Run captured-vector forensics on authorized serverCPU,not local training."""
import json,shlex
from ops import guard,save,run,OUT
guard();stage='/data/songcl/Project/Cluster_project/pipeline/fle_content_norm_capture_ceb5e6c1'
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(OUT/'norm_forensics.py'),'songcl@192.168.1.115:'+stage+'/'])
save('forensics_upload.json',dict(returncode=upload.returncode,stderr=upload.stderr));assert upload.returncode==0
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 python -B '+shlex.quote(stage+'/norm_forensics.py')
execution=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],90)
save('forensics_execution.json',dict(returncode=execution.returncode,stdout=execution.stdout,stderr=execution.stderr));assert execution.returncode==0,execution.stderr
value=json.loads(execution.stdout);save('norm_forensics_result.json',value)
print(json.dumps({'rows':value['rows'],'threshold_unchanged':value['native_threshold_unchanged']}))
