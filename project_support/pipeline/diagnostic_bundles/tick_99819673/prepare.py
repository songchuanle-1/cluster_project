"""Stage only this lease-bound native experiment; no production deployment."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import register
c=register.c
OUT,ROOT=register.OUT,register.ROOT


def stage():
    owner,_=c.guard(1200)
    supplement=c.save('matched_control_preregistration.json',{
        'preregistered_at':c.now(),'candidate_id':c.CID,
        'wrong_affinity':'Within each parent, order valid fine indices ascending, cyclically shift affinity feature rows by one. Compute Q from shifted features, but apply the same MH formula using ORIGINAL receiver masses pi and ORIGINAL value rows. Recompute A/P, do not permute pi or values. Singleton identity. No alternate cycles/temperatures selected.',
        'matched':'Identical graph, heads, dimensions, mass vector, values, equation, counts and FLOPs. Q is conjugate-permuted before MH. Each arm has its own exact stationarity; final conductance magnitudes are not claimed equal because pi remains fixed.',
        'additional_strict_control':'Also cycle affinity rows only WITHIN equal-n subsets of each parent, ascending fine-index order. pi is invariant under that permutation, so Pcontrol=RPR^T and accepted transition weight multiset is preserved. Report actual moved-token/receiver coverage; identity groups are not informative nulls. This arm is a control, not a separately selectable model.',
        'clarification':'n_i counts valid inst_feats SUPERPOINT rows assigned to fine leaf, not raw sensor point multiplicities. The preserved mean is over these superpoint-row readbacks before learned fusion.',
        'numerical':'All output/inverse/frozen identity/invariant tolerances remain1e-6. Use FP64 ONLY for diagnostic summation of mean error; executed transport remains original FP32.',
        'readouts':'Native chosen query fixed. All/FG/non-target probability MAE; content-minus-wrong scene deltas; PT-T and original-vs-wrong mask change; per-parent offdiag transition and weighted fine mean. Labels are readout only. No efficacy threshold from8scenes.',
        'limits':'This capture does not establish full-source invariance or native training backward. No train/admission from operator PASS.'})
    frozen=c.tick.load(ROOT/'pipeline/diagnostic_bundles/tick_658721c0/native_manifest.json')
    runtime=(ROOT/'pipeline/diagnostic_bundles/tick_658721c0/native_runtime.py').read_text(encoding='utf-8')
    runtime=runtime.replace('658721c071ae487ea47224e55d51abde',c.TOKEN).replace('01a04987-fdbe-7301-b2f0-f9b6ab60f74c',c.THREAD)
    payload={'native_runtime.py':runtime.encode(),'worker.py':(OUT/'worker.py').read_bytes(),'transport.py':(OUT/'transport.py').read_bytes()}
    manifest=copy.deepcopy(frozen)
    manifest.update(stage=c.STAGE,current_token=c.TOKEN,candidate_id=c.CID,
        protocol=c.evidence(OUT/'preregistration.json'),matched_control=c.evidence(supplement),
        cohort=c.tick.load(ROOT/'pipeline/diagnostic_bundles/tick_e7cf135a/cohort.json')['cohort'])
    manifest['diagnostic_files']={name:hashlib.sha256(value).hexdigest() for name,value in payload.items()}
    c.save('native_manifest.json',manifest)
    payload['native_manifest.json']=(OUT/'native_manifest.json').read_bytes()
    c.save('execution_lease.json',{'token':c.TOKEN,'thread_id':c.THREAD,'project':'cluster_project','deadline_at':owner['deadline_at'],'native_manifest_sha256':c.tick.digest(OUT/'native_manifest.json')})
    payload['execution_lease.json']=(OUT/'execution_lease.json').read_bytes()
    encoded={name:base64.b64encode(value).decode('ascii') for name,value in payload.items()}
    hashes={name:hashlib.sha256(value).hexdigest() for name,value in payload.items()}
    code='''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE);stage.mkdir(exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 with path.open('xb') as stream:stream.write(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'staged':str(stage),'files':len(PAYLOAD)}))
'''
    observed=c.save('staging.json',c.remote('STAGE='+repr(c.STAGE)+'\nPAYLOAD='+repr(encoded)+'\nHASHES='+repr(hashes)+'\n'+code))
    assert c.tick.load(observed)['returncode']==0
    c.advance([supplement,OUT/'native_manifest.json',OUT/'worker.py',OUT/'transport.py',observed,Path(__file__)],
        'Execute fixed primitive and8scene native transport-vs-wrong-affinity diagnostic; no training or admission.')
    print(json.dumps({'staged':c.STAGE,'files':len(payload)}))


def run():
    c.guard(1200)
    code='''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
p=subprocess.run([sys.executable,'-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json')],capture_output=True,text=True,timeout=580)
r={'returncode':p.returncode,'stdout':p.stdout[-8000:],'stderr':p.stderr[-14000:]}
path=stage/'native_transport_result.json'
if path.exists():r['result']=json.loads(path.read_text())
print(json.dumps(r))
'''
    observed=c.remote('STAGE='+repr(c.STAGE)+'\n'+code,timeout=620,conda=True)
    execution=c.save('native_execution.json',observed)
    assert observed['returncode']==0,'Observer failed; reconcile without blind replay'
    result=observed['data'].get('result',{})
    path=c.save('native_transport_result.json',result)
    c.advance([execution,path],'Analyze frozen transport test, then advance actual source/backward/resources only if supported. Preserve every failure.')
    print(json.dumps({'returncode':observed['data']['returncode'],'completed':result.get('execution_completed'),
        'error':result.get('error'),'primitive':result.get('primitive'),'summary':result.get('summary')},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('probe','stage','run'))
    operation=parser.parse_args().operation
    if operation=='probe':c.probe()
    elif operation=='stage':stage()
    else:run()
