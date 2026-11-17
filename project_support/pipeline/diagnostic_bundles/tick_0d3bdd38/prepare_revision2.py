"""Freeze the diagnostic revision before executing it anywhere."""
from datetime import datetime,timezone
import ast,copy,json
from ops import guard,save,evidence,add,run,ssh,ROOT,OUT,OLD,STAGE,CID
import foreground_tick as tick

guard(900)
local=OUT/'norm_revision2'
for name in ('neighbor_content.py','native_runtime.py','native_diagnostic.py','cpu_contracts.py','interval_cpu_checks.py'):
    ast.parse((local/name).read_text(encoding='utf-8'),filename=name)
old=tick.load(ROOT/'pipeline/diagnostic_bundles/tick_dbeca5d6/native_manifest.json')
manifest=copy.deepcopy(old);manifest['stage']=STAGE
manifest['diagnostic_files']={name:tick.digest(local/name) for name in (*old['diagnostic_files'],'cpu_contracts.py','interval_cpu_checks.py')}
manifest['diagnostic_revision']={'revision':2,'scope':'diagnostic-only simultaneous native and true norm feasibility by scalar radius;original model,donor map,thresholds and cohort unchanged',
    'preregistration':evidence(OUT/'norm_interval_prereg.md')}
save('norm_revision2/native_manifest.json',manifest)
save('norm_revision2/cpu_manifest.json',{'operator_path':old['assets']['operator_path'],'operator_sha256':old['assets']['operator_sha256']})
work=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
assert len(c['diagnostic_revision_history'])==1 and c['diagnostic_revision_history'][0]['result']=='failed'
c['diagnostic_revision_history'].append({'revision':2,'failure_scope':'implementation','preregistered_at':datetime.now(timezone.utc).isoformat(),
    'reason':'Single true-norm rounding did not constrain the original float32 reduction;both must hold.',
    'change':'Monotone scalar-radius feasibility solver,fixed64bound,no donor-direction/self/source/model/threshold change.',
    'prediction':'Saved failure vectors and original CPU/native controls satisfy BOTH unchanged1e-6checks;otherwise FAIL.',
    'failure_evidence':[evidence(OLD/'precision_cpu_result.json'),evidence(OLD/'norm_repair/native_diagnostic_result.json')],
    'result':'pending','evidence':[evidence(OUT/'norm_interval_prereg.md'),evidence(local/'neighbor_content.py'),evidence(local/'native_manifest.json')]})
c['stage']='validation';c['next_action']='Execute both saved failure-vector controls and all original CPU contracts first;only if both PASS run original8TRAINscene native diagnostic with current exclusive lease. No third diagnostic arithmetic revision.'
add(c,[OUT/'norm_interval_prereg.md',local/'neighbor_content.py',local/'native_manifest.json'])
guard();tick.save(ROOT/'pipeline/research_work.json',work)
probe='from pathlib import Path\nimport json\nPath('+repr(STAGE)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'
save('revision2_stage.json',ssh(probe))
files=[str(local/name) for name in (*manifest['diagnostic_files'],'native_manifest.json','cpu_manifest.json')]
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*files,'songcl@192.168.1.115:'+STAGE+'/'])
save('revision2_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr});assert upload.returncode==0,upload.stderr
print(json.dumps({'diagnostic_revision':2,'registered_before_execution':True,'producer_files':len(manifest['diagnostic_files']),'new_models':0}))
