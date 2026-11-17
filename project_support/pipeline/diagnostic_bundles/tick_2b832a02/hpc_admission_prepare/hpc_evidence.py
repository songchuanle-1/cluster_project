"""HPC-specific reviewed-evidence gate; default disabled, no import operations."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,os,sys
SCRIPT=Path(__file__).resolve().parent;TICK=SCRIPT.parent
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard
DRAFT_EXECUTION_DISABLED=True
CID='hierarchy-tree-resolvent-nonlinear-composition';EXP='M218-HPC'
BASE='d58576b396cfb54577652be972f3ffaffda508c9';COMMIT='6282263d805c1741234f97afc981a05aca2ad6e3'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
CONFIG='configs/Quard/ctf_hcg_csort_hpc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hpc.yaml'
PAIRS=[('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')]
EXE=TICK/'hpc_execution'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p).resolve();assert p.is_relative_to(ROOT.resolve());return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def require_execution():
 if DRAFT_EXECUTION_DISABLED:raise RuntimeError('DRAFT_DISABLED: materialize a reviewed root-only copy and bind the actual independent review first')
 guard();assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
 independent_ref()
def independent_ref():
 e=read(SCRIPT/'evidence_bindings.json')['independent_review']
 assert isinstance(e,dict) and isinstance(e.get('sha256'),str) and len(e['sha256'])==64,'Actual independent review SHA is missing'
 p=(ROOT/e['path']).resolve();assert p.is_relative_to(TICK.resolve()) and p.name=='hpc_actual_independent_review.json'
 assert sha(p)==e['sha256'];return e

def reviewed():
 guard();peer_ref=independent_ref();peer=read(ROOT/peer_ref['path'])
 assert peer['status']=='FOUR_ACTUAL_HPC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
 assert peer['candidate_id']==CID and peer['code_commit']==COMMIT and peer['goal_sha256']==GOAL and peer['material_concerns']==[]
 assert len(peer['raw_results'])==4
 m=read(EXE/'native_manifest.json');b=read(EXE/'execution_binding.json');lease=read(EXE/'execution_lease.json')
 assert b['owner']==EXPECTED and set(b['owner'])==set(EXPECTED) and b['physical_gpu']==0 and b['runtime_code_commit']==BASE
 assert b['candidate_id']==CID and b['code_commit']==COMMIT and b['native_manifest_sha256']==sha(EXE/'native_manifest.json') and b['execution_lease_sha256']==sha(EXE/'execution_lease.json')
 assert b['frozen_preparation_sha256']=='ab13cba6418ab9ba733e2b0ecfbe203a220b4b472346623a3835ce11803593b3' and b['frozen_template_sha256']=='4198b93f7118c83111455e08439ab86250dddb88b64cccf06d4197d984c95736'
 assert m['source_preparation_sha256']=='c94f9c289dbf92019d01d3674907a4765368fa3849160ff8268f7788f921a70c'
 assert m['candidate_id']==CID and m['code_commit']==COMMIT and m['config']==CONFIG and m['goal_sha256']==GOAL and m['runtime_code_commit']==BASE
 assert m['current_token']==EXPECTED['token'] and m['physical_gpu']==0 and m['allowed_gpus']==[0] and m['context_sha256']==EXPECTED['context_sha256'] and m['pending_sha256']==EXPECTED['pending_sha256'] and m['deadline_at']==EXPECTED['deadline_at']
 assert m['gpu_uuid']==b['gpu_uuid']==lease['gpu_uuid']=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
 assert lease['native_manifest_sha256']==sha(EXE/'native_manifest.json') and lease['token']==EXPECTED['token'] and lease['context_sha256']==EXPECTED['context_sha256'] and lease['pending_sha256']==EXPECTED['pending_sha256']
 results={};refs=[]
 for mode,target in PAIRS:
  path=EXE/(mode+'_'+target+'_execution.json');env=read(path);raw=env['result'];request=read(EXE/(mode+'_'+target+'_request.json'))
  matches=[x for x in peer['raw_results'] if (x['mode'],x['target'])==(mode,target)];assert len(matches)==1;x=matches[0]
  assert x['execution_path']==ref(path)['path'] and x['execution_sha256']==sha(path) and x['request_id']==request['request_id']==env['identity']['request_id'] and x['result_sha256']==env['result_sha256']
  assert all(env['identity'].get(k)==value for k,value in request.items() if k not in ['mode','target'])
  assert raw['source_preparation_sha256']==m['source_preparation_sha256'] and raw['diagnostic_worker_sha256']==m['diagnostic_files']['worker.py']=='bff46bdc79d98dc5275bb140a5bf901ca709b3966339f28dc5e5586ee9736cbf' and raw['runtime_sha256']==m['diagnostic_files']['native_runtime.py']=='958817cdb40361683a496a64cac641ba95c5d6e52ad9059d0c1baef4325ba947'
  assert env['certainty']=='terminal' and env['returncode']==0 and raw['execution_completed'] is True
  assert all(raw[k]==value for k,value in {'candidate_id':CID,'code_commit':COMMIT,'goal_sha256':GOAL,'mode':mode,'target':target,'current_token':EXPECTED['token'],'physical_gpu':0,'native_manifest_sha256':sha(EXE/'native_manifest.json'),'context_sha256':EXPECTED['context_sha256'],'pending_sha256':EXPECTED['pending_sha256'],'deadline_at':EXPECTED['deadline_at']}.items())
  assert raw['native_model_and_yaml_unchanged'] is True and raw['config_sha256']==m['candidate_config_sha256'] and raw['stage']==b['stage'] and raw['gpu_uuid']==b['gpu_uuid']
  assert raw['source_hashes']==(m['candidate_source_hashes'] if target=='candidate' else m['assets']['source_hashes'])
  results[mode+'_'+target]=raw;refs.append(ref(path))
 champion=results['smoke_champion'];candidate=results['smoke_candidate']
 assert champion['batches']==candidate['batches'] and champion['common_initialized_parameters']==candidate['common_initialized_parameters'] and champion['initialization']==candidate['initialization']
 for raw in [champion,candidate]:
  assert raw['optimizer_steps']==raw['native_loss_forwards']==raw['native_criterion_backwards']==2 and len(raw['steps'])==len(raw['losses'])==len(raw['batches'])==2
  assert all(math.isfinite(x) for x in raw['losses'])
  assert all(raw[k] is True for k in ['native_data_loaded','native_train_function_executed','backward_finite','intended_path_observed','native_smoke_checks_passed','native_tracked_each_module_updated','wrappers_and_hooks_restored'])
 assert len(candidate['HPC_resolvent_observations'])==2 and candidate['new_operator_parameters']==0
 for raw in (champion,candidate):
  assert raw['full_named_parameter_initialization']==raw['common_initialized_parameters'] and len(raw['ffn_calls'])==6
 for observed in candidate['HPC_resolvent_observations']:
  assert observed['original_prepare_calls']==1 and observed['original_two_solver_calls']==2 and observed['actual_three_LN_calls']==observed['actual_three_FFN_calls']==[1,1,1] and observed['actual_cross_level_component_exercised'] is True
  assert [x['phase'] for x in observed['solver_calls']]==['analysis','synthesis']
 for raw in [results['resources_champion'],results['resources_candidate']]:
  assert (raw['batch_size'],raw['lang_num_max'],raw['warmup'],raw['repeat'],raw['native_predict_calls'])==(1,1,20,100,121)
  assert len(raw['measurements_ms'])==100 and all(math.isfinite(x) and x>0 for x in raw['measurements_ms'])
  assert raw['source_body_executed_without_replacement'] is True and raw['parameter_flags_preserved'] is True and raw['profile']['flops']<=10e9 and raw['profile']['within10G'] is True
 a,c=results['resources_champion'],results['resources_candidate']
 assert all(a[k]==c[k] for k in ['input_sha256','scan_ids','ann_ids','initialization']) and a['profile']['profiler_file_sha256']==c['profile']['profiler_file_sha256']
 refs.extend(ref(EXE/n) for n in ['native_manifest.json','execution_binding.json','execution_lease.json']);refs.append(peer_ref)
 return m,results,refs

def review_ref():
 e=read(TICK/'hpc_summary_outputs.json')['review'];assert sha(ROOT/e['path'])==e['sha256'];return e
