"""HVD disabled native port checks; stdlib only, no model/transport/GPU execution."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,os,subprocess,sys
import author_guard as ag
ag.author_guard();ROOT=ag.ROOT;HERE=ag.HERE;NATIVE=HERE/'native'
PRODUCER=ROOT/'pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native'
MOTHER=ROOT/'pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare'
checks=[]
def check(name,condition):
    if not condition:raise AssertionError(name)
    checks.append(name)
def function(source,name):return next(ast.get_source_segment(source,node) for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name==name)
prep=json.loads((NATIVE/'preparation.json').read_text(encoding='utf8'))
template=json.loads((NATIVE/'manifest_template.json').read_text(encoding='utf8'))
binding=json.loads((NATIVE/'source_version_binding.json').read_text(encoding='utf8'))
proof_path=ROOT/'pipeline/diagnostic_bundles/tick_265517f1/hvd_version_prepare/isolated_source_version.json'
proof=json.loads(proof_path.read_text(encoding='utf8'))
worker=(NATIVE/'worker.py').read_text(encoding='utf8');runtime=(NATIVE/'native_runtime.py').read_text(encoding='utf8')
producer=(PRODUCER/'worker.py').read_text(encoding='utf8')
check('declared_native_diagnostic_hash_graph_exact',all(ag.sha(NATIVE/name)==digest for name,digest in template['diagnostic_files'].items()))
check('declared_preparation_hash_graph_exact',all(ag.sha(NATIVE/name)==digest for name,digest in prep['prepared_file_hashes'].items()))
for path in list(NATIVE.rglob('*.py'))+[HERE/'author_guard.py',HERE/'author_native_packet.py',Path(__file__)]:ast.parse(path.read_text(encoding='utf8'))
check('all_authored_and_candidate_python_AST_parse',True)
check('candidate8_and_yaml_exact_original_HVD_source9',len(template['candidate_source_hashes'])==8 and all(ag.sha(NATIVE/'candidate_model'/name)==digest for name,digest in template['candidate_source_hashes'].items()) and ag.sha(NATIVE/'candidate.yaml')==template['candidate_config_sha256'])
check('source_proof_exact9_and_real_e38_parent6bc',proof['source_files_exact9']==binding['source_files'] and len(binding['source_files'])==9 and binding['code_commit']==proof['code_commit']=='e38d92db60f43dde00ae0e537493dc3f3dfc82db' and binding['parent_commit']==proof['parent_commit']=='6bc36adfe42764aac2209e6600fb3a783e2fa374')
check('original_source_proof_owner_preserved_separate_from_current_provenance',binding['original_source_proof_owner_preserved']==proof['owner'] and proof['owner']['token']=='265517f1c8984940a6925367924f062f' and binding['author_provenance_only']['prepared_under_current_owner']['token']=='c7451cf19cec4fc5aa23d2984eb0a249' and binding['author_provenance_only']['execution_binding'] is False)
check('complete_original_resources_source_bytes_exact',function(worker,'resources')==function(producer,'resources'))
check('original_resource_20warm100_handlers_and_full_unsupported_report_retained',all(text in function(worker,'resources') for text in ('range(20)','range(100)',"'unsupported_ops': dict(analysis.unsupported_ops())","assert handlers == expected","loader_cfg.batch_size = 1","profile_cfg.lang_num_max = 1")))
fields=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
check('all_ten_execution_fields_NULL_and_DRAFT_true',all(template[field] is None for field in fields) and template['draft_execution_disabled'] is True and 'DRAFT_EXECUTION_DISABLED = True' in runtime)
check('actual_runtime_candidate_and_gpu0_sharing_metadata_correct',"CANDIDATE_COMMIT = 'e38d92db60f43dde00ae0e537493dc3f3dfc82db'" in runtime and "RUNTIME_EXPECTED_COMMIT = '6bc36adfe42764aac2209e6600fb3a783e2fa374'" in runtime and "PHYSICAL_GPU == 0" in runtime and "'minimum_free_mib_before_launch': 20000" in runtime and "'max_project_tasks_per_gpu': 1" in runtime and template['resource_authorization']['sha256']=='783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88')
check('no_MIC_candidate_suffix_or_core_left_in_final_runtime_worker',not any(term in worker+'\n'+runtime for term in ('_mic','mobius_interaction','ancestry_mobius','M229-MIC','65792','actual_subset_slices')))
check('original_natural_TRAIN2_common_initialization_and_loss_loop_retained',all(text in worker for text in ('yield from itertools.islice(iter(self.native),2)',"'dec.cluster_att.variance_decomposition.'",'retain three original LayerNorms','train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer)',"loss.numel()==1 and bool(torch.isfinite(loss).all())")))
check('whole_new_core_weight_gradient_and_weight_module_update_keys_present',all(key in worker for key in ('whole_variance_decomposition_weight_gradient','whole_variance_decomposition_weight_updated','whole_variance_decomposition_module_updated')) and "return {}  # HVD trainability is assessed across the whole new core." in worker and "any(g is not None and g['abs_max']>0 for n,g in gradients.items() if n.endswith('weight'))" in worker)
check('actual_HVD_moment_pack_factor_and_restoration_observers_present',all(text in worker for text in ('original_components(points,p0,p1,p2,fine_count,middle_count,coarse_count)','original_group_mean(values,labels,count)','original_pack(normalized,stats,p1,p2)','actual_group_mean_calls','actual_factor_concat_calls','actual_split_calls','actual_final_index_copy_calls',"core.factor[2].register_forward_hook(linear_post(1))")))
# Each transparency wrapper calls its bound original exactly once in its AST.
smoke_ast=ast.parse(function(worker,'smoke'))
wrapped={'observed_components':'original_components','observed_group_mean':'original_group_mean','observed_pack':'original_pack','observed_plan':'original_plan','observed_cat':'original_cat','observed_split':'original_split','observed_copy':'original_copy'}
for name,original in wrapped.items():
 node=next(node for node in ast.walk(smoke_ast) if isinstance(node,ast.FunctionDef) and node.name==name)
 assert sum(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id==original for node in ast.walk(node))==1
check('seven_actual_path_wrappers_call_original_once_without_replay',True)
# Exercise actual port's pure topology observer against actual pinned production planner.
helper=(NATIVE/'candidate_model/variance_decomposition.py').read_text(encoding='utf8')
selected=[node for node in ast.parse(helper).body if isinstance(node,ast.FunctionDef) and node.name=='build_support_plan']
selected += [node for node in ast.parse(worker).body if isinstance(node,ast.FunctionDef) and node.name in ('hvd_plan_observation','hvd_coverage_preflight')]
namespace={'copy':copy};exec(compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])),'actual_HVD_port_topology','exec'),namespace)
members=([3,0,3],[1,99,99,3],[99,2,99,0]);widths=[5,5,4]
plan=namespace['build_support_plan'](*members,3,widths);observed=namespace['hvd_plan_observation'](plan,members,3,widths)
check('actual_port_topology_observer_handles_supported_holes',observed['true_supported_nodes_by_scale']==[2,2,2] and observed['unsupported_or_padding_nodes_by_scale']==[3,3,2] and plan=={key:observed[key] for key in plan})
empty=namespace['build_support_plan']([],[],[],0,[0,0,0]);observed_empty=namespace['hvd_plan_observation'](empty,([],[],[]),0,[0,0,0])
check('actual_port_topology_observer_keeps_empty_scene_optional',observed_empty['point_count']==0 and observed_empty['true_supported_nodes_by_scale']==[0,0,0])
# Both actual files must refuse before native_manifest access, fcntl, NVML or Torch.
commands=[]
for name in ('native_runtime.py','worker.py'):
 command=[sys.executable,'-B','-X','utf8',str(NATIVE/name)]
 completed=subprocess.run(command,cwd=str(NATIVE),env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,encoding='utf8',timeout=15)
 assert completed.returncode!=0 and 'HVD native preparation is execution-disabled' in completed.stderr
 assert 'ModuleNotFoundError' not in completed.stderr and not completed.stdout
 commands.append({'command':command,'returncode':completed.returncode,'refusal':completed.stderr.strip().splitlines()[-1]})
check('actual_runtime_and_worker_default_disabled_fail_closed_before_manifest_NVML_Torch',True)
check('no_active_manifest_lease_request_result_release_or_bytecode_artifacts',not any(path.name in {'native_manifest.json','lease.json','request.json','release.json','active_binding.json'} or path.name.endswith('_result.json') or path.name=='__pycache__' for path in HERE.rglob('*')))
old_frozen=json.loads((MOTHER/'FROZEN.json').read_text(encoding='utf8'))
check('original_NULL_mother_packet_complete_frozen_hash_graph_preserved',all(ag.sha(MOTHER/name)==digest for name,digest in old_frozen['files'].items()) and json.loads((MOTHER/'source_manifest.json').read_text(encoding='utf8'))['code_commit'] is None)
check('final_MIC_producer_worker_and_runtime_unchanged',ag.sha(PRODUCER/'worker.py')=='5bdaa5532dd9b794b8e215caac81e1bef1e3ba1c2b654f7dd68fe33106c60348' and ag.sha(PRODUCER/'native_runtime.py')=='20fdf514a2928ddf72ee29f97a1eb714517f781336bff204ef24943bc7557ea6')
result={'schema_version':1,'candidate_id':template['candidate_id'],'experiment_id':'M230-HVD','recorded_at':datetime.now(timezone.utc).isoformat(),
 'status':'STDLIB_NATIVE_PORT_HASH_AST_TOPOLOGY_AND_ACTUAL_DEFAULT_DISABLED_CHECKS_PASSED_NOT_NATIVE',
 'check_count':len(checks),'checks':checks,'actual_disabled_commands':commands,
 'worker_sha256':ag.sha(NATIVE/'worker.py'),'runtime_sha256':ag.sha(NATIVE/'native_runtime.py'),
 'Torch':'NOT_RUN','autograd':'NOT_RUN','full_forward':'NOT_RUN','native':'NOT_RUN','resources':'NOT_RUN',
 'GPU_NVML_SSH_Git':'NOT_RUN','scientific_admission':False,'operational_ready':False,
 'root_identity_impersonated':False,'shared_state_or_source_mutation':False,
 'limitations':'Actual path wrappers and native source are parsed/hashed; only pure topology functions and import-time disabled refusal run locally. No Tensor/model/autograd/device/data/resource or efficacy evidence.'}
ag.write_json(HERE/'static_validation.json',result)
print(json.dumps({'passed':True,'check_count':len(checks),'worker_sha256':result['worker_sha256'],'static_validation_sha256':ag.sha(HERE/'static_validation.json')}))
