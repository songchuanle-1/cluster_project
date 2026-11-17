"""Project-local actual-result summaries. No GPU, source or queue operation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, statistics, subprocess, sys
from anchor_bfc_packet import guard, ROOT, EXPECTED

HERE=Path(__file__).resolve().parent
EXE=HERE/'aef_execution'
CID='hierarchy-parent-antisymmetric-edge-flux'
EXP='M216-AEF'
COMMIT='56b2a96dc48cc8a88f0f7105527ef448113b1060'
BASE='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
CONFIG='configs/Quard/ctf_hcg_csort_aef/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aef.yaml'
PAIRS=[('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')]
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def git(*a):return subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
def finite(v):
 if isinstance(v,dict):
  if 'finite' in v:assert v['finite'] is True and v.get('nonfinite_count',0)==0
  for x in v.values():finite(x)
 elif isinstance(v,list):
  for x in v:finite(x)
def main():
 guard();m=read(EXE/'native_manifest.json');b=read(EXE/'execution_binding.json');raw={};refs=[]
 assert b['owner']==EXPECTED and b['physical_gpu']==0 and b['runtime_code_commit']==BASE
 assert m['code_commit']==COMMIT and m['candidate_id']==CID and m['goal_sha256']==GOAL
 assert m['current_token']==EXPECTED['token'] and m['allowed_gpus']==[0] and m['physical_gpu']==0
 assert b['native_manifest_sha256']==sha(EXE/'native_manifest.json')
 for mode,target in PAIRS:
  p=EXE/f'{mode}_{target}_execution.json';e=read(p);r=e['result'];q=read(EXE/f'{mode}_{target}_request.json')
  assert e['certainty']=='terminal' and e['returncode']==0 and r['execution_completed'] is True
  assert e['identity']['request_id']==q['request_id']
  assert all(r[k]==v for k,v in {'candidate_id':CID,'code_commit':COMMIT,'goal_sha256':GOAL,'mode':mode,'target':target,'current_token':EXPECTED['token'],'physical_gpu':0,'native_manifest_sha256':sha(EXE/'native_manifest.json')}.items())
  assert r['gpu_uuid']==b['gpu_uuid'] and r['stage']==b['stage']
  assert r['native_model_and_yaml_unchanged'] is True and r['config_sha256']==m['candidate_config_sha256']
  if target=='candidate':assert r['source_hashes']==m['candidate_source_hashes']
  assert hashlib.sha256(json.dumps(r,indent=2,allow_nan=False).encode()).hexdigest()==e['result_sha256']
  raw[mode+'_'+target]=r;refs.append(ref(p))
 sc=raw['smoke_champion'];s=raw['smoke_candidate'];rc=raw['resources_champion'];r=raw['resources_candidate']
 assert sc['common_initialized_parameters']==s['common_initialized_parameters']
 assert sc['batches']==s['batches'] and sc['initialization']==s['initialization']
 assert s['initialization']['kind']=='native_train_pretrain' and s['initialization']['seed']==1999 and s['initialization']['trained_m95_checkpoint_loaded'] is False
 for target,x in [('champion',sc),('candidate',s)]:
  assert x['optimizer_steps']==x['native_loss_forwards']==x['native_criterion_backwards']==2
  assert len(x['losses'])==len(x['steps'])==len(x['batches'])==len(x['native_backward_records'])==2
  assert all(math.isfinite(z) for z in x['losses'])
  assert all(x[k] is True for k in ['native_data_loaded','native_train_function_executed','native_smoke_checks_passed','backward_finite','intended_path_observed','wrappers_and_hooks_restored','native_tracked_each_module_updated'])
  assert len(x['ffn_calls'])==(6 if target=='champion' else 4)
  assert len(x['AEF_flux_observations'])==(0 if target=='champion' else 2)
  for k in ['raw_bank_observations','hcg_readbacks','inst_to_mask_path_observations']:assert len(x[k])==2
  assert len(x['csort_raw_input_observations'])==4
  for step in x['steps']:
   assert step['all_observed_gradients_finite'] is True and step['optimizer_step_completed'] is True
   finite(step['tracked_module_gradients'])
  for z in x['raw_bank_observations']:assert all(z[k] is True for k in ['unchanged_after_full_forward','ids_unchanged_after_full_forward','maps_unchanged_after_full_forward'])
  for z in x['csort_raw_input_observations']:assert z['original_raw_objects'] is True and z['original_childmap_object'] is True
  for z in x['inst_to_mask_path_observations']:assert z['single_native_inst_update_exact'] is True
 for step in s['steps']:
  assert set(step['native_parameter_block_gradients'])=={'left_input','right_input'}
  for k,z in step['native_parameter_block_gradients'].items():
   assert z['finite'] is True and z['nonfinite_count']==0 and z['abs_max']>0
   assert step['parameter_block_before_step_hash'][k]!=step['parameter_block_after_step_hash'][k]
  for k in ['ffn_0','ffn_2','edge_map']:assert step['module_before_step_hash'][k]!=step['module_after_step_hash'][k]
 for z in s['AEF_flux_observations']:
  assert z['actual_real_mst_edges']>0 and z['original_middle_norm_calls']==z['original_flux_forward_calls']==z['actual_shared_map_calls']==z['actual_original_GELU_calls']==1
  assert z['actual_signed_scatter_calls']==2
  assert all(z[k] is True for k in ['original_ID_signed_scatter_observed','returned_original_bank_shape','unsupported_and_batch_padding_update_zero','final_output_is_actual_signed_scatter_reshape'])
 for z in s['hcg_readbacks']:assert z['AEF_middle_original_skip_and_exact_HCG_input'] is True
 for k in ['input_sha256','scan_ids','ann_ids','initialization']:assert rc[k]==r[k]
 for x in [rc,r]:
  assert (x['batch_size'],x['lang_num_max'],x['warmup'],x['repeat'],x['native_predict_calls'])==(1,1,20,100,121)
  a=x['measurements_ms'];assert len(a)==100 and all(math.isfinite(z) and z>0 for z in a)
  assert statistics.median(a)==x['median_ms']
  assert x['profile']['flops']<=10e9 and x['profile']['within10G'] is True
  assert x['source_body_executed_without_replacement'] is True and x['parameter_flags_preserved'] is True
 assert rc['profile']['profiler_file_sha256']==r['profile']['profiler_file_sha256']
 assert r['peak_allocated_bytes']<=rc['peak_allocated_bytes']*1.15
 paths={'framework/model/Quard_model/'+m['candidate_name']+'/'+k:v for k,v in m['candidate_source_hashes'].items()};paths[CONFIG]=m['candidate_config_sha256']
 assert len(paths)==9 and git('show','-s','--format=%P',COMMIT).decode().strip()==BASE
 assert set(git('diff-tree','--no-commit-id','--name-status','-r',COMMIT).decode().splitlines())=={'A\t'+k for k in paths}
 for p,h in paths.items():assert hashlib.sha256(git('show',COMMIT+':'+p)).hexdigest()==h
 config_paths=git('ls-tree','-r','--name-only',COMMIT).decode().splitlines()
 assert [p for p in config_paths if Path(p).name==Path(CONFIG).name]==[CONFIG]
 original_config='configs/Quard/ctf_hcg_csort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml'
 assert git('show',COMMIT+':'+CONFIG)==git('show',BASE+':'+original_config)
 # Independent detailed semantic and resource reviews must already be real, complete and hash-bound.
 review_config=read(HERE/'aef_review_inputs.json');reviews=[]
 for entry in review_config['independent_reviews']:
  p=ROOT/entry['path'];assert sha(p)==entry['sha256'];rv=read(p)
  assert rv.get('material_concerns')==[],p
  reviews.append(entry)
 refs.extend(ref(EXE/n) for n in ['native_manifest.json','execution_binding.json','execution_lease.json'])
 refs.extend(reviews);now=datetime.now(timezone.utc).isoformat();identity={'id':EXP,'candidate_id':CID,'config':CONFIG,'code_commit':COMMIT,'goal_sha256':GOAL}
 obs={'native_semantics_and_pairing_checked':True,'resource_protocol_checked':True,'losses':s['losses'],'paired_batches':s['batches'],
 'common_initialized_parameter_observations':{k:v for k,v in s['common_initialized_parameters'].items() if k!='names'},
 'actual_mst_edges':[z['actual_real_mst_edges'] for z in s['AEF_flux_observations']],
 'resource_observations':{t:{k:x[k] for k in ['parameters','median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes','profile']} for t,x in [('champion',rc),('candidate',r)]},
 'existing_memory_condition_needs_separate_retention_decision':False,
 'relative_candidate_delta':{k:r[k]/rc[k]-1 for k in ['median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes']}}
 limitations={'efficacy':'UNKNOWN','novelty':'UNKNOWN','pure_TRAIN_memory':'UNKNOWN; smoke peak includes observer, resource process no optimizer','offdiagonal_probe':'NOT_IMPLEMENTED_NOT_MEASURED','optional_boundaries':'Only actual natural coverage; unexercised cases NOT_EXERCISED','conservation':'Unweighted FP32 sum descriptive only; no tolerance/point-weighted/Markov gate','timing':'Candidate measured slower; no new latency threshold'}
 review={**identity,'recorded_at':now,'review_status':'RAW_SEMANTICS_VALIDATED_NOT_ADMISSION','observations':obs,'raw_results':refs[:4],'independent_reviews':reviews,'evidence':refs,'limitations':limitations,'standard_PASS_receipt_queue_written':False}
 save(HERE/'aef_actual_four_result_review.json',review);refs.append(ref(HERE/'aef_actual_four_result_review.json'))
 smoke={**identity,'recorded_at':now,'steps':2,'losses':s['losses'],'native_data_loaded':True,'backward_finite':True,'intended_path_observed':True,'split':'train','command':s['actual_train_command'],'data_source':s['data_source']['train'],'evidence':refs,'paired_TRAIN_batches':s['batches'],'limitations':limitations}
 resource={**identity,'recorded_at':now,'passed_existing_resource_requirements':True,'protocol':{'batch_size':1,'lang_num_max':1,'warmup':20,'repeat':100,'counted_flops_limit':10e9},'observations':obs['resource_observations'],'evidence':refs,'limitations':limitations}
 constraints={**identity,'recorded_at':now,'passed':True,'source_hashes':paths,'checks':{'exact_nine_sources_and_YAML_match_tested_child026c':True,'actual_two_TRAIN_batches_common_initialization_paired':True,'native_original_loss_backward_updates_and_real_AEF_path':True,'original_skip_rawbanks_CSORT_HCG_single_inst_observed':True,'independent_package_and_unique_native_YAML':True,'same_seed1999_schedule50_maxiters70_data_pretrain_optimizer_precision':True,'current_goal_bans_and_GPU0_only_scope':True},'evidence':refs,'limitations':limitations}
 for name,v in [('aef_native_smoke.json',smoke),('aef_resource_comparison.json',resource),('aef_constraints_independence.json',constraints)]:save(HERE/name,v)
 print(json.dumps({'summary':ref(HERE/'aef_actual_four_result_review.json'),'losses':s['losses'],'edges':obs['actual_mst_edges'],'resource_delta':obs['relative_candidate_delta'],'admission_written':False}))
if __name__=='__main__':main()
