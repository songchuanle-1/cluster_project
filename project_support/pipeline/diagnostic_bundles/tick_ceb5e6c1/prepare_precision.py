"""Bind a single diagnostic arithmetic repair;all production assets unchanged."""
from datetime import datetime,timezone
import copy,json
from ops import guard,save,run,ssh,evidence,ROOT,OUT
import foreground_tick as tick
guard();stage='/data/songcl/Project/Cluster_project/pipeline/fle_content_norm_precision_ceb5e6c1'
manifest=copy.deepcopy(tick.load(ROOT/'pipeline/diagnostic_bundles/tick_dbeca5d6/native_manifest.json'))
manifest['stage']=stage
manifest['diagnostic_files']={name:tick.digest(OUT/'norm_repair'/name) for name in manifest['diagnostic_files']}
manifest['diagnostic_revision']={'revision':1,'scope':'float64donornormalizationthenonecast;original1e-6normandnativecontrolsretained;addedtrue-normcheck',
    'preregistration':evidence(OUT/'norm_precision_prereg.md')}
save('norm_repair/native_manifest.json',manifest)
probe='''import json,socket
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
Path(%r).mkdir(parents=True,exist_ok=False)
print(json.dumps({'created':True}))
'''%stage
save('precision_stage_created.json',ssh(probe))
files=[str(OUT/'norm_repair'/name) for name in [*manifest['diagnostic_files'],'native_manifest.json']]
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*files,'songcl@192.168.1.115:'+stage+'/'])
save('precision_upload.json',dict(returncode=upload.returncode,stderr=upload.stderr));assert upload.returncode==0
work=tick.load(ROOT/'pipeline/research_work.json');candidate=next(c for c in work['candidates'] if c['id']=='fle-self-neighbor-content-separation')
candidate.setdefault('diagnostic_revision_history',[]).append({'revision':1,'failure_scope':'implementation','preregistered_at':datetime.now(timezone.utc).isoformat(),
    'reason':'Capturedactualnormdrift>1e-6,notsolelymeasurement','change':'Single-roundhigher-precisiondiagnosticnormscalingonly;unchangedmodelandthresholds',
    'prediction':'Originalnative1e-6normcontrolandaddedtrue-normcontrolbothpassbeforetaskinterpretation','result':'pending',
    'failure_evidence':[evidence(OUT/'norm_forensics_result.json')],'evidence':[evidence(OUT/'norm_precision_prereg.md')]})
candidate['next_action']='Run preregistered precision-repair controls and original8scene nativecohort;do not widen1e-6or change modelprecision. Preserveoldfailures.'
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'diagnostic_precision_revision':1,'model_revision':False,'tolerance':1e-6}))
