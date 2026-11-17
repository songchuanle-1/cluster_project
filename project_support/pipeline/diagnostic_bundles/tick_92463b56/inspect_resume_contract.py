"""Check checkpoint integrity and the installed native resume contract on CPU."""
from ops import *

guard(240)
program=r'''import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import ast,hashlib,json,importlib.util
from pathlib import Path
from datetime import datetime,timezone
import torch
torch.set_num_threads(2)
path=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1/20261019_093003/last.pth')
checkpoint=torch.load(path,map_location='cpu',weights_only=False,mmap=True)
meta=checkpoint['meta']
metadata={'epoch':int(meta['epoch']),'best_miou':float(meta['best_miou']),'epochs_no_improve':int(meta['epochs_no_improve']),'saved_at_native':meta['time']}
failed=[];counts={}
for category in ('model','optimizer'):
 checked=0;elements=0
 values=checkpoint['model'].items() if category=='model' else ((str(k)+'.'+str(key),tensor) for k,value in checkpoint['optimizer']['state'].items() for key,tensor in value.items())
 for name,value in values:
  if isinstance(value,torch.Tensor):
   checked+=1;elements+=value.numel()
   if value.is_floating_point() and not bool(torch.isfinite(value).all()):failed.append(category+'.'+name)
 counts[category]={'tensor_count':checked,'numel':elements,'all_finite':not any(x.startswith(category+'.') for x in failed)}
origin=Path(importlib.util.find_spec('gorilla').origin).parent
functions=[]
for file in sorted(origin.rglob('*checkpoint*.py')):
 source=file.read_text();tree=ast.parse(source)
 for node in ast.walk(tree):
  if isinstance(node,ast.FunctionDef) and node.name in ('resume','save_checkpoint'):
   functions.append({'path':str(file),'file_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'name':node.name,'line':node.lineno,'source':ast.get_source_segment(source,node)})
assert any(x['name']=='resume' for x in functions)
native=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1/20261019_093003/20261019_093003.log')
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'metadata':metadata,'finiteness':counts,'nonfinite_tensors':failed,'resume_functions':functions,'scheduler_state':checkpoint['scheduler'],'rng_state_present':any('rng' in key.lower() or 'random' in key.lower() for key in checkpoint),'exact_mid_epoch_replay':False,'planned_start_epoch':metadata['epoch']+1,'native_log':{'path':str(native),'sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'bytes':native.stat().st_size},'cuda_initialized':torch.cuda.is_initialized(),'training_launches':0,'remote_writes':0}))
'''
activation='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster'
command=activation+' && '+shlex.join(['python','-B','-c',program])
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],timeout=240)
assert result.returncode==0,result.stderr[-3000:]
data=json.loads(result.stdout)
assert data['metadata']['epoch']==5 and not data['cuda_initialized']
assert not data['nonfinite_tensors']
save('resume_contract_cpu.json',data)
native=OUT/'native_training.log'
guard(60)
assert not native.exists()
copy=run(['scp',*SSH,'songcl@192.168.1.115:'+data['native_log']['path'],str(native)],timeout=60)
assert copy.returncode==0,copy.stderr[-3000:]
assert tick.digest(native)==data['native_log']['sha256']
advance([OUT/'resume_contract_cpu.json',OUT/'inspect_resume_contract.py',native])
print(json.dumps({'metadata':data['metadata'],'finiteness':data['finiteness'],'rng_state_present':data['rng_state_present'],'planned_start_epoch':data['planned_start_epoch'],'native_log_hash_verified':True,'resume_functions':data['resume_functions']},ensure_ascii=True,indent=2))
