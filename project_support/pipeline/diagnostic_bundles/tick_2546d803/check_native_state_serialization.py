"""CPU proof of native checkpoint serialization versus Module.state_dict."""
from ops import *

guard(240)
advance([OUT/'resume_progress_verification.json'],next_action='Investigate the stopped pre-training observer mismatch using the exact native CPU serializer;preserve failure and do not relaunch blindly.')
manifest=tick.load(OUT/'runtime_manifest.json')
program=r'''import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
import ast,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
root=Path(MANIFEST['root']);os.chdir(root);sys.path[:0]=[str(root),str(root/'framework/lib')]
from tools import train
from gorilla.solver.checkpoint import get_state_dict
torch=train.torch;torch.set_num_threads(2)
assert not torch.cuda.is_initialized()
checkpoint=torch.load(MANIFEST['checkpoint'],map_location='cpu',weights_only=False,mmap=True)
cfg=train.gorilla.Config.fromfile(MANIFEST['config'])
model=train.resolve_network(MANIFEST['config'])(**cfg.model)
assert not torch.cuda.is_initialized()
ordinary=model.state_dict();saved=checkpoint['model']
extra=sorted(set(saved)-set(ordinary));missing=sorted(set(ordinary)-set(saved))
details={}
for key in extra:
 module_name,buffer_name=key.rsplit('.',1);module=model.get_submodule(module_name)
 value=getattr(module,buffer_name)
 details[key]={'registered_buffer':buffer_name in module._buffers,'nonpersistent':buffer_name in module._non_persistent_buffers_set,'is_parameter':key in dict(model.named_parameters()),'matches_saved_value_before_load':torch.equal(value.cpu(),saved[key]),'shape':list(value.shape),'dtype':str(value.dtype)}
optimizer=train.gorilla.build_optimizer(model,cfg.optimizer)
scheduler=train.gorilla.build_lr_scheduler(optimizer,cfg.lr_scheduler)
meta=train.gorilla.resume(model=model,filename=MANIFEST['checkpoint'],optimizer=optimizer,scheduler=scheduler,strict=False,map_location='cpu')
native=get_state_dict(model)
state_key_equal=set(native)==set(saved)
different=[key for key in set(native)&set(saved) if not torch.equal(native[key],saved[key])]
optimizer_actual=optimizer.state_dict();optimizer_expected=checkpoint['optimizer']
optimizer_different=[]
for index,state in optimizer_expected['state'].items():
 for key,value in state.items():
  actual=optimizer_actual['state'][index][key]
  equal=torch.equal(actual,value) if isinstance(value,torch.Tensor) else actual==value
  if not equal:optimizer_different.append(str(index)+'.'+key)
scheduler_equal=all(scheduler.state_dict()[key]==value for key,value in checkpoint['scheduler'].items())
source_path=Path('/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/gorilla/solver/checkpoint.py')
source=source_path.read_text();tree=ast.parse(source)
functions=[{'name':node.name,'source':ast.get_source_segment(source,node)} for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name in ('get_state_dict','_save_to_state_dict')]
assert extra==['text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'] and not missing
assert all(value['registered_buffer'] and value['nonpersistent'] and not value['is_parameter'] and value['matches_saved_value_before_load'] for value in details.values())
assert state_key_equal and not different and not optimizer_different and scheduler_equal
assert not torch.cuda.is_initialized()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'ordinary_state_count':len(ordinary),'native_saved_state_count':len(saved),'native_restored_state_count':len(native),'ordinary_omitted_buffers':details,'missing_saved_keys':missing,'native_key_sets_equal':state_key_equal,'native_tensor_mismatches':different,'all_native_saved_tensors_equal':not different and state_key_equal,'optimizer_state_entries':len(optimizer_actual['state']),'optimizer_tensor_mismatches':optimizer_different,'scheduler_equal':scheduler_equal,'restored_metadata':{'epoch':int(meta['epoch']),'best_miou':float(meta['best_miou']),'epochs_no_improve':int(meta['epochs_no_improve'])},'native_serializer_source_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),'serializer_functions':functions,'cuda_initialized':torch.cuda.is_initialized(),'native_optimizer_steps':0,'training_launches':0,'model_or_config_changed':False,'diagnosis':'Operational observer compared Module.state_dict with the different native save serializer;exact two omitted nonpersistent nonlearned buffers also match saved values. Full native serialized model/optimizer/scheduler CPU equality passes. No model incompatibility or scientific gate conclusion.'}))
'''
program='MANIFEST='+repr(manifest)+'\n'+program
result=ssh(program,conda=True,timeout=240)
save('native_serialization_cpu_proof.json',result)
advance([OUT/'native_serialization_cpu_proof.json',OUT/'check_native_state_serialization.py'])
print(json.dumps({k:v for k,v in result.items() if k!='serializer_functions'},ensure_ascii=True,indent=2))
