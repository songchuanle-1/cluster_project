"""Independent CPU norms of exact captured float32 vectors;no gate relaxation."""
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import numpy as np
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
stage=Path(__file__).resolve().parent;path=stage/'failed_norm_input.npz'
data=np.load(path,allow_pickle=False);rows=[]
for key in sorted(k for k in data.files if k.startswith('nonself_')):
    b=key.split('_')[1];x=data[key].reshape(-1,8,32).astype(np.float64)
    y=data['replacement_'+b].reshape(-1,8,32).astype(np.float64)
    original=np.linalg.norm(x,axis=-1);changed=np.linalg.norm(y,axis=-1)
    gpu_original=data['native_norm_'+b].astype(np.float64);gpu_changed=data['native_replacement_norm_'+b].astype(np.float64)
    error=np.abs(changed-original);gpu_error=np.abs(gpu_changed-gpu_original);i,h=np.unravel_index(np.argmax(gpu_error),gpu_error.shape)
    rows.append({'batch_expression':int(b),'vectors':int(error.size),'native_float32_max_norm_error':float(gpu_error.max()),
        'independent_float64_max_true_norm_error':float(error.max()),'native_above_1e_6':int((gpu_error>1e-6).sum()),
        'true_above_1e_6':int((error>1e-6).sum()),'original_native_reduction_max_error':float(np.abs(gpu_original-original).max()),
        'replacement_native_reduction_max_error':float(np.abs(gpu_changed-changed).max()),
        'worst_native_row':int(i),'worst_native_head':int(h),'worst_native_original_norm':float(gpu_original[i,h]),
        'worst_native_replacement_norm':float(gpu_changed[i,h]),'worst_native_error':float(gpu_error[i,h]),
        'same_row_true_norm_error':float(error[i,h]),'float32_ulp_at_target':float(np.spacing(data['native_norm_'+b][i,h]))})
result={'observed_at':datetime.now(timezone.utc).isoformat(),'capture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'rows':rows,'native_threshold_unchanged':1e-6,'classification':'measurement_and_or_scaling_error_only;invalidnativecontrolnotPASS',
    'model_or_intervention_changed':False,'cuda_calls':0,'optimizer_steps':0}
with (stage/'norm_forensics_result.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps(result))
