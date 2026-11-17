"""Read-only PSBR raw-result semantic reviewer; never emits PASS/receipt/queue.

Only stdlib is imported. Real input is the exact adapter execution directory,
with binding, manifest, lease, four requests and four execution envelopes.
This report is evidence for a later owning-root decision, never admission.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

CID = 'hierarchy-parent-segmented-bidirectional-token-state'
EID = 'M209-PSBR'
COMMIT = '74fcd21df0af9a971792038ffe251af1ffea2604'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
CONFIG = 'configs/Quard/ctf_hcg_csort_psbr/' + NAME + '_psbr.yaml'
FROZEN = 'pipeline/diagnostic_bundles/tick_8fafa3d4/psbr_native_prepare'
PREP_SHA = '1e1de105f34ce4f6f87fe862bf35ee2c7c0bf26bf7404b0550559534a0e7472e'
TEMPLATE_SHA = 'f90e2662cb188b838ff7e6d6b60179529a983d91a32cb06187262aee70267263'
RELEASE = 'pipeline/diagnostic_bundles/tick_8fafa3d4/psbr_execution_adapter/adapter_release.json'
RELEASE_SHA = 'b17d424e493bcd49e1858bc6fc4b897d6fab5970a25240cea143e826f40e20d7'
PAIRS = [('smoke', 'champion'), ('smoke', 'candidate'), ('resources', 'champion'), ('resources', 'candidate')]
HANDLERS = {'flop_count': 'b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba',
            'jit_analysis': '110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31',
            'jit_handles': 'ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129'}


class Refused(ValueError):
    pass


def need(value, message):
    if not value:
        raise Refused(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    def reject(value):
        raise Refused('Nonstandard JSON number: ' + value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=reject)


def hash_string(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def tensor(value, nonzero=False):
    need(isinstance(value, dict), 'Missing tensor observation')
    need(value['finite'] is True and value['nonfinite_count'] == 0, 'Nonfinite tensor observation')
    need(isinstance(value['shape'], list) and value['dtype'] == 'torch.float32', 'Missing shape or changed native FP32 dtype')
    need(finite(value['abs_max']) and value['abs_max'] >= 0, 'Invalid observed tensor magnitude')
    if nonzero:
        need(value['abs_max'] > 0, 'Required native branch has zero gradient')


def gradients(record, key, nonzero=False):
    need(isinstance(record[key], list) and record[key], 'Missing actual gradient hook: ' + key)
    for value in record[key]:
        tensor(value, nonzero)


def level_hashes(value):
    need(set(value) == {'0', '1', '2'} and all(hash_string(x) for x in value.values()), 'Incomplete FFN level fingerprints')


def common(raw, manifest, mode, target):
    need(raw['execution_completed'] is True and not raw.get('error_type') and not raw.get('error'), 'Worker did not complete successfully')
    need((raw['mode'], raw['target'], raw['candidate_id'], raw['code_commit'], raw['goal_sha256']) ==
         (mode, target, CID, COMMIT, GOAL), 'Raw identity/mode/target mismatch')
    package = 'framework.model.Quard_model.' + NAME + ('_psbr' if target == 'candidate' else '')
    need(raw['model_package'] == package, 'Wrong/fallback model resolver')
    expected_sources = manifest['candidate_source_hashes'] if target == 'candidate' else manifest['assets']['source_hashes']
    need(raw['source_hashes'] == expected_sources, 'Raw source hashes do not match exact manifest')
    need(raw['native_model_and_yaml_unchanged'] is True, 'Native source/YAML claim absent')
    need(raw['config_sha256'] == raw['original_config_sha256'] == manifest['candidate_config_sha256'], 'Native YAML hash mismatch')
    need(hash_string(raw['runtime_config_sha256']), 'Runtime YAML hash missing')
    init = raw['initialization']
    need(init['kind'] == 'native_train_pretrain' and init['seed'] == 1999 and init['trained_m95_checkpoint_loaded'] is False,
         'Wrong seed or full-model initialization')
    need(init['path'] == manifest['assets']['pretrain'] and init['sha256'] == manifest['assets']['pretrain_sha256'], 'Pretrain mismatch')
    need(init['loader'] == 'gorilla.load_checkpoint(strict=False,map_location=cpu)', 'Pretrain loader changed')
    need(raw['native_train_source_sha256'] == manifest['assets']['native_train_source_sha256'], 'Native train source mismatch')
    selected_name = NAME + ('_psbr' if target == 'candidate' else '')
    need(raw['config_source'] == (manifest['stage'] + '/candidate.yaml' if target == 'candidate' else manifest['assets']['config_path']), 'Wrong native source config path')
    need(raw['runtime_config_path'] == manifest['stage'] + '/runtime_config_' + mode + '_' + target + '/' + selected_name + '.yaml', 'Wrong private native config resolver path')
    adaptation = raw['configuration_adaptations']
    need(set(adaptation) == {'work_dir', 'dist'} and adaptation['dist'] == 'False, native single-GPU CLI default' and
         adaptation['work_dir']['to'] == manifest['stage'] + '/native_' + mode + '_' + target and adaptation['work_dir']['from'], 'Non-path native config adaptation')
    need(raw['new_training'] == 0, 'Unexpected formal training in diagnostic')
    need(raw['data_source']['train']['training'] is True, 'Raw train data source absent')


def named_hashes(value, names):
    need(isinstance(value, dict) and set(value) == set(names) and all(hash_string(x) for x in value.values()), 'Incomplete tracked-module fingerprints')


def smoke(raw, candidate):
    for key in ('native_data_loaded','native_train_function_executed','backward_finite','native_tracked_each_module_updated',
                'observer_readout_complete','native_smoke_checks_passed','wrappers_and_hooks_restored','native_smoke_training','intended_path_observed'):
        need(raw[key] is True, 'Missing native smoke observation: '+key)
    need(raw['training_checkpoint_saved'] is False and raw['auxiliary_autograd_grad_or_backward_used'] is False, 'Unexpected checkpoint or auxiliary backward')
    need(raw['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED', 'Unrecorded diagnostic must not be claimed as measured')
    need(all(type(raw[k]) is int and raw[k]==2 for k in ('optimizer_steps','native_loss_forwards','native_criterion_backwards')), 'Not exactly two native optimizer/loss/backward steps')
    need(len(raw['losses'])==len(raw['steps'])==len(raw['batches'])==len(raw['native_backward_records'])==2 and all(finite(x) for x in raw['losses']), 'Incomplete finite two-step observations')
    need(raw['actual_train_command']=='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)', 'Changed native TRAIN entry')
    need(raw['native_dataloader_config']=={'batch_size':2,'num_workers':4,'persistent_workers':True}, 'Changed native TRAIN loader config')
    names={'ffn_0','ffn_2','Wx','Wh','Wo'} if candidate else {'ffn_0','ffn_1','ffn_2'}
    for batch in raw['batches']:
        need(hash_string(batch['sha256']) and batch['scan_ids'] and batch['ann_ids'] and batch['scenes_len'], 'Missing actual TRAIN fingerprint')
    for forward,record in enumerate(raw['native_backward_records'],1):
        need(record['forward']==forward and type(record['count']) is int and record['count']==1, 'Not one native criterion backward per forward')
        tensor(record['gradient'])
    for forward,record in enumerate(raw['steps'],1):
        need(record['forward']==forward and record['optimizer_step_completed'] is True and record['all_observed_gradients_finite'] is True and record['nonfinite_parameter_names']==[] and type(record['gradient_tensor_count']) is int and record['gradient_tensor_count']>0, 'Native backward/optimizer incomplete')
        need(set(record['tracked_module_gradients'])==names, 'Tracked operator gradient inventory mismatch')
        for name,parameters in record['tracked_module_gradients'].items():
            need(parameters and any(k.endswith('weight') for k in parameters), 'Missing module weights')
            for key,value in parameters.items():tensor(value,key.endswith('weight'))
        for key in ('module_before_step_hash','module_after_step_hash','weight_before_step_hash','weight_after_step_hash'):named_hashes(record[key],names)
        need(all(record['module_before_step_hash'][n]!=record['module_after_step_hash'][n] and record['weight_before_step_hash'][n]!=record['weight_after_step_hash'][n] for n in names), 'Actual per-step module/weight update missing')
    named_hashes(raw['native_tracked_initial_hash'],names);named_hashes(raw['native_tracked_after_hash'],names)
    need(all(raw['native_tracked_initial_hash'][n]!=raw['native_tracked_after_hash'][n] for n in names), 'Missing net native parameter updates')
    inventory=raw['dynamic_parameter_inventory']
    if candidate:
        need(inventory['middle_old_ffn_parameters']==0 and inventory['new_recurrence_parameters']==262656 and set(inventory['new_recurrence_parameter_names'])=={'Wx.weight','Wx.bias','Wh.weight','Wo.weight','Wo.bias'} and raw['new_operator_parameters']==262656, 'Actual registered PSBR inventory differs')
    else:
        need(inventory['new_recurrence_parameters'] is None and raw['new_operator_parameters'] is None, 'Control has new recurrence')
    need(len(raw['ffn_calls'])==(4 if candidate else 6) and len(raw['raw_bank_observations'])==len(raw['hcg_readbacks'])==len(raw['inst_to_mask_path_observations'])==2 and len(raw['csort_raw_input_observations'])==4, 'Incomplete hierarchy/path observations')
    for forward in (1,2):
        need([x['level'] for x in raw['ffn_calls'] if x['forward']==forward]==([0,2] if candidate else [0,1,2]), 'Wrong original FFN call graph')
        need(sorted(x['pair'] for x in raw['csort_raw_input_observations'] if x['forward']==forward)==[0,1], 'Wrong CSORT pair count')
    for record in raw['ffn_calls']:
        tensor(record['input']);tensor(record['output']);gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
    need([r['forward'] for r in raw['raw_bank_observations']]==[1,2] and [r['forward'] for r in raw['hcg_readbacks']]==[1,2], 'Hierarchy observations do not cover both original TRAIN forwards')
    for record in raw['raw_bank_observations']:
        need(all(record[k] is True for k in ('unchanged_after_full_forward','ids_unchanged_after_full_forward','maps_unchanged_after_full_forward')), 'Within-forward raw banks/IDs/maps mutated')
        need(all(hash_string(record[k]) for k in ('raw_sha256','id_sha256','map_sha256')), 'Missing raw/input hierarchy fingerprints')
        for x in record['levels']:tensor(x)
    for record in raw['csort_raw_input_observations']:
        need(record['original_raw_objects'] is True and record['original_childmap_object'] is True and record['original_calls']==1, 'CSORT did not use actual raw objects once')
        tensor(record['output'])
    for record in raw['hcg_readbacks']:
        need(record['original_residual_levels']==({'0':True,'2':True} if candidate else {'0':True,'1':True,'2':True}), 'Original residual branch changed')
        if candidate:need(record['PSBR_middle_exact_HCG_input'] is True, 'PSBR output not observed at HCG input')
        for value in record['levels']:tensor(value)
        tensor(record['output']);gradients(record,'native_point_message_gradients',True)
    for forward,record in enumerate(raw['inst_to_mask_path_observations'],1):
        need(record['forward']==forward and record['single_native_inst_update_exact'] is True and record['new_extra_injection'] is False, 'Wrong actual inst update path')
        need(all(hash_string(record[k]) for k in ('inst_before_sha256','cluster_message_sha256','ILA_query_sha256')), 'Missing actual inst path fingerprints')
        tensor(record['gate'])
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):gradients(record,key,True)
    recs=raw['PSBR_recurrence_observations'];need(len(recs)==(2 if candidate else 0),'Wrong recurrence calls')
    for forward,record in enumerate(recs,1):
        need(record['forward']==forward and type(record['nonsingleton_supported_parent_groups']) is int and record['nonsingleton_supported_parent_groups']>=1, 'Wh history was not exercised in actual batch')
        need(record['original_forward_calls']==1 and all(record[k] is True for k in ('inverse_write_to_original_ids_exact','unsupported_and_padding_zero','both_direction_boundaries_observed')), 'Recurrence boundary/inverse observations failed')
        need(record['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED' and all(hash_string(record[k]) for k in ('positions_sha256','parent_ids_sha256','support_sha256','output_sha256')), 'Missing actual geometry/support records')
        tensor(record['input']);tensor(record['output']);gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
        shape=record['input']['shape'];need(len(shape)==3 and shape[-1]==256 and len(record['batches'])==shape[0], 'Malformed recurrence batch geometry')
        by_batch={}
        for b in record['batches']:
            index=b['batch'];K=b['middle_prefix'];supported=b['true_supported_original_ids'];empty=b['unsupported_internal_ids'];counts=b['real_point_counts']
            need(type(index) is int and index not in by_batch and type(K) is int and 0<=K<=shape[1] and b['padded_width']==shape[1] and b['batch_padding_rows']==shape[1]-K, 'Wrong actual padding/prefix record')
            need(len(counts)==K and all(type(x) is int and x>=0 for x in counts) and supported==[j for j,n in enumerate(counts) if n>0] and empty==[j for j,n in enumerate(counts) if n==0], 'Support must distinguish real point support, internal empty and tail padding')
            by_batch[index]={'supported':supported,'seen':[]}
        need(set(by_batch)==set(range(shape[0])), 'Missing actual geometry batch')
        nonsingleton=0;group_pairs=set()
        for group in record['groups']:
            b,p,order,n=group['batch'],group['parent'],group['order'],group['token_count']
            need(b in by_batch and type(p) is int and p>=0 and (b,p) not in group_pairs and type(n) is int and n==len(order) and n>0 and len(set(order))==n, 'Malformed/duplicate actual parent group')
            group_pairs.add((b,p));by_batch[b]['seen'].extend(order);nonsingleton+=n>=2
            need(all(type(j) is int and j in by_batch[b]['supported'] for j in order), 'Empty/padded token entered recurrence')
            need(group['original_Wx_calls']==group['original_Wo_calls']==1 and group['zero_boundary_forward'] is True and group['zero_boundary_backward'] is True and len(group['wh_calls'])==2*n, 'Wx/Wh/Wo actual call or reset count wrong')
            need(all(hash_string(group[k]) for k in ('input_sha256','paired_input_sha256','output_sha256')), 'Missing actual group fingerprints')
            tensor(group['projected_summary']);tensor(group['output'])
            for i,call in enumerate(group['wh_calls']):
                direction='forward' if i<n else 'backward';offset=i if i<n else i-n;token=order[offset if i<n else n-1-offset]
                need(call['direction']==direction and call['sequence_offset']==offset and call['original_middle_id']==token and call['group_boundary'] is (offset==0) and hash_string(call['input_state_sha256']), 'Actual bidirectional original-ID order record is inconsistent')
                if offset==0:need(call['input_state_is_zero'] is True,'Wh boundary state not zero')
                tensor(call['output'])
        need(nonsingleton==record['nonsingleton_supported_parent_groups'] and nonsingleton>=1 and all(sorted(b['seen'])==b['supported'] for b in by_batch.values()), 'Actual support groups not a partition or no nonsingleton')
    common=raw['common_initialized_parameters']
    need(common['excluded_name_fragments']==['cluster_ffn.1.','middle_recurrence.'] and common['scope'] and common['paired_equality']=='NOT_VALIDATED_BY_SINGLE_TARGET_WORKER', 'Wrong initialized-parameter observation scope')
    need(isinstance(common['names'],list) and common['names'] and len(set(common['names']))==common['tensor_count'] and type(common['parameter_count']) is int and common['parameter_count']>0 and hash_string(common['sha256']), 'Missing common named-parameter observation')
    need(not any(any(fragment in name for fragment in common['excluded_name_fragments']) for name in common['names']) and any('cluster_ffn_norm.1.' in name for name in common['names']), 'Common readout wrongly excludes middle LN or includes replaced module')
    need(type(raw['smoke_peak_allocated_bytes']) is int and raw['smoke_peak_allocated_bytes']>0 and type(raw['smoke_peak_reserved_bytes']) is int and raw['smoke_peak_reserved_bytes']>0, 'Missing observed smoke memory')
    need(raw['smoke_memory_scope'] and raw['pure_training_peak_memory'].startswith('UNKNOWN'), 'Missing diagnostic-memory limit')


def resources(raw):
    need((raw['batch_size'], raw['lang_num_max'], raw['warmup'], raw['repeat']) == (1, 1, 20, 100), 'Resource protocol changed')
    need(raw['optimizer_steps'] == raw['native_loss_forwards'] == raw['native_criterion_backwards'] == 0 and raw['native_predict_calls'] == 121, 'Resource process contains training or lacks actual measured calls')
    values = raw['measurements_ms']
    need(len(values) == 100 and all(finite(x) and x > 0 for x in values), '100 finite timing observations required')
    ordered = sorted(values); p90 = ordered[89] + (ordered[90] - ordered[89]) * 0.1
    # Encoding/derived-statistic consistency, not a latency acceptance threshold.
    need(math.isclose(raw['median_ms'], statistics.median(values), rel_tol=1e-12, abs_tol=1e-12) and
         math.isclose(raw['p90_ms'], p90, rel_tol=1e-12, abs_tol=1e-12), 'Reported timing statistics disagree with measurements')
    need(hash_string(raw['input_sha256']) and raw['scan_ids'] and raw['ann_ids'], 'Missing real resource sample identity')
    need(raw['parameter_flags_preserved'] is True and raw['source_body_executed_without_replacement'] is True and
         raw['validation_accuracy_evaluated_for_selection'] is False, 'Resource path/validation boundary changed')
    for k in ('parameters', 'peak_allocated_bytes', 'peak_reserved_bytes'):
        need(type(raw[k]) is int and raw[k] > 0, 'Invalid actual resource observation: ' + k)
    profile = raw['profile']
    need(profile['profiler_file_sha256'] == HANDLERS, 'Historical fvcore handlers changed')
    need(finite(profile['flops']) and profile['flops'] > 0 and finite(profile['flops_g']) and profile['flops_g'] == profile['flops'] / 1e9, 'Invalid counted FLOPs')
    need(profile['within10G'] is (profile['flops'] <= 10e9), 'FLOPs budget flag inconsistent')
    need(isinstance(profile['unsupported_ops'], dict) and isinstance(profile['by_operator'], dict) and profile['fvcore_version'], 'Missing unsupported/operator/profiler disclosure')
    need(all(type(n) is int and n >= 0 for n in profile['unsupported_ops'].values()), 'Malformed unsupported-op counts')
    need(raw['full_optimizer_training_peak'].startswith('UNKNOWN'), 'Resource profile must not claim full TRAIN peak')


def review_payloads(raws, manifest):
    """Pure semantic checks; no result/receipt creation. Missing observation refuses."""
    need(manifest['candidate_id']==CID and manifest['code_commit']==COMMIT and manifest['goal_sha256']==GOAL and manifest['config']==CONFIG and manifest['experiment_id']==EID, 'Foreign PSBR manifest')
    for mode,target in PAIRS:
        raw=raws[mode+'_'+target];common(raw,manifest,mode,target)
        need(raw['experiment_id']==EID and raw['config']==CONFIG and raw['stage']==manifest['stage'] and raw['physical_gpu']==manifest['physical_gpu'] and raw['gpu_uuid']==manifest['gpu_uuid'], 'Wrong PSBR raw execution metadata')
        need(raw['diagnostic_worker_sha256']==manifest['diagnostic_files']['worker.py'] and raw['runtime_sha256']==manifest['diagnostic_files']['native_runtime.py'] and raw['source_preparation_sha256']==manifest['source_preparation_sha256'], 'Raw diagnostic source hash metadata changed')
        need(all(raw[k]==manifest[k] for k in ('current_token','tick_generated_at','deadline_at','context_sha256','pending_sha256')), 'Raw current identity differs from actual execution manifest')
        smoke(raw,target=='candidate') if mode=='smoke' else resources(raw)
    s,c=raws['smoke_candidate'],raws['smoke_champion']
    need(s['batches']==c['batches'], 'Two actual TRAIN batch fingerprints not paired')
    need(s['initialization']==c['initialization'] and s['native_dataloader_config']==c['native_dataloader_config'] and s['data_source']==c['data_source'], 'Native seed/pretrain/data/loader mismatch')
    a,b=raws['resources_candidate'],raws['resources_champion']
    need(all(a[k]==b[k] for k in ('input_sha256','scan_ids','ann_ids','initialization','data_source')), 'Actual resource input/init/data pair mismatch')
    need(a['profile']['fvcore_version']==b['profile']['fvcore_version'], 'Resource fvcore version mismatch')
    need(a['profile']['flops']<=10e9, 'Candidate exceeds unchanged standard 10G budget')
    delta = lambda x, y: 100 * (x / y - 1)
    resource_facts = {'candidate': {k: a[k] for k in ('parameters', 'median_ms', 'p90_ms', 'peak_allocated_bytes', 'peak_reserved_bytes')},
                      'champion': {k: b[k] for k in ('parameters', 'median_ms', 'p90_ms', 'peak_allocated_bytes', 'peak_reserved_bytes')},
                      'candidate_standard_flops': a['profile']['flops'], 'champion_standard_flops': b['profile']['flops'],
                      'delta_flops': a['profile']['flops'] - b['profile']['flops'],
                      'delta_median_pct': delta(a['median_ms'], b['median_ms']), 'delta_p90_pct': delta(a['p90_ms'], b['p90_ms']),
                      'delta_predict_allocated_pct': delta(a['peak_allocated_bytes'], b['peak_allocated_bytes']),
                      'delta_predict_reserved_pct': delta(a['peak_reserved_bytes'], b['peak_reserved_bytes']),
                      'delta_smoke_allocated_pct': delta(s['smoke_peak_allocated_bytes'], c['smoke_peak_allocated_bytes']),
                      'delta_smoke_reserved_pct': delta(s['smoke_peak_reserved_bytes'], c['smoke_peak_reserved_bytes']),
                      'unsupported_ops_candidate': a['profile']['unsupported_ops'], 'unsupported_ops_champion': b['profile']['unsupported_ops'],
                      'same_input_sha256': a['input_sha256'], 'same_profiler_handlers': HANDLERS,
                      'pure_training_peak': 'UNKNOWN; smoke includes diagnostic observer overhead', 'unmeasured_no_cluster_baseline': 'UNKNOWN; control is original M95'}
    triggered = a['peak_allocated_bytes'] > 1.15 * b['peak_allocated_bytes'] or s['smoke_peak_allocated_bytes'] > 1.15 * c['smoke_peak_allocated_bytes']
    resource_facts['existing_memory_15pct_retention_condition_observed'] = triggered
    resource_facts['memory_condition_scope'] = 'Existing +15% condition on observed prediction/smoke allocated peaks; smoke is not pure TRAIN. No new memory or latency gate.'
    ci,bi=s['common_initialized_parameters'],c['common_initialized_parameters']
    common_observation={'candidate':ci,'champion':bi,'names_equal':ci['names']==bi['names'],
        'tensor_counts_equal':ci['tensor_count']==bi['tensor_count'],'parameter_counts_equal':ci['parameter_count']==bi['parameter_count'],
        'fingerprints_equal':ci['sha256']==bi['sha256'],
        'scope':'Recorded named parameters only, not buffers/full common state. Equality/difference reported; no new exact full-common-state hash gate.',
        'original_fine_coarse_initial_hash_equal':{n:s['native_tracked_initial_hash'][n]==c['native_tracked_initial_hash'][n] for n in ('ffn_0','ffn_2')}}
    return {'candidate_losses':s['losses'],'native_optimizer_steps':s['optimizer_steps'],'paired_TRAIN_batches':s['batches'],
        'common_initialized_parameter_observations':common_observation,
        'actual_recurrence_nonsingleton_group_counts':[r['nonsingleton_supported_parent_groups'] for r in s['PSBR_recurrence_observations']],
        'recurrence_geometry_observation_scope':'Hash-bound worker checked actual Wx input against sorted detached current centroids; reviewer verifies stored support/group/order/reset/inverse records. Raw centroid vectors were not stored for external re-sorting.',
        'offdiagonal_dependency_probe':'NOT_IMPLEMENTED_NOT_MEASURED; native Wh gradient/update is not a measured offdiagonal Jacobian or task-level benefit',
        'first_raw_bank_digest_comparison':{k:s['raw_bank_observations'][0][k]==c['raw_bank_observations'][0][k] for k in ('raw_sha256','id_sha256','map_sha256')},
        'raw_bank_digest_scope':'Cross-target exact-output equality was not preregistered; differences are reported without inferring magnitude/cause.',
        'resource_observations':resource_facts,'existing_memory_condition_needs_separate_retention_decision':triggered,
        'native_semantics_and_pairing_checked':True,'admission_authorized_by_this_report':False,'efficacy':'UNKNOWN'}


def review_directory(project, directory):
    project, directory = Path(project).resolve(), Path(directory).resolve()
    need(directory.is_relative_to(project), 'Execution directory outside project')
    binding, manifest = read(directory/'execution_binding.json'), read(directory/'native_manifest.json')
    need(binding['candidate_id'] == CID and binding['code_commit'] == COMMIT and binding['goal_sha256'] == GOAL, 'Foreign execution binding')
    need(binding['frozen_preparation_sha256'] == PREP_SHA and binding['frozen_template_sha256'] == TEMPLATE_SHA and binding['adapter_release_sha256'] == RELEASE_SHA, 'Execution binding does not match external frozen package anchors')
    need(digest(project/FROZEN/'preparation.json') == PREP_SHA and digest(project/FROZEN/'manifest_template.json') == TEMPLATE_SHA and digest(project/RELEASE) == RELEASE_SHA, 'External prepared artifacts changed')
    prep = read(project/FROZEN/'preparation.json')
    for name, expected_hash in prep['prepared_file_hashes'].items():
        f = (project/FROZEN/name).resolve()
        need(f.is_relative_to((project/FROZEN).resolve()) and digest(f) == expected_hash, 'Frozen prepared file changed: ' + name)
    release = read(project/RELEASE)
    for name, expected_hash in release['source_hashes'].items():
        need(digest((project/RELEASE).parent/name) == expected_hash, 'Frozen adapter source changed: ' + name)
    need(digest(directory/'native_manifest.json') == binding['native_manifest_sha256'] and digest(directory/'execution_lease.json') == binding['execution_lease_sha256'], 'Manifest/lease bytes changed')
    need(binding['stage'] == manifest['stage'] and binding['owner']['token'] == manifest['current_token'] and binding['physical_gpu'] == manifest['physical_gpu'] == 0 and binding['gpu_uuid'] == manifest['gpu_uuid'], 'Stage/token/authorized physicalGPU0 binding mismatch')
    need(binding['stage'] == '/data/songcl/Project/Cluster_project/pipeline/psbr_' + binding['owner']['token'][:8] and
         binding['gpu_uuid'] == 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c', 'Wrong fixed stage or physical GPU UUID')
    template = read(project/FROZEN/'manifest_template.json')
    expected_manifest = copy.deepcopy(template)
    old = binding['owner']
    expected_manifest.update(current_token=old['token'], stage=binding['stage'], tick_generated_at=old['generated_at'], deadline_at=old['deadline_at'],
                             physical_gpu=0, gpu_uuid=binding['gpu_uuid'], allowed_gpus=binding['server_binding']['allowed_gpus'],
                             context_sha256=old['context_sha256'], pending_sha256=old['pending_sha256'], runtime_code_commit=binding['runtime_code_commit'])
    need(manifest == expected_manifest, 'Manifest is not exact frozen template plus execution binding')
    lease = read(directory/'execution_lease.json')
    expected_lease = {'project': 'cluster_project', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253',
                      'native_manifest_sha256': binding['native_manifest_sha256'], 'token': old['token'], 'generated_at': old['generated_at'],
                      'deadline_at': old['deadline_at'], 'server_id': 'server-4', 'physical_gpu': 0, 'gpu_uuid': binding['gpu_uuid'],
                      'allowed_gpus': binding['server_binding']['allowed_gpus'], 'goal_sha256': GOAL,
                      'context_sha256': old['context_sha256'], 'pending_sha256': old['pending_sha256']}
    need(lease == expected_lease, 'Lease is not exact original binding; it is never renewed for review')
    raws, evidence, process_observations = {}, [], {}
    for mode, target in PAIRS:
        name = mode + '_' + target
        request, envelope = read(directory/(name+'_request.json')), read(directory/(name+'_execution.json'))
        expected = {'project': 'cluster_project', 'candidate_id': CID, 'code_commit': COMMIT, 'stage': binding['stage'],
                    'token': binding['owner']['token'], 'request_id': request['request_id'], 'operation': 'run',
                    'physical_gpu': binding['physical_gpu'], 'gpu_uuid': binding['gpu_uuid'], 'native_manifest_sha256': binding['native_manifest_sha256']}
        need(request == dict(expected, mode=mode, target=target) and envelope['identity'] == expected and envelope['certainty'] == 'terminal' and type(envelope['returncode']) is int and envelope['returncode'] == 0, 'Missing/uncertain/wrong original request execution: ' + name)
        command = envelope['command']
        tail = ['-B', binding['stage']+'/worker.py', '--lease', binding['stage']+'/execution_lease.json', '--mode', mode, '--target', target]
        process = envelope['original_process_identity']
        need(isinstance(command, list) and len(command) == 9 and command[1:] == tail and process['argv'] in (command, []) and
             type(envelope['pid']) is int and envelope['pid'] > 0 and process['pid'] == envelope['pid'] and
             isinstance(process['start_ticks'], str) and process['start_ticks'].isdigit(), 'Missing/wrong original native worker argv or PID/startticks: ' + name)
        process_observations[name] = {'pid': envelope['pid'], 'start_ticks': process['start_ticks'],
                                      'early_proc_argv_observed_equal': process['argv'] == command,
                                      'scope': 'Exact constructed Popen command/direct terminal wait/result chain verified. Empty early /proc argv is unobserved, not independent PID identity proof for later signals.'}
        need(all(hash_string(envelope[k]) for k in ('result_sha256', 'stdout_sha256', 'stderr_sha256')), 'Missing actual remote result/stdout/stderr file hashes')
        raws[name] = envelope['result']
        need(raws[name]['native_manifest_sha256']==binding['native_manifest_sha256'], 'Raw manifest hash differs from actual original binding')
        for suffix in ('_request.json', '_execution.json'):
            f = directory/(name+suffix)
            evidence.append({'path': f.relative_to(project).as_posix(), 'sha256': digest(f)})
    observations = review_payloads(raws, manifest)
    for f in (directory/'execution_binding.json', directory/'native_manifest.json', directory/'execution_lease.json', project/FROZEN/'worker.py'):
        evidence.append({'path': f.relative_to(project).as_posix(), 'sha256': digest(f)})
    return {'review_status': 'RAW_SEMANTICS_VALIDATED_NOT_ADMISSION', 'id': EID, 'candidate_id': CID, 'config': CONFIG,
            'code_commit': COMMIT, 'runtime_code_commit': binding['runtime_code_commit'],
            'runtime_scope': 'Runtime checkout identity is separately observed; candidate package is staged hash-bound74f. No synchronization is inferred.',
            'goal_sha256': GOAL, 'process_observations': process_observations, 'observations': observations, 'evidence': evidence,
            'standard_smoke_fields_mapping': {'steps': 'observed optimizer_steps integer2, not raw steps list', 'losses': 'candidate actual two losses',
                'command': 'candidate actual_train_command', 'data_source': 'candidate data_source.train', 'split': 'train',
                'identity': 'M209-PSBR/config/74f/goal from independently validated binding', 'native_flags': 'Only validated actual true fields; never defaulted'},
            'remaining_admission_boundary': 'Owning root must review constraints/independence/current policy and resource retention condition, then separately create standard artifacts and receipt. This reviewer writes none.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='D:/project/cluster_project')
    parser.add_argument('--execution-dir', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    destination = Path(args.report).resolve()
    need(destination.parent == Path(__file__).resolve().parent and not destination.exists(), 'Only a fresh review JSON in this bundle may be written')
    try:
        result = review_directory(args.project, args.execution_dir)
        code = 0
    except (Refused, KeyError, TypeError, ValueError, OSError, IndexError) as error:
        result = {'review_status': 'REFUSED_OR_INCOMPLETE', 'error_type': type(error).__name__, 'error': str(error),
                  'admission_authorized_by_this_report': False, 'standard_artifacts_written': False}
        code = 2
    result['recorded_at'] = datetime.now(timezone.utc).isoformat()
    result['standard_PASS_receipt_queue_written'] = False
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'review_status': result['review_status'], 'report': str(destination), 'sha256': digest(destination)}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
