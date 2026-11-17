"""Bounded remote CPU fixture using already verified source assets."""
import json
import shlex
from ops import guard, save, run, OUT

guard(240)
stage = '/data/songcl/Project/Cluster_project/pipeline/m95_padding_control_6a3484ad'
upload = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
              str(OUT/'padding_gradient_fixture.py'), 'songcl@192.168.1.115:'+stage+'/'])
save('gradient_upload.json', {'returncode': upload.returncode, 'stderr': upload.stderr})
assert upload.returncode == 0
command = ('test "$(hostname)" = dl04-MS-7E06 && source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
           'conda activate project_cluster && CUDA_VISIBLE_DEVICES= python -B '+shlex.quote(stage+'/padding_gradient_fixture.py')+
           ' --manifests '+shlex.quote(stage+'/native_manifest.json')+' '+
           shlex.quote('/data/songcl/Project/Cluster_project/pipeline/fle_shape_control_6a3484ad/native_manifest.json'))
response = run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', 'songcl@192.168.1.115',
                shlex.join(['bash', '-lc', command])], 90)
save('gradient_execution.json', {'returncode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr})
fetch = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
             'songcl@192.168.1.115:'+stage+'/padding_gradient_result.json', str(OUT/'padding_gradient_result.json')])
save('gradient_fetch.json', {'returncode': fetch.returncode, 'stderr': fetch.stderr})
assert fetch.returncode == 0, response.stderr
print(response.stdout)
