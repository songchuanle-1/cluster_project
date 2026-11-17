"""DCE-specific reviewed-evidence gate; default disabled, no import operations."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,os,sys,re
SCRIPT=Path(__file__).resolve().parent;TICK=SCRIPT.parent
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard
DRAFT_EXECUTION_DISABLED=True
CID='hierarchy-directed-cavity-edge-composition';EXP='M220-DCE'
BASE='d0e2f95712ed16446907706fbf6a65d34996a9ad'
SOURCE_BINDINGS=json.loads((SCRIPT/'source_bindings.json').read_text('utf8'));COMMIT=SOURCE_BINDINGS.get('code_commit')
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
CONFIG='configs/Quard/ctf_hcg_csort_dce/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_dce.yaml'
PAIRS=[('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')]
EXE=TICK/'dce_execution'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p).resolve();assert p.is_relative_to(ROOT.resolve());return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def require_execution():
 if DRAFT_EXECUTION_DISABLED:raise RuntimeError('DRAFT_DISABLED: materialize a reviewed root-only copy and bind the actual independent review first')
 bound_source();guard();assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
 independent_ref()
def independent_ref():
 e=read(SCRIPT/'evidence_bindings.json')['independent_review']
 assert isinstance(e,dict) and isinstance(e.get('sha256'),str) and len(e['sha256'])==64,'Actual independent review SHA is missing'
 p=(ROOT/e['path']).resolve();assert p.is_relative_to(TICK.resolve()) and p.name=='dce_actual_independent_review.json'
 assert sha(p)==e['sha256'];return e

def bound_source():
 assert isinstance(COMMIT,str) and re.fullmatch(r'[0-9a-f]{40}',COMMIT),'Actual compatible source commit is missing'
 assert SOURCE_BINDINGS['parent_commit']==BASE
 assert SOURCE_BINDINGS['original_source_preparation']['sha256']=='44e75f7c33e15d049716b8b477a601e8fbbc74a226c13a5552ace927a3e3ed5e' and SOURCE_BINDINGS['native_protocol']['sha256']=='4b3c658abb4687b38cde3788de8f4c46687c96b76c66563d6fdbe47bb3714f58'
 for name in ('native_preparation','manifest_template','source_version','original_source_preparation','native_protocol'):
  value=SOURCE_BINDINGS.get(name);assert isinstance(value,dict) and re.fullmatch(r'[0-9a-f]{64}',str(value.get('sha256',''))),name+' actual reference missing'
  path=(ROOT/value['path']).resolve();assert path.is_relative_to(ROOT.resolve()) and sha(path)==value['sha256'],name
 version=read(ROOT/SOURCE_BINDINGS['source_version']['path'])
 assert version['code_commit']==COMMIT and version['parent_commit']==BASE and version['diff_exact9A'] is True
 native=read(ROOT/SOURCE_BINDINGS['native_preparation']['path'])
 assert native['source_commit']==COMMIT and native['source_parent_commit']==BASE and native['source_preparation']['sha256']=='44e75f7c33e15d049716b8b477a601e8fbbc74a226c13a5552ace927a3e3ed5e'
 assert native['source_files']==version['frozen_source_files'] and len(native['source_files'])==9
 native_dir=(ROOT/SOURCE_BINDINGS['native_preparation']['path']).parent.resolve()
 for name,h in native['prepared_file_hashes'].items():
  path=(native_dir/name).resolve();assert path.is_relative_to(native_dir) and sha(path)==h
 assert native['manifest_template']==SOURCE_BINDINGS['manifest_template']
 return native

def reviewed():
 native=bound_source();guard();peer_ref=independent_ref();peer=read(ROOT/peer_ref['path'])
 assert peer['status']=='FOUR_ACTUAL_DCE_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
 assert peer['candidate_id']==CID and peer['code_commit']==COMMIT and peer['goal_sha256']==GOAL and peer['material_concerns']==[]
 assert len(peer['raw_results'])==4
 m=read(EXE/'native_manifest.json');b=read(EXE/'execution_binding.json');lease=read(EXE/'execution_lease.json')
 assert b['owner']==EXPECTED and set(b['owner'])==set(EXPECTED) and b['physical_gpu']==0 and b['runtime_code_commit']==BASE
 assert b['candidate_id']==CID and b['code_commit']==COMMIT and b['native_manifest_sha256']==sha(EXE/'native_manifest.json') and b['execution_lease_sha256']==sha(EXE/'execution_lease.json')
 assert b['frozen_preparation_sha256']==SOURCE_BINDINGS['native_preparation']['sha256'] and b['frozen_template_sha256']==SOURCE_BINDINGS['manifest_template']['sha256']
 assert m['source_preparation_sha256']=='44e75f7c33e15d049716b8b477a601e8fbbc74a226c13a5552ace927a3e3ed5e'
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
  assert raw['source_preparation_sha256']==m['source_preparation_sha256'] and raw['diagnostic_worker_sha256']==m['diagnostic_files']['worker.py']==native['prepared_file_hashes']['worker.py'] and raw['runtime_sha256']==m['diagnostic_files']['native_runtime.py']==native['prepared_file_hashes']['native_runtime.py']
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
 expected_excluded=['dec.cluster_att.cluster_ffn.0.','dec.cluster_att.cluster_ffn.1.','dec.cluster_att.cluster_ffn.2.','dec.cluster_att.cavity.']
 assert candidate['common_initialized_parameters']['excluded_name_prefixes']==expected_excluded
 assert set(candidate['common_initialized_parameters']['shapes'])==set(candidate['common_initialized_parameters']['names'])
 # Whole-cavity aggregation and exact observation fields are verified by the actual
 # immutable DCE worker plus SHA-bound independent semantic reviewer. Individual
 # map/edge/row positivity or each-map update is deliberately not a promotion gate.
 assert candidate['native_tracked_each_module_updated'] is True
 assert len(candidate['DCE_directed_cavity_observations'])==2
 for observed in candidate['DCE_directed_cavity_observations']:
  assert observed['actual_true_fine_paths']>0 and observed['actual_map_calls']==observed['actual_GELU_calls']==6 and observed['actual_private_mean_calls']==observed['actual_exclusive_calls']==2 and observed['actual_three_LN_calls']==[1,1,1]
 for step in candidate['steps']:
  gradient=step['whole_cavity_weight_gradient'];assert gradient['finite'] and gradient['abs_max']>0
  assert step['whole_cavity_weight_updated'] is True and step['whole_cavity_module_updated'] is True
 for raw in [results['resources_champion'],results['resources_candidate']]:
  assert (raw['batch_size'],raw['lang_num_max'],raw['warmup'],raw['repeat'],raw['native_predict_calls'])==(1,1,20,100,121)
  assert len(raw['measurements_ms'])==100 and all(math.isfinite(x) and x>0 for x in raw['measurements_ms'])
  assert raw['source_body_executed_without_replacement'] is True and raw['parameter_flags_preserved'] is True and raw['profile']['flops']<=10e9 and raw['profile']['within10G'] is True
 a,c=results['resources_champion'],results['resources_candidate']
 assert all(a[k]==c[k] for k in ['input_sha256','scan_ids','ann_ids','initialization']) and a['profile']['profiler_file_sha256']==c['profile']['profiler_file_sha256']
 refs.extend(ref(EXE/n) for n in ['native_manifest.json','execution_binding.json','execution_lease.json']);refs.append(peer_ref)
 return m,results,refs

def review_ref():
 e=read(TICK/'dce_summary_outputs.json')['review'];assert sha(ROOT/e['path'])==e['sha256'];return e
