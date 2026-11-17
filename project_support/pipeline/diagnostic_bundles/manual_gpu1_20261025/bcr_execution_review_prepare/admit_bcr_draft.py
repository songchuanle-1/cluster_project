"""Owning-root BCR admission draft, derived from dfb6440d/admit_psbr.py.

Default is read-only checks. Only --execute-root permits the original
standard-artifact/decision/receipt/canonical-waiting writes after actual gates.
This script never syncs source, dispatches, connects remotely, or runs a model.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
TICK = ROOT/'pipeline/diagnostic_bundles/tick_7526f819'
EXECUTION = TICK/'bcr_gpu1_execution'
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN = '7526f819f16e4f688566119d347cd198'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
CID = 'hierarchy-parent-bidirectional-complement-recurrence'
EXP = 'M212-BCR'
COMMIT = '11a811618179ab1ddc0cee299194667413b7fdb9'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
CONFIG = 'configs/Quard/ctf_hcg_csort_bcr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr.yaml'
REVIEW = HERE/'actual_four_result_review.json'
REVIEW_SHA = None  # Supplied only after an actual local four-result report exists.
REVIEWER_SHA = None  # Owning root must pass the exact independently reviewed checker SHA.
EXPECTED_INDEPENDENT_STATUS = 'FOUR_ACTUAL_BCR_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
EXPECTED_AUTHORIZATION = {'path': 'pipeline/authorizations/experiment_first_20261021.json', 'sha256': '2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'}
GPU1_GRANT = {'path': 'pipeline/authorizations/server4_gpu1_20261025.json', 'sha256': '90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8'}
PAIRS = [('smoke', 'champion'), ('smoke', 'candidate'), ('resources', 'champion'), ('resources', 'candidate')]


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'Evidence outside project')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def save(path, value, exclusive=False):
    path = Path(path)
    if exclusive:
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
    else:
        temporary = path.with_name(path.name+'.'+TOKEN+'.tmp')
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT/'Cluster'), *args], text=True, encoding='utf-8').strip()


def current_owner():
    owner = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    mode = read(ROOT/'pipeline/execution_mode.json')
    require(owner['token'] == TOKEN and owner['thread_id'] == mode['target_thread_id'] == os.environ.get('CODEX_THREAD_ID') == THREAD,
            'Actual current root owner/environment/target mismatch; never override the thread')
    require(datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at']), 'Original deadline expired')
    require(sha(ROOT/'pipeline/headless/.tick_context.json') == owner['context_sha256'] and
            sha(ROOT/'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256'], 'Current context/pending changed')
    require(sha(ROOT/'pipeline/goal.json') == GOAL, 'Goal changed')
    return owner


def source_checks(manifest):
    require(git('rev-parse', 'HEAD') == COMMIT, 'Main HEAD must actually equal tested11a before formal admission')
    require(not git('diff', '--cached', '--name-only'), 'Index is not empty')
    protected = read(ROOT/'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json')['protected_existing_worktree']
    status = subprocess.check_output(['git', '-C', str(ROOT/'Cluster'), 'status', '--porcelain', '--untracked-files=all'], text=True, encoding='utf-8')
    require({(line[:2], line[3:]) for line in status.splitlines() if line} == {(x['status'], x['path']) for x in protected}, 'Protected28 status changed')
    require(all(sha(ROOT/'Cluster'/x['path']) == x['sha256'] for x in protected), 'Protected28 bytes changed')
    source = ROOT/'Cluster/framework/model/Quard_model'/manifest['candidate_name']
    require(len(manifest['candidate_source_hashes']) == 8, 'Wrong source inventory')
    for name, expected in manifest['candidate_source_hashes'].items():
        path = source/name
        require(sha(path) == expected, 'Actual source differs from tested manifest: '+name)
        blob = subprocess.check_output(['git', '-C', str(ROOT/'Cluster'), 'show', COMMIT+':'+path.relative_to(ROOT/'Cluster').as_posix()])
        require(hashlib.sha256(blob).hexdigest() == expected, 'Admitted Git blob differs: '+name)
    require(manifest['config'] == CONFIG and sha(ROOT/'Cluster'/CONFIG) == manifest['candidate_config_sha256'], 'Native config hash changed')
    config_blob = subprocess.check_output(['git', '-C', str(ROOT/'Cluster'), 'show', COMMIT+':'+CONFIG])
    require(hashlib.sha256(config_blob).hexdigest() == manifest['candidate_config_sha256'], 'Native YAML Git11a blob differs')
    old_config = ROOT/'Cluster/configs/Quard/ctf_hcg_csort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml'
    require((ROOT/'Cluster'/CONFIG).read_bytes() == old_config.read_bytes(), 'Original native YAML bytes changed')


def actual_checks(independent_path, independent_sha):
    owner = current_owner()
    require(isinstance(REVIEW_SHA,str) and len(REVIEW_SHA)==64 and isinstance(REVIEWER_SHA,str) and len(REVIEWER_SHA)==64,'Actual local report/checker SHA must be explicitly bound; draft cannot assume results')
    require(sha(ROOT/GPU1_GRANT['path'])==GPU1_GRANT['sha256'],'Exact explicit GPU1 grant missing/changed')
    require(sha(REVIEW) == REVIEW_SHA and sha(HERE/'review_bcr.py') == REVIEWER_SHA, 'Actual semantic review/source changed')
    independent_path = Path(independent_path).resolve()
    require(independent_path.is_relative_to(ROOT) and sha(independent_path) == independent_sha, 'Independent review path/SHA mismatch')
    independent = read(independent_path)
    require(independent['status'] == EXPECTED_INDEPENDENT_STATUS and independent['material_concerns'] == [], 'Independent semantics/resource review did not pass')
    require((independent['candidate_id'], independent['code_commit'], independent['goal_sha256']) == (CID, COMMIT, GOAL), 'Independent review identity mismatch')
    for mode, target in PAIRS:
        matches = [x for x in independent['raw_results'] if x['mode'] == mode and x['target'] == target]
        require(len(matches) == 1, 'Independent raw pair missing/ambiguous')
        item = matches[0]; expected = EXECUTION/(mode+'_'+target+'_execution.json')
        require((ROOT/item['execution_path']).resolve() == expected.resolve() and sha(expected) == item['execution_sha256'], 'Independent raw artifact drift')
        envelope = read(expected)
        require(item['result_sha256'] == envelope['result_sha256'] and item['request_id'] == envelope['identity']['request_id'], 'Independent original request/result mismatch')
    spec = importlib.util.spec_from_file_location('actual_bcr_semantics', HERE/'review_bcr.py')
    reviewer = importlib.util.module_from_spec(spec); spec.loader.exec_module(reviewer)
    fresh = reviewer.review_directory(ROOT, EXECUTION)
    reviewed = read(REVIEW)
    require(fresh['review_status'] == reviewed['review_status'] == 'RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' and fresh['observations'] == reviewed['observations'], 'Current raw semantics no longer match actual review')
    require(fresh['observations']['existing_memory_condition_needs_separate_retention_decision'] is False, 'Original memory-retention condition needs a separate real decision')
    binding = read(EXECUTION/'execution_binding.json'); manifest = read(EXECUTION/'native_manifest.json')
    require(binding['owner'] == {k: owner[k] for k in binding['owner']} and binding['physical_gpu'] == 1, 'Execution is not this original current owner/binding')
    source_checks(manifest)
    policy = read(ROOT/'pipeline/closure_policy.json'); auth = policy['experiment_first']['authorization']
    require(policy['enabled'] is True and policy['experiment_first']['enabled'] is True and auth==EXPECTED_AUTHORIZATION and sha(ROOT/auth['path']) == auth['sha256'], 'Current experiment-first authorization changed')
    import yaml
    server=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
    require(1 in server['allowed_gpus'] and server['max_tasks_per_gpu']==1 and server['dispatch_enabled'] is True and server['host']=='192.168.1.115' and server['expected_hostname']=='dl04-MS-7E06','Current GPU1 resource eligibility changed')
    require(str(server['expected_gpu_uuids'].get(1,server['expected_gpu_uuids'].get('1')))=='GPU-7f82edb9-f620-8045-caea-a75232265cd1','GPU1 UUID changed')
    return owner, fresh, manifest, auth


def main():
    global REVIEW_SHA, REVIEWER_SHA
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-review-sha',required=True)
    parser.add_argument('--reviewer-sha',required=True)
    parser.add_argument('--independent-review', required=True)
    parser.add_argument('--independent-sha', required=True)
    parser.add_argument('--execute-root', action='store_true', help='Root-reviewed explicit standard/receipt/waiting writes; never launches')
    args = parser.parse_args()
    REVIEW_SHA,REVIEWER_SHA=args.local_review_sha,args.reviewer_sha
    owner, review, manifest, auth = actual_checks(args.independent_review, args.independent_sha)
    if not args.execute_root:
        print(json.dumps({'status': 'ACTUAL_CHECKS_ONLY_NO_STANDARD_OR_SHARED_WRITES', 'id': EXP, 'code_commit': COMMIT,
                          'standard_PASS_receipt_queue_written': False, 'training_launched': False}))
        return
    sys.path.insert(0, str(SKILL))
    import closure
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT)); require(lock is not None, 'Canonical pipeline lock busy')
    try:
        owner, review, manifest, auth = actual_checks(args.independent_review, args.independent_sha)
        queue = monitor.load_queue(str(ROOT)); work = read(ROOT/'pipeline/research_work.json')
        require(not any(t.get('id') == EXP for ts in queue['gpu_queues'].values() for t in ts) and monitor.load_experiment(str(ROOT), EXP) is None, 'Existing experiment cannot be admitted twice')
        candidate = next(c for c in work['candidates'] if c['id'] == CID)
        require(candidate['stage'] == 'validation' and candidate['code_commit'] == COMMIT and candidate['authorization'] == auth, 'Candidate is not current validation11a')
        require(not candidate.get('revision_history') and not any(candidate.get(k) for k in ['human_hold', 'scope_hold', 'numerical_hold', 'dispatch_hold', 'hold']), 'Candidate hold/revision cannot be bypassed')
        btc_before = copy.deepcopy(next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M211-BTC'))
        require(btc_before['status']=='running' and str(btc_before['gpu'])=='0' and btc_before['pid']==2784474 and btc_before['launch_verified'] is True,'Protected BTC0 identity changed; root must reconcile actual state')
        btc_experiment_path=ROOT/'pipeline/experiments/M211-BTC.json';btc_experiment_sha=sha(btc_experiment_path)
        btc_receipt_path=ROOT/btc_before['admission_receipt'];btc_receipt_sha=sha(btc_receipt_path)
        m206_before = copy.deepcopy(next(t for t in queue['gpu_queues']['server-4'] if t['id'] == 'M206-CGCA'))
        raws = {mode+'_'+target: read(EXECUTION/(mode+'_'+target+'_execution.json'))['result'] for mode, target in PAIRS}
        smoke = raws['smoke_candidate']; observation = review['observations']; now = datetime.now(timezone.utc).isoformat()
        evidence = [ref(EXECUTION/(mode+'_'+target+'_execution.json')) for mode, target in PAIRS]
        evidence += [ref(EXECUTION/n) for n in ['execution_binding.json', 'native_manifest.json', 'execution_lease.json']]
        evidence += [ref(REVIEW), ref(Path(args.independent_review)), ref(Path(__file__))]
        evidence.append(GPU1_GRANT)
        identity = {'id': EXP, 'candidate_id': CID, 'config': CONFIG, 'code_commit': COMMIT, 'goal_sha256': GOAL}
        standard_smoke = {**identity, 'steps': smoke['optimizer_steps'], 'losses': smoke['losses'],
            'native_data_loaded': smoke['native_data_loaded'], 'backward_finite': smoke['backward_finite'],
            'intended_path_observed': smoke['intended_path_observed'], 'split': 'train', 'command': smoke['actual_train_command'],
            'data_source': smoke['data_source']['train'], 'native_train_cli_reference': smoke['native_train_cli_reference'],
            'paired_TRAIN_batches': smoke['batches'], 'common_initialized_parameter_observations': observation['common_initialized_parameter_observations'],
            'actual_n_ge3_supported_parent_group_counts': observation['actual_n_ge3_supported_parent_group_counts'],
            'actual_map_call_counts': observation['actual_map_call_counts'],
            'actual_depth_ge2_scan_call_counts': observation['actual_depth_ge2_scan_call_counts'],
            'actual_required_weight_blocks': observation['actual_required_weight_blocks'],
            'evidence': evidence, 'recorded_at': now, 'limitations': {'training_efficacy': 'UNKNOWN', 'full_buffer_values': 'NOT_RECORDED',
            'offdiagonal_probe': 'NOT_IMPLEMENTED_NOT_MEASURED',
            'empty_padding_singleton_coverage': {k: observation[k] for k in ['actual_unsupported_internal_rows', 'actual_padding_rows', 'actual_supported_singleton_groups']},
            'raw_cross_target_digest_scope': observation['raw_bank_digest_scope'], 'pure_TRAIN_memory': smoke['pure_training_peak_memory']}}
        resources = {**identity, 'passed_existing_resource_requirements': True, 'recorded_at': now,
            'protocol': {'batch_size': 1, 'lang_num_max': 1, 'warmup': 20, 'repeat': 100, 'counted_flops_limit': 10e9},
            'observations': observation['resource_observations'], 'evidence': evidence,
            'limitations': 'Original handlers and full unsupported dictionaries retained. Counted FLOPs do not include all actual CPU/Python work. Smoke memory includes observer/topology/source-recording overhead; pure TRAIN memory and efficacy UNKNOWN.'}
        constraints = {**identity, 'passed': True, 'recorded_at': now, 'checks': {
            'current_main_HEAD_equals_actual_tested11a': True, 'eight_sources_and_YAML_equal_manifest_and_Git11a': True,
            'all28_protected_status_and_bytes_unchanged_index_empty': True, 'original_YAML_seed_schedule_data_optimizer': True,
            'actual_two_TRAIN_batches_and_common_named_initialization_paired': True, 'original_FPS_rawbanks_CSORT_HCG_single_injection': True,
            'only_replaced_middle_FFN_with_original_skip_shared_scan_readout_no_new_gate_language_route_QKV_or_residual_path': True},
            'structural_change': 'Replace only original middle FFN delta with original-parent geometry-ordered exclusive prefix/suffix recurrence. One shared scan and one own/left/right readout have328192 parameters replacing525568, actual total delta-197376. Keep original cf skip/LayerNorm, fine/coarse FFNs, raw CSORT/FPS/IDs/HCG and single inst update. Native five weight-block gradients/updates and consumed depth2 nonzero prior-state loss path were actually reviewed.',
            'source_hashes': manifest['candidate_source_hashes'], 'config_sha256': manifest['candidate_config_sha256'],
            'frozen_native_preparation': ref(ROOT/candidate['worker_preparation']['preparation']['path']),
            'evidence': evidence, 'research_scope': 'Experiment-first technical admission only. No efficacy/whole-mechanism novelty claim; earlier PSBR/HRC/HAP realizations do not reject BCR or all hierarchy.',
            'resources': 'Only server4 physicalGPU1/max1 under exact grant90f. Existing GPU0 BTC is protected. M206 remains paused despite allowed GPU1. This creates waiting work, not launch or sync.'}
        paths = {'smoke': TICK/'bcr_native_smoke.json', 'resources': TICK/'bcr_resource_comparison.json', 'constraints': TICK/'bcr_constraints_independence.json'}
        receipt_path = ROOT/'pipeline/admissions'/f'{EXP}.json'
        require(not receipt_path.exists() and not any(p.exists() for p in paths.values()), 'Refuse overwriting existing standard artifacts/receipt')
        for kind, value in [('smoke', standard_smoke), ('resources', resources), ('constraints', constraints)]:
            save(paths[kind], value, exclusive=True)
        decision_args = ['C:/Program Files (x86)/Git/bin/bash.exe', str(SKILL/'log_decision.sh'), 'cluster_project', 'queue_push',
            'Admit BCR11a after actual paired native and resource review', 'Queue exact tested M212-BCR on authorized GPU1',
            'Actual original TRAIN2/native gradients/FFN0/2 and shared scan/readout and five weight-block updates/original-middle-skip-HCG-inst path and matched resource pair independently reviewed. Preserve all numeric readouts and unsupported ops; unexercised zero/padding/singleton boundaries and offdiagonal probe, pure TRAIN memory and efficacy remain unknown. No new threshold/revision/seed/data/schedule/GPU grant.',
            '; '.join(x['path']+' SHA'+x['sha256'] for x in [ref(p) for p in paths.values()]+[ref(Path(args.independent_review))])]
        decision_run = subprocess.run(decision_args, capture_output=True, text=True, encoding='utf-8', timeout=30, env=os.environ.copy())
        require(decision_run.returncode == 0, 'Decision logger failed: '+decision_run.stderr)
        decision = Path(decision_run.stdout.strip().split('-> ', 1)[1].strip())
        receipt = {**identity, 'profile': 'experiment_first', 'authorization': auth, 'native_smoke': ref(paths['smoke']),
            'decision': ref(decision), 'created_at': now, 'independent_review': ref(Path(args.independent_review)),
            'gates': {name: {'passed': True, 'evidence': [ref(paths[kind]), ref(Path(args.independent_review))]}
                      for name, kind in [('native_backward', 'smoke'), ('resources', 'resources'), ('independence', 'constraints'), ('constraints', 'constraints')]},
            'efficacy': 'UNKNOWN until actual original formal training; admission is not accuracy gain.'}
        task = {'id': EXP, 'label': 'BCR exclusive bidirectional complement recurrence', 'config': CONFIG, 'code_commit': COMMIT,
            'admission_receipt': receipt_path.relative_to(ROOT).as_posix(), 'status': 'waiting', 'gpu': '1', 'server': 'server-4',
            'profile': 'experiment_first', 'requires_exclusive_ownership': True, 'added_at': now,
            'note': 'Original byte-identical native YAML/seed1999/epochs50/maxiters70; actual paired diagnostic TRAIN2 and resources reviewed. GPU1 only; BTC0 and M206 pause protected. Diagnostic admission is not efficacy.'}
        current_owner()
        save(receipt_path, receipt, exclusive=True)
        closure.admission(ROOT, task)
        prospective = copy.deepcopy(queue); prospective['gpu_queues']['server-4'].append(task)
        closure.validate_foreground_dispatch_budget(ROOT, prospective, task)
        candidate.setdefault('execution_preparation_history', []).append({
            'recorded_at': now, 'reason': 'Preserve original externally anchored unexecuted preparation state before actual four-arm admission.',
            'current_status_fields': {k: copy.deepcopy(candidate.get(k)) for k in [
                'config_status', 'source_status', 'native_status', 'resource_status', 'native_worker_adapter',
                'implementation_status', 'native_execution_code_commit', 'native_smoke_status', 'resource_profile_status', 'admission_status']},
            'worker_preparation': copy.deepcopy(candidate['worker_preparation']),
            'execution_adapter': copy.deepcopy(candidate['execution_adapter'])})
        candidate.update(stage='deployment', training_status='waiting', native_status='actual_TRAIN2_backward_exclusive_recurrence_five_weight_blocks_observed',
            resource_status='actual_original_protocol_pair_passed', experiment_first_admission=True, admission_receipt=ref(receipt_path),
            native_execution=ref(REVIEW), native_execution_code_commit=COMMIT,
             native_smoke_status='ACTUAL_TRAIN2_PASSED', resource_profile_status='ACTUAL_PAIRED_RESOURCES_PASSED', admission_status='ADMITTED_WAITING',
            config_status='Exact original YAML is now verified in main Git11a and actual native smoke/resources.',
            source_status='TESTED11A_PRESENT_MAIN_ACTUAL_NATIVE_PAIR_VERIFIED',
            native_worker_adapter='ACTUAL_FRESH_BINDING_FOUR_ARMS_TERMINAL_REVIEWED',
            implementation_status='ACTUAL_NATIVE_TRAIN2_AND_RESOURCE_PAIR_VERIFIED',
            next_action='Exact tested BCR11a admitted waiting on only GPU1. Canonical fresh dispatch must recheck source/runtime/assets/idle/exclusive ownership and actual progress. Do not touch GPU0 BTC, resume M206 or alter original seed/YAML/schedule.')
        for key in ['blocker_kind', 'blocker', 'blocked_at', 'retry_after', 'unblock_condition']:
            candidate.pop(key, None)
        candidate['worker_preparation'].update(status='ACTUAL_NATIVE_TRAIN2_AND_RESOURCES_COMPLETED_PASSED',
            native_backward_passed=True, resources_passed=True, native_backward_executed=True,
            resource_profile_executed=True, active_native_manifest_or_execution_lease_created=True)
        candidate['execution_adapter'].update(status='ACTUAL_FRESH_BINDING_FOUR_ARMS_TERMINAL_REVIEWED',
            native_execution_tested=True, native_execution_code_commit=COMMIT,
            remote_adapter_execution_tested=True, active_binding_manifest_lease_created=True, standard_summaries_created=True,
            standard_result_formatter_implemented=True, standard_result_formatter=ref(Path(__file__)),
            active_binding=ref(EXECUTION/'execution_binding.json'), native_manifest=ref(EXECUTION/'native_manifest.json'),
            execution_lease=ref(EXECUTION/'execution_lease.json'), actual_four_result_review=ref(REVIEW),
            execution_results={mode+'_'+target: ref(EXECUTION/(mode+'_'+target+'_execution.json')) for mode, target in PAIRS},
            provenance='Root used the existing reviewed static catalog with a fresh exact owner/assets/idleGPU1/three-lock binding. Four original M95/BCR GPU1 smoke/resource requests completed terminal with independent semantic review. Original immutable request/terminal/result identities are retained; no unrecorded retry or idleness proof is inferred. The frozen preparation/release remain unchanged historical/static anchors; actual execution is separately bound here. This is diagnostic admission, not formal training or efficacy.')
        for path in [*paths.values(), receipt_path, decision, REVIEW, Path(args.independent_review), Path(__file__)]:
            item = ref(path)
            if item not in candidate['evidence']:
                candidate['evidence'].append(item)
        work['updated_at'] = now; save(ROOT/'pipeline/research_work.json', work)
        monitor.save_queue(str(ROOT), prospective)
        experiment = copy.deepcopy(task)
        experiment['history'] = [{'ts': now, 'status': 'waiting', 'action': 'actual_experiment_first_admission_queued', 'receipt': ref(receipt_path)}]
        monitor.save_experiment(str(ROOT), experiment)
        require(next(t for t in monitor.load_queue(str(ROOT))['gpu_queues']['server-4'] if t['id'] == 'M206-CGCA') == m206_before, 'Protected M206 changed')
        require(next(t for t in monitor.load_queue(str(ROOT))['gpu_queues']['server-4'] if t['id']=='M211-BTC')==btc_before and sha(btc_experiment_path)==btc_experiment_sha and sha(btc_receipt_path)==btc_receipt_sha,'Protected BTC0 queue/experiment/receipt changed')
        result = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'token': TOKEN, 'task': task, 'receipt': ref(receipt_path),
            'decision': ref(decision), 'standard_artifacts': {k: ref(v) for k, v in paths.items()},
            'canonical_admission_validated': True, 'canonical_tick_budget_validated': True, 'm206_queue_unchanged': True,
            'training_launched': False, 'source_synced': False, 'BTC0_queue_experiment_receipt_unchanged':True, 'GPU1_resource_grant':GPU1_GRANT}
        save(TICK/'bcr_admission_queue_result.json', result, exclusive=True)
        print(json.dumps({'id': EXP, 'status': 'waiting', 'receipt': ref(receipt_path), 'training_launched': False, 'source_synced': False, 'BTC0_queue_experiment_receipt_unchanged':True, 'GPU1_resource_grant':GPU1_GRANT}, ensure_ascii=False))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
