"""Independent integer-distance and NumPy evaluation of the frozen counterexample."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import torch

stage=Path(__file__).resolve().parent
manifest=json.loads((stage/'manifest.json').read_text())
source=Path(manifest['operator_path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['operator_sha256']
spec=importlib.util.spec_from_file_location('exact_fle_confirm',source)
operator=importlib.util.module_from_spec(spec);spec.loader.exec_module(operator)
torch.set_num_threads(1)
path=stage/'counterexample_lattice40_rotation_z_pi4.npz'
arrays=np.load(path,allow_pickle=False)
x=arrays['features'];xyz=arrays['coordinates'];rotated=arrays['transformed'];leaves=arrays['leaves']
assert np.array_equal(xyz,xyz.astype(np.int64))
delta=xyz.astype(np.int64)[:,None,:]-xyz.astype(np.int64)[None,:,:]
exact_squared=np.sum(delta*delta,axis=-1)
ordered=np.sort(exact_squared,axis=-1)
exact_tie=ordered[:,31]==ordered[:,32]
g0=operator.build_graph(xyz,leaves);g1=operator.build_graph(rotated,leaves)
assert np.array_equal(exact_tie,g0['fallback'].numpy())
features=torch.from_numpy(x)
out0=operator.exchange(features,g0);out1=operator.exchange(features,g1)
assert np.array_equal(out0.numpy(),arrays['original_output']) and np.array_equal(out1.numpy(),arrays['transformed_output'])
def independent(graph):
    indices=graph['indices'].numpy();allowed=graph['allowed'].numpy()
    grouped=x[indices].reshape(40,32,8,32)
    scores=(x.reshape(40,1,8,32)*grouped).sum(-1)/np.sqrt(32)
    scores=np.where(allowed[:,:,None],scores,-np.inf)
    scores-=scores.max(1,keepdims=True)
    probability=np.exp(scores);probability/=probability.sum(1,keepdims=True)
    ordinary=(probability[:,:,:,None]*grouped).sum(1).reshape(40,256)
    return np.where(graph['fallback'].numpy()[:,None],x.mean(0)[None,:],ordinary)
ind0=independent(g0);ind1=independent(g1)
independent_error=max(float(np.max(np.abs(ind0-out0.numpy()))),float(np.max(np.abs(ind1-out1.numpy()))))
assert independent_error<=1e-12
oracle=dict(g1);oracle['fallback']=torch.from_numpy(exact_tie.copy())
oracle_out=operator.exchange(features,oracle)
oracle_error=float((oracle_out-out0).abs().max())
assert oracle_error<=1e-12
changed=np.flatnonzero(g0['fallback'].numpy()!=g1['fallback'].numpy())
rows=[]
for i in changed:
    d=np.sqrt(np.sum((rotated-rotated[i])**2,axis=1));rank=np.sort(d)
    rows.append({'recipient':int(i),'original_exact_squared_k32':int(ordered[i,31]),'original_exact_squared_k33':int(ordered[i,32]),
        'transformed_numpy_k32':float(rank[31]),'transformed_numpy_k33':float(rank[32]),
        'output_max_error':float((out1[i]-out0[i]).abs().max())})
assert len(changed)==8
result={'passed_confirmation':True,'observed_at':datetime.now(timezone.utc).isoformat(),
    'counterexample_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'independent_numpy_max_error':independent_error,
    'exact_integer_cutoff_ties':int(exact_tie.sum()),'fallback_flips':len(changed),'changed_recipients':rows,
    'diagnostic_oracle_output_error':oracle_error,'observed_output_max_error':float((out1-out0).abs().max()),
    'interpretation':'Machine-roundoff changes exact floating cutoff equality;this switches8recipients from symmetric leaf mean to ordinary K32attention. Integer-tie oracle restores lattice result,not a production fix.',
    'source_changed':False,'native_mask_effect':'unknown','material_novelty':'unestablished','cuda_initialized':torch.cuda.is_initialized()}
assert not result['cuda_initialized']
with (stage/'counterexample_confirmation.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps({'confirmed':True,'fallback_flips':len(changed),'independent_error':independent_error,'oracle_error':oracle_error}))
