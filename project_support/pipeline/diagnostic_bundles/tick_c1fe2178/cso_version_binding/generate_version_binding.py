"""Default NOP. Derive a byte-exact version association only after real current gates."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys

ROOT = Path('D:/project/cluster_project').resolve()
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
BOUND = TICK / 'cso_native_bound'
EXECUTION = TICK / 'cso_native_execution'
SOURCE = 'af45707d7b6089f764843337c5f88af285383f88'
SOURCE_PARENT = 'd21477b0d85e6ddcef428ea98ddf6b86fcc38f7e'
INTEGRATED = '5413102c57b526035f3920b5e7a81f3b58ad764d'
RUNTIME = 'b1e639b3ceb14bb5c65d9f81a084d41c834b951c'
GPU_UUID = 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
AUTHOR = '/root/cso_readiness'
READSET = {}
CORE = {'input_norm.weight', 'input_norm.bias', 'project.weight', 'readout.0.weight',
        'readout.0.bias', 'readout.2.weight', 'readout.2.bias', 'readout.3.weight', 'readout.3.bias'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'Missing/invalid required file: ' + str(path))
    data = path.read_bytes()
    digest = sha(data)
    require(path not in READSET or READSET[path] == digest, 'Input changed: ' + str(path))
    READSET[path] = digest
    return data


def read(path):
    return json.loads(raw(path))


def ref(path):
    path = Path(path).resolve()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(raw(path))}


def current_review(path, owner, flag, actual=None):
    path = Path(path).resolve()
    require(path.is_relative_to(TICK), 'Only this tick may supply a new review')
    review = read(path)
    require(review['owner'] == owner and review['passed'] is True and review['material_concerns'] == [], 'Current independent review did not pass')
    reviewer = review['reviewer_thread_id']
    require(reviewer and reviewer not in (owner['thread_id'], '/root', AUTHOR), 'Independent reviewer identity required')
    require(review[flag] is True, 'Review lacks explicit required gate: ' + flag)
    if actual is not None:
        require(review['actual_sha256'] == ref(actual)['sha256'], 'Review is not bound to exact raw actual')
        if 'actual_path' in review:
            require((ROOT / review['actual_path']).resolve() == actual.resolve(), 'Review actual path mismatch')
    return review


def owner_guard():
    require(sys.dont_write_bytecode and not sys.flags.optimize, 'Use ordinary python -B without -O')
    owner = read(TICK / 'current_owner_binding.json')
    require(owner['token'] == 'c1fe217800894083b65baac45f79aa83' and owner['thread_id'] == '01a159c5-29ab-7a22-ba7f-e79174757253', 'Wrong current owner')
    require(len(owner) == 6 and datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at']), 'Owner expired or not owner6')
    require(os.environ.get('CODEX_THREAD_ID') == owner['thread_id'], 'Only the authorized foreground root thread may generate')
    live = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    require({k: live[k] for k in owner} == owner, 'Foreground ownership changed')
    mode = read(ROOT / 'pipeline/execution_mode.json')
    require(mode['mode'] == 'foreground' and mode['target_thread_id'] == owner['thread_id'], 'Wrong execution mode')
    for filename, key in (('.tick_context.json', 'context_sha256'), ('.tick_context_state.next.json', 'pending_sha256')):
        require(ref(ROOT / 'pipeline/headless' / filename)['sha256'] == owner[key], 'Context/pending changed')
    return owner


def git(worktree, *args):
    worktree = Path(worktree).resolve()
    require(worktree.is_relative_to(ROOT / 'pipeline/isolated_versions'), 'Unexpected worktree')
    command = ['git', '--no-optional-locks', '-c', 'safe.directory=' + worktree.as_posix(),
               '-c', 'core.fsmonitor=false', '-C', str(worktree), *args]
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_CONFIG_NOSYSTEM='1')
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=30)
    require(result.returncode == 0, 'Read-only Git failure: ' + result.stderr.decode('utf8', 'replace')[-1000:])
    return result.stdout


def verify_git(proof, exact9):
    worktrees = [(proof['source_worktree'], INTEGRATED, RUNTIME),
                 (proof['native_source_worktree'], SOURCE, SOURCE_PARENT)]
    observed = []
    for location, commit, parent in worktrees:
        require(git(location, 'rev-parse', 'HEAD').decode().strip() == commit, 'Worktree HEAD changed')
        require(git(location, 'rev-list', '--parents', '-n', '1', commit).decode().split() == [commit, parent], 'Commit parent mismatch')
        require(not git(location, 'status', '--porcelain=v1', '--untracked-files=all'), 'Retained source worktree is dirty')
        changes = git(location, 'diff-tree', '--no-commit-id', '--name-status', '-r', commit).decode().splitlines()
        require(set(changes) == {'A\t' + name for name in exact9} and len(changes) == 9, 'Commit is not exact nine additions')
        files = {}
        for name, digest in exact9.items():
            blob = git(location, 'rev-parse', commit + ':' + name).decode().strip()
            data = git(location, 'cat-file', 'blob', commit + ':' + name)
            require(blob == proof['blob_ids'][name] and sha(data) == digest, 'Commit blob changed: ' + name)
            require(sha(raw(Path(location) / name)) == digest, 'Working source bytes changed: ' + name)
            files[name] = {'git_blob': blob, 'sha256': digest}
        observed.append({'worktree': str(Path(location).resolve()), 'HEAD': commit, 'parent': parent,
                         'clean': True, 'only_nine_additions': True, 'files_exact9': files})
    require(observed[0]['files_exact9'] == observed[1]['files_exact9'], 'Integrated/native source blobs differ')
    return observed


def finite_positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def gradients(records):
    require(records and all(r['finite'] is True for r in records), 'Nonfinite or missing native gradient observation')


def check_smoke(r):
    for key in ('native_data_loaded', 'native_train_function_executed', 'intended_path_observed', 'backward_finite',
                'observer_readout_complete', 'native_smoke_checks_passed', 'wrappers_and_hooks_restored',
                'native_tracked_each_parameter_updated', 'native_smoke_training'):
        require(r[key] is True, 'Smoke missing actual gate: ' + key)
    require(r['training_checkpoint_saved'] is False and r['auxiliary_autograd_grad_or_backward_used'] is False, 'Unexpected training adaptation')
    require(r['optimizer_steps'] == r['native_criterion_backwards'] == r['native_loss_forwards'] == 2, 'Not two original TRAIN steps')
    require(r['actual_train_command'] == 'tools.train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer)', 'Not native TRAIN function')
    require(r['optimizer_type'] == 'AdamW' and r['scheduler_type'] == 'PolyLR', 'Optimizer/scheduler changed')
    loader = r['native_dataloader_config']
    require(loader['batch_size'] == 2 and loader['num_workers'] == 4 and loader['persistent_workers'] is True, 'Natural loader changed')
    require(r['data_source']['train']['prefix'] == 'train' and r['data_source']['train']['training'] is True, 'Not natural TRAIN data')
    require(r['initialization']['seed'] == 1999 and r['initialization']['trained_m95_checkpoint_loaded'] is False, 'Initialization changed')
    for key in ('batches', 'losses', 'steps', 'core_calls', 'raw_bank_observations', 'inst_to_mask_path_observations'):
        require(len(r[key]) == 2 and [v['forward'] for v in r[key]] == [1, 2], 'Missing two natural observations: ' + key)
    require(all(b['sha256'] and len(b['scan_ids']) == 2 and len(b['ann_ids']) == 8 for b in r['batches']), 'Natural two-scene/eight-expression batch identities missing')
    require(all(isinstance(v['loss'], (int, float)) and math.isfinite(v['loss']) for v in r['losses']), 'Native loss not finite')
    comparison, reference, common = (r[k] for k in ('original_common_initialization_comparison', 'original_common_reference', 'common_initialized_parameters'))
    require(comparison['passed'] is True and comparison['same_names'] is True and comparison['same_shapes'] is True and comparison['same_dtypes'] is True, 'Original common initialization mismatch')
    require(comparison['candidate_tensor_count'] == comparison['reference_tensor_count'] == reference['tensor_count'] == common['tensor_count'] == 841, 'Not actual common841')
    require(comparison['different_parameter_names'] == comparison['only_candidate_names'] == comparison['only_reference_names'] == [], 'Common parameters differ')
    names = reference['names']
    require(len(names) == len(set(names)) == 841 and set(names) == set(comparison['candidate_names']) == set(common['names']), 'Common names mismatch')
    require(reference['shapes'] == comparison['candidate_shapes'] == common['shapes'] and reference['dtypes'] == comparison['candidate_dtypes'], 'Common shapes/dtypes mismatch')
    require(reference['sha256'] == comparison['candidate_sha256'] == comparison['reference_sha256'] == common['sha256'], 'Common hash mismatch')
    require(reference['reference_measurement_entry_RNG_restored_exact'] is True and comparison['candidate_source_initialization_untouched'] is True, 'Common source/RNG not preserved')
    require(comparison['copied_common_weights'] is False and comparison['post_reference_rng_substituted'] is False, 'Common weights/RNG substituted')
    for step in r['steps']:
        require(step['all_observed_parameter_gradients_finite'] is True and step['nonfinite_parameter_names'] == [] and step['original_optimizer_step_completed'] is True, 'Native step invalid')
        for key in ('tracked_gradients', 'before_hash', 'after_hash', 'actual_parameter_updated'):
            require(set(step[key]) == CORE, 'Not exact nine CSO core tensors')
        require(all(g['finite'] is True and finite_positive(g['abs_max']) for g in step['tracked_gradients'].values()), 'Core gradient inactive/nonfinite')
        require(all(step['actual_parameter_updated'][n] is True and step['before_hash'][n] != step['after_hash'][n] for n in CORE), 'Core parameter did not update')
        require(step['actual_same_leaf_ordered_point_pairs'] > 0, 'No natural within-leaf covariance support')
    require(set(r['native_tracked_initial_hash']) == set(r['native_tracked_after_hash']) == CORE, 'Core identity changed')
    require(all(r['native_tracked_initial_hash'][n] != r['native_tracked_after_hash'][n] for n in CORE), 'Core final state unchanged')
    for record in r['core_calls']:
        require(record['actual_source_forward'] is True and record['actual_fine_message_delivered_to_HCG'] is True and record['input']['finite'] is True and record['output']['finite'] is True, 'Core/HCG path missing')
        for key in ('native_input_gradients', 'native_output_gradients', 'native_HCG_output_gradients'):
            gradients(record[key])
    for record in r['inst_to_mask_path_observations']:
        require(record['single_original_inst_writeback_exact'] is True and record['extra_injection'] is False, 'Original inst_feats writeback changed')
        for key in ('native_post_cluster_inst_gradients', 'native_post_ILA_inst_gradients', 'native_final_mask_gradients'):
            gradients(record[key])
    require(all(v['raw_unchanged'] is True and v['ids_unchanged'] is True and v['maps_unchanged'] is True for v in r['raw_bank_observations']), 'Raw bank changed')
    require(len(r['csort_observations']) == 4 and all(v['raw_object_identity_preserved'] is True and v['original_calls'] == 1 and v['output']['finite'] is True for v in r['csort_observations']), 'Original CSORT changed')
    support = r['covariance_support_observations']
    require(support and all(v['covariance_finite'] is True and v['full_covariance_shape'][-2:] == [8, 8] and v['cross_leaf_pairs'] == 0 and v['receiver_donor_edges'] == 0 and v['input_values_unchanged'] is True for v in support), 'Invalid full covariance support')
    require(all(any(v['forward'] == step and v['same_leaf_ordered_point_pairs'] > 0 and finite_positive(v['offdiagonal_covariance_abs_max']) for v in support) for step in (1, 2)), 'Natural full offdiagonal covariance absent')


def check_resources(r):
    require(r['optimizer_steps'] == r['native_loss_forwards'] == r['native_criterion_backwards'] == 0 and r['native_predict_calls'] == 121, 'Resource process must be predict-only')
    require((r['batch_size'], r['lang_num_max'], r['warmup'], r['repeat']) == (1, 1, 20, 100), 'Resource protocol changed')
    require(r['parameter_flags_preserved'] is True and r['source_body_executed_without_replacement'] is True and r['validation_accuracy_evaluated_for_selection'] is False, 'Resource model/protocol changed')
    values = r['measurements_ms']
    require(len(values) == 100 and all(finite_positive(x) for x in values), 'Missing real resource repeats')
    require(math.isclose(statistics.median(values), r['median_ms'], rel_tol=1e-10), 'Median mismatch')
    ordered = sorted(values)
    require(math.isclose(ordered[89] * 0.9 + ordered[90] * 0.1, r['p90_ms'], rel_tol=1e-10), 'p90 mismatch')
    require(all(finite_positive(r[k]) for k in ('parameters', 'median_ms', 'p90_ms', 'peak_allocated_bytes', 'peak_reserved_bytes')), 'Invalid resource measurements')
    require(finite_positive(r['profile']['flops']) and r['profile']['flops'] <= 10e9 and r['profile']['within10G'] is True, 'Native unchanged profiler exceeds10G or is invalid')
    require(math.isclose(r['profile']['flops'] / 1e9, r['profile']['flops_g'], rel_tol=1e-12), 'FLOPs unit summary mismatch')
    expected = {'flop_count': 'b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba',
                'jit_analysis': '110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31',
                'jit_handles': 'ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129'}
    require(r['profile']['profiler_file_sha256'] == expected, 'Resource profiler handlers changed')


def actual(mode, owner, manifest, source, frozen, protocol_review):
    path = EXECUTION / ('run_' + mode + '_candidate_actual.json')
    record = read(path)
    require(record['owner'] == owner and record['certainty'] == 'terminal' and record['returncode'] == 0, 'Actual transport not current terminal rc0')
    observation = record['observation']
    require(json.loads(record['stdout']) == observation, 'Raw transport/observation mismatch')
    require(observation['certainty'] == 'terminal' and observation['returncode'] == 0, 'Remote worker did not finish rc0')
    result = observation['result']
    require(observation['result_sha256'] == sha(json.dumps(result, indent=2, allow_nan=False).encode('utf8')), 'Raw remote result hash mismatch')
    require(result['owner'] == owner and result['execution_completed'] is True and result['mode'] == mode and result['target'] == 'candidate', 'Wrong/incomplete actual result')
    require(result['code_commit'] == SOURCE and result['candidate_id'] == manifest['candidate_id'] and result['experiment_id'] == 'M236-CSO', 'Actual source identity mismatch')
    require(result['native_model_and_yaml_unchanged'] is True and result['new_training'] == 0 and result['scientific_admission'] is False, 'Actual protocol changed')
    require(result['physical_gpu'] == 0 and result['gpu_uuid'] == GPU_UUID, 'Wrong physical GPU')
    require(result['native_manifest_sha256'] == ref(EXECUTION / 'native_manifest.json')['sha256'], 'Actual manifest mismatch')
    require(result['source_binding_sha256'] == ref(EXECUTION / 'source_binding.json')['sha256'], 'Actual source binding mismatch')
    require(result['diagnostic_worker_sha256'] == frozen['files']['worker.py'] == ref(BOUND / 'worker.py')['sha256'], 'Actual worker mismatch')
    require(result['runtime_sha256'] == frozen['files']['native_runtime.py'] == ref(BOUND / 'native_runtime.py')['sha256'], 'Actual runtime producer mismatch')
    require(result['source_hashes'] == source['candidate_source_hashes'] == manifest['candidate_source_hashes'], 'Actual source byte hashes mismatch')
    require(result['config_sha256'] == source['candidate_config_sha256'] == manifest['candidate_config_sha256'], 'Actual config bytes mismatch')
    require(result['native_train_source_sha256'] == manifest['assets']['native_train_source_sha256'], 'Native train source changed')
    require(result['stage'] == manifest['stage'] and result['goal_sha256'] == manifest['goal_sha256'] and result['config'] == manifest['config'], 'Actual manifest identity changed')
    request_path, intent_path = (EXECUTION / ('run_' + mode + '_candidate_' + suffix + '.json') for suffix in ('request', 'intent'))
    request, intent = read(request_path), read(intent_path)
    require(record['request_sha256'] == ref(request_path)['sha256'] and record['intent_sha256'] == ref(intent_path)['sha256'], 'Actual request/intent hashes do not close')
    require(request['owner'] == intent['owner'] == owner and request['mode'] == intent['mode'] == mode and request['target'] == intent['target'] == 'candidate', 'Request/intent owner or arm mismatch')
    require(request['action'] == intent['action'] == 'run' and intent['no_replay'] is True, 'Actual is not original run intent')
    require(intent['request_sha256'] == record['request_sha256'] and intent['remote_stage'] == manifest['stage'], 'Intent binding mismatch')
    require(request['native_manifest_sha256'] == result['native_manifest_sha256'] and request['source_version_sha256'] == source['source_version_sha256'], 'Request source/manifest mismatch')
    require(request['transport_sha256'] == ref(BOUND / 'run_native_once.py')['sha256'] == frozen['files']['run_native_once.py'], 'Transport producer changed')
    require(request['independent_review_sha256'] == ref(protocol_review)['sha256'], 'Protocol review differs from actual request')
    if mode == 'smoke':
        check_smoke(result)
    else:
        check_resources(result)
    return path, record, result


def generate(args):
    owner = owner_guard()
    prep = current_review(args.preparation_review, owner, 'generator_ready_passed')
    require(prep['generator_sha256'] == ref(__file__)['sha256'], 'Generator changed since preparation review')
    frozen, source, manifest, version = (read(path) for path in (BOUND / 'FROZEN.json', EXECUTION / 'source_binding.json', EXECUTION / 'native_manifest.json', BOUND / 'source_version.json'))
    require(all(v['owner'] == owner for v in (frozen, source, manifest, version)), 'Packet is not current owner6')
    require(source['source_commit'] == version['source_commit'] == manifest['code_commit'] == SOURCE, 'Packet source is not af457')
    require(source['source_parent_commit'] == version['source_parent_commit'] == manifest['source_parent_commit'] == SOURCE_PARENT, 'Original source parent changed')
    require(source['runtime_original_parent_commit'] == version['runtime_original_parent_commit'] == manifest['runtime_code_commit'] == RUNTIME, 'Original runtime b1 changed')
    require(manifest['source_binding_sha256'] == ref(EXECUTION / 'source_binding.json')['sha256'], 'Manifest source binding hash mismatch')
    require(source['source_version_sha256'] == frozen['source_version_sha256'] == ref(BOUND / 'source_version.json')['sha256'], 'Source version hash mismatch')
    require(source['source_version_proof'] == version, 'Embedded source version differs')
    for name, digest in frozen['files'].items():
        path = (BOUND / name).resolve()
        require(path.is_relative_to(BOUND) and ref(path)['sha256'] == digest, 'Frozen producer changed: ' + name)
    for item in frozen['anchors'].values():
        require(ref(ROOT / item['path'])['sha256'] == item['sha256'], 'Frozen anchor changed')
    require(manifest['physical_gpu'] == 0 and manifest['allowed_gpus'] == [0] and manifest['gpu_uuid'] == GPU_UUID, 'Manifest GPU scope changed')
    require(manifest['private_candidate_loading']['source_commit'] == SOURCE and manifest['private_candidate_loading']['runtime_head'] == RUNTIME, 'Private source/runtime identity changed')
    require(set(manifest['private_candidate_loading']['parameter_tensor_names']) == CORE and manifest['private_candidate_loading']['parameter_tensor_count'] == 9 and manifest['private_candidate_loading']['parameter_count'] == 41856, 'Core identity changed')
    protocol = current_review(args.native_protocol_review, owner, 'source_and_native_protocol_review_passed')
    for key, path in (('FROZEN_sha256', BOUND / 'FROZEN.json'), ('source_version_sha256', BOUND / 'source_version.json'), ('worker_sha256', BOUND / 'worker.py'), ('runtime_sha256', BOUND / 'native_runtime.py'), ('transport_sha256', BOUND / 'run_native_once.py')):
        require(protocol[key] == ref(path)['sha256'], 'Protocol review producer mismatch: ' + key)
    proof_path = ROOT / 'pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json'
    review_path = ROOT / 'pipeline/diagnostic_bundles/tick_7caf419d/peer_review/cso_integration_independent_review.json'
    require(ref(proof_path)['sha256'] == '41dd72acfb62ff4fc7ff690f751c820fca80536dc3b5b552a62c704ea5a99c7a', 'Historical commit proof changed')
    require(ref(review_path)['sha256'] == '04608ef80c5f5590e785038d471fe9127d501d0734c85e4adb6058cc401ace44', 'Historical integration review changed')
    proof, historical_review = read(proof_path), read(review_path)
    require(historical_review['passed'] is True and historical_review['material_concerns'] == [] and historical_review['commit_proof_sha256'] == ref(proof_path)['sha256'], 'Historical byte-association review did not pass')
    require(proof['commit'] == INTEGRATED and proof['parent_commit'] == RUNTIME and proof['native_source_commit'] == SOURCE and proof['native_source_parent_commit'] == SOURCE_PARENT, 'Historical commit identity changed')
    exact9 = proof['files_exact9_sha256']
    require(len(exact9) == 9 and source['source_files'] == version['source_files_exact9'] == exact9, 'Not the same exact nine source files')
    require({Path(p).name: digest for p, digest in exact9.items() if p.endswith('.py')} == manifest['candidate_source_hashes'], 'Manifest source files differ from exact9')
    require(exact9[manifest['config']] == manifest['candidate_config_sha256'], 'Manifest config differs from exact9')
    git_observation = verify_git(proof, exact9)
    smoke_path, smoke_record, smoke = actual('smoke', owner, manifest, source, frozen, args.native_protocol_review)
    resources_path, resources_record, resources = actual('resources', owner, manifest, source, frozen, args.native_protocol_review)
    smoke_review = current_review(args.smoke_review, owner, 'native_smoke_passed', smoke_path)
    resources_review = current_review(args.resources_review, owner, 'resource_gate_passed', resources_path)
    for reviewer in (smoke_review, resources_review):
        require(reviewer['reviewer_thread_id'] != frozen.get('author_thread_id'), 'Actual reviewer is packet author')
    input_paths = [smoke_path, resources_path, args.smoke_review, args.resources_review, args.preparation_review, args.native_protocol_review,
                   BOUND / 'FROZEN.json', BOUND / 'source_version.json', BOUND / 'worker.py', BOUND / 'native_runtime.py', BOUND / 'run_native_once.py',
                   EXECUTION / 'source_binding.json', EXECUTION / 'native_manifest.json', proof_path, review_path]
    now = datetime.now(timezone.utc).isoformat()
    evidence = {'owner': owner, 'association_recorded_at': now, 'author_thread_id': AUTHOR,
                'kind': 'DERIVED_EXACT_BYTE_VERSION_ASSOCIATION_NOT_NEW_EXECUTION', 'passed': True, 'material_concerns': [],
                'candidate_id': manifest['candidate_id'], 'experiment_id': 'M236-CSO', 'associated_code_commit': INTEGRATED,
                'actual_execution_code_commit': SOURCE, 'actual_source_parent_commit': SOURCE_PARENT, 'actual_runtime_HEAD': RUNTIME,
                'raw_execution_owners_preserved': {'smoke': smoke_record['owner'], 'resources': resources_record['owner']},
                'historical_commit_proof_owner_preserved': proof['owner'], 'historical_review_owner_preserved': historical_review['owner'],
                'files_exact9_sha256': exact9, 'current_read_only_git_observations': git_observation,
                'inputs': [ref(p) for p in input_paths], 'producer': ref(__file__),
                'native_TRAIN2': 'ACTUAL_CURRENT_OWNER_PASSED_WITH_NEW_INDEPENDENT_REVIEW',
                'resources': 'ACTUAL_CURRENT_OWNER_PASSED_WITH_NEW_INDEPENDENT_REVIEW',
                'identity_semantics': 'Exact-byte version association only: actual private worker loaded source af457 on runtime b1; integrated541 contains identical nine candidate blobs on b1. No claim that actual execution checked out integrated541.',
                'raw_actual_source_owner_or_metadata_modified': False, 'new_execution_claimed': False,
                'SSH_or_Torch_or_remote_sync_or_rerun': False, 'scientific_admission': False, 'efficacy': 'UNKNOWN', 'novelty': 'UNKNOWN'}
    outputs = ['version_bound_evidence.json', 'native_smoke.version_bound.json', 'resources.version_bound.summary.json']
    require(all(not (HERE / name).exists() for name in outputs), 'Derived outputs already exist; never overwrite or re-sign')
    require(datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at']), 'Owner expired during verification')
    for path, digest in READSET.items():
        require(sha(path.read_bytes()) == digest, 'Input changed before publication: ' + str(path))
    def save(name, value):
        with (HERE / name).open('x', encoding='utf8', newline='\n') as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
    save(outputs[0], evidence)
    association = ref(HERE / outputs[0])
    derived_smoke = {'id': 'M236-CSO', 'candidate_id': manifest['candidate_id'], 'config': manifest['config'], 'code_commit': INTEGRATED,
                     'goal_sha256': smoke['goal_sha256'], 'steps': 2, 'losses': [v['loss'] for v in smoke['losses']],
                     'native_data_loaded': True, 'backward_finite': True, 'intended_path_observed': True, 'split': 'train',
                     'command': smoke['actual_train_command'], 'data_source': smoke['data_source']['train'],
                     'evidence': [ref(smoke_path), ref(args.smoke_review), association, ref(EXECUTION / 'source_binding.json'), ref(BOUND / 'source_version.json')],
                     'normalization_owner': owner, 'normalization_recorded_at': now, 'original_execution_owner': smoke['owner'],
                     'original_execution_observed_at': smoke['observed_at'], 'original_execution_code_commit': SOURCE,
                     'original_source_parent_commit': SOURCE_PARENT, 'runtime_original_parent_commit': RUNTIME, 'version_association': association,
                     'derivation': 'Steps/losses/flags retain exact current raw observations. code_commit541 is a separately proven exact-byte association; raw actual sourceaf457 and owner remain unchanged.',
                     'new_execution_claimed': False, 'scientific_admission': False, 'efficacy': 'UNKNOWN', 'novelty': 'UNKNOWN'}
    summary = {'owner': owner, 'recorded_at': now, 'candidate_id': manifest['candidate_id'], 'experiment_id': 'M236-CSO',
               'associated_code_commit': INTEGRATED, 'actual_execution_code_commit': SOURCE, 'actual_runtime_HEAD': RUNTIME,
               'resource_gate_passed': True, 'actual': ref(resources_path), 'actual_independent_review': ref(args.resources_review), 'version_association': association,
               'batch_size': resources['batch_size'], 'lang_num_max': resources['lang_num_max'], 'warmup': resources['warmup'], 'repeat': resources['repeat'],
               'parameters': resources['parameters'], 'flops_g': resources['profile']['flops_g'], 'median_ms': resources['median_ms'], 'p90_ms': resources['p90_ms'],
               'peak_allocated_bytes': resources['peak_allocated_bytes'], 'peak_reserved_bytes': resources['peak_reserved_bytes'],
               'measurement_scope': resources['measurement_scope'], 'exclusive_measurement_claimed': False,
               'full_optimizer_training_peak': resources['full_optimizer_training_peak'], 'original_no_cluster_resource_delta': resources['original_no_cluster_resource_delta'],
               'validation_accuracy_evaluated_for_selection': False, 'scientific_admission': False, 'efficacy': 'UNKNOWN', 'novelty': 'UNKNOWN'}
    save(outputs[1], derived_smoke)
    save(outputs[2], summary)
    print(json.dumps({'status': 'DERIVED_BYTE_ASSOCIATION_ONLY_NO_ADMISSION', 'outputs': [ref(HERE / p) for p in outputs]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--preparation-review', type=Path, default=TICK / 'peer_review/cso_version_binding_prepare_independent_review.json')
    parser.add_argument('--native-protocol-review', type=Path, default=TICK / 'peer_review/cso_native_bound_independent_review.json')
    parser.add_argument('--smoke-review', type=Path, default=TICK / 'peer_review/cso_native_smoke_actual_independent_review.json')
    parser.add_argument('--resources-review', type=Path, default=TICK / 'peer_review/cso_resources_actual_independent_review.json')
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'status': 'NOT_RUN_DEFAULT_NOP', 'actual_native_gate_claimed': False, 'actual_resource_gate_claimed': False, 'scientific_admission': False}))
        return
    try:
        generate(args)
    except Exception as error:
        print(json.dumps({'status': 'FAIL_CLOSED_NO_ADMISSION', 'error_type': type(error).__name__, 'error': str(error)}))
        raise SystemExit(2)


if __name__ == '__main__':
    main()
