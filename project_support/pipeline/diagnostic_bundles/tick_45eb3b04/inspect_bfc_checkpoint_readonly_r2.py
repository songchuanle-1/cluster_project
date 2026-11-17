"""Single fixed BFC full-checkpoint CPU read, explicitly authorized by root.

No model import, CUDA API, GPU query, restart, signal, remote write or ledger write.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess

ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
TOKEN='45eb3b045c6243518d56eade38d5cd17'

def main():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text())
    assert owner['token']==TOKEN and owner['thread_id']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    pre=json.loads((HERE/'bfc_checkpoint_cpu_preflight.json').read_text())['result']
    assert pre['runtime_HEAD']=='48fc302c3c02ffef0b241be3593c386b6b65a72e' and len(pre['same_config_runs'])==1
    run=pre['same_config_runs'][0]['run_directory']
    assert run.endswith('/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc/20261026_003527')
    phase=json.loads((HERE/'original_phase_reconciliation.json').read_text())
    source=next(t['source8'] for t in phase['result']['tasks'] if t['id']=='M213-BFC')
    # Native BFC state-key metadata is a local, already measured reference; no
    # historical checkpoint or tensor is loaded on the local workstation.
    rawpath=ROOT/'pipeline/diagnostic_bundles/tick_336ca5d7/bfc_execution/smoke_candidate_execution.json'
    raw=json.loads(rawpath.read_text())['result']
    inventory=raw['dynamic_parameter_inventory']
    expected={'run':run,'source8':source,'config':pre['original_config'],
      'state_keys':inventory['state_dict_keys'],'parameter_count':inventory['actual_full_model_parameters'],
      'named_parameter_tensors':inventory['actual_named_parameter_tensors'],
      'source_reference':{'path':rawpath.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(rawpath.read_bytes()).hexdigest()}}
    payload=r'''import socket,pathlib,json,hashlib,subprocess,os,sys,resource,ast,importlib.util
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06','Wrong server identity'
EXPECTED=__EXPECTED__
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1').resolve()
run=pathlib.Path(EXPECTED['run']).resolve();checkpoint=run/'last.pth'
assert run.parent.name=='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc' and run.name=='20261026_003527'
assert run.parent.parent==pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints')
def memory():
 return {line.split(':',1)[0]:int(line.split(':',1)[1].split()[0])*1024 for line in pathlib.Path('/proc/meminfo').read_text().splitlines() if line.split(':',1)[0] in ['MemAvailable','MemTotal','SwapFree']}
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def git(*args):return subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True).stdout
head=git('rev-parse','HEAD').decode().strip();assert head=='48fc302c3c02ffef0b241be3593c386b6b65a72e'
before=checkpoint.stat();mem=memory();budget=max(16*1024**3,12*before.st_size+4*1024**3)
assert mem['MemAvailable']>=budget,'Insufficient conservative CPU memory budget; no Torch load'
source_result={}
for rel in list(EXPECTED['source8'])+['framework/dataset/scannetv2.py','tools/train.py']:
 actual=digest(root/rel);committed=hashlib.sha256(git('show',head+':'+rel)).hexdigest()
 assert actual==committed and (rel not in EXPECTED['source8'] or actual==EXPECTED['source8'][rel]),'Exact admitted source mismatch'
 source_result[rel]=actual
assert digest(root/EXPECTED['config'])=='77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea'
assert digest(run/pathlib.Path(EXPECTED['config']).name)==digest(root/EXPECTED['config']),'Original run config lineage mismatch'
checksum=digest(checkpoint)
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import torch
torch.set_num_threads(1)
try:ckpt=torch.load(checkpoint,map_location='cpu',weights_only=False)
except TypeError:ckpt=torch.load(checkpoint,map_location='cpu')
assert isinstance(ckpt,dict)
state=ckpt.get('state_dict',ckpt.get('model'))
assert isinstance(state,dict) and state,'Full model state missing'
keys=list(state);raw_keys=keys[:];stripped_module_prefix=bool(keys) and all(k.startswith('module.') for k in keys)
if stripped_module_prefix:state={k[7:]:v for k,v in state.items()};keys=list(state)
missing=sorted(set(EXPECTED['state_keys'])-set(keys));unexpected=sorted(set(keys)-set(EXPECTED['state_keys']))
records=[];nonfinite=[];devices=set();total=0;dtype_counts={};non_tensor=[]
for key,value in state.items():
 if not isinstance(value,torch.Tensor):non_tensor.append(key);continue
 devices.add(str(value.device));total+=value.numel();dt=str(value.dtype);dtype_counts[dt]=dtype_counts.get(dt,0)+1
 records.append([key,list(value.shape),dt,value.numel()])
 if value.is_floating_point() or value.is_complex():
  if not bool(torch.isfinite(value).all().item()):nonfinite.append(key)
assert not non_tensor and not nonfinite and devices=={'cpu'}
mix='dec.cluster_att.middle_butterfly.mix.weight'
assert mix in state and list(state[mix].shape)==[512,512]
assert 'dec.cluster_att.cluster_ffn.1.0.weight' not in state
optimizer=ckpt.get('optimizer');scheduler=ckpt.get('scheduler')
assert isinstance(optimizer,dict) and optimizer and isinstance(scheduler,dict) and scheduler
groups=optimizer.get('param_groups');states=optimizer.get('state')
assert isinstance(groups,list) and groups and isinstance(states,dict) and states
parameter_ids=[pid for g in groups for pid in g['params']];assert len(parameter_ids)==len(set(parameter_ids)) and set(states)<=set(parameter_ids)
opt_nonfinite=[];shape_bad=[];op_tensors=0;op_elements=0;step_min=None;step_max=None
for pid,value in states.items():
 if not isinstance(value,dict) or not value:shape_bad.append(str(pid)+':empty');continue
 if 'exp_avg' in value and 'exp_avg_sq' in value and value['exp_avg'].shape!=value['exp_avg_sq'].shape:shape_bad.append(str(pid)+':moments')
 for name,t in value.items():
  if isinstance(t,torch.Tensor):
   assert t.device.type=='cpu';op_tensors+=1;op_elements+=t.numel()
   if (t.is_floating_point() or t.is_complex()) and not bool(torch.isfinite(t).all().item()):opt_nonfinite.append(str(pid)+':'+name)
  if name=='step':
   n=float(t.item() if isinstance(t,torch.Tensor) else t);step_min=n if step_min is None else min(step_min,n);step_max=n if step_max is None else max(step_max,n)
assert not opt_nonfinite and not shape_bad
meta=ckpt.get('meta');assert isinstance(meta,dict)
meta_result={};meta_types={}
for key in ['epoch','best_miou','epochs_no_improve']:
 value=meta[key];meta_types[key]=type(value).__module__+'.'+type(value).__name__
 if key=='best_miou':value=float(value);assert __import__('math').isfinite(value)
 else:normalized=int(value);assert normalized==value and normalized>=0;value=normalized
 meta_result[key]=value
assert 1<=meta_result['epoch']<50
after=checkpoint.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns) and digest(checkpoint)==checksum
assert git('rev-parse','HEAD').decode().strip()==head
# Inspect the original save/load implementation text; do not import gorilla or
# instantiate any model. No state/parameter tensor body is serialized in output.
gorilla_spec=importlib.util.find_spec('gorilla');entry=[]
if gorilla_spec and gorilla_spec.submodule_search_locations:
 for file in pathlib.Path(next(iter(gorilla_spec.submodule_search_locations))).rglob('checkpoint.py'):
  text=file.read_text();tree=ast.parse(text)
  for node in tree.body:
   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in ['resume','load_checkpoint','save_checkpoint']:
    segment=ast.get_source_segment(text,node) or ''
    entry.append({'path':str(file),'file_sha256':digest(file),'function':node.name,'line':node.lineno,'end_line':node.end_lineno,
      'explicit_RNG_restore_tokens_present':any(s in segment for s in ['set_rng_state','setstate','random_state','sampler_state']),
      'optimizer_load_state_dict':('optimizer.load_state_dict' in segment),'scheduler_load_state_dict':('scheduler.load_state_dict' in segment)})
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'runtime_HEAD':head,'checkpoint':str(checkpoint),'checkpoint_size_bytes':before.st_size,'checkpoint_mtime_ns':before.st_mtime_ns,'checkpoint_sha256':checksum,'checkpoint_stat_and_hash_stable_across_load':True,'map_location':'cpu','torch_version':str(torch.__version__),'torch_threads':torch.get_num_threads(),'CPU_memory_before':mem,'required_conservative_available_bytes':budget,'CPU_memory_after':memory(),'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'checkpoint_top_level_keys':list(ckpt),'meta':meta_result,'meta_original_types':meta_types,'model_state':{'all_keys_enumerated':True,'all_shapes_enumerated':True,'state_tensor_count':len(records),'keys_match_actual_native_BFC':not missing and not unexpected,'uniform_module_prefix_stripped':stripped_module_prefix,'raw_state_key_count':len(raw_keys),'native_state_key_count':len(EXPECTED['state_keys']),'missing_key_count':len(missing),'unexpected_key_count':len(unexpected),'missing_keys':missing,'unexpected_keys':unexpected,'expected_native_named_parameter_tensors':EXPECTED['named_parameter_tensors'],'expected_native_parameter_count':EXPECTED['parameter_count'],'state_tensor_elements_including_buffers':total,'dtypes':dtype_counts,'devices':sorted(devices),'nonfinite_keys':nonfinite,'key_shape_dtype_numel_sha256':hashlib.sha256(json.dumps(sorted(records),separators=(',',':')).encode()).hexdigest(),'key_shape_scope':'All checkpoint state keys/shapes enumerated and hashed; key set compared to actual native BFC record. No full independent reference shape table/model construction was used.','butterfly_mix_weight_shape':list(state[mix].shape)},'optimizer_state':{'state_count':len(states),'group_count':len(groups),'parameter_ID_count':len(parameter_ids),'state_keys_belong_to_groups':True,'moment_shapes_match':not shape_bad,'all_tensor_state_CPU_and_finite':not opt_nonfinite,'tensor_count':op_tensors,'tensor_elements':op_elements,'step_range':[step_min,step_max],'group_lengths':[len(g['params']) for g in groups],'group_lrs':[float(g['lr']) for g in groups]},'scheduler_state':{'keys':list(scheduler),'last_epoch':scheduler.get('last_epoch'),'base_lrs':scheduler.get('base_lrs'),'_last_lr':scheduler.get('_last_lr')},'source48fc_matches_committed_blob':source_result,'original_run_config_matches_current_mapped_BFC_config':True,'source_key_reference':EXPECTED['source_reference'],'gorilla_save_load_source_metadata':entry,'model_imported_or_constructed':False,'CUDA_or_torch_cuda_API_used':False,'GPU_queried':False,'forward_backward_optimizer_step_or_resume':False,'remote_file_modified':False,'read_only':True}))
'''.replace('__EXPECTED__',repr(expected))
    command='/home/songcl/.conda/envs/project_cluster/bin/python -B -'
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115',command]
    run_result=subprocess.run(args,input=payload,capture_output=True,text=True,encoding='utf8',timeout=180)
    report={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'transport':'SSH_KEY_BATCHMODE_STRICT_KNOWN_HOST',
      'returncode':run_result.returncode,'stderr':run_result.stderr,'result':json.loads(run_result.stdout) if run_result.returncode==0 else None,
      'failure_stdout':run_result.stdout if run_result.returncode else None,'only_BFC_same_original_run_checkpoint_read':True,
      'checkpoint_read_is_not_resume_authorization_or_repair_validation':True}
    path=HERE/'bfc_checkpoint_readonly_evidence_r2.json'
    with path.open('x',encoding='utf8') as out:json.dump(report,out,indent=2,ensure_ascii=False,allow_nan=False);out.write('\n')
    print(json.dumps({'returncode':run_result.returncode,'evidence_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'meta':report['result']['meta'] if report['result'] else None,'error':run_result.stderr if run_result.returncode else None}))

if __name__=='__main__':main()
