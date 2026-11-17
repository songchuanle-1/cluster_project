"""Source-bound aggregation capability evidence; not another failed GPU replay."""
import json
from ops import guard,remote,save,evidence
guard(120)
program=r'''
import os,json,inspect,hashlib,ast
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
from datetime import datetime,timezone
import torch,torch_scatter
path=Path(inspect.getsourcefile(torch_scatter.scatter_mean))
text=path.read_text()
lines=text.splitlines()
indices=[i for i,line in enumerate(lines) if 'atomic operations' in line or 'non-deterministic' in line]
excerpt='\n'.join(lines[max(0,i-1):i+5] for i in [])
excerpt='\n'.join('\n'.join(lines[max(0,i-1):i+5]) for i in indices)
model=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/hier_postprocess.py')
source=model.read_text()
tree=ast.parse(source)
node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='aggregate_cluster')
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'torch_version':torch.__version__,'torch_scatter_version':torch_scatter.__version__,'scatter_source_path':str(path),'scatter_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'atomic_nondeterminism_documented':bool(indices),'source_excerpt':excerpt,'model_source_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'actual_aggregate_cluster':ast.get_source_segment(source,node),'cuda_initialized':torch.cuda.is_initialized(),'gpu_kernel_replays':0,'scope':'Installed native source documents atomic nondeterminism;consistent with observed1.907e-6 reaggregation mismatch,but does NOT isolate or prove its cause. Original1e-6gate remains FAILED;no numerical threshold or native model changed.'}))
'''
value=remote('server-4',program,timeout=100,conda=True)
path=save('native_aggregation_source_binding.json',value)
print(json.dumps({'evidence':evidence(path),'data':value.get('data'),'returncode':value['returncode'],'stderr':value['stderr'][-1000:]},ensure_ascii=False,indent=2))
