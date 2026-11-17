"""Follow up terminal observational alignment using the same validated control."""
from datetime import datetime,timezone
import copy,json,shlex
from ops import guard,save,run,ssh,add,evidence,ROOT,OUT,TOKEN,THREAD
import foreground_tick as tick

CID='fle-native-nonself-target-mixing-audit'
owner=guard(900)
observed=tick.load(OUT/'attention_audit/native_attention_result.json')
assert observed['passed'] and observed['native_forwards']==32
save('target_observation_disposition.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'native_forwards':32,'expressions':128,'primary_known_expressions':observed['primary_known_expressions'],
    'delta':observed['primary_scene_mean'],'scene_ci95':observed['primary_scene_ci95'],'interpretation':'Target-aligned relative to uniform on this TRAINcohort;not causal mask benefit. 9expressions have no eligible target nonself support,not missing binary labels.',
    'evidence':[evidence(OUT/'attention_audit/native_attention_result.json')]})
local=OUT/'terminal_content';stage='/data/songcl/Project/Cluster_project/pipeline/fle_terminal_content_0d3bdd38'
manifest=copy.deepcopy(tick.load(OUT/'attention_audit/native_manifest.json'));manifest['stage']=stage
manifest['diagnostic_files']={name:tick.digest(local/name) for name in ('native_runtime.py','native_diagnostic.py','neighbor_content.py')}
manifest['terminal_content_preregistration']=evidence(OUT/'terminal_content_prereg.md')
save('terminal_content/native_manifest.json',manifest)
lease={'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')}
save('terminal_content/execution_lease.json',lease)
work=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
c.update(stage='validation',gate_result='Observational32TRAINscene delta-.0105940,CI[-.0160851,-.0065348];weights target-aligned relative uniform but causal mask effect unknown.',
    next_action='Execute SAME32scene/unique terminalbest same-prefix causal content control using unchanged tested diagnosticrevision2;stop on original controls,no training or arithmeticrevision3.')
add(c,[OUT/'attention_audit/native_attention_result.json',OUT/'target_observation_disposition.json',OUT/'terminal_content_prereg.md',local/'native_manifest.json'])
guard();tick.save(ROOT/'pipeline/research_work.json',work)
save('terminal_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files=[str(local/name) for name in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')]
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*files,'songcl@192.168.1.115:'+stage+'/'])
save('terminal_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr});assert upload.returncode==0
guard(600)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
         'python -B '+shlex.quote(stage+'/native_diagnostic.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3',
              'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(1250,int(remaining)-120))
save('terminal_native_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/native_diagnostic_result.json',str(local/'native_diagnostic_result.json')])
save('terminal_native_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr});assert fetch.returncode==0,response.stderr
r=tick.load(local/'native_diagnostic_result.json')
if any('failure_capture' in row for row in r.get('control_attempts',[])):
    fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/failed_norm_input.npz',str(local/'failed_norm_input.npz')])
    save('terminal_failure_input_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
print(json.dumps({'passed':r['passed'],'native_forwards':r['native_forwards'],'suffix_replays':r['suffix_replays'],'scenes':len(r['scenes']),
    'delta':r.get('scene_mean_normal_minus_intervention_piou'),'ci95':r.get('scene_bootstrap_95ci'),'error_type':r.get('error_type'),'error':r.get('error'),
    'stderr_tail':response.stderr[-1200:] if response.returncode else None}))
