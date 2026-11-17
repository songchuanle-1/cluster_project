"""CPU canonical incidence comparison and a prediction-blind float64 check."""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser()
p.add_argument('--root',required=True)
a=p.parse_args()
root=Path(a.root)
dirs=[root/('native_m95_'+str(i)) for i in (1,2)]
def load(p):return json.loads(p.read_text())
def order(c):return np.lexsort(tuple(c[:,i] for i in reversed(range(c.shape[1]))))
def stats(x,y):
    assert x.shape==y.shape and x.dtype==y.dtype
    d=np.abs(x.astype(np.float64)-y.astype(np.float64))
    return {'different':int(np.count_nonzero(x!=y)),'elements':int(x.size),
        'max_absolute':float(d.max(initial=0)),'mean_absolute':float(d.mean()) if d.size else 0.}
results=[load(d/'native_trace_result.json') for d in dirs]
probes=[load(d/'native_stride_result.json') for d in dirs]
assert all(x['passed'] for x in (*results,*probes))
arrays=[np.load(d/'native_stride_arrays.npz',allow_pickle=False) for d in dirs]
for directory,probe in zip(dirs,probes):
    h=hashlib.sha256()
    with (directory/'native_stride_arrays.npz').open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    assert h.hexdigest()==probe['raw_sha256']
assert all(np.array_equal(arrays[0][k],arrays[1][k]) for k in ('input_features','input_indices','weight'))
orders=[order(x['output_indices']) for x in arrays]
assert np.array_equal(arrays[0]['output_indices'][orders[0]],arrays[1]['output_indices'][orders[1]])
for data in arrays:
    assert np.array_equal(data['input_indices'],data['indice_indices'])
    assert np.array_equal(data['output_indices'],data['indice_out_indices'])
canonical=[]
references=[]
for data,permutation,probe in zip(arrays,orders,probes):
    ranks=np.argsort(permutation)
    fwd=data['indice_pair_fwd'][:,permutation]
    bwd=data['indice_pair_bwd'].copy()
    valid=bwd>=0
    assert np.all(bwd[valid]<len(ranks))
    bwd[valid]=ranks[bwd[valid]]
    item={'pair_fwd':fwd,'pair_bwd':bwd}
    for key in data.files:
        if key.startswith('indice_pair_mask_fwd_splits_'):item[key]=data[key][permutation]
        elif key.startswith('indice_mask_argsort_fwd_splits_'):
            indices=data[key]
            assert np.array_equal(np.sort(indices),np.arange(len(permutation)))
            item[key]=ranks[indices]
    canonical.append(item)
    assert probe['configuration']['ALL_WEIGHT_IS_KRSC']=='True'
    w=data['weight']
    assert w.shape[0]==data['output_features'].shape[1] and w.shape[-1]==data['input_features'].shape[1]
    w=w.reshape(w.shape[0],-1,w.shape[-1]).astype(np.float64)
    assert fwd.shape[0]==w.shape[1]
    chosen=fwd[:,:256]
    reference=np.zeros((chosen.shape[1],w.shape[0]),dtype=np.float64)
    for kernel in range(w.shape[1]):
        ids=chosen[kernel]
        valid=ids>=0
        assert np.all(ids[valid]<len(data['input_features']))
        reference[valid]+=data['input_features'][ids[valid]].astype(np.float64)@w[:,kernel,:].T
    references.append(reference)
summary={'passed':True,'observed_at':datetime.now(timezone.utc).isoformat(),
    'native_input_equal':True,'weights_equal':True,'coordinate_sets_equal':True,
    'native_batch_equal':results[0]['input_sha256']==results[1]['input_sha256'],
    'native_rng_before_equal':results[0]['rng_before']==results[1]['rng_before'],
    'native_rng_after_forward_equal':results[0]['rng_after_forward']==results[1]['rng_after_forward'],
    'cache_observations':[x['cache_after'] for x in probes],
    'same_actual_descriptor':probes[0]['cache_after']['descriptor']==probes[1]['cache_after']['descriptor'],
    'row_order_equal':bool(np.array_equal(arrays[0]['output_indices'],arrays[1]['output_indices'])),
    'native_aligned_output':stats(arrays[0]['output_features'][orders[0]],arrays[1]['output_features'][orders[1]]),
    'canonical_incidence_equal':{k:bool(np.array_equal(canonical[0][k],canonical[1][k])) for k in canonical[0]},
    'float64_reference_pair':stats(references[0],references[1]),
    'float64_reference_sample_size':256,'reference_sampling':'first256 lexicographic output coordinates,not prediction selected',
    'native_vs_float64_reference':[],
    'loss_abs_difference':abs(results[0]['loss']-results[1]['loss']),
    'kernel_unique_cause':'UNKNOWN;observational descriptors/incidences are not a counterfactual kernel intervention',
    'efficacy':'UNKNOWN','novel_architecture':False,'optimizer_steps':0,
    'scope':'one preregistered actualnative pair,not seedvariance/CI;float64 errors are reports,not tolerance relaxations'}
for data,permutation,reference in zip(arrays,orders,references):
    error=np.abs(data['output_features'][permutation[:256]].astype(np.float64)-reference)
    summary['native_vs_float64_reference'].append({'max_absolute':float(error.max()),'mean_absolute':float(error.mean())})
assert summary['native_batch_equal'] and summary['native_rng_before_equal'] and summary['native_rng_after_forward_equal']
assert all(v for k,v in summary['canonical_incidence_equal'].items() if k in ('pair_fwd','pair_bwd'))
with (root/'native_stride_comparison.json').open('x') as f:json.dump(summary,f,indent=2,allow_nan=False)
print(json.dumps(summary))
