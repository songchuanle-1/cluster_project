"""Hash-bind independent diagnostic instrumentation,without editing frozen originals."""
from datetime import datetime,timezone
import copy,json
from ops import guard,save,run,ssh,evidence,ROOT,OUT,TOKEN
import foreground_tick as tick
guard();stage='/data/songcl/Project/Cluster_project/pipeline/fle_content_norm_capture_ceb5e6c1'
original=tick.load(ROOT/'pipeline/diagnostic_bundles/tick_dbeca5d6/native_manifest.json')
manifest=copy.deepcopy(original);manifest['stage']=stage
manifest['diagnostic_files']={name:tick.digest(OUT/'norm_capture'/name) for name in original['diagnostic_files']}
assert manifest['diagnostic_files']['neighbor_content.py']==original['diagnostic_files']['neighbor_content.py']
assert manifest['diagnostic_files']['native_runtime.py']==original['diagnostic_files']['native_runtime.py']
assert manifest['assets']==original['assets'] and manifest['cohort']==original['cohort'] and manifest['tolerance']==original['tolerance']==1e-6
manifest['instrumentation']={'revision':1,'scope':'Record norm failure before original strict assertion only','source_or_model_changed':False,
    'preregistration':evidence(OUT/'norm_capture_prereg.md')}
save('norm_capture/native_manifest.json',manifest)
probe='''import json,socket
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
Path(%r).mkdir(parents=True,exist_ok=False)
print(json.dumps({'stage':%r,'created':True,'torch_imported':False}))
'''%(stage,stage)
save('capture_stage_created.json',ssh(probe))
files=[str(OUT/'norm_capture'/name) for name in [*manifest['diagnostic_files'],'native_manifest.json']]
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*files,'songcl@192.168.1.115:'+stage+'/'])
save('capture_stage_upload.json',dict(returncode=upload.returncode,stdout=upload.stdout,stderr=upload.stderr));assert upload.returncode==0
work=tick.load(ROOT/'pipeline/research_work.json');candidate=next(c for c in work['candidates'] if c['id']=='fle-self-neighbor-content-separation')
candidate.update(stage='validation',failure_scope='implementation',next_action='Execute preregistered norm-failure capture using unchanged1e-6 and originalassets/cohort;distinguish scaling from norm-measurement error before any correction. No modelsource or protocol relaxation.')
candidate['evidence'] += [evidence(OUT/'native_diagnostic_result.json'),evidence(OUT/'norm_capture_prereg.md'),evidence(OUT/'norm_capture/native_manifest.json')]
candidate.setdefault('diagnostic_instrumentation_history',[]).append({'revision':1,'preregistered_at':datetime.now(timezone.utc).isoformat(),
    'change':'Failure-input/metadata capture only;originalscaling/assertion/modelunchanged','result':'pending',
    'failure_evidence':[evidence(OUT/'native_diagnostic_result.json')],'evidence':[evidence(OUT/'norm_capture_prereg.md')]})
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'prepared_capture':True,'model_revision':False,'tolerance':1e-6}))
