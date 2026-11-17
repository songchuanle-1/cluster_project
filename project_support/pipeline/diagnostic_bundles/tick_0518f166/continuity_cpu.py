"""Exact-input support continuity controls; unchanged source on CPU only."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
from fractions import Fraction
import hashlib,importlib.util,json
from pathlib import Path
import numpy as np
import torch
STAGE=Path(__file__).resolve().parent;manifest=json.loads((STAGE/'manifest.json').read_text())
source=Path(manifest['operator_path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['operator_sha256']
assert hashlib.sha256((STAGE/'continuity_prereg.md').read_bytes()).hexdigest()==manifest['prereg_sha256']
spec=importlib.util.spec_from_file_location('frozen_fle_continuity',source)
operator=importlib.util.module_from_spec(spec);spec.loader.exec_module(operator);torch.set_num_threads(1)
result={'execution_passed':False,'cases':[],'gradients':[],'native_network_forwards':0,'native_backwards':0,
    'native_FPS_calls':0,'optimizer_steps':0,'source_changed':False,'model_revisions':0,'cpu_exchange_calls':0}
def exact_support(coordinates):
    origin=[Fraction.from_float(float(x)) for x in coordinates[0]]
    squared=[sum(((Fraction.from_float(float(x))-y)**2 for x,y in zip(row,origin)),Fraction(0)) for row in coordinates]
    order=sorted(range(40),key=lambda i:(squared[i],i))
    return order[:32],squared[order[32]]-squared[order[31]]
def apply(features,graph):
    result['cpu_exchange_calls']+=1
    return operator.exchange(features,graph)
try:
    points=np.array([[0.,0.,0.]]+[[j/128.,0.,0.] for j in range(1,31)]+[[1.,0.,0.],[-1.,0.,0.]]+[[float(j),0.,0.] for j in range(2,9)])
    assert points.shape==(40,3)
    leaves=np.zeros(40,dtype=np.int64);cases=[('exact_tie',points.copy(),None)]
    for power in (4,8,12,16,20):
        for direction in (-1,1):
            changed=points.copy();changed[31,0]+=direction*2.**(-power)
            assert np.array_equal(changed,changed.astype(np.float32).astype(np.float64))
            cases.append(('cutoff_'+str(direction)+'_2^-'+str(power),changed,power))
    far=points.copy();far[39,0]+=2.**-20
    cases.extend([('far_motion_tie_preserved',far,None),('common_exact_translation',points+[16.,-8.,4.],None)])
    assert len(cases)==13
    for dtype in (torch.float64,torch.float32):
        sparse=torch.zeros(40,256,dtype=dtype);sparse[39]=1.;constant=torch.ones_like(sparse)
        for label,coordinates,power in cases:
            graph=operator.build_graph(coordinates,leaves,k=32);selected,gap=exact_support(coordinates);tied=gap==0
            assert bool(graph['fallback'][0])==tied and 39 not in selected
            if not tied:assert set(graph['indices'][0].tolist())==set(selected)
            output=apply(sparse,graph)[0];null=apply(constant,graph)[0]
            used=list(range(40)) if tied else selected
            reference=sparse.numpy()[used].mean(axis=0);expected=np.full(256,1./40. if tied else 0.)
            tolerance=1e-12 if dtype==torch.float64 else 1e-6
            error=float(np.max(np.abs(output.numpy()-reference)))
            assert error<=tolerance and np.max(np.abs(output.numpy()-expected))<=tolerance
            assert float((null-1.).abs().max())<=tolerance
            result['cases'].append({'case':label,'dtype':str(dtype),'epsilon_power':power,'exact_squared_cutoff_gap':str(gap),
                'fallback':tied,'effective_support_size':len(used),'far_donor_in_top32':False,'far_donor_component_output':float(output[0]),
                'jump_from_exact_tie':abs(float(output[0])-1./40.),'numpy_reference_max_error':error,
                'constant_feature_max_error':float((null-1.).abs().max()),'coordinates_sha256':hashlib.sha256(coordinates.tobytes()).hexdigest()})
            if label in ('exact_tie','cutoff_1_2^-20'):
                differentiable=sparse.clone().requires_grad_(True);value=apply(differentiable,graph)
                gradient,=torch.autograd.grad(value[0].sum(),differentiable);expected_gradient=1./40. if tied else 0.
                assert float((gradient[39]-expected_gradient).abs().max())<=tolerance
                result['gradients'].append({'case':label,'dtype':str(dtype),'far_donor_gradient_per_component':float(gradient[39,0]),'expected':expected_gradient})
    perturbations=[row for row in result['cases'] if row['epsilon_power'] is not None]
    assert len(perturbations)==20 and all(row['jump_from_exact_tie']==1./40. for row in perturbations)
    assert not torch.cuda.is_initialized()
    result.update(execution_passed=True,cuda_initialized=False,fixture_count=1,geometry_conditions=13,precision_conditions=26,
        perturbation_conditions=20,epsilon_powers=[4,8,12,16,20],nonvanishing_jump_component=1./40.,
        coordinate_rounding_or_cutoff_content_ambiguity_required=False,operator_sha256=manifest['operator_sha256'],
        scientific_status='Conditional exact-tie support discontinuity on artificial fixed leaf;not native FPS incidence,trainedfeatures,maskharm,efficacy or novelty',
        source_repair='NOT_IMPLEMENTED;noepsilonselected')
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:
    result['observed_at']=datetime.now(timezone.utc).isoformat()
    with (STAGE/'continuity_result.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps({key:result.get(key) for key in ('execution_passed','geometry_conditions','precision_conditions','perturbation_conditions','nonvanishing_jump_component','cpu_exchange_calls','cuda_initialized')}))
