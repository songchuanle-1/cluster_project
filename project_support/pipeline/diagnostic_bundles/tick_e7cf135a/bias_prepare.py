"""Stage the separately preregistered label-free output explanation."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import register

c=register.c
ROOT,BASE=register.ROOT,register.OUT
c.CID='hierarchy-scale-output-constant-shift-explanation'
c.OUT=BASE/'constant_runtime'
c.STAGE+='/constant_runtime'


def main():
    owner,_=c.guard(1200)
    c.OUT.mkdir(exist_ok=False)
    worker=(BASE/'worker.py').read_text(encoding='utf-8')
    marker="                for b in range(B):\n                    n=len(composed[b][0]);inverse=torch.argsort(permutations[b])"
    assert worker.count(marker)==1
    worker=worker.replace(marker,"                arms={key:value for key,value in arms.items() if key in ('omit_middle','omit_coarse','cycle_middle_messages','cycle_coarse_messages')}\n"+marker)
    marker='                scene_offset=0'
    assert worker.count(marker)==1
    decomposition='''                decompositions={}
                for label,(output,masks) in arm_outputs.items():
                    decompositions[label]=[]
                    for b in range(B):
                        n=len(composed[b][0]);query=int(selected[b])
                        baseline_logits=held['native_masks'][b,query,:n]
                        intervention_logits=masks[b,query,:n]
                        delta=intervention_logits-baseline_logits
                        constant=delta.mean();residual=delta-constant
                        reconstructed_delta=constant+residual
                        reconstructed_logits=baseline_logits+reconstructed_delta
                        delta_error=error(reconstructed_delta,delta)
                        logits_error=error(reconstructed_logits,intervention_logits)
                        assert max(delta_error,logits_error)<=MANIFEST['tolerance'],'Constant/residual reconstruction failed'
                        energy=float(delta.square().sum())
                        decompositions[label].append({'constant':constant,'residual':residual,
                            'constant_logits':baseline_logits+constant,'residual_logits':baseline_logits+residual,
                            'reconstructed_logits':reconstructed_logits,
                            'stats':{'constant_logit_shift':float(constant),
                                'delta_max_abs':float(delta.abs().max()),'delta_rms':float(delta.square().mean().sqrt()),
                                'residual_max_abs':float(residual.abs().max()),'residual_rms':float(residual.square().mean().sqrt()),
                                'residual_mean_abs':float(residual.mean().abs()),
                                'constant_energy_fraction':float(constant.square()*n)/energy if energy else None,
                                'residual_energy_fraction':float(residual.square().sum())/energy if energy else None,
                                'delta_reconstruction_max_abs':delta_error,'logits_reconstruction_max_abs':logits_error,
                                'labels_used_for_decomposition':False}})
'''
    worker=worker.replace(marker,decomposition+marker)
    marker="                            row['arms'][label]={'all_mae_delta':float(delta.mean()),"
    assert worker.count(marker)==1
    add='''                            decomposition=decompositions[label][b]
                            explained={}
                            for part in ('constant','residual','reconstructed'):
                                part_error=(decomposition[part+'_logits'].sigmoid()-target).abs()-native_error
                                explained[part]={'all_mae_delta':float(part_error.mean()),
                                    'foreground_mae_delta':mean_or_none(part_error[foreground]),
                                    'other_mae_delta':mean_or_none(part_error[other])}
                            row.setdefault('bias_arms',{})[label]={'decomposition':decomposition['stats'],'readouts':explained,
                                'nonlinear_all_mae_interaction':float(delta.mean())-explained['constant']['all_mae_delta']-explained['residual']['all_mae_delta']}
'''
    worker=worker.replace(marker,add+marker)
    interaction="                        row['middle_coarse_interaction_all_mae']=(row['arms']['cycle_middle_coarse_messages']['all_mae_delta']\n                            -row['arms']['cycle_middle_messages']['all_mae_delta']-row['arms']['cycle_coarse_messages']['all_mae_delta'])\n"
    assert worker.count(interaction)==1
    worker=worker.replace(interaction,'')
    worker=worker.replace("save('native_scale_result.json',result)","save('native_constant_result.json',result)")
    worker=worker.replace('Feature-only diagnostic on frozen M95; not full-source numerical admission or trained efficacy.',
        'Label-free output decomposition of existing frozen M95 scale interventions; no calibration model, full-source admission or trained efficacy.')
    ast.parse(worker)
    with (c.OUT/'worker.py').open('x',encoding='utf-8') as stream:stream.write(worker)
    runtime=(ROOT/'pipeline/diagnostic_bundles/tick_658721c0/native_runtime.py').read_text(encoding='utf-8').replace('658721c071ae487ea47224e55d51abde',c.TOKEN).replace('01a04987-fdbe-7301-b2f0-f9b6ab60f74c',c.THREAD)
    payload={'native_runtime.py':runtime.encode('utf-8'),'worker.py':worker.encode('utf-8')}
    manifest=copy.deepcopy(c.tick.load(BASE/'native_manifest.json'))
    manifest.update(stage=c.STAGE,candidate_id=c.CID,protocol=c.evidence(BASE/'constant_shift_preregistration.json'))
    manifest['diagnostic_files']={name:hashlib.sha256(value).hexdigest() for name,value in payload.items()}
    c.save('native_manifest.json',manifest)
    payload['native_manifest.json']=(c.OUT/'native_manifest.json').read_bytes()
    c.save('execution_lease.json',{'token':c.TOKEN,'thread_id':c.THREAD,'project':'cluster_project',
        'deadline_at':owner['deadline_at'],'native_manifest_sha256':c.tick.digest(c.OUT/'native_manifest.json')})
    payload['execution_lease.json']=(c.OUT/'execution_lease.json').read_bytes()
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
    staged=c.save('staging.json',c.remote('STAGE='+repr(c.STAGE)+'\nPAYLOAD='+repr(encoded)+'\nHASHES='+repr(hashes)+'\n'+code))
    assert c.tick.load(staged)['returncode']==0
    c.advance([c.OUT/'native_manifest.json',c.OUT/'worker.py',staged,Path(__file__)],
        'Execute preregistered fixed-query constant/residual explanatory readout; no source/model revision or training.')
    code='''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
process=subprocess.run([sys.executable,'-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json')],capture_output=True,text=True,timeout=580)
r={'returncode':process.returncode,'stdout':process.stdout[-8000:],'stderr':process.stderr[-14000:]}
path=stage/'native_constant_result.json'
if path.exists():r['result']=json.loads(path.read_text())
print(json.dumps(r))
'''
    observation=c.remote('STAGE='+repr(c.STAGE)+'\n'+code,timeout=620,conda=True)
    execution=c.save('native_execution.json',observation)
    assert observation['returncode']==0
    result=observation['data'].get('result',{})
    path=c.save('native_constant_result.json',result)
    c.advance([execution,path],'Inspect all constant/residual reconstruction controls and scene-stratified errors before any mechanism conclusion; no bias-correction training.')
    print(json.dumps({'returncode':observation['data']['returncode'],'execution_completed':result.get('execution_completed'),
        'error':result.get('error'),'summary':result.get('summary')}))


if __name__=='__main__':main()
