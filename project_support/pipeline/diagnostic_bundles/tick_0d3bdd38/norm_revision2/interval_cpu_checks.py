"""Both saved failures, unchanged native and true norm controls;CPU only."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import numpy as np
import torch
from neighbor_content import permute_nonself

torch.set_num_threads(1)
stage=Path(__file__).resolve().parent
result={'passed':False,'checks':[],'native_forwards':0,'optimizer_steps':0,'CPU_feature_gradient_executions':0,'diagnostic_revision':2,'tolerance_unchanged':1e-6}
try:
    for label,path in [('capture','/data/songcl/Project/Cluster_project/pipeline/fle_content_norm_capture_ceb5e6c1/failed_norm_input.npz'),
                       ('repair1','/data/songcl/Project/Cluster_project/pipeline/fle_content_norm_precision_ceb5e6c1/failed_norm_input.npz')]:
        data=np.load(path,allow_pickle=False)
        for b in range(4):
            x=torch.from_numpy(data['nonself_'+str(b)])
            n=len(x);coords=data['positions'][b,:n];ids=data['leaves_'+str(b)]
            identity,_=permute_nonself(x,coords,ids,identity=True)
            assert torch.equal(identity,x)
            value,receipt=permute_nonself(x,coords,ids)
            assert torch.isfinite(value).all()
            assert receipt['norm_max_error']<=1e-6 and receipt['true_norm_max_error']<=1e-6
            result['checks'].append({'capture':label,'expression':b,'input_sha256':hashlib.sha256(x.numpy().tobytes()).hexdigest(),**receipt})
    torch.manual_seed(1999)
    x=torch.randn(8,256,dtype=torch.float64,requires_grad=True)
    coords=np.arange(24,dtype=np.float64).reshape(8,3);ids=np.zeros(8,dtype=np.int64)
    value,receipt=permute_nonself(x,coords,ids)
    gradient,=torch.autograd.grad(value.square().mean(),x)
    assert torch.isfinite(gradient).all() and gradient.norm()>0
    assert receipt['norm_max_error']<=1e-12 and receipt['true_norm_max_error']<=1e-12
    result.update(passed=True,CPU_feature_gradient_executions=1,float64_tolerance_unchanged=1e-12)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:
    result.update(observed_at=datetime.now(timezone.utc).isoformat(),cuda_initialized=torch.cuda.is_initialized())
    assert not result['cuda_initialized']
    with (stage/'interval_cpu_result.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps({'passed':result['passed'],'captured_conditions':len(result['checks']),
    'max_native_error':max(r['norm_max_error'] for r in result['checks']),
    'max_true_error':max(r['true_norm_max_error'] for r in result['checks']),
    'adjusted_vectors':sum(r['interval_adjusted_rows'] for r in result['checks'])}))
