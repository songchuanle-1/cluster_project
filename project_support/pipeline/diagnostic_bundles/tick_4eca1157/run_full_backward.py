"""One fresh process per counterpart/condition;no in-memoryBNcarryover."""
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
p.add_argument('--condition',choices=['original','reference'],required=True)
a=p.parse_args()
owner=guard(550)
assert all(tick.load(OUT/('flag_'+name)/'native_contract_result.json')['passed'] for name in ('m95','fle'))
label='backward_'+a.model+'_'+a.condition
local=OUT/label
local.mkdir(exist_ok=False)
for name in ('padding_contract.py','native_full_backward.py'):shutil.copyfile(OUT/name,local/name)
shutil.copyfile(OLD/'native_qf/native_runtime.py',local/'native_runtime.py')
manifest=copy.deepcopy(tick.load(OUT/'models.json')[a.model])
stage=STAGE+'/'+label
manifest['stage']=stage
manifest['full_backward_preregistration']=evidence(OUT/'full_backward_prereg.md')
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','padding_contract.py','native_full_backward.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
    'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
work=tick.load(ROOT/'pipeline/research_work.json')
c=next(c for c in work['candidates'] if c['id']==CID)
c.update(stage='validation',gate_result='Both native originalflag interfacesPASS;all initialfailures retained. Fulltrain-modebackward smoke pending,not trainingadmission.',
    next_action='One frozen freshprocess '+label+' native.train loss/backward/originalclip,nooptimizerupdates;reportpartialfailures/memory,not efficacy.')
add(c,[OUT/'flag_m95/native_contract_result.json',OUT/'flag_fle/native_contract_result.json',
       OUT/'full_backward_prereg.md',local/'native_manifest.json',local/'native_full_backward.py'])
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
save(label+'_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files=[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')]
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*files,'songcl@192.168.1.115:'+stage+'/'])
save(label+'_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr})
assert upload.returncode==0
guard(450)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
    'python -B '+shlex.quote(stage+'/native_full_backward.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')+' --condition '+a.condition)
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ServerAliveInterval=15',
    '-o','ServerAliveCountMax=3','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(1000,int(remaining)-120))
save(label+'_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr,
    'finished_at':datetime.now(timezone.utc).isoformat()})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+stage+'/native_full_backward_result.json',
    str(local/'native_full_backward_result.json')])
save(label+'_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
assert fetch.returncode==0,response.stderr
r=tick.load(local/'native_full_backward_result.json')
work=tick.load(ROOT/'pipeline/research_work.json')
c=next(c for c in work['candidates'] if c['id']==CID)
add(c,[local/'native_full_backward_result.json',OUT/(label+'_execution.json')])
c.update(gate_result=label+' '+('PASS' if r['passed'] else 'FAILED')+' singlefixedbatchnativebackward;nooptimizer or efficacy.',
    next_action='Reconcile all FOUR frozencondition results/scopes and fullstepmemory;retainfailures;no automaticrepairtraining orVAL.')
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({k:v for k,v in r.items() if k not in ('before','after','binding')},ensure_ascii=False))
