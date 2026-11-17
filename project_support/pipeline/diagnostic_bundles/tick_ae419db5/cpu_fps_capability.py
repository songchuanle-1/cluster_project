"""Check the original binary CPU branch once before declaring CUDA necessary."""
import json
from ops import ROOT, OUT, CID, guard, remote, save, evidence, tick, now

guard(180)
program = r'''
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1')
import hashlib,importlib,json,sys
from pathlib import Path
import torch
torch.set_num_threads(1)
root=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
sys.path[:0]=[str(root),str(root/'framework/lib')]
from tools import train
module=importlib.import_module('pointnet2.pointnet2_utils')
backend=importlib.import_module('pointnet2._ext')
cpp=root/'pointnet2/_ext_src/src/sampling.cpp'
source=cpp.read_text().splitlines()
result={'source_cpu_branch_excerpt':'\n'.join(str(i+1)+':'+source[i] for i in range(69,min(95,len(source)))),
 'wrapper_path':str(Path(module.__file__).resolve()),
 'binary_sha256':hashlib.sha256(Path(backend.__file__).read_bytes()).hexdigest(),
 'cpu_fps_supported':False,'native_model_mask_test':False}
try:
 inputs=torch.tensor([[[0.,0.,0.],[1.,0.,0.],[0.,2.,0.]]],dtype=torch.float32)
 indices=module.FurthestPointSampling.apply(inputs,2)
 result.update(cpu_fps_supported=True,indices=indices.tolist(),device=str(indices.device))
except Exception as error:
 result.update(error_type=type(error).__name__,error=str(error))
assert not torch.cuda.is_initialized()
result['cuda_initialized']=False
print(json.dumps(result))
'''
result = remote(program, timeout=120, conda=True)
path = save('native_cpu_fps_capability.json', {'observed_at': now(), **result,
    'scope': 'One original binary CPU capability probe,not full geometry/mask/efficacy;do not treat a no-CUDA support error as hypothesis failure.'})
work = tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(row for row in work['candidates'] if row['id'] == CID)
candidate['evidence'].append(evidence(path))
candidate['updated_at'] = now()
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
print(json.dumps(result, indent=2))
