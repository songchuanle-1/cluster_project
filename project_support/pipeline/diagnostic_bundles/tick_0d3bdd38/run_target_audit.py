"""Register,freeze,prepare and execute only the declared terminal TRAIN audit."""
from datetime import datetime,timezone
import ast,copy,json,shlex
from ops import guard,save,run,ssh,add,evidence,ROOT,OUT,OLD,TOKEN,THREAD
import foreground_tick as tick

CID='fle-native-nonself-target-mixing-audit'
stage='/data/songcl/Project/Cluster_project/pipeline/fle_targetmix_0d3bdd38'
local=OUT/'attention_audit'
owner=guard(900)
names=('native_runtime.py','native_attention_audit.py','attention_readout.py','cpu_prepare.py')
for name in names:ast.parse((local/name).read_text(encoding='utf-8'),filename=name)
work=tick.load(ROOT/'pipeline/research_work.json');assert not any(c['id']==CID for c in work['candidates'])
work['candidates'].append({'id':CID,'stage':'diagnosis','kind':'trained_point_path_error_diagnosis',
    'hypothesis':'At unique terminal M203bestepoch13,learned fine nonself weights suppress cross-target mixing beyond uniform weights on identical original geometric support;diagnose an actual point-feature alignment gap,not causal task efficacy.',
    'matched_control':'Same native recipient/features/edge support/self exclusion,uniform versus actual attention weights;exact whole-leaf fallback,all-labels-equal null and complement controls;GT observed only after unmodified native forward.',
    'next_action':'Freeze32SHA-ranked TRAINscenes/first4expressiongroups before prediction;CPUcontracts then original native forward and source/output controls;scene-level uncertainty. No model/admission/training.',
    'failure_scope':'inconclusive','preregistered_at':datetime.now(timezone.utc).isoformat(),
    'evidence':[evidence(OUT/'target_mixing_prereg.md'),evidence(local/'attention_readout.py'),evidence(ROOT/'pipeline/reviews/motivation_review_20261018_0d3bdd38_targetmix.md'),evidence(ROOT/'pipeline/designs/exp_design_20261018_0d3bdd38_targetmix.md')]})
guard();tick.save(ROOT/'pipeline/research_work.json',work)
manifest=copy.deepcopy(tick.load(ROOT/'pipeline/diagnostic_bundles/tick_dbeca5d6/native_manifest.json'))
manifest.update(candidate_id=CID,stage=stage,cohort=[])
best=tick.load(OLD/'exit_result.json')['checkpoint_metadata']['best.pth'];assert best['meta']['epoch']==13
manifest['assets'].update(checkpoint=best['path'],checkpoint_sha256=best['sha256'],checkpoint_bytes=best['bytes'],checkpoint_mtime_ns=best['mtime_ns'],
    selection='Unique terminalbestepoch13 from original frozen plan;not selected using this TRAINdiagnostic')
manifest['diagnostic_files']={name:tick.digest(local/name) for name in names}
manifest['preregistration']=evidence(OUT/'target_mixing_prereg.md')
save('attention_audit/preparation_manifest.json',manifest)
save('target_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*[str(local/name) for name in names],str(local/'preparation_manifest.json'),'songcl@192.168.1.115:'+stage+'/'])
save('target_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr});assert upload.returncode==0
prefix='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
command=prefix+'CUDA_VISIBLE_DEVICES= python -B '+shlex.quote(stage+'/cpu_prepare.py')
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],240)
save('target_cpu_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/cpu_prepare_result.json',str(local/'cpu_prepare_result.json')])
save('target_cpu_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr});assert fetch.returncode==0 and response.returncode==0,response.stderr
prepared=tick.load(local/'cpu_prepare_result.json');assert prepared['passed'] and prepared['scenes']==32 and prepared['expressions']==128
manifest['cohort']=prepared['cohort'];manifest['preparation_result']=evidence(local/'cpu_prepare_result.json')
save('attention_audit/native_manifest.json',manifest)
owner=guard(900)
lease={'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],
       'native_manifest_sha256':tick.digest(local/'native_manifest.json'),'scope':'32sceneTRAINobservation only,unique terminalbest,physicalGPU0andthreeflocks,no training'}
save('attention_audit/execution_lease.json',lease)
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(local/'native_manifest.json'),str(local/'execution_lease.json'),'songcl@192.168.1.115:'+stage+'/'])
save('target_native_binding_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr});assert upload.returncode==0
work=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
c.update(stage='validation',next_action='Run frozen32scene terminal native observation with original returned outputs and liveGPU/lease guards;then analyze matched cross-target mixing without efficacy/admission claims.')
add(c,[local/'cpu_prepare_result.json',local/'native_manifest.json']);guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'CPU_readout_controls':'PASS','cohort_scenes':32,'cohort_expressions':128,'native_starting':True}),flush=True)
command=prefix+'python -B '+shlex.quote(stage+'/native_attention_audit.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3',
              'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(1250,int(remaining)-120))
save('target_native_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/native_attention_result.json',str(local/'native_attention_result.json')])
save('target_native_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr});assert fetch.returncode==0,response.stderr
r=tick.load(local/'native_attention_result.json')
print(json.dumps({k:r.get(k) for k in ['passed','native_forwards','unknown_label_expressions','primary_known_scenes','primary_known_expressions','primary_scene_mean','primary_scene_ci95','error_type','error']}))
