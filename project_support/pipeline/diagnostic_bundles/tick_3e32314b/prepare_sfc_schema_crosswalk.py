"""Read frozen SFC producer and prior FCB consumer only; no modules/entries/tests run."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
NATIVE=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_native_prepare'
OLD=ROOT/'pipeline/diagnostic_bundles/tick_9169196d/fcb_promotion_prepare'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert sha(NATIVE/'preparation.json')=='173e5f02eaabfa02c37ad71646f9f136d9655a771aa3baf9b4382c6b3a90da77'
assert sha(NATIVE/'worker.py')=='edbe486295bc95edb80b332a649e9d6166c427f272a385bd56442ed7be4158b8'
native=json.loads((NATIVE/'preparation.json').read_text(encoding='utf-8'))
worker=(NATIVE/'worker.py').read_text(encoding='utf-8');consumer=(OLD/'fcb_evidence.py').read_text(encoding='utf-8')
wt,ct=ast.parse(worker),ast.parse(consumer)
def declared_keys(tree):return {n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)}|{n.arg for n in ast.walk(tree) if isinstance(n,ast.keyword) and n.arg}
keys=declared_keys(wt);oldkeys=declared_keys(ct)
required=['SFC_synchronous_forest_observations','actual_nodes','actual_rounds','actual_neighbor_mean_calls','actual_cell_calls','actual_GELU_calls','actual_state_index_copy_calls',
    'actual_final_index_copy_calls','actual_true_fine_paths','actual_true_edges','actual_original_builder_calls','actual_three_LN_calls','actual_state_update_rows',
    'actual_finished_components_no_fake_updates','actual_all_neighbor_same_OLDstate','final_hD_direct_delta_from_actual_index_copy_captures','unsupported_padding_deltas_zero',
    'all_observed_internal_gradients_finite','whole_synchronous_forest_weight_gradient','whole_synchronous_forest_weight_updated','whole_synchronous_forest_module_updated',
    'names','shapes','tensor_count','parameter_count','sha256','excluded_name_prefixes']
obsolete=['FCB_fine_coarse_bipartite_observations','actual_true_pairs','actual_pair_map_calls','actual_middle_map_calls','actual_map_calls','actual_private_mean_calls',
    'actual_same_q_two_marginals','actual_middle_context_from_original_fine_parent_mean','final_deltas_from_actual_captures_exact',
    'whole_fine_coarse_bipartite_weight_gradient','whole_fine_coarse_bipartite_weight_updated','whole_fine_coarse_bipartite_module_updated']
checks=[]
for name in required:
    assert name in keys,name;checks.append({'name':'actual_producer_declares_'+name,'passed':True})
assert all(name in oldkeys and name not in keys for name in obsolete)
checks.append({'name':'all_FCB_specific_obsolete_keys_must_be_removed','passed':True})
assert "record['actual_rounds']==record['actual_neighbor_mean_calls']==record['actual_cell_calls']==record['actual_GELU_calls']==record['actual_state_index_copy_calls']" in worker
assert 'whole_synchronous_forest_weight_gradient' in worker and "'own_columns'" in worker and "'neighbor_mean_columns'" in worker
checks.append({'name':'actual_round_equality_and_two_descriptive_columns_verified','passed':True})
mapping={
    'top_level_observation_list':{'FCB':'FCB_fine_coarse_bipartite_observations','SFC':'SFC_synchronous_forest_observations','actual_cardinality':'Candidate two natural TRAIN forwards ->list length2; champion list empty. Candidate ffn_calls empty, champion original ffn_calls6.'},
    'active_core_count':{'FCB':'actual_true_pairs>0 / actual_true_fine_paths>0','SFC':'actual_nodes>0 is the actual producer final gate; actual_true_fine_paths and actual_true_edges also reported. No pair count exists.'},
    'operator_counts':{'remove':['actual_pair_map_calls==actual_middle_map_calls==1','actual_map_calls==actual_GELU_calls==2','actual_private_mean_calls==3'],
        'SFC_exact_producer_relation':'actual_rounds == actual_neighbor_mean_calls == actual_cell_calls == actual_GELU_calls == actual_state_index_copy_calls',
        'round_definition':'R is max actual component diameter across the batch. Components use exactly their own D updates; valid true support gives D2 orD4, but consumer must not requireD4 or both. Final original-ID scatter count actual_final_index_copy_calls is3 for nonempty core.',
        'not_produced':['actual_private_mean_calls','actual_map_calls','actual_pair_map_calls','actual_middle_map_calls','actual_cell_rows','actual_initial_stack_calls','actual_prepare_calls']},
    'actual_true_boolean_flags':['actual_finished_components_no_fake_updates','actual_all_neighbor_same_OLDstate','final_hD_direct_delta_from_actual_index_copy_captures','unsupported_padding_deltas_zero'],
    'common_unchanged_relation':{'compare_both_actual_smokes':['batches','initialization','common_initialized_parameters'],
        'expected_excluded_name_prefixes':['dec.cluster_att.cluster_ffn.0.','dec.cluster_att.cluster_ffn.1.','dec.cluster_att.cluster_ffn.2.','dec.cluster_att.synchronous_forest.'],
        'fields':'names/shapes/tensor_count/parameter_count/sha256 retain exact spelling and dynamic actual values. set(shapes)==set(names); never hardcode835/843/847. Original3LN remains common.'},
    'whole_core_step_gate':{'FCB_keys':obsolete[-3:],'SFC_keys':['whole_synchronous_forest_weight_gradient','whole_synchronous_forest_weight_updated','whole_synchronous_forest_module_updated'],
        'existing_gate_only':'Per original step: whole gradient finite=True, finite abs_max>0, whole weight_updated=True/module_updated=True. Candidate tracked module is one synchronous_forest core, not one tracked module perround/node/scale.',
        'descriptive_only':'native_parameter_block_gradients own_columns/neighbor_mean_columns and descriptive_parameter_block_changed may beNone/zero/False. Bias, perround/node/level/call contributions may be zero; no separate positive/update or callback-completeness gate.'},
    'paths_and_shapes':{'plans':'One metadata plan per actual scene/batch item; actual_original_builder_calls==len(plans), no new hardcodedB2 check.',
        'plan_fields':['fine_ids','middle_ids','coarse_ids','node_keys','neighbors','components','edge_count','point_count'],
        'component_shape':'components[{root_id,nodes,diameter,edge_count}], nodes are local packed original-ID positions. node_keys[(level,original_id)].',
        'round_calls_shape':'round_calls[{round,receivers,neighbor_sources,neighbor_counts,input,input_sha256,same_OLD_state_before_all_updates,linear_output,output,output_sha256,original_cell_calls,original_GELU_calls,original_state_index_copy_calls,functional_update_after_OLDstate_reads,actual_state_sha256}]',
        'mean_calls_shape':'mean_calls[{round,input_state_sha256,output,output_sha256,counts,source_receivers,original_mean_calls,returned_original_object_unchanged,mean_replayed_by_observer,all_original_neighbors_old_state}]',
        'primitive_calls_shape':'primitive_calls kind initial_stack/own_gather/neighbor_gather/state_write/final_gather/final_scatter, original_calls1/returned_original_object_unchanged. These are captures, not extra computational replay.',
        'record_counts':'actual_state_update_rows=sum len(round_calls[i].receivers); source emits actual_nodes/actual_true_edges/actual_true_fine_paths. They describe original support, not newly imposed coverage thresholds.'},
    'unchanged_safety_and_path_fields':{'native_steps':'optimizer_steps/native_loss_forwards/native_criterion_backwards each2, actual finite losses, native_train_function_executed/backward_finite/intended_path_observed/native_smoke_checks_passed/native_tracked_each_module_updated/wrappers_and_hooks_restored true.',
        'internal_gradient':'all_observed_internal_gradients_finite in(None,True); individual finite-only. Do not require callbacks for everyround orpositive gradients for each.',
        'readback_key':'hcg_readbacks records SFC_original_three_skips_and_exact_HCG_inputs list3True. Original raw_bank_observations/CSORT/inst_to_mask_path_observations keep existing fields.',
        'optional_shape':'actual_optional_boundary_counts[{batch,components:[{root,D,nodes}],empty_scene,one_true_fine,unsupported_or_padding:[3counts]}]; no FCB nonancestor_pair or marginal structure.'},
    'resource_protocol':'All existing raw resource fields/handler/source identities unchanged: bs1/lang1/warmup20/repeat100/native_predict_calls121,100measurements,<=10G profile/within10G, same actual input and handlers; original15%-allocated condition/no latencygate. Smoke observer peak is not pureTRAIN memory.',
    'summary_and_admission_text':'Replace FCB constraints sentence and log_decision arguments (pairmap/sameq/marginals/thirdfineparentmean) by actual SFC trueforest OLDstate full-neighbor-degree mean/sharedcell/GELU/singlefunctional statecopy/D2finished/threehDdelta/3LN/rawskips/HCG/singleinst. Do not merely rename headers while retaining FCB claims. Standard receipt/profile/once-intents/FIFO/three-lock/UUID/owner/deadline contracts remain unchanged.'}
crosswalk={'schema_version':1,'status':'FROZEN_SFC_PRODUCER_TO_DISABLED_CONSUMER_PORT_HANDOFF_NOT_NATIVE_PASS','recorded_at':datetime.now(timezone.utc).isoformat(),
    'candidate_id':native['candidate_id'],'experiment_id':native['experiment_id'],'code_commit':native['code_commit'],'source_parent_commit':native['source_parent_commit'],'runtime_expected_commit':native['runtime_expected_commit'],
    'anchors':{'native_preparation':ref(NATIVE/'preparation.json'),'worker':ref(NATIVE/'worker.py'),'runtime':ref(NATIVE/'native_runtime.py'),'template':ref(NATIVE/'manifest_template.json'),'source_binding':ref(NATIVE/'source_version_binding.json'),
        'prior_FCB_promotion_preparation':ref(OLD/'preparation.json'),'prior_FCB_evidence_consumer':ref(OLD/'fcb_evidence.py'),'prior_FCB_summary':ref(OLD/'summarize_fcb_actual.py'),'prior_FCB_admission':ref(OLD/'admit_fcb_queue.py')},
    'mapping':mapping,'required_SFC_key_names':required,'obsolete_FCB_key_names':obsolete,
    'no_new_gates':['No fixedR4 orrequiredD4/mixedcomponent/degreeboundary/per-scene coverage','No perround/node/column/bias positivity orupdate','No FP32 marginal/conservation/convergence/Jacobian/offdiagonal gate','No latencygate orpureTRAIN memory claim'],
    'binding_requirements':'Future disabled package keeps actualraw/localreview/independentpeer refsNone and DRAFTTrue until real four envelopes plus real currentreview exist. SFCsourcec9be54 is actual childFCBd4d; parent technical receipt+actualmain/runtime d4d must be genuine. Do not read oldFCB raw asSFC or claim current0314 promotion.',
    'actual_raw_results':None,'actual_four_result_review':None,'actual_independent_review':None,'DRAFT_consumer_required':True,
    'scope_limits':'AST/static producer field declaration and original frozen shell handoff only. Producer31/independent17 evidence remains earlier software-only; no runtime result orconsumer implementation is validated here.',
    'model_forward_Torch_Git_SSH_GPU_or_shared_operation':False,'old_suites_executed':False,'material_concerns':[]}
save('sfc_producer_schema_crosswalk.json',crosswalk)
save('sfc_producer_schema_ast_check.json',{'status':'PASS_BOUNDED_STATIC_DECLARATION_CHECK_NOT_NATIVE','recorded_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),
    'crosswalk':ref(HERE/'sfc_producer_schema_crosswalk.json'),'worker':ref(NATIVE/'worker.py'),'oldconsumer':ref(OLD/'fcb_evidence.py'),
    'worker_or_runtime_imported_or_executed':False,'model_Torch_Git_SSH_GPU_shared_operation':False})
print(json.dumps({'crosswalk':ref(HERE/'sfc_producer_schema_crosswalk.json'),'static_check':ref(HERE/'sfc_producer_schema_ast_check.json'),'check_count':len(checks)}))
