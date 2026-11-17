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
p.add_argument('--replicate',choices=['1','2'],required=True)
a=p.parse_args()
a.condition='original'
owner=guard(380)
assert all(tick.load(OUT/('flag_'+name)/'native_contract_result.json')['passed'] for name in ('m95','fle'))
RCID='native-train-prefix-repeatability-audit'
label='repeat_'+a.model+'_'+a.replicate
work=tick.load(ROOT/'pipeline/research_work.json')
if a.model=='m95' and a.replicate=='1':
    assert not any(c['id']==RCID for c in work['candidates'])
    c={'id':RCID,'stage':'diagnosis','hypothesis_id':'native_training_prefix_bitwise_repeatability',
       'hypothesis':'Same originalcheckpoint/batch/seed/native.train should replay prefix andtargetgradients bitwise;observed counterpart prefixdrift needs measurement.',
       'matched_control':'Two independent fresh ORIGINAL processes per existingmodel;no referencepatch,newseed,optimizer orVAL.',
       'gate_result':'NOT_RUN','failure_scope':'inconclusive',
       'next_action':'Execute frozen originalrepeat1/2forM95/FLE and compare rawprefix/RNG/gradients;no retryuntilmatching.',
       'evidence':[evidence(OUT/'repeat_prereg.md'),evidence(OUT/'analysis_summary.json')]}
    work['candidates'].append(c)
    old=next(c for c in work['candidates'] if c['id']==CID)
    old.update(stage='complete',failure_scope='inconclusive',
        gate_result='Finite uniformpadding correctness auditCOMPLETE:source/nativeinterfaces+4fullbackwards pass;initialfailures retained/explained;no efficacy/productionpatch/admission.',
        next_action='Do not automaticallytrain a singleopfix/restartFLE. Uniformrollout/scientificadmission remains separate;new nativeprefixrepeatability diagnostic uses separateID.')
    guard()
    tick.save(ROOT/'pipeline/research_work.json',work)
    goal=tick.load(ROOT/'pipeline/goal.json')
    review='# Motivation Review - Native Training Prefix Repeatability\n\n## 1. Goal\n```json\n'+json.dumps(goal,ensure_ascii=False,indent=2)+'\n```\nTarget.5100,historicalbest.5020,gap.0080.\n\n'
    review+='## 2. Story Status\nNativepaddingcontract passes but counterpartprefixes differ beforeintervention;measure repeatability before causalclaim.\n\n## 3. Experiment Assessment\nFourfrozenstepinputs identical,allnativebackwardspass,nooptimizer. Instantloss isnot efficacy.\n\n## 4. Gap Analysis\nPrefixdifference magnitude,RNGrelationship andtargetgradientnoise unknown.\n\n## 5. Design Rationale\nSameoriginalmodelrepeat is a discriminating control,not a newmechanism,tuningor repeatedtraining.\n\n## 6. Next Batch\nSee exp_design_20261018_4eca1157_repeat.md;alloriginalconstraints retained.\n'
    rp=ROOT/'pipeline/reviews/motivation_review_20261018_4eca1157_repeat.md'
    assert not rp.exists()
    rp.write_text(review,encoding='utf-8')
    design='# Experiment Design - Native Repeatability\n\n## 1. Motivation\n'+goal['description']+'\nAvoid attributingnativeprefixnoise to pointupdate mechanism.\n\n'
    design+='## 2. Current Best Results\nM95historical.5020,FLEcached.4885315597;no newtrainedresult.\n\n## 3. Analysis & Direction\nTwo originalprocesses percounterpart distinguish repeatability from referencechanges.\n\n## 4. Experiment Plan\nSame4originalnative.train/backward/clip,saveprefix/RNGstate,rawcomparison;nooptimizer.\n\n## 5. GPU Allocation Plan\nOnlyserver4physicalGPU0,oneprocess atatime,fresh3locks.\n\n## 6. Implementation Checklist\nSourceboundsharedsmoke,2repeats/model,rawdataanalysispending. No productionchanges/queue/VAL.\n\n## 7. Risk Assessment\nTwofreshprocesses do not estimate generaltrainingseednoise;do not loosen1e-6gates,claimarchitecturegain or chaseexactmatches.\n'
    dp=ROOT/'pipeline/designs/exp_design_20261018_4eca1157_repeat.md'
    assert not dp.exists()
    dp.write_text(design,encoding='utf-8')
    c=next(c for c in work['candidates'] if c['id']==RCID)
    add(c,[rp,dp])
    guard()
    tick.save(ROOT/'pipeline/research_work.json',work)
local=OUT/label
local.mkdir(exist_ok=False)
shutil.copyfile(OUT/'padding_contract.py',local/'padding_contract.py')
shutil.copyfile(OUT/'native_repeat.py',local/'native_full_backward.py')
shutil.copyfile(OLD/'native_qf/native_runtime.py',local/'native_runtime.py')
manifest=copy.deepcopy(tick.load(OUT/'models.json')[a.model])
stage=STAGE+'/'+label
manifest['stage']=stage
manifest['candidate_id']=RCID
manifest['repeat_preregistration']=evidence(OUT/'repeat_prereg.md')
manifest['diagnostic_files']={n:tick.digest(local/n) for n in ('native_runtime.py','padding_contract.py','native_full_backward.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
    'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
work=tick.load(ROOT/'pipeline/research_work.json')
c=next(c for c in work['candidates'] if c['id']==RCID)
c.update(stage='validation',gate_result='Both native originalflag interfacesPASS;all initialfailures retained. Fulltrain-modebackward smoke pending,not trainingadmission.',
    next_action='One frozen freshprocess '+label+' native.train loss/backward/originalclip,nooptimizerupdates;reportpartialfailures/memory,not efficacy.')
add(c,[OUT/'repeat_prereg.md',local/'native_manifest.json',local/'native_full_backward.py'])
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
save(label+'_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files=[str(local/n) for n in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')]
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*files,'songcl@192.168.1.115:'+stage+'/'])
save(label+'_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr})
assert upload.returncode==0
guard(340)
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
c=next(c for c in work['candidates'] if c['id']==RCID)
add(c,[local/'native_full_backward_result.json',OUT/(label+'_execution.json')])
c.update(gate_result=label+' '+('PASS' if r['passed'] else 'FAILED')+' singlefixedbatchnativebackward;nooptimizer or efficacy.',
    next_action='Compare both ORIGINAL repeats per model rawprefix/RNG/gradientdifferences;no repeatedtrialsuntilmatching,training orVAL.')
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({k:v for k,v in r.items() if k not in ('before','after','binding')},ensure_ascii=False))
