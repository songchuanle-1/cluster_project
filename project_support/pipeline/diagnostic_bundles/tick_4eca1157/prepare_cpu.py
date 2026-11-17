"""Create upstream review/design, freeze current diagnostics,run remoteCPU."""
from datetime import datetime, timezone
import copy
import json
import shlex
from ops import guard, save, run, ssh, add, evidence, ROOT, OUT, OLD, CID, STAGE
import foreground_tick as tick

guard(1000)
goal = tick.load(ROOT/'pipeline/goal.json')
review = '# Motivation Review - cluster_project\n\n## 1. Goal\n```json\n'+json.dumps(goal,ensure_ascii=False,indent=2)+'\n```\nHistoricalbest.5020,target.5100,gap.0080.\n\n'
review += '## 2. Story Status\n|Hypothesis|Status|Evidence|Gap|\n|---|---|---|---|\n|Maskedpadding affectsvalidhierarchy output|Confirmed for FLE/M95|Prior nativebatch2,same-shape nulls0|Uniformcontract untested|\n|Pointpath matters for mask|Observed in one32TRAINreplicate|PriorQF|Initialnormfailure,efficacyCIcross0|\n\n'
review += '## 3. Experiment Assessment\n|Experiment|mIoU|Relation|Contribution|\n|---|---|---|---|\n|M203-FLE,cached|.4885315597|Negative trainedscreen|Branchstopped|\n|AvailableM95epoch16,cached|.5024607182|Matchedexistingweights,notchampionverification|Both shareglobalmeanbug|\n\n'
review += '## 4. Gap Analysis\nNeed finite/no-padding/allmasked/gradient correctness andactualnative interface/resource tests for BOTH models. Fulltrainingbackward,wholetrainingmemory,efficacy,generalization,noveltyUNKNOWN.\n\n'
review += '## 5. Design Rationale\nFollow the same stablepaddingID. ExactsourceAST reference changes only globalmean;uniform safetycontract,no optimization sweep,no productionpatch,no newarchitecture claim. All failed evidence/bans retained. No originalpaper review performed because this is a nonnovel correctnessdiagnostic.\n\n'
review += '## 6. Next Batch\nSee exp_design_20261018_4eca1157.md and contract_prereg.md,created beforetests. No trainingadmission.\n'
rp = ROOT/'pipeline/reviews/motivation_review_20261018_4eca1157.md'
assert not rp.exists()
rp.write_text(review,encoding='utf-8')
design = '# Experiment Design - cluster_project\n\n## 1. Motivation\n'+goal['description']+'\nSameID correctnesscontinuation;notamodelvariant.\n\n'
design += '## 2. Current Best Results\n|ID|Config|State|BestmIoU|Acc50|spmIoU|Epochs|\n|---|---|---|---|---|---|---|\n|HistoricalM95|Cached|Historicalbest|.5020|Unknown|Unknown|Unknown|\n|M203FLE|Unchanged|Cachedearlystop|.4885315597|Unknown|Unknown|23/50|\n\n'
design += '## 3. Analysis & Direction\nSharedinvalidpaddingcontext can change pointfeaturefusion and masks. Correctnessrepair is NOT newhierarchicalattention or evidence of trainedgain. Keep historicalmetricmeaning unchanged.\n\n'
design += '## 4. Experiment Plan\n|ID|Config/Protocol|Purpose|Expected criterion|Priority|\n|---|---|---|---|---|\n|'+CID+'|contract_prereg.md|CPU source/trainedweightdegeneracy andgradients,then nativeinterfacebackward/resources|Frozen1e-12CPU/1e-6native/nooptimizer|P0|\n\n'
design += '## 5. GPU Allocation Plan\n|Server|PhysicalGPU|Assignment|\n|---|---|---|\n|server4|0|AfterCPUcontrols,onlyfreshidle/3locks|\n|server3|1|Authorizedfallback only afterverifiedassets|\nNo otherGPU/project/scheduler.\n\n'
design += '## 6. Implementation Checklist\n- [x] Frozenmatchedprotocol andexistingweights.\n- [ ] CPUcontracttests.\n- [ ] Nativeinterface/gradient/resource tests.\n- [ ] Fullmodeltrainingbackward/efficacy,NOT authorizedbythisdiagnostic.\nNo productioncode/config/commit/queue/VAL changes.\n\n'
design += '## 7. Risk Assessment\nNativeprecision,boundarycases,actualgradients andresource overhead may fail. Preserve failures/classifyimplementation or inconclusive;neverweaken tolerance. Interfacebenchmark is not wholemodel/trainingresourcePASS.\n\n## 8. Smell Check\nA maskedmeanone-op is explicitly NOT admitted as Phase1coreinnovation. This is matched correctnessdiagnosis,not new trainingcandidate.\n'
dp = ROOT/'pipeline/designs/exp_design_20261018_4eca1157.md'
assert not dp.exists()
dp.write_text(design,encoding='utf-8')
models = {}
for tag, directory, epoch in [('m95','m95_native',16),('fle','shape_native',13)]:
    m = copy.deepcopy(tick.load(OLD/directory/'native_manifest.json'))
    m['expected_epoch'] = epoch
    for obsolete in ('original_checkpoint','checkpoint_bytes','checkpoint_mtime_ns'):
        m['assets'].pop(obsolete,None)
    models[tag] = m
save('models.json',models)
save('diagnostic_binding.json',{'created_at':datetime.now(timezone.utc).isoformat(),'reference_revision':1,
    'files':{n:tick.digest(OUT/n) for n in ('padding_contract.py','cpu_contract.py')},
    'preregistration':evidence(OUT/'contract_prereg.md'),'production_modified':False})
work = tick.load(ROOT/'pipeline/research_work.json')
c = next(c for c in work['candidates'] if c['id']==CID)
c.update(stage='validation',next_action='Execute uniformreference1 CPU exactsource/trainedweights contract before nativeinterface/backward/resources;NO productionfix/train/VAL.')
add(c,[rp,dp,OUT/'contract_prereg.md',OUT/'diagnostic_binding.json'])
guard()
tick.save(ROOT/'pipeline/research_work.json',work)
save('remote_stage.json',ssh('from pathlib import Path\nimport json\nPath('+repr(STAGE)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files = [str(OUT/n) for n in ('padding_contract.py','cpu_contract.py','models.json','diagnostic_binding.json')]
upload = run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*files,'songcl@192.168.1.115:'+STAGE+'/'])
save('cpu_upload.json',{'returncode':upload.returncode,'stderr':upload.stderr})
assert upload.returncode==0
command = ('test "$(hostname)" = dl04-MS-7E06 && source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
           'conda activate project_cluster && CUDA_VISIBLE_DEVICES= python -B '+shlex.quote(STAGE+'/cpu_contract.py'))
response = run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],180)
save('cpu_execution.json',{'returncode':response.returncode,'stdout':response.stdout,'stderr':response.stderr})
fetch = run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
             'songcl@192.168.1.115:'+STAGE+'/cpu_contract_result.json',str(OUT/'cpu_contract_result.json')])
save('cpu_fetch.json',{'returncode':fetch.returncode,'stderr':fetch.stderr})
assert fetch.returncode==0,response.stderr
r = tick.load(OUT/'cpu_contract_result.json')
print(json.dumps({'passed':r['passed'],'models':r['models'],'synthetic_cpu_backwards':r['synthetic_cpu_backwards'],
                  'error':r.get('error'),'stderr_tail':response.stderr[-1200:] if response.returncode else None}))
