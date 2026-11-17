"""Read-only PSNC actual four-result reviewer. Never emits standard PASS/receipt/queue.
Common/resource/directory checks derive from frozen dfb6440d PSBR reviewer;
PSNC spectral/native checks are specific to actual worker69e2 observations.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

CID='hierarchy-parent-spectral-nonlinear-token-coupling'
EID='M210-PSNC'
COMMIT='43dce016c1a1713c2a5dab7061810dc2efde8954'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
CONFIG='configs/Quard/ctf_hcg_csort_psnc/'+NAME+'_psnc.yaml'
FROZEN='pipeline/diagnostic_bundles/tick_42ce600b/psnc_operational_prepare/native'
PREP_SHA='eebd34a6d2123cc8728d5e2dd6ebc8d055473e5bbf8da1fd33f909ae4e1c77d6'
TEMPLATE_SHA='d55848c32d8e95a3d4d34dc1a339050fb9f8b2d96b2bc74fe18c3a138bb63bd4'
RELEASE='pipeline/diagnostic_bundles/tick_42ce600b/psnc_operational_prepare/adapter_release.json'
RELEASE_SHA='a4000485b1cffdff7cb623ed2840a4d6b3c531baac5ed1b4a6a04cb04b48c749'
PAIRS=[('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')]
HANDLERS={'flop_count':'b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba','jit_analysis':'110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31','jit_handles':'ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129'}
class Refused(ValueError):pass


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

def common(raw, manifest, mode, target):
    need(raw['execution_completed'] is True and not raw.get('error_type') and not raw.get('error'), 'Worker did not complete successfully')
    need((raw['mode'], raw['target'], raw['candidate_id'], raw['code_commit'], raw['goal_sha256']) ==
         (mode, target, CID, COMMIT, GOAL), 'Raw identity/mode/target mismatch')
    package = 'framework.model.Quard_model.' + NAME + ('_psnc' if target == 'candidate' else '')
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
    selected_name = NAME + ('_psnc' if target == 'candidate' else '')
    need(raw['config_source'] == (manifest['stage'] + '/candidate.yaml' if target == 'candidate' else manifest['assets']['config_path']), 'Wrong native source config path')
    need(raw['runtime_config_path'] == manifest['stage'] + '/runtime_config_' + mode + '_' + target + '/' + selected_name + '.yaml', 'Wrong private native config resolver path')
    adaptation = raw['configuration_adaptations']
    need(set(adaptation) == {'work_dir', 'dist'} and adaptation['dist'] == 'False, native single-GPU CLI default' and
         adaptation['work_dir']['to'] == manifest['stage'] + '/native_' + mode + '_' + target and adaptation['work_dir']['from'], 'Non-path native config adaptation')
    need(raw['new_training'] == 0, 'Unexpected formal training in diagnostic')
    need(raw['data_source']['train']['training'] is True, 'Raw train data source absent')

def named_hashes(value, names):
    need(isinstance(value, dict) and set(value) == set(names) and all(hash_string(x) for x in value.values()), 'Incomplete tracked-module fingerprints')

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
    need(binding['stage'] == '/data/songcl/Project/Cluster_project/pipeline/psnc_' + binding['owner']['token'][:8] and
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
                'identity': 'M209-PSNC/config/74f/goal from independently validated binding', 'native_flags': 'Only validated actual true fields; never defaulted'},
            'remaining_admission_boundary': 'Owning root must review constraints/independence/current policy and resource retention condition, then separately create standard artifacts and receipt. This reviewer writes none.'}


def smoke(raw,candidate):
    need(type(raw['optimizer_steps']) is int and raw['optimizer_steps']==2,'Need two actual optimizer steps')
    need(raw['native_loss_forwards']==raw['native_criterion_backwards']==2 and raw['native_predict_calls']==0,'Native TRAIN counts mismatch')
    for flag in ('native_data_loaded','backward_finite','intended_path_observed','native_train_function_executed','native_smoke_checks_passed','observer_readout_complete','wrappers_and_hooks_restored','native_tracked_each_module_updated'):
        need(raw[flag] is True,'Missing native observed flag: '+flag)
    need(raw['auxiliary_autograd_grad_or_backward_used'] is False and raw['training_checkpoint_saved'] is False,'Diagnostic altered backward/checkpoint path')
    need(raw['actual_train_command'] and raw['native_train_cli_reference'] and raw['data_source']['train']['prefix']=='train','Missing actual native TRAIN provenance')
    need(len(raw['losses'])==2 and all(finite(v) for v in raw['losses']),'Two finite native losses required')
    for key in ('steps','batches','native_backward_records','raw_bank_observations','hcg_readbacks','inst_to_mask_path_observations'):
        need(len(raw[key])==2,'Missing actual two-forward observations: '+key)
    need(len(raw['ffn_calls'])==6 and len(raw['csort_raw_input_observations'])==4,'FFN/CSORT actual counts changed')
    for batch in raw['batches']:
        need(hash_string(batch['sha256']) and batch['scan_ids'] and batch['ann_ids'],'Missing actual TRAIN batch fingerprint')
    tracked=('ffn_0','ffn_1','ffn_2')
    named_hashes(raw['native_tracked_initial_hash'],tracked);named_hashes(raw['native_tracked_after_hash'],tracked)
    for record in raw['steps']:
        need(record['all_observed_gradients_finite'] is True and record['gradient_tensor_count']>0 and record['nonfinite_parameter_names']==[] and record['optimizer_step_completed'] is True,'Native optimizer/backward incomplete')
        for name in tracked:
            grads=record['tracked_module_gradients'][name]
            need(grads and all(v is not None for v in grads.values()),'Missing original FFN parameter gradient')
            for pname,value in grads.items():tensor(value,pname.endswith('weight'))
            need(record['module_before_step_hash'][name]!=record['module_after_step_hash'][name] and record['weight_before_step_hash'][name]!=record['weight_after_step_hash'][name],'Original FFN actual update absent')
    for record in raw['native_backward_records']:
        need(record['count']==1,'Extra/missing native loss backward');tensor(record['gradient'])
    for forward in (1,2):need([v['level'] for v in raw['ffn_calls'] if v['forward']==forward]==[0,1,2],'Original FFN calls changed')
    for record in raw['ffn_calls']:
        tensor(record['input']);tensor(record['output']);gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
    for record in raw['raw_bank_observations']:
        need(all(record[k] is True for k in ('unchanged_after_full_forward','ids_unchanged_after_full_forward','maps_unchanged_after_full_forward')),'Raw banks/IDs/maps mutated')
        need(all(hash_string(record[k]) for k in ('raw_sha256','id_sha256','map_sha256')),'Raw bank identity missing')
    for record in raw['csort_raw_input_observations']:
        need(record['original_raw_objects'] is True and record['original_childmap_object'] is True and record['original_calls']==1,'CSORT no longer original raw source');tensor(record['output'])
    for record in raw['hcg_readbacks']:
        tensor(record['output']);gradients(record,'native_point_message_gradients',True)
        levels={'0':True,'2':True} if candidate else {'0':True,'1':True,'2':True}
        need(record['original_residual_levels']==levels,'Original fine/coarse residual FFN path changed')
        if candidate:need(record['PSNC_middle_exact_HCG_input'] is True,'Spectral refined middle did not reach original HCG')
    for record in raw['inst_to_mask_path_observations']:
        need(record['single_native_inst_update_exact'] is True and record['new_extra_injection'] is False,'Original single point update changed');tensor(record['gate'])
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):gradients(record,key,True)
    inv=raw['dynamic_parameter_inventory']
    need(inv['original_FFN_parameters_by_level']=={'0':525568,'1':525568,'2':525568} and inv['new_declared_parameters']==0 and inv['DCT_or_geometry_registered_buffer_names']==[],'Original FFN inventory or new parameter/buffer scope changed')
    spectral=raw['PSNC_spectral_observations'];need(len(spectral)==(2 if candidate else 0),'Unexpected spectral branch count')
    for record in spectral:
        tensor(record['input']);tensor(record['output']);tensor(record['work_input'])
        need(record['original_delta_calls']==record['original_middle_ffn_calls']==record['original_middle_norm_calls']==1,'Original middle norm/FFN/delta was not called exactly once')
        need(record['returned_original_bank_shape'] is True and record['unmixed_original_f_rows_exact'] is True,'Inverse scatter/unmixed rows changed')
        gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
        groups=record['groups'];mixed=[g for g in groups if g['n']>1]
        need(record['actual_nonsingleton_supported_groups']==len(mixed)>0 and len(record['DCT_calls'])==len(mixed),'No actual supported mixed DCT branch')
        for batch in record['batches']:
            counts=batch['real_point_counts'];k=batch['middle_prefix']
            need(len(counts)==k and batch['padded_width']>=k and batch['batch_padding_rows']==batch['padded_width']-k,'Real support prefix/padding mismatch')
            need(batch['true_supported_original_ids']==[j for j,n in enumerate(counts) if n>0] and batch['unsupported_internal_ids']==[j for j,n in enumerate(counts) if n==0],'True point support mismatch')
            local=[g for g in groups if g['batch']==batch['batch']];covered=[]
            for g in local:
                need(g['n']==len(g['order'])>0 and len(set(g['order']))==g['n'] and all(j in batch['true_supported_original_ids'] for j in g['order']),'Invalid parent group order/support');covered+=g['order']
            need(sorted(covered)==batch['true_supported_original_ids'] and len(covered)==len(set(covered)),'Parent groups do not partition true support')
        for group,q in zip(mixed,record['DCT_calls']):
            need(all(q[k]==group[k] for k in ('batch','parent','order','n')),'DCT order differs from same-forward parent group');tensor(q['Q'])
            need(q['Q']['shape']==[group['n'],group['n']] and hash_string(q['Q_sha256']) and finite(q['measured_QtQ_identity_max_abs_error']) and q['measured_QtQ_identity_max_abs_error']>=0,'Missing actual finite DCT/orthogonality observation')
        need(record['sentinel_present_only_in_work_tensor'] is True and record['private_zero_work_row_observed'] is True and record['same_ffn_output_requires_grad'] is True,'Private same-call f0 sentinel/autograd path missing')
        tensor(record['same_call_f0_output']);gradients(record,'native_f0_output_gradients',False)
        need(record['work_input']['shape'][1]==record['input']['shape'][1]+1 and record['output']['shape']==record['input']['shape'],'Private work sentinel escaped original bank shape')
        for k in ('analysis_work_max_abs_error','synthesis_inverse_max_abs_error'):need(finite(record[k]) and record[k]>=0,'Invalid spectral reference observation')
        need(record['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED' and record['operator_zero_affine_identity_FP32'].startswith('NOT_RUN'),'Unexecuted operator diagnostics overclaimed')
    need(raw['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED' and raw['pure_training_peak_memory'].startswith('UNKNOWN') and raw['smoke_memory_scope'],'Unmeasured probe/TRAIN memory claim changed')
    for key in ('smoke_peak_allocated_bytes','smoke_peak_reserved_bytes'):need(type(raw[key]) is int and raw[key]>0,'Missing actual smoke memory')


def review_payloads(raws,manifest):
    need(manifest['candidate_id']==CID and manifest['code_commit']==COMMIT and manifest['goal_sha256']==GOAL and manifest['config']==CONFIG and manifest['experiment_id']==EID and manifest['tolerance']==1e-6,'Foreign PSNC manifest or changed frozen numeric metadata')
    for mode,target in PAIRS:
        raw=raws[mode+'_'+target];common(raw,manifest,mode,target)
        need(raw['experiment_id']==EID and raw['config']==CONFIG and raw['stage']==manifest['stage'] and raw['physical_gpu']==manifest['physical_gpu'] and raw['gpu_uuid']==manifest['gpu_uuid'],'Wrong actual PSNC execution metadata')
        need(raw['diagnostic_worker_sha256']==manifest['diagnostic_files']['worker.py'] and raw['runtime_sha256']==manifest['diagnostic_files']['native_runtime.py'] and raw['source_preparation_sha256']==manifest['source_preparation_sha256'],'Worker/runtime/source-preparation hashes mismatch')
        need(all(raw[k]==manifest[k] for k in ('current_token','tick_generated_at','deadline_at','context_sha256','pending_sha256')),'Raw owner differs from execution manifest')
        smoke(raw,target=='candidate') if mode=='smoke' else resources(raw)
    s,c=raws['smoke_candidate'],raws['smoke_champion'];a,b=raws['resources_candidate'],raws['resources_champion']
    need(s['batches']==c['batches'] and s['initialization']==c['initialization'] and s['native_dataloader_config']==c['native_dataloader_config'] and s['data_source']==c['data_source'],'Native TRAIN batch/init/loader/data pair mismatch')
    ci,bi=s['common_initialized_parameters'],c['common_initialized_parameters']
    for k in ('names','tensor_count','parameter_count','sha256','excluded_name_fragments'):need(ci[k]==bi[k],'Same original named-parameter initialization differs: '+k)
    need(ci['excluded_name_fragments']==[] and hash_string(ci['sha256']),'PSNC original common initialization coverage missing')
    need(s['dynamic_parameter_inventory']['state_dict_keys']==c['dynamic_parameter_inventory']['state_dict_keys'],'State dict key set changed')
    need(all(a[k]==b[k] for k in ('input_sha256','scan_ids','ann_ids','initialization','data_source')) and a['profile']['fvcore_version']==b['profile']['fvcore_version'],'Resource input/init/data/handler pair mismatch')
    need(a['profile']['flops']<=10e9,'Candidate exceeds unchanged standard10G budget')
    delta=lambda x,y:100*(x/y-1)
    facts={'candidate':{k:a[k] for k in ('parameters','median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes')},'champion':{k:b[k] for k in ('parameters','median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes')},'candidate_standard_flops':a['profile']['flops'],'champion_standard_flops':b['profile']['flops'],'delta_flops':a['profile']['flops']-b['profile']['flops'],'delta_median_pct':delta(a['median_ms'],b['median_ms']),'delta_p90_pct':delta(a['p90_ms'],b['p90_ms']),'delta_predict_allocated_pct':delta(a['peak_allocated_bytes'],b['peak_allocated_bytes']),'delta_predict_reserved_pct':delta(a['peak_reserved_bytes'],b['peak_reserved_bytes']),'delta_smoke_allocated_pct':delta(s['smoke_peak_allocated_bytes'],c['smoke_peak_allocated_bytes']),'delta_smoke_reserved_pct':delta(s['smoke_peak_reserved_bytes'],c['smoke_peak_reserved_bytes']),'unsupported_ops_candidate':a['profile']['unsupported_ops'],'unsupported_ops_champion':b['profile']['unsupported_ops'],'same_input_sha256':a['input_sha256'],'same_profiler_handlers':HANDLERS,'pure_training_peak':'UNKNOWN; smoke includes diagnostic observer/spectral reference overhead','unmeasured_no_cluster_baseline':'UNKNOWN; control is original M95'}
    triggered=a['peak_allocated_bytes']>1.15*b['peak_allocated_bytes'] or s['smoke_peak_allocated_bytes']>1.15*c['smoke_peak_allocated_bytes'];facts['existing_memory_15pct_retention_condition_observed']=triggered;facts['memory_condition_scope']='Existing +15% condition on observed prediction/smoke allocated peaks; smoke is not pure TRAIN. No new memory/latency gate.'
    spectral=s['PSNC_spectral_observations'];errors=[v[k] for v in spectral for k in ('analysis_work_max_abs_error','synthesis_inverse_max_abs_error')]
    return {'candidate_losses':s['losses'],'native_optimizer_steps':s['optimizer_steps'],'paired_TRAIN_batches':s['batches'],'common_initialized_parameter_observations':{'names_equal':True,'tensor_count':ci['tensor_count'],'parameter_count':ci['parameter_count'],'fingerprints_equal':True,'sha256':ci['sha256'],'scope':ci['scope'],'full_buffer_values':'NOT_RECORDED'},'actual_spectral_nonsingleton_group_counts':[v['actual_nonsingleton_supported_groups'] for v in spectral],'analysis_synthesis_reference_max_abs_error':max(errors),'reference_within_unchanged_manifest_tolerance_observation':max(errors)<=manifest['tolerance'],'QtQ_max_abs_error_observed':max(q['measured_QtQ_identity_max_abs_error'] for v in spectral for q in v['DCT_calls']),'numeric_scope':'QtQ/reference readouts observed, not a new threshold. Unexecuted zero/singleton/affine/identityQ and offdiagonal diagnostics remain NOT_RUN.','actual_unsupported_internal_rows':[v['actual_unsupported_internal_rows'] for v in spectral],'actual_padding_rows':[v['actual_padding_rows'] for v in spectral],'actual_supported_singleton_groups':[v['actual_supported_singleton_groups'] for v in spectral],'first_raw_bank_digest_comparison':{k:s['raw_bank_observations'][0][k]==c['raw_bank_observations'][0][k] for k in ('raw_sha256','id_sha256','map_sha256')},'raw_bank_digest_scope':'Cross-target exact output equality is not a preregistered gate; no magnitude/cause inferred from digest differences.','offdiagonal_dependency_probe':'NOT_IMPLEMENTED_NOT_MEASURED','resource_observations':facts,'existing_memory_condition_needs_separate_retention_decision':triggered,'native_semantics_and_pairing_checked':True,'resource_protocol_checked':True,'admission_authorized_by_this_report':False,'efficacy':'UNKNOWN'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',default='D:/project/cluster_project');parser.add_argument('--execution-dir',required=True);parser.add_argument('--output')
    args=parser.parse_args()
    try:result=review_directory(args.project,args.execution_dir)
    except (Refused,KeyError,TypeError,ValueError,OSError) as error:result={'review_status':'REFUSED_MISSING_OR_INVALID_ACTUAL_EVIDENCE','error_type':type(error).__name__,'error':str(error),'candidate_id':CID,'code_commit':COMMIT,'admission_authorized_by_this_report':False,'standard_artifacts_written':False}
    result['standard_PASS_receipt_queue_written']=False
    if args.output:
        path=Path(args.output).resolve();root=Path(args.project).resolve();need(path.is_relative_to(root/'pipeline/diagnostic_bundles'),'Report outside diagnostics')
        with path.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    return 0 if result.get('review_status')=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' else 2

if __name__=='__main__':raise SystemExit(main())
