"""Native counterpart execution only after frozen CPU contract succeeds."""
import argparse
import copy
from datetime import datetime,timezone
import json
import shlex
import shutil
from ops import guard,save,run,ssh,add,evidence,ROOT,OUT,OLD,TOKEN,THREAD,CID,STAGE
import foreground_tick as tick

p=argparse.ArgumentParser()
p.add_argument('--model',choices=['m95','fle'],required=True)
a=p.parse_args()
owner=guard(700)
cpu=tick.load(OUT/'cpu_contract_result.json')
assert cpu['passed'] and not cpu['cuda_initialized']
local=OUT/('native_'+a.model)
local.mkdir(exist_ok=False)
for name in ('padding_contract.py','native_contract.py'):shutil.copyfile(OUT/name,local/name)
shutil.copyfile(OLD/'native_qf/native_runtime.py',local/'native_runtime.py')
manifest=copy.deepcopy(tick.load(OUT/'models.json')[a.model])
stage=STAGE+'/'+a.model
manifest['stage']=stage
manifest['contract_preregistration']=evidence(OUT/'contract_prereg.md')
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','padding_contract.py','native_contract.py')}
save('native_'+a.model+'/native_manifest.json',manifest)
save('native_'+a.model+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
    'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
work=tick.load(ROOT/'pipeline/research_work.json')
c=next(c for c in work['candidates'] if c['id']==CID)
c.update(stage='validation',gate_result='CPU bothsource/trainedweightscontractPASS;nativeinterface/gradient/resource tests pending,not admission.',
    next_action='Execute frozen '+a.model+' nativeinterface diagnosticreference1,originalcontrols1e-6,bs1warmup20repeat100;no productionfix/training/VAL.')
add(c,[OUT/'cpu_contract_result.json',OUT/'cpu_execution.json',local/'native_manifest.json',local/'native_contract.py'])
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
save(a.model+'_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files=[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')]
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*files,'songcl@192.168.1.115:'+stage+'/'])
save(a.model+'_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr})
assert upload.returncode==0
guard(600)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(stage+'/native_contract.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ServerAliveInterval=15',
    '-o','ServerAliveCountMax=3','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(1250,int(remaining)-120))
save(a.model+'_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,
    'finished_at':datetime.now(timezone.utc).isoformat()})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/native_contract_result.json',
    str(local/'native_contract_result.json')])
save(a.model+'_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
assert fetch.returncode==0,response.stderr
r=tick.load(local/'native_contract_result.json')
work=tick.load(ROOT/'pipeline/research_work.json')
c=next(c for c in work['candidates'] if c['id']==CID)
c.update(gate_result=a.model+' actualnativeinterface '+('PASS' if r['passed'] else 'FAILED')+';fullmodeltrainingbackward/efficacy not established.',
    next_action='Continue the OTHER frozen counterpart and actualfailure diagnosis;no productionpatch,training,VAL or admission.')
add(c,[local/'native_contract_result.json',OUT/(a.model+'_execution.json')])
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'model':a.model,'passed':r['passed'],'native_forwards':r['native_forwards'],
    'native_interface_backwards':r['native_interface_backwards'],'controls':r.get('controls'),
    'original_masked_gradient_max':r.get('original_masked_gradient_max'),
    'reference_valid_gradient_max':r.get('reference_valid_gradient_max'),
    'resources':{key:{k:v for k,v in value.items() if k!='samples_ms'} for key,value in r.get('resources',{}).items()},
    'mask_change':r.get('reference_mask_logits_max_change'),'error':r.get('error'),
    'stderr_tail':response.stderr[-1600:] if response.returncode else None}))
