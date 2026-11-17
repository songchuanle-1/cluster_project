"""Inspect the original CPA checkpoints without CUDA or remote mutation."""
from ops import *

guard(240)
program = r'''import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import json,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
import torch
root=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
stage=Path('/data/songcl/Project/Cluster_project/pipeline/cpa_explore_72695a5d')
manifest=json.loads((stage/'runtime_manifest.json').read_text())
cpdir=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1/20261019_093003')
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def summarize(value,depth=0):
 if isinstance(value,torch.Tensor):
  return {'type':'tensor','shape':list(value.shape),'dtype':str(value.dtype),'device':str(value.device),'scalar':value.item() if value.numel()==1 else None}
 if isinstance(value,(int,float,str,bool)) or value is None:return value
 if isinstance(value,dict):
  if depth>2:return {'type':'dict','count':len(value),'keys':[str(k) for k in value.keys()][:30]}
  return {str(k):summarize(v,depth+1) for k,v in list(value.items())[:40]}
 if isinstance(value,(list,tuple)):
  return [summarize(v,depth+1) for v in value[:15]] if len(value)<=15 else {'type':type(value).__name__,'count':len(value)}
 return {'type':type(value).__name__}
def state_summary(value):
 if not isinstance(value,dict):return summarize(value)
 result={'keys':[str(k) for k in value]}
 if 'state' in value:
  states=value['state'];result['state_entries']=len(states)
  if states:
   first=next(iter(states.values()));result['first_state']=summarize(first)
   result['step_range']=[min(float(x['step']) for x in states.values() if 'step' in x),max(float(x['step']) for x in states.values() if 'step' in x)] if any('step' in x for x in states.values()) else None
 if 'param_groups' in value:
  result['param_groups']=[{k:summarize(v) for k,v in group.items() if k!='params'}|{'parameter_count':len(group['params'])} for group in value['param_groups']]
 for key in value:
  if key not in ('state','param_groups'):result[key]=summarize(value[key])
 return result
records={}
for name in ('last.pth','best.pth'):
 path=cpdir/name;before=path.stat();digest=sha(path)
 checkpoint=torch.load(str(path),map_location='cpu',weights_only=False,mmap=True)
 record={'path':str(path),'bytes':before.st_size,'mtime_ns':before.st_mtime_ns,'sha256':digest,'keys':list(checkpoint),'metadata':{},'states':{}}
 for key,value in checkpoint.items():
  if isinstance(value,dict) and any(isinstance(v,torch.Tensor) for v in value.values()):
   tensors=[v for v in value.values() if isinstance(v,torch.Tensor)]
   record['states'][key]={'tensor_count':len(tensors),'numel':sum(v.numel() for v in tensors),'devices':sorted(set(str(v.device) for v in tensors))}
  elif any(word in key.lower() for word in ('optim','sched')):record['states'][key]=state_summary(value)
  else:record['metadata'][key]=summarize(value)
 after=path.stat();record['stable_during_read']=before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns
 records[name]=record
 del checkpoint
source=root/'tools/train.py';lines=source.read_text().splitlines()
selected=set()
for i,line in enumerate(lines):
 if any(term in line for term in ('resume','checkpoint','best_','patience','scheduler.step')):
  selected.update(range(max(0,i-3),min(len(lines),i+6)))
source_excerpt=[{'line':i+1,'text':lines[i]} for i in sorted(selected)]
spec=importlib.util.find_spec('gorilla')
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'torch_version':torch.__version__,'cuda_visible_devices':os.environ['CUDA_VISIBLE_DEVICES'],'cuda_initialized':torch.cuda.is_initialized(),'checkpoints':records,'runtime_files':{p:{'expected_sha256':v,'actual_sha256':sha(root/p),'unchanged':sha(root/p)==v} for p,v in manifest['runtime_files'].items()},'train_source_excerpt':source_excerpt,'gorilla_spec_origin':spec.origin if spec else None,'remote_writes':0,'training_launches':0},allow_nan=False))
'''
activation='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster'
command=activation+' && '+shlex.join(['python','-B','-c',program])
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],timeout=240)
if result.returncode:
    save('checkpoint_cpu_error.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'returncode':result.returncode,'stdout':result.stdout[-4000:],'stderr':result.stderr[-6000:]})
    raise RuntimeError(result.stderr[-3000:])
data=json.loads(result.stdout)
assert not data['cuda_initialized'] and all(x['stable_during_read'] for x in data['checkpoints'].values())
assert all(x['unchanged'] for x in data['runtime_files'].values())
save('checkpoint_cpu.json',data)
advance([OUT/'checkpoint_cpu.json',OUT/'inspect_checkpoint_cpu.py'])
print(json.dumps({k:v for k,v in data.items() if k not in ('runtime_files','train_source_excerpt')},ensure_ascii=True,indent=2))
