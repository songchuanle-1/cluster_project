"""CPU-only comparisons of exact-input sparse controls and aligned block traces."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('--root',required=True)
p.add_argument('--kind',choices=['sparse','aligned'],required=True)
a=p.parse_args()
root=Path(a.root)
def load(path):return json.loads(path.read_text())
def stats(x,y):
    assert x.shape==y.shape and x.dtype==y.dtype
    d=np.abs(x.astype(np.float64)-y.astype(np.float64))
    return {'different':int(np.count_nonzero(x!=y)),'elements':int(x.size),
        'max_absolute':float(d.max(initial=0)),'mean_absolute':float(d.mean()) if d.size else 0.}
def order(coords):return np.lexsort(tuple(coords[:,i] for i in reversed(range(coords.shape[1]))))
summary={'passed':True,'observed_at':datetime.now(timezone.utc).isoformat(),'kind':a.kind}
if a.kind=='sparse':
    models={}
    for model in ('m95','fle'):
        dirs=[root/('sparse_'+model+'_'+str(i)) for i in (1,2)]
        results=[load(d/'native_sparse_result.json') for d in dirs]
        assert all(r['passed'] for r in results)
        arrays=[np.load(d/'operator_arrays.npz',allow_pickle=False) for d in dirs]
        controls=[np.load(d/'control_bundle.npz',allow_pickle=False) for d in dirs]
        assert results[0]['control_source_sha256']==results[1]['control_source_sha256']
        assert results[0]['layer_weight_sha256']==results[1]['layer_weight_sha256']
        assert all(np.array_equal(controls[0][k],controls[1][k]) for k in ('xf','xi'))
        cross={str(i):{k:stats(arrays[0][str(i)+'_'+k],arrays[1][str(i)+'_'+k]) for k in ('yf','gx','gw')} for i in (0,1)}
        coords=[c['yi'] for c in controls]
        assert np.array_equal(coords[0][order(coords[0])],coords[1][order(coords[1])])
        models[model]={'frozen_native_input_equal':True,'weight_equal':True,'shared_cotangent_source_equal':True,
            'native_coordinate_sets_equal':True,'native_output_row_order_equal':bool(np.array_equal(*coords)),
            'native_coordinate_aligned_output':stats(controls[0]['yf'][order(coords[0])],controls[1]['yf'][order(coords[1])]),
            'within_process_pairs':[r['within_process_pair'] for r in results],
            'cross_process_original_operator_pairs':cross,
            'null_controls':[r['zero_cotangent_max'] for r in results]}
    summary['models']=models
else:
    dirs=[root/('aligned_fle_'+str(i)) for i in (1,2)]
    results=[load(d/'native_trace_result.json') for d in dirs]
    assert all(r['passed'] for r in results)
    evs=[load(d/'trace_events.json')['events'] for d in dirs]
    arrays=[np.load(d/'trace_arrays.npz',allow_pickle=False) for d in dirs]
    down=[next(e for e in es if e['label']=='unet.conv.2' and e['phase']=='post') for es in evs]
    coords=[arr[e['tensors']['x.indices']['raw_key']] for arr,e in zip(arrays,down)]
    permutations=[order(c) for c in coords]
    assert np.array_equal(coords[0][permutations[0]],coords[1][permutations[1]])
    summaries=[]
    for e1,e2 in zip(*evs):
        assert (e1['label'],e1['phase'],e1['sequence'])==(e2['label'],e2['phase'],e2['sequence'])
        if e1['phase']!='post' or not e1['label'].startswith(('unet.conv.2','unet.u.blocks.block0')):continue
        pairs=[]
        for arr,event,coord,permutation in zip(arrays,(e1,e2),coords,permutations):
            if 'x.indices' in event['tensors']:
                actual=arr[event['tensors']['x.indices']['raw_key']]
                assert np.array_equal(actual,coord),'SubM row order changed;do not misalign tensors'
            key='x.features' if 'x.features' in event['tensors'] else 'x'
            feature=arr[event['tensors'][key]['raw_key']]
            assert feature.shape[0]==len(coord)
            pairs.append(feature[permutation])
        summaries.append({'sequence':e1['sequence'],'label':e1['label'],'aligned_feature_difference':stats(*pairs)})
    summary.update(model='fle',native_input_equal=results[0]['input_sha256']==results[1]['input_sha256'],
        model_equal=results[0]['model_loaded_sha256']==results[1]['model_loaded_sha256'],
        rng_before_equal=results[0]['rng_before']==results[1]['rng_before'],
        norm_eval=[r['norm_eval'] for r in results],first_block_norm_training=[r['first_block_norm_training'] for r in results],
        coordinate_sets_equal=True,row_order_equal=bool(np.array_equal(*coords)),boundaries=summaries,
        first_coordinate_aligned_difference=next((s for s in summaries if s['aligned_feature_difference']['different']),None))
    assert summary['native_input_equal'] and summary['model_equal'] and summary['rng_before_equal']
summary['scope']='frozen original native diagnostic only;not seedvariance/CI,unique kernelcause or trained benefit'
destination=root/(a.kind+'_control_comparison.json')
with destination.open('x') as f:json.dump(summary,f,indent=2,allow_nan=False)
print(json.dumps(summary))
