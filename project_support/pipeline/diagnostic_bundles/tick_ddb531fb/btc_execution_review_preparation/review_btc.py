"""Read-only BTC actual four-result reviewer. Never emits standard PASS/receipt/queue.
Common/resource/directory checks derive from frozen dfb6440d PSBR reviewer;
BTC inside/outside/leaf/native checks are specific to actual worker a39f observations.
"""
import argparse
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

CID='hierarchy-parent-binary-tree-complement-composition'
EID='M211-BTC'
COMMIT='00e2b18c6b8d568a64edb496e6979d766440883c'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
CONFIG='configs/Quard/ctf_hcg_csort_btc/'+NAME+'_btc.yaml'
FROZEN='pipeline/diagnostic_bundles/tick_7dcc29e8/btc_operational_prepare/native'
PREP_SHA='82b7ae52260fdfb79c69e96d20c8e8b5ea501a70bfaaf4e71d3028ad0c9cbe18'
TEMPLATE_SHA='4a28e488fae8972056ce6481e6ac3e91ff9d0b86dc687181b1434400e83768a5'
RELEASE='pipeline/diagnostic_bundles/tick_7dcc29e8/btc_operational_prepare/adapter_release.json'
RELEASE_SHA='765beabf35ae7312fbddc6f9ac882df329f68c98df12d40d843a8469c626b30e'
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
    package = 'framework.model.Quard_model.' + NAME + ('_btc' if target == 'candidate' else '')
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
    selected_name = NAME + ('_btc' if target == 'candidate' else '')
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
    need(binding['stage'] == '/data/songcl/Project/Cluster_project/pipeline/btc_' + binding['owner']['token'][:8] and
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
        need(hashlib.sha256(json.dumps(raws[name], indent=2, allow_nan=False).encode('utf-8')).hexdigest()==envelope['result_sha256'], 'Actual Linux worker result serialization hash mismatch: '+name)
        need(raws[name]['native_manifest_sha256']==binding['native_manifest_sha256'], 'Raw manifest hash differs from actual original binding')
        for suffix in ('_request.json', '_execution.json'):
            f = directory/(name+suffix)
            evidence.append({'path': f.relative_to(project).as_posix(), 'sha256': digest(f)})
    observations = review_payloads(raws, manifest)
    for f in (directory/'execution_binding.json', directory/'native_manifest.json', directory/'execution_lease.json', project/FROZEN/'worker.py'):
        evidence.append({'path': f.relative_to(project).as_posix(), 'sha256': digest(f)})
    return {'review_status': 'RAW_SEMANTICS_VALIDATED_NOT_ADMISSION', 'id': EID, 'candidate_id': CID, 'config': CONFIG,
            'code_commit': COMMIT, 'runtime_code_commit': binding['runtime_code_commit'],
            'runtime_scope': 'Runtime checkout identity is separately observed; candidate package is staged hash-bound00e. No synchronization is inferred.',
            'goal_sha256': GOAL, 'process_observations': process_observations, 'observations': observations, 'evidence': evidence,
            'standard_smoke_fields_mapping': {'steps': 'observed optimizer_steps integer2, not raw steps list', 'losses': 'candidate actual two losses',
                'command': 'candidate actual_train_command', 'data_source': 'candidate data_source.train', 'split': 'train',
                'identity': 'M211-BTC/config/00e/goal from independently validated binding', 'native_flags': 'Only validated actual true fields; never defaulted'},
            'remaining_admission_boundary': 'Owning root must review constraints/independence/current policy and resource retention condition, then separately create standard artifacts and receipt. This reviewer writes none.'}


def topology_functions():
    """Execute only hash-verified pure stdlib production/observer topology functions."""
    directory=Path('D:/project/cluster_project')/FROZEN
    environment={'math':math}
    for filename,name in [('candidate_model/middle_tree.py','build_parent_forest'),('worker.py','forest_observation')]:
        tree=ast.parse((directory/filename).read_text(encoding='utf-8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(directory/filename),'exec'),environment)
    return environment['build_parent_forest'],environment['forest_observation']


def tree_record(record):
    tensor(record['input']);tensor(record['output'])
    need(record['input']['shape']==record['output']['shape'],'Tree output escaped original middle bank')
    need(record['original_middle_norm_calls']==record['original_tree_forward_calls']==1,'Original middle norm/tree call count changed')
    for flag in ('returned_original_bank_shape','original_ID_inverse_scatter_observed','unsupported_and_batch_padding_update_zero'):
        need(record[flag] is True,'Missing actual BTC inverse/scatter/source control: '+flag)
    gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
    need(record['root_inside_actual_calls']==0,'Unused rootinside unexpectedly evaluated')
    need(record['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED','Unimplemented probe overclaimed')
    build,describe=topology_functions(); groups=[];plan=[]
    for batch in record['batches']:
        k=batch['middle_prefix'];width=batch['padded_width'];counts=batch['real_point_counts']
        need(type(k) is int and type(width) is int and len(counts)==k<=width and all(type(n) is int and n>=0 for n in counts),'Malformed native middle support/prefix')
        need(batch['batch_padding_rows']==width-k and batch['true_supported_original_ids']==[i for i,n in enumerate(counts) if n>0] and batch['unsupported_internal_ids']==[i for i,n in enumerate(counts) if n==0],'True native support/padding mismatch')
        forest=build(batch['centers'],batch['parent_ids'],[n>0 for n in counts],width)
        local,entries=describe(forest)
        for g in local:g['batch']=batch['batch']
        for e in entries:e['batch']=batch['batch']
        groups.extend(local);plan.extend(entries)
    groups=json.loads(json.dumps(groups));plan=json.loads(json.dumps(plan))
    need(record['groups']==groups,'Actual forest differs from original stable geometry/parent/support topology')
    need(record['actual_builder_calls']==len(record['batches'])==record['input']['shape'][0],'Actual production builder count differs from native batch')
    n3=sum(g['n']>=3 for g in groups)
    need(record['actual_n_ge3_supported_parent_groups']==n3>0,'INCONCLUSIVE: original TRAIN batch lacks proper-inside n>=3 coverage; no replacement sample')
    need(record['actual_singleton_supported_parent_groups']==sum(g['n']==1 for g in groups),'Singleton coverage summary mismatch')
    need(record['actual_unsupported_internal_rows']==sum(len(b['unsupported_internal_ids']) for b in record['batches']) and record['actual_padding_rows']==sum(b['batch_padding_rows'] for b in record['batches']),'Padding/empty coverage summary mismatch')
    calls=record['map_calls'];need(len(calls)==len(plan),'Original map call count does not match production topology')
    roots={(g['batch'],g['parent']):g['root'] for g in groups}
    for index,(call,expected) in enumerate(zip(calls,plan)):
        need(all(call[k]==v for k,v in expected.items()) and call['call_index']==index and call['forward']==record['forward'],'Actual shared-map dependency/order mismatch')
        need(call['actual_input_sources_exact'] is True,'Original actual map sources were not preserved')
        zero=any(kind=='outside' and node==roots[(call['batch'],call['parent'])] for kind,node in call['input_refs'])
        need(call['root_outside_zero_observed'] is zero,'Root outside zero observation mismatch')
        tensor(call['input']);tensor(call['linear_output']);tensor(call['output'])
        need(call['input']['shape']==[512] and call['output']['shape']==[256] and call['linear_output']['shape']==[256],'Original shared map dimensions changed')
        gradients(call,'native_input_gradients');gradients(call,'native_output_gradients')
        if call['map']!='leaf':
            need(call['activation_original_calls']==1,'Original inside/outside GELU not observed once')
            gradients(call,'native_linear_output_gradients')
        else:need(call['output_sha256']==call['linear_output_sha256'],'Leaf unexpectedly used extra activation')
    proper=[v for v in calls if v['map']=='inside']
    need(proper and any(g['finite'] and g['abs_max']>0 for v in proper for g in v['native_output_gradients']),'Actual proper-inside original loss dependency not observed; not a whole-mechanism rejection')


def smoke(raw,candidate):
    need(type(raw['optimizer_steps']) is int and raw['optimizer_steps']==2,'Need two actual optimizer steps')
    need(raw['native_loss_forwards']==raw['native_criterion_backwards']==2 and raw['native_predict_calls']==0,'Native TRAIN counts mismatch')
    for flag in ('native_data_loaded','backward_finite','intended_path_observed','native_train_function_executed','native_smoke_checks_passed','observer_readout_complete','wrappers_and_hooks_restored','native_tracked_each_module_updated'):
        need(raw[flag] is True,'Missing native actual flag: '+flag)
    need(raw['auxiliary_autograd_grad_or_backward_used'] is False and raw['training_checkpoint_saved'] is False and raw['native_failure_is_not_whole_mechanism_rejection'] is True,'Diagnostic backward/checkpoint/scope changed')
    need(raw['actual_train_command'] and raw['native_train_cli_reference'] and raw['data_source']['train']['prefix']=='train','Missing actual original TRAIN provenance')
    need(len(raw['losses'])==2 and all(finite(v) for v in raw['losses']),'Two finite native losses required')
    need(len(raw['loss_tensor_observations'])==len(raw['loss_component_observations'])==2,'Missing actual native loss/component observations')
    for v in raw['loss_tensor_observations']:tensor(v)
    for values in raw['loss_component_observations']:
        need(values,'Empty native loss components')
        for v in values.values():tensor(v)
    for key in ('steps','batches','native_backward_records','raw_bank_observations','hcg_readbacks','inst_to_mask_path_observations'):
        need(len(raw[key])==2,'Missing original two-forward observations: '+key)
    need(len(raw['ffn_calls'])==(4 if candidate else 6) and len(raw['csort_raw_input_observations'])==4,'FFN/CSORT actual call counts changed')
    for batch in raw['batches']:need(hash_string(batch['sha256']) and batch['scan_ids'] and batch['ann_ids'],'Missing real TRAIN batch fingerprint')
    tracked=('ffn_0','ffn_2','tree_inside','tree_outside','tree_leaf') if candidate else ('ffn_0','ffn_1','ffn_2')
    named_hashes(raw['native_tracked_initial_hash'],tracked);named_hashes(raw['native_tracked_after_hash'],tracked)
    need(all(raw['native_tracked_initial_hash'][n]!=raw['native_tracked_after_hash'][n] for n in tracked),'Tracked original module did not update')
    for record in raw['steps']:
        need(record['all_observed_gradients_finite'] is True and record['gradient_tensor_count']>0 and record['nonfinite_parameter_names']==[] and record['optimizer_step_completed'] is True,'Native optimizer/backward incomplete')
        need(set(record['tracked_module_gradients'])==set(tracked),'Wrong original tracked map/FFN inventory')
        for name in tracked:
            grads=record['tracked_module_gradients'][name]
            need(grads and all(v is not None for v in grads.values()),'Missing original FFN/map native parameter gradient')
            for pname,value in grads.items():tensor(value,pname.endswith('weight'))
            need(record['module_before_step_hash'][name]!=record['module_after_step_hash'][name] and record['weight_before_step_hash'][name]!=record['weight_after_step_hash'][name],'Actual FFN/map weight update absent')
    for record in raw['native_backward_records']:need(record['count']==1,'Extra/missing original loss backward');tensor(record['gradient'])
    levels=[0,2] if candidate else [0,1,2]
    for forward in (1,2):need([v['level'] for v in raw['ffn_calls'] if v['forward']==forward]==levels,'Original remaining FFN calls changed')
    for record in raw['ffn_calls']:
        tensor(record['input']);tensor(record['output']);gradients(record,'native_input_gradients',True);gradients(record,'native_output_gradients',True)
    for record in raw['raw_bank_observations']:
        need(all(record[k] is True for k in ('unchanged_after_full_forward','ids_unchanged_after_full_forward','maps_unchanged_after_full_forward')),'Raw banks/IDs/maps mutated')
        need(all(hash_string(record[k]) for k in ('raw_sha256','id_sha256','map_sha256')),'Raw bank identity absent')
    for record in raw['csort_raw_input_observations']:
        need(record['original_raw_objects'] is True and record['original_childmap_object'] is True and record['original_calls']==1,'CSORT raw source changed');tensor(record['output'])
    for record in raw['hcg_readbacks']:
        tensor(record['output']);gradients(record,'native_point_message_gradients',True)
        need(record['original_residual_levels']=={str(i):True for i in levels},'Remaining fine/coarse/original skip path changed')
        if candidate:need(record['BTC_middle_original_skip_and_exact_HCG_input'] is True,'Original middle cf skip/tree output did not reach HCG')
    for record in raw['inst_to_mask_path_observations']:
        need(record['single_native_inst_update_exact'] is True and record['new_extra_injection'] is False,'Original single point update changed');tensor(record['gate'])
        for key in ('native_post_cluster_inst_gradients','native_post_ILA_inst_gradients','native_final_mask_gradients'):gradients(record,key,True)
    inv=raw['dynamic_parameter_inventory'];expected={'0':525568,'1':0 if candidate else 525568,'2':525568}
    need(inv['original_FFN_parameters_by_level']==expected and inv['new_declared_parameters']==(393984 if candidate else 0) and inv['geometry_registered_buffer_names']==[],'Replacement parameter/buffer inventory changed')
    trees=raw['BTC_tree_observations'];need(len(trees)==(2 if candidate else 0),'Unexpected actual BTC branch count')
    for record in trees:tree_record(record)
    need(raw['offdiagonal_dependency_probe']=='NOT_IMPLEMENTED_NOT_MEASURED' and raw['pure_training_peak_memory'].startswith('UNKNOWN') and raw['smoke_memory_scope'],'Unmeasured probe/pure TRAIN claim changed')
    for key in ('smoke_peak_allocated_bytes','smoke_peak_reserved_bytes'):need(type(raw[key]) is int and raw[key]>0,'Missing actual smoke memory')


def review_payloads(raws,manifest):
    need(manifest['candidate_id']==CID and manifest['code_commit']==COMMIT and manifest['goal_sha256']==GOAL and manifest['config']==CONFIG and manifest['experiment_id']==EID and manifest['tolerance']==1e-6,'Foreign BTC manifest or changed frozen metadata')
    for mode,target in PAIRS:
        raw=raws[mode+'_'+target];common(raw,manifest,mode,target)
        need(raw['experiment_id']==EID and raw['config']==CONFIG and raw['stage']==manifest['stage'] and raw['physical_gpu']==manifest['physical_gpu'] and raw['gpu_uuid']==manifest['gpu_uuid'],'Wrong actual BTC execution metadata')
        need(raw['diagnostic_worker_sha256']==manifest['diagnostic_files']['worker.py'] and raw['runtime_sha256']==manifest['diagnostic_files']['native_runtime.py'] and raw['source_preparation_sha256']==manifest['source_preparation_sha256'],'Worker/runtime/source-preparation hash mismatch')
        need(all(raw[k]==manifest[k] for k in ('current_token','tick_generated_at','deadline_at','context_sha256','pending_sha256')),'Raw owner differs from original execution manifest')
        smoke(raw,target=='candidate') if mode=='smoke' else resources(raw)
    s,c=raws['smoke_candidate'],raws['smoke_champion'];a,b=raws['resources_candidate'],raws['resources_champion']
    need(s['batches']==c['batches'] and s['initialization']==c['initialization'] and s['native_dataloader_config']==c['native_dataloader_config'] and s['data_source']==c['data_source'],'Original TRAIN batch/init/loader/data pair mismatch')
    ci,bi=s['common_initialized_parameters'],c['common_initialized_parameters']
    for k in ('names','tensor_count','parameter_count','sha256','excluded_name_prefixes'):need(ci[k]==bi[k],'Same original common named initialization differs: '+k)
    exclusions=['dec.cluster_att.cluster_ffn.1.','dec.cluster_att.middle_tree.']
    need(ci['excluded_name_prefixes']==exclusions and ci['tensor_count']==len(ci['names']) and hash_string(ci['sha256']) and any(n.startswith('dec.cluster_att.cluster_ffn_norm.1.') for n in ci['names']),'Common exact prefix scope changed or middle LayerNorm omitted')
    need(not any(n.startswith(tuple(exclusions)) for n in ci['names']),'Excluded replacement parameters leaked into common pairing')
    need(all(a[k]==b[k] for k in ('input_sha256','scan_ids','ann_ids','initialization','data_source')) and a['profile']['fvcore_version']==b['profile']['fvcore_version'],'Resource sample/init/data/profiler pair mismatch')
    need(a['profile']['flops']<=10e9,'Candidate exceeds original standard10G budget')
    need(a['parameters']==s['dynamic_parameter_inventory']['actual_full_model_parameters'] and b['parameters']==c['dynamic_parameter_inventory']['actual_full_model_parameters'],'Actual model parameter inventory disagrees across modes')
    need(a['parameters']-b['parameters']==393984-525568,'Actual replacement parameter delta differs from frozen source inventory')
    delta=lambda x,y:100*(x/y-1)
    facts={'candidate':{k:a[k] for k in ('parameters','median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes')},'champion':{k:b[k] for k in ('parameters','median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes')},'candidate_standard_flops':a['profile']['flops'],'champion_standard_flops':b['profile']['flops'],'delta_flops':a['profile']['flops']-b['profile']['flops'],'delta_parameters':a['parameters']-b['parameters'],'delta_median_pct':delta(a['median_ms'],b['median_ms']),'delta_p90_pct':delta(a['p90_ms'],b['p90_ms']),'delta_predict_allocated_pct':delta(a['peak_allocated_bytes'],b['peak_allocated_bytes']),'delta_predict_reserved_pct':delta(a['peak_reserved_bytes'],b['peak_reserved_bytes']),'delta_smoke_allocated_pct':delta(s['smoke_peak_allocated_bytes'],c['smoke_peak_allocated_bytes']),'delta_smoke_reserved_pct':delta(s['smoke_peak_reserved_bytes'],c['smoke_peak_reserved_bytes']),'unsupported_ops_candidate':a['profile']['unsupported_ops'],'unsupported_ops_champion':b['profile']['unsupported_ops'],'same_input_sha256':a['input_sha256'],'same_profiler_handlers':HANDLERS,'pure_training_peak':'UNKNOWN; smoke includes actual topology/observer/source-recording overhead','unmeasured_no_cluster_baseline':'UNKNOWN; control is original M95'}
    triggered=a['peak_allocated_bytes']>1.15*b['peak_allocated_bytes'] or s['smoke_peak_allocated_bytes']>1.15*c['smoke_peak_allocated_bytes'];facts['existing_memory_15pct_retention_condition_observed']=triggered;facts['memory_condition_scope']='Existing +15% condition on observed prediction/smoke allocated peaks; smoke is not pure TRAIN. No new latency/numeric gate.'
    trees=s['BTC_tree_observations']
    return {'candidate_losses':s['losses'],'native_optimizer_steps':s['optimizer_steps'],'paired_TRAIN_batches':s['batches'],'common_initialized_parameter_observations':{'names_equal':True,'tensor_count':ci['tensor_count'],'parameter_count':ci['parameter_count'],'fingerprints_equal':True,'sha256':ci['sha256'],'scope':ci['scope'],'excluded_name_prefixes':exclusions,'full_buffer_values':'NOT_RECORDED'},'actual_n_ge3_supported_parent_group_counts':[v['actual_n_ge3_supported_parent_groups'] for v in trees],'actual_tree_map_call_counts':[{k:sum(c['map']==k for c in v['map_calls']) for k in ('inside','outside','leaf')} for v in trees],'root_inside_actual_calls':[v['root_inside_actual_calls'] for v in trees],'actual_unsupported_internal_rows':[v['actual_unsupported_internal_rows'] for v in trees],'actual_padding_rows':[v['actual_padding_rows'] for v in trees],'actual_supported_singleton_groups':[v['actual_singleton_supported_parent_groups'] for v in trees],'first_raw_bank_digest_comparison':{k:s['raw_bank_observations'][0][k]==c['raw_bank_observations'][0][k] for k in ('raw_sha256','id_sha256','map_sha256')},'raw_bank_digest_scope':'Cross-target exact intermediate output equality is not a preregistered gate; no magnitude/cause inferred from digest differences.','offdiagonal_dependency_probe':'NOT_IMPLEMENTED_NOT_MEASURED','resource_observations':facts,'existing_memory_condition_needs_separate_retention_decision':triggered,'native_semantics_and_pairing_checked':True,'resource_protocol_checked':True,'admission_authorized_by_this_report':False,'efficacy':'UNKNOWN'}


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
