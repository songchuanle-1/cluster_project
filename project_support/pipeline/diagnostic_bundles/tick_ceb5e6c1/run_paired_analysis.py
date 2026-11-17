"""Send the frozen analysis to authorized server4 CPU after full VAL export."""
import json
import shlex
from ops import guard, run, save, OUT
import foreground_tick as tick

guard()
assert (OUT/'fullval/candidate_fle_epoch13.json').exists()
stage = '/data/songcl/Project/Cluster_project/pipeline/fle_fullval_ceb5e6c1'
upload = run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
              str(OUT/'fullval/paired_analysis.py'),'songcl@192.168.1.115:'+stage+'/'])
save('paired_analysis_upload.json', {'returncode': upload.returncode, 'stderr': upload.stderr})
assert upload.returncode == 0
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
           'conda activate project_cluster && CUDA_VISIBLE_DEVICES= python -B '+shlex.quote(stage+'/paired_analysis.py'))
response = run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',
                shlex.join(['bash','-lc',command])],75)
save('paired_analysis_execution.json', {'returncode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr})
assert response.returncode == 0, response.stderr
fetch = run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
             'songcl@192.168.1.115:'+stage+'/paired_analysis_result.json',str(OUT/'fullval/paired_analysis_result.json')])
save('paired_analysis_fetch.json', {'returncode': fetch.returncode, 'stderr': fetch.stderr})
assert fetch.returncode == 0
print(response.stdout)
