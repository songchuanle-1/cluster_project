"""Prediction-blind eight-scene TRAIN task replication,no validation selection."""
import copy
from datetime import datetime,timezone
import shutil
from ops import *
owner=guard(900)
reference=tick.load(OUT/'raw_key_revision1/native_manifest.json')
cohort=reference['cohort'][:8]
assert len(cohort)==8 and len({s['scene_id'] for s in cohort})==8
protocol={'preregistered_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
 'cohort':[{'scene_id':s['scene_id'],'group_index':s['group_index'],'expression_ids':s['expression_ids']} for s in cohort],
 'selection':'First8scenes of the previously frozen TRAIN manifest,not selected by current outputs;includes2earlier scenes for within-protocol replication plus6additional scenes',
 'conditions':'Unchanged revision1 worker:own identity,refinedkey reference,rawkey candidate,uniformmean,cyclicvalue mismatch;all pair within the SAME capture',
 'readout':'Actual full native criterion and matching equality;final positive-query IoU averaged per expression then per scene. Loss effects aggregate over2scenes/batch,not8independent losses.',
 'interpretation':'No tiny-sample effect threshold,VALselection or population efficacy claim. Preserve worse-than-original results;investigate semantic discrimination versus mean/mismatch. No automatic admission from path activity.',
 'counts':'4nativeforward/backward captures;8physicalscenes/32expressions,not28independentconditions. Existing2captures and242resourcepredictcalls are separate,not double-counted.',
 'new_training':False,'optimizer_steps':0}
save('eight_scene_protocol.json',protocol)
advance([OUT/'eight_scene_protocol.json'],next_action='Execute four frozen same-prefix task-control batches across8TRAINscenes;do not change keys/operators/thresholds from revision1')
summary=[]
for pair in range(4):
    owner=guard(600)
    label='eight_scene_'+str(pair)
    local=OUT/label
    local.mkdir(exist_ok=False)
    for n in ('native_runtime.py','native_raw_key.py','coarse_cross_attention_r1.py'):
        shutil.copyfile(OUT/'raw_key_revision1'/n,local/n)
    manifest=copy.deepcopy(reference)
    stage=STAGE+'/'+label
    manifest.update(stage=stage,cohort=cohort[2*pair:2*pair+2],replication_protocol=evidence(OUT/'eight_scene_protocol.json'))
    manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','native_raw_key.py','coarse_cross_attention_r1.py')}
    save(label+'/native_manifest.json',manifest)
    save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
    ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
    sc=run(['scp',*SSH,*[str(p) for p in local.iterdir()],'songcl@192.168.1.115:'+stage+'/'])
    assert sc.returncode==0,sc.stderr
    command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_raw_key.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
    remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
    result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(700,int(remaining)-180))
    save(label+'_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
    output='native_raw_key_result.json'
    pull=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/'+output,str(local/output)])
    assert pull.returncode==0,pull.stderr
    value=tick.load(local/output)
    advance([local/output,local/'native_manifest.json',OUT/(label+'_execution.json')],
        gate_result='Eight-scene task replication pair'+str(pair)+' executed='+str(value.get('execution_completed'))+';admission remains unpassed')
    summary.append({'pair':pair,'scene_ids':value.get('scene_ids'),'execution_completed':value.get('execution_completed'),'controls_passed':value.get('controls_passed'),'error':value.get('error'),'loss_deltas':{c['condition']:c['native_loss_delta'] for c in value.get('coarse_conditions',[])}})
    if not value.get('execution_completed'):break
save('eight_scene_execution_summary.json',summary)
print(json.dumps(summary,ensure_ascii=False))
