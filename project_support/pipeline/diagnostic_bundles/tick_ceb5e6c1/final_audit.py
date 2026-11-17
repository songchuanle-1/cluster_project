"""Independent CPU arithmetic audit and final authorized resource observation."""
from datetime import datetime, timezone
import json
import shlex
from ops import guard, save, ssh, run, OUT, ROOT
import foreground_tick as tick

guard()
stage='/data/songcl/Project/Cluster_project/pipeline/fle_fullval_ceb5e6c1'
program=r'''
import json,math,hashlib,socket
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
assert socket.gethostname()=='dl04-MS-7E06'
p=Path(STAGE)
ref=json.loads((p/'reference_m95_epoch16.json').read_text())
cur=json.loads((p/'candidate_fle_epoch13.json').read_text())
result=json.loads((p/'paired_analysis_result.json').read_text())
def key(r):return (r['split'],r['scene_id'],tuple(sorted(r['object_ids'])),r['ann_id'])
a={key(r):r for r in ref['records']};b={key(r):r for r in cur['records']}
assert len(a)==len(b)==9508 and a.keys()==b.keys()
groups={}
for name,predicate in [('all',lambda r:True),('mixed_fine_leaf',lambda r:r['mixed_fine_leaf'] is True),('no_mixed_fine_leaf',lambda r:r['mixed_fine_leaf'] is False)]:
    keys=[k for k in a if predicate(b[k])];scenes=sorted({k[1] for k in keys})
    per={s:[b[k]['piou']-a[k]['piou'] for k in keys if k[1]==s] for s in scenes}
    sums=[math.fsum(per[s]) for s in scenes];counts=[len(per[s]) for s in scenes]
    delta=math.fsum(b[k]['piou']-a[k]['piou'] for k in keys)/len(keys)
    macro=math.fsum(math.fsum(per[s])/len(per[s]) for s in scenes)/len(scenes)
    expected=result['groups'][name]
    assert abs(delta-expected['delta'])<1e-12 and abs(macro-expected['macro_scene_delta'])<1e-12
    draws=np.random.default_rng(1999).integers(0,len(scenes),size=(5000,len(scenes)))
    independent=np.array([math.fsum(sums[int(i)] for i in draw)/sum(counts[int(i)] for i in draw) for draw in draws])
    ci=np.quantile(independent,[.025,.975])
    assert max(abs(ci-np.array(expected['expression_delta_ci95'])))<1e-12
    groups[name]={'expressions':len(keys),'scenes':len(scenes),'delta_error':abs(delta-expected['delta']),
                  'macro_error':abs(macro-expected['macro_scene_delta']),'ci_error':float(max(abs(ci-np.array(expected['expression_delta_ci95']))))}
partitions={s:sorted({r['fine_partition_sha256'] for r in cur['records'] if r['scene_id']==s}) for s in sorted({r['scene_id'] for r in cur['records']})}
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'passed':True,'full_identity_independent_join':True,
    'groups':groups,'partition_hash_counts_by_scene':{s:len(v) for s,v in partitions.items()},
    'scope':'Independent aggregation/implementation audit,NOT independent native repeat or noise-floor estimate'}))
'''.replace('STAGE',repr(stage))
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
         'conda activate project_cluster && CUDA_VISIBLE_DEVICES= python -B -c '+shlex.quote(program))
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],90)
save('independent_analysis_execution.json',{'returncode':response.returncode,'stderr':response.stderr,'stdout':response.stdout})
assert response.returncode==0,response.stderr
save('independent_analysis_audit.json',json.loads(response.stdout))

probe=r'''
import json,socket,subprocess,fcntl
from datetime import datetime,timezone
assert socket.gethostname()==HOSTNAME
row=subprocess.check_output(['nvidia-smi','-i',GPU,'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert row.split(',')[1].strip()==UUID
contexts=subprocess.check_output(['nvidia-smi','-i',GPU,'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
locks={}
if GPU=='0':
    for kind in ['training','diagnostic','exclusive']:
        with open('/tmp/cluster_project_gpu0_'+kind+'.lock','rb') as h:
            try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='released_at_probe'
            except BlockingIOError:locks[kind]='busy_preserved'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':row,'contexts':contexts,'lifetime_locks':locks}))
'''
for label,host,hostname,gpu,uuid in [('server4','192.168.1.115','dl04-MS-7E06','0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),('server3','192.168.1.120','sysu311-MS-7C59','1','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0')]:
    code=probe.replace('HOSTNAME',repr(hostname)).replace('GPU',repr(gpu)).replace('UUID',repr(uuid))
    save(label+'_final_resources.json',ssh(code,host))
source=tick.load(ROOT/'pipeline/diagnostic_bundles/tick_b4174e26/manifest.json')
name='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1'
local={relative:tick.digest(ROOT/'Cluster/framework/model/Quard_model'/name/relative) for relative in source['source_hashes']}
assert local==source['source_hashes']
save('production_source_postcheck.json',{'unchanged':True,'source_hashes':local,'goal_sha256':tick.digest(ROOT/'pipeline/goal.json'),'local_scientific_execution':False})
print(json.dumps({'independent_statistics_audit':'PASS','unchanged_production_sources':len(local),'resources_saved':True}))
