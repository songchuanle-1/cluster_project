"""CPU controls before the single diagnostic arithmetic repair is used natively."""
from datetime import datetime,timezone
import importlib.util,json,os
from pathlib import Path
import numpy as np
import torch
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
torch.set_num_threads(1);stage=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('norm_revision',stage/'neighbor_content.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
data=np.load('/data/songcl/Project/Cluster_project/pipeline/fle_content_norm_capture_ceb5e6c1/failed_norm_input.npz',allow_pickle=False)
rows=[]
for b in range(4):
    x=torch.from_numpy(data['nonself_'+str(b)]);n=len(x)
    coords=data['positions'][b,:n];leaves=data['leaves_'+str(b)]
    identity,_=module.permute_nonself(x,coords,leaves,identity=True);assert torch.equal(x,identity)
    value,receipt=module.permute_nonself(x,coords,leaves)
    assert torch.isfinite(value).all() and receipt['true_norm_max_error']<=1e-6
    rows.append({'case':'captured_'+str(b),**receipt,'legacy_CPU_norm_pass':receipt['norm_max_error']<=1e-6})
for n,label in ((1,'singleton'),(8,'zero_ties')):
    x=torch.zeros(n,256);value,receipt=module.permute_nonself(x,np.zeros((n,3)),np.zeros(n,dtype=np.int64))
    assert torch.equal(value,x);rows.append({'case':label,**receipt})
torch.manual_seed(1999);x=torch.randn(8,256,dtype=torch.float64,requires_grad=True)
coords=np.arange(24,dtype=np.float64).reshape(8,3);leaves=np.zeros(8,dtype=np.int64)
value,receipt=module.permute_nonself(x,coords,leaves)
gradient,=torch.autograd.grad(value.square().mean(),x)
assert torch.isfinite(gradient).all() and gradient.norm()>0 and receipt['norm_max_error']<=1e-12 and receipt['true_norm_max_error']<=1e-12
rows.append({'case':'float64_finite_gradient',**receipt})
result={'passed':True,'observed_at':datetime.now(timezone.utc).isoformat(),'controls':rows,'cuda_initialized':torch.cuda.is_initialized(),
    'CPU_feature_gradient_executions':1,'legacy_native_threshold_unchanged':1e-6,'native_cohort':'NOT_RUN_BY_THIS_CPU_CHECK'}
assert not result['cuda_initialized']
with (stage/'precision_cpu_result.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps(result))
