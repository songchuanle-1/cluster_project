"""Run only the original frozen M203best fullVALexport;no reference rerun."""
from datetime import datetime,timezone
import json,shlex
from ops import guard,save,run,OUT
import foreground_tick as tick
guard();stage='/data/songcl/Project/Cluster_project/pipeline/fle_fullval_ceb5e6c1'
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/paired_validation_isolated.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],1250)
save('fullval_execution.json',dict(returncode=response.returncode,stdout=response.stdout,stderr=response.stderr))
for name in ('candidate_fle_epoch13.json','paired_candidate_capture_index.json'):
    fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/'+name,str(OUT/'fullval'/name)])
    save('fullval_fetch_'+name,dict(returncode=fetch.returncode,stderr=fetch.stderr))
    if fetch.returncode:print(json.dumps({'fullval_failed':True,'returncode':response.returncode,'stderr_tail':response.stderr[-2500:]}));raise SystemExit(2)
result=tick.load(OUT/'fullval/candidate_fle_epoch13.json')
print(json.dumps({'returncode':response.returncode,'native_miou':result['native_float32_miou'],'expressions':len(result['records']),
    'scenes':result['unique_scenes'],'native_forwards':result['native_forwards'],'subgroups_known':sum(r.get('mixed_fine_leaf') is not None for r in result['records'])}))
