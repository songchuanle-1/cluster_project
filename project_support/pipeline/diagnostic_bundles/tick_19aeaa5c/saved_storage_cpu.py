"""Actual-source retained-storage accounting,not a GPU peak measurement."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
import hashlib,importlib.util,json
from pathlib import Path
import numpy as np
import torch
STAGE=Path(__file__).resolve().parent;manifest=json.loads((STAGE/'manifest.json').read_text())
source=Path(manifest['operator_path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['operator_sha256']
assert hashlib.sha256((STAGE/'saved_storage_prereg.md').read_bytes()).hexdigest()==manifest['prereg_sha256']
spec=importlib.util.spec_from_file_location('frozen_fle_saved_storage',source)
operator=importlib.util.module_from_spec(spec);spec.loader.exec_module(operator);torch.set_num_threads(1)
result={'execution_passed':False,'cases':[],'cpu_exchange_calls':0,'cpu_feature_gradient_executions':0,
    'native_network_forwards':0,'native_backwards':0,'native_FPS_calls':0,'optimizer_steps':0,'source_changed':False}
def apply(features,graph):
    result['cpu_exchange_calls']+=1
    return operator.exchange(features,graph)
try:
    for label,n,leafsize in (('single16',16,16),('single64',64,64),('single128',128,128),('sixteen_leaves8',128,8)):
        rng=np.random.default_rng(1999);coordinates=rng.normal(size=(n,3));leaves=np.arange(n,dtype=np.int64)//leafsize
        graph=operator.build_graph(coordinates,leaves,k=32)
        assert not bool(graph['fallback'].any())
        torch.manual_seed(1999);features=torch.randn(n,256,dtype=torch.float32,requires_grad=True)
        packed=[]
        def pack(tensor):
            packed.append(tensor)
            return tensor
        with torch.autograd.graph.saved_tensors_hooks(pack,lambda tensor:tensor):
            output=apply(features,graph)
            loss=output.square().mean()
        input_pointer=features.untyped_storage().data_ptr()
        unique={};records=[]
        for tensor in packed:
            storage=tensor.untyped_storage();pointer=storage.data_ptr()
            record={'shape':list(tensor.shape),'stride':list(tensor.stride()),'dtype':str(tensor.dtype),
                'storage_bytes':storage.nbytes(),'input_alias':pointer==input_pointer,'floating':tensor.is_floating_point()}
            records.append(record)
            if pointer not in unique:unique[pointer]=dict(record,reference_count=0)
            unique[pointer]['reference_count']+=1
        new_float=[record for record in unique.values() if record['floating'] and not record['input_alias']]
        expected=n*32*256*4
        assert max(record['storage_bytes'] for record in new_float)==expected
        assert any(record['shape']==[n,32,8,32] and record['storage_bytes']==expected for record in records)
        gradient,=torch.autograd.grad(loss,features);result['cpu_feature_gradient_executions']+=1
        plain=features.detach().clone().requires_grad_(True);plain_output=apply(plain,graph)
        plain_gradient,=torch.autograd.grad(plain_output.square().mean(),plain);result['cpu_feature_gradient_executions']+=1
        with torch.no_grad():null=apply(features.detach(),graph)
        assert torch.equal(output,plain_output) and torch.equal(output,null)
        gradient_error=float((gradient-plain_gradient).abs().max())
        assert gradient_error<=1e-6 and torch.isfinite(gradient).all() and float(gradient.norm())>0.
        result['cases'].append({'case':label,'n':n,'leaf_size':leafsize,'valid_edges':int(graph['allowed'].sum()),
            'allocated_neighbor_slots':n*32,'masked_neighbor_slots':n*32-int(graph['allowed'].sum()),
            'expected_gather_storage_bytes':expected,'maximum_new_floating_saved_storage_bytes':max(record['storage_bytes'] for record in new_float),
            'all_unique_saved_storage_bytes':sum(record['storage_bytes'] for record in unique.values()),
            'new_floating_unique_saved_storage_bytes':sum(record['storage_bytes'] for record in new_float),
            'saved_reference_count':len(records),'unique_saved_storages':list(unique.values()),'saved_views':records,
            'forward_bitwise_equal':True,'gradient_max_error':gradient_error,'gradient_norm':float(gradient.norm()),
            'coordinates_sha256':hashlib.sha256(coordinates.tobytes()).hexdigest(),
            'features_sha256':hashlib.sha256(features.detach().numpy().tobytes()).hexdigest()})
        del packed,output,loss,plain,plain_output,gradient,plain_gradient,features,null
    assert result['cpu_exchange_calls']==12 and result['cpu_feature_gradient_executions']==8
    assert not torch.cuda.is_initialized()
    result.update(execution_passed=True,cuda_initialized=False,source_sha256=manifest['operator_sha256'],
        torch_version=torch.__version__,case_count=4,new_trainable_parameters=0,
        measurement='CPU forward retained saved-for-backward unique storage,not totalallocationpeak or CUDAmemory',
        scientific_status='Finite activation accounting only;notnativeVRAM,taskbenefit,memorysavings,repairorresourceadmission')
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:
    result['observed_at']=datetime.now(timezone.utc).isoformat()
    with (STAGE/'saved_storage_result.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps({'execution_passed':result['execution_passed'],'cases':[{k:row[k] for k in ('case','n','valid_edges','allocated_neighbor_slots','maximum_new_floating_saved_storage_bytes','new_floating_unique_saved_storage_bytes')} for row in result['cases']],
    'cpu_exchange_calls':result['cpu_exchange_calls'],'cpu_feature_gradient_executions':result['cpu_feature_gradient_executions'],'cuda_initialized':result.get('cuda_initialized')}))
