"""Stage/execute only exact tested RSTR files in an isolated diagnostic directory."""
import argparse
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT
STAGE=c.STAGE+'_numeric_decomposition'
VOUT=OUT/'numeric_decomposition'


def stage():
    owner,_=c.guard(1500)
    VOUT.mkdir(exist_ok=False)
    worker=(OUT/'numeric_decomposition_worker.py').read_text(encoding='utf-8')
    old=(ROOT/'pipeline/diagnostic_bundles/tick_fefdcc2a/worker.py').read_text(encoding='utf-8')
    resource=old[old.index('def resources('):old.index('\ndef controls(')]
    resource=resource.replace('pce-resource-only','rstr-resource-only')
    worker=worker.replace('\ndef main():','\n'+resource+'\ndef main():')
    ast.parse(worker)
    with (VOUT/'worker.py').open('x',encoding='utf-8') as stream:stream.write(worker)
    protocol=c.save('numeric_decomposition_execution_preregistration.json',{'preregistered_at':c.now(),'candidate_id':c.CID,
        'source':c.evidence(OUT/'independent_bundle.json'),
        'full_source_controls':'Fresh actual native loss capture;3complete hierarchy+active-encoder identity repetitions; valid-SP reverse with transported memberships/inverse restore; disabled transport vs original parent forward. Original1e-6, FP32, no FPS/seed/threshold alteration.',
        'backward':'Actual model.train native loss.backward through backbone, entire bank, CTF and transport, no replacement/frozenbank. Retain actual input/output path gradient; all existing observed tensors finite and fine FFN nonzero. No optimizer.',
        'adverse_investigation':'Before examining results, capture native row stochasticity/nonnegative/detailed balance and pre-fusion pi-weighted variance before/after. Stationary convex kernel predicts variance nonincrease; preserve original FG adverse readouts. This describes smoothing, not efficacy.',
        'resources':'Fresh separate champion/candidate process, same first nativeVALexpression/resource sample only; no VALaccuracy selection; unchanged original FVCorehandlers;bs1,warmup20,repeat100,median/P90,peakallocated/reserved,parameter count;default10G and originalPareto. Fulloptimizerpeak unknown.',
        'revision':'Initial independent R0, defaultmax2 evidenced preregistered revisions; original failures immutable.',
        'training':0,'commit':False,'production_deployment':False})
    runtime=(ROOT/'pipeline/diagnostic_bundles/tick_658721c0/native_runtime.py').read_text(encoding='utf-8').replace('658721c071ae487ea47224e55d51abde',c.TOKEN).replace('01a04987-fdbe-7301-b2f0-f9b6ab60f74c',c.THREAD)
    payload={'native_runtime.py':runtime.encode(),'worker.py':worker.encode()}
    package=ROOT/'Cluster/framework/model/Quard_model'/'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr'
    for path in package.glob('*.py'):payload['candidate_model/'+path.name]=path.read_bytes()
    config=ROOT/'Cluster/configs/Quard/ctf_hcg_csort_rstr'/(package.name+'.yaml')
    payload['candidate.yaml']=config.read_bytes()
    manifest=copy.deepcopy(c.tick.load(OUT/'native_manifest.json'))
    manifest.update(stage=STAGE,protocol=c.evidence(protocol),candidate_source_hashes={Path(n).name:hashlib.sha256(v).hexdigest() for n,v in payload.items() if n.startswith('candidate_model/')})
    manifest['diagnostic_files']={n:hashlib.sha256(v).hexdigest() for n,v in payload.items()}
    (VOUT/'native_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    payload['native_manifest.json']=(VOUT/'native_manifest.json').read_bytes()
    lease={'token':c.TOKEN,'thread_id':c.THREAD,'project':'cluster_project','deadline_at':owner['deadline_at'],'native_manifest_sha256':c.tick.digest(VOUT/'native_manifest.json')}
    (VOUT/'execution_lease.json').write_text(json.dumps(lease,indent=2),encoding='utf-8')
    payload['execution_lease.json']=(VOUT/'execution_lease.json').read_bytes()
    encoded={n:base64.b64encode(v).decode('ascii') for n,v in payload.items()};hashes={n:hashlib.sha256(v).hexdigest() for n,v in payload.items()}
    code='''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE);stage.mkdir(exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'stage':str(stage),'files':len(PAYLOAD)}))
'''
    observed=c.save('numeric_decomposition_staging.json',c.remote('STAGE='+repr(STAGE)+'\nPAYLOAD='+repr(encoded)+'\nHASHES='+repr(hashes)+'\n'+code))
    assert c.tick.load(observed)['returncode']==0
    c.advance([protocol,VOUT/'native_manifest.json',VOUT/'worker.py',observed,Path(__file__),OUT/'numeric_decomposition_worker.py'],
        'Execute actual native backward/full-source controls and matched resource pair; preserve numeric/adverse results. No admission/commit/training.')
    print(json.dumps({'staged':STAGE,'files':len(payload)}))


def run(mode,target):
    c.guard(1200)
    code='''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
p=subprocess.run([sys.executable,'-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json'),'--mode',MODE,'--target',TARGET],capture_output=True,text=True,timeout=580)
r={'returncode':p.returncode,'stdout':p.stdout[-8000:],'stderr':p.stderr[-14000:]}
path=stage/(MODE+'_'+TARGET+'_result.json')
if path.exists():r['result']=json.loads(path.read_text())
print(json.dumps(r))
'''
    observed=c.remote('STAGE='+repr(STAGE)+'\nMODE='+repr(mode)+'\nTARGET='+repr(target)+'\n'+code,timeout=620,conda=True)
    label=mode+'_'+target
    execution=c.save('numeric_decomposition_'+label+'_execution.json',observed)
    assert observed['returncode']==0,'Observer failed; reconcile without blind retry'
    result=observed['data'].get('result',{})
    path=c.save('numeric_decomposition_'+label+'_result.json',result)
    c.advance([execution,path],'Evaluate full-source/native loss/resource evidence, repair only evidenced within the same stableID and original gates; no trained efficacy claim.')
    print(json.dumps({k:result.get(k) for k in ('execution_completed','error','all_full_source_controls_passed','maximum_full_source_control_error','transport_path_gradients','native_operator','median_ms','p90_ms','profile','peak_allocated_bytes')},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('stage','controls','resources','decompose'));parser.add_argument('--target',choices=('champion','candidate'),default='candidate')
    args=parser.parse_args()
    if args.operation=='stage':stage()
    else:run(args.operation,args.target)
