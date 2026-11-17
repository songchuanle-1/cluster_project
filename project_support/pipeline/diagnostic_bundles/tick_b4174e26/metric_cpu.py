"""Exact admitted-operator geometry controls on CPU,not native mask execution."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import numpy as np
import torch
from scipy.spatial import cKDTree,distance_matrix

STAGE=Path(__file__).resolve().parent
manifest=json.loads((STAGE/'manifest.json').read_text())
source=Path(manifest['operator_path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['operator_sha256']
spec=importlib.util.spec_from_file_location('admitted_fle_metric',source)
operator=importlib.util.module_from_spec(spec);spec.loader.exec_module(operator)
torch.set_num_threads(1)
result={'execution_passed':False,'controls':[],'cases':[],'native_forwards':0,'native_backwards':0,'optimizer_steps':0,
    'scientific_status':'CPU probe-feature conditional metric robustness only;not trained point features or mask efficacy'}
try:
    rng=np.random.default_rng(1999)
    fixtures={'gaussian40':rng.normal(size=(40,3)),
        'lattice40':np.array(sorted(itertools.product(range(-2,3),repeat=3),key=lambda p:(sum(v*v for v in p),*p))[:40],dtype=np.float64)}
    c=math.cos(math.pi/4);s=math.sin(math.pi/4)
    rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]],dtype=np.float64)
    transforms={'identity':lambda x:x.copy(),'reflection':lambda x:x*np.array([-1.,1.,1.]),
        'axis_permutation':lambda x:x[:,[2,0,1]],'scale2':lambda x:x*2.,'scale_half':lambda x:x*.5,
        'translation':lambda x:x+np.array([16.,-8.,4.]),'rotation_z_pi4':lambda x:x@rotation.T,
        'negative_x_compression':lambda x:x*np.array([1/16,1.,1.])}
    for fixture,coords in fixtures.items():
        torch.manual_seed(1999);features=torch.randn(40,256,dtype=torch.float64)
        leaves=np.zeros(40,dtype=np.int64)
        graph=operator.build_graph(coords,leaves)
        native=operator.exchange(features,graph)
        repeated=operator.exchange(features,operator.build_graph(coords,leaves))
        assert torch.equal(native,repeated)
        distances=distance_matrix(coords,coords)
        for name,transform in transforms.items():
            geometry=transform(coords);changed_graph=operator.build_graph(geometry,leaves)
            actual=operator.exchange(features,changed_graph)
            actual32=operator.exchange(features.float(),changed_graph)
            native32=operator.exchange(features.float(),graph)
            valid=graph['allowed'];different_sets=[]
            for i in range(len(coords)):
                a=set(graph['indices'][i][valid[i]].tolist());b=set(changed_graph['indices'][i][changed_graph['allowed'][i]].tolist())
                different_sets.append(a!=b)
            d0,_=cKDTree(coords).query(coords,k=list(range(1,34)))
            d1,_=cKDTree(geometry).query(geometry,k=list(range(1,34)))
            expected_distances=distances*(2 if name=='scale2' else .5 if name=='scale_half' else 1)
            row={'fixture':fixture,'transform':name,'operator_max_error_float64':float((native-actual).abs().max()),
                'operator_max_error_float32':float((native32-actual32).abs().max()),'neighbor_set_changed_recipients':sum(different_sets),
                'fallback_original':int(graph['fallback'].sum()),'fallback_transformed':int(changed_graph['fallback'].sum()),
                'fallback_changed_recipients':int((graph['fallback']!=changed_graph['fallback']).sum()),
                'max_pairwise_distance_residual':float(np.max(np.abs(distance_matrix(geometry,geometry)-expected_distances))),
                'minimum_cutoff_gap_original':float(np.min(d0[:,32]-d0[:,31])),
                'minimum_cutoff_gap_transformed':float(np.min(d1[:,32]-d1[:,31])),
                'isometry_or_uniform_scale':not name.startswith('negative'),
                'within_native_tolerance':float((native32-actual32).abs().max())<=1e-6}
            if name=='identity':assert row['operator_max_error_float64']==0
            if not row['within_native_tolerance'] and row['isometry_or_uniform_scale']:
                filename='counterexample_'+fixture+'_'+name+'.npz'
                with (STAGE/filename).open('xb') as stream:
                    np.savez_compressed(stream,features=features.numpy(),coordinates=coords,transformed=geometry,leaves=leaves,
                        original_indices=graph['indices'].numpy(),transformed_indices=changed_graph['indices'].numpy(),
                        original_fallback=graph['fallback'].numpy(),transformed_fallback=changed_graph['fallback'].numpy(),
                        original_output=native.numpy(),transformed_output=actual.numpy())
                row['counterexample']=filename
            result['cases'].append(row)
    singleton=torch.randn(1,256,dtype=torch.float64)
    graph=operator.build_graph(np.zeros((1,3)),np.zeros(1,dtype=np.int64))
    assert torch.equal(operator.exchange(singleton,graph),singleton)
    result['controls'].append({'case':'singleton','passed':True})
    graph=operator.build_graph(fixtures['lattice40'],np.zeros(40,dtype=np.int64))
    assert torch.count_nonzero(operator.exchange(torch.zeros(40,256,dtype=torch.float64),graph))==0
    result['controls'].append({'case':'zero_features','passed':True})
    assert not torch.cuda.is_initialized()
    result.update(execution_passed=True,cuda_initialized=False,operator_sha256=manifest['operator_sha256'],
        metric_failures=[{'fixture':r['fixture'],'transform':r['transform'],'max_error':r['operator_max_error_float32']} for r in result['cases'] if r['isometry_or_uniform_scale'] and not r['within_native_tolerance']],
        native_train_membership_tests='NOT_RUN_CUDA_FPS_REQUIRED',source_changed=False,model_revision=False)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:
    result['observed_at']=datetime.now(timezone.utc).isoformat()
    with (STAGE/'metric_cpu_result.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps({'execution_passed':result['execution_passed'],'case_count':len(result['cases']),'metric_failures':result.get('metric_failures'),'cuda_initialized':result.get('cuda_initialized')}))
