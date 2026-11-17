"""Owning-root PSNC admission draft, derived from dfb6440d/admit_psbr.py.

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
TICK = HERE.parent
EXECUTION = TICK/'psnc_execution'
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN = 'a4f7314098ed4dbd8351aa005661583d'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
CID = 'hierarchy-parent-spectral-nonlinear-token-coupling'
EXP = 'M210-PSNC'
COMMIT = '43dce016c1a1713c2a5dab7061810dc2efde8954'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
CONFIG = 'configs/Quard/ctf_hcg_csort_psnc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psnc.yaml'
REVIEW = HERE/'actual_four_result_review.json'
REVIEW_SHA = '69ca0aee312744106885d2f617b5ca8369436e20a952363b66d4317c811d7563'
REVIEWER_SHA = '363b0c49569d4e560f979d757fcbaff113f7783ff1a5bbdab7ba866e6f3653ca'
EXPECTED_INDEPENDENT_STATUS = 'FOUR_ACTUAL_PSNC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
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
    require(git('rev-parse', 'HEAD') == COMMIT, 'Main HEAD must actually equal tested43 before formal admission')
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
    require(hashlib.sha256(config_blob).hexdigest() == manifest['candidate_config_sha256'], 'Native YAML Git43 blob differs')
    old_config = ROOT/'Cluster/configs/Quard/ctf_hcg_csort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml'
    require((ROOT/'Cluster'/CONFIG).read_bytes() == old_config.read_bytes(), 'Original native YAML bytes changed')


def actual_checks(independent_path, independent_sha):
    owner = current_owner()
    require(sha(REVIEW) == REVIEW_SHA and sha(HERE/'review_psnc.py') == REVIEWER_SHA, 'Actual semantic review/source changed')
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
    spec = importlib.util.spec_from_file_location('actual_psnc_semantics', HERE/'review_psnc.py')
    reviewer = importlib.util.module_from_spec(spec); spec.loader.exec_module(reviewer)
    fresh = reviewer.review_directory(ROOT, EXECUTION)
    reviewed = read(REVIEW)
    require(fresh['review_status'] == reviewed['review_status'] == 'RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' and fresh['observations'] == reviewed['observations'], 'Current raw semantics no longer match actual review')
    require(fresh['observations']['existing_memory_condition_needs_separate_retention_decision'] is False, 'Original memory-retention condition needs a separate real decision')
    binding = read(EXECUTION/'execution_binding.json'); manifest = read(EXECUTION/'native_manifest.json')
    require(binding['owner'] == {k: owner[k] for k in binding['owner']} and binding['physical_gpu'] == 0, 'Execution is not this original current owner/binding')
    source_checks(manifest)
    policy = read(ROOT/'pipeline/closure_policy.json'); auth = policy['experiment_first']['authorization']
    require(policy['enabled'] is True and policy['experiment_first']['enabled'] is True and sha(ROOT/auth['path']) == auth['sha256'], 'Current experiment-first authorization changed')
    return owner, fresh, manifest, auth


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--independent-review', required=True)
    parser.add_argument('--independent-sha', required=True)
    parser.add_argument('--execute-root', action='store_true', help='Root-reviewed explicit standard/receipt/waiting writes; never launches')
    args = parser.parse_args()
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
        require(candidate['stage'] == 'validation' and candidate['code_commit'] == COMMIT and candidate['authorization'] == auth, 'Candidate is not current validation43')
        require(not candidate.get('revision_history') and not any(candidate.get(k) for k in ['human_hold', 'scope_hold', 'numerical_hold', 'dispatch_hold', 'hold']), 'Candidate hold/revision cannot be bypassed')
        m206_before = copy.deepcopy(next(t for t in queue['gpu_queues']['server-4'] if t['id'] == 'M206-CGCA'))
        raws = {mode+'_'+target: read(EXECUTION/(mode+'_'+target+'_execution.json'))['result'] for mode, target in PAIRS}
        smoke = raws['smoke_candidate']; observation = review['observations']; now = datetime.now(timezone.utc).isoformat()
        evidence = [ref(EXECUTION/(mode+'_'+target+'_execution.json')) for mode, target in PAIRS]
        evidence += [ref(EXECUTION/n) for n in ['execution_binding.json', 'native_manifest.json', 'execution_lease.json']]
        evidence += [ref(REVIEW), ref(Path(args.independent_review)), ref(Path(__file__))]
        identity = {'id': EXP, 'candidate_id': CID, 'config': CONFIG, 'code_commit': COMMIT, 'goal_sha256': GOAL}
        standard_smoke = {**identity, 'steps': smoke['optimizer_steps'], 'losses': smoke['losses'],
            'native_data_loaded': smoke['native_data_loaded'], 'backward_finite': smoke['backward_finite'],
            'intended_path_observed': smoke['intended_path_observed'], 'split': 'train', 'command': smoke['actual_train_command'],
            'data_source': smoke['data_source']['train'], 'native_train_cli_reference': smoke['native_train_cli_reference'],
            'paired_TRAIN_batches': smoke['batches'], 'common_initialized_parameter_observations': observation['common_initialized_parameter_observations'],
            'spectral_nonsingleton_group_counts': observation['actual_spectral_nonsingleton_group_counts'],
            'spectral_numeric_observations': {k: observation[k] for k in ['analysis_synthesis_reference_max_abs_error', 'QtQ_max_abs_error_observed', 'numeric_scope']},
            'evidence': evidence, 'recorded_at': now, 'limitations': {'training_efficacy': 'UNKNOWN', 'full_buffer_values': 'NOT_RECORDED',
            'offdiagonal_probe': 'NOT_IMPLEMENTED_NOT_MEASURED', 'zero_singleton_affine_identityQ_FP32': 'NOT_RUN',
            'empty_padding_singleton_coverage': {k: observation[k] for k in ['actual_unsupported_internal_rows', 'actual_padding_rows', 'actual_supported_singleton_groups']},
            'raw_cross_target_digest_scope': observation['raw_bank_digest_scope'], 'pure_TRAIN_memory': smoke['pure_training_peak_memory']}}
        resources = {**identity, 'passed_existing_resource_requirements': True, 'recorded_at': now,
            'protocol': {'batch_size': 1, 'lang_num_max': 1, 'warmup': 20, 'repeat': 100, 'counted_flops_limit': 10e9},
            'observations': observation['resource_observations'], 'evidence': evidence,
            'limitations': 'Original handlers and full unsupported dictionaries retained. Counted FLOPs do not include all actual CPU/Python work. Smoke memory includes observer/reference overhead; pure TRAIN memory and efficacy UNKNOWN.'}
        constraints = {**identity, 'passed': True, 'recorded_at': now, 'checks': {
            'current_main_HEAD_equals_actual_tested43': True, 'eight_sources_and_YAML_equal_manifest_and_Git43': True,
            'all28_protected_status_and_bytes_unchanged_index_empty': True, 'original_YAML_seed_schedule_data_optimizer': True,
            'actual_two_TRAIN_batches_and_common_named_initialization_paired': True, 'original_FPS_rawbanks_CSORT_HCG_single_injection': True,
            'no_new_parameters_gate_language_route_QKV_or_residual_path': True},
            'structural_change': 'Original middle FFN is evaluated in a fixed parent-wise geometry-ordered orthogonal DCT domain and inverse-synthesized with same-call differentiable f0 correction; original middle skip and all original parameters remain. Fine/coarse, raw CSORT banks, FPS/IDs/HCG and final inst_feats injection are retained.',
            'source_hashes': manifest['candidate_source_hashes'], 'config_sha256': manifest['candidate_config_sha256'],
            'frozen_native_preparation': ref(ROOT/'pipeline/diagnostic_bundles/tick_42ce600b/psnc_operational_prepare/native/preparation.json'),
            'evidence': evidence, 'research_scope': 'Experiment-first technical admission only. No efficacy/whole-mechanism novelty claim; earlier PSBR/HRC/HAP realizations do not reject PSNC or all hierarchy.',
            'resources': 'Only server4 physicalGPU0/max1. M206 remains paused; GPU1 released. This creates waiting work, not launch or sync.'}
        paths = {'smoke': TICK/'psnc_native_smoke.json', 'resources': TICK/'psnc_resource_comparison.json', 'constraints': TICK/'psnc_constraints_independence.json'}
        receipt_path = ROOT/'pipeline/admissions'/f'{EXP}.json'
        require(not receipt_path.exists() and not any(p.exists() for p in paths.values()), 'Refuse overwriting existing standard artifacts/receipt')
        for kind, value in [('smoke', standard_smoke), ('resources', resources), ('constraints', constraints)]:
            save(paths[kind], value, exclusive=True)
        decision_args = ['C:/Program Files (x86)/Git/bin/bash.exe', str(SKILL/'log_decision.sh'), 'cluster_project', 'queue_push',
            'Admit PSNC43 after actual paired native and resource review', 'Queue exact tested M210-PSNC on authorized GPU0',
            'Actual original TRAIN2/native gradients/FFN updates/spectral-HCG-inst path and matched resource pair independently reviewed. Preserve all numeric readouts and unsupported ops; zero/singleton/affine/QI and offdiagonal probes, pure TRAIN memory and efficacy remain unknown. No new threshold/revision/seed/data/schedule/GPU grant.',
            '; '.join(x['path']+' SHA'+x['sha256'] for x in [ref(p) for p in paths.values()]+[ref(Path(args.independent_review))])]
        decision_run = subprocess.run(decision_args, capture_output=True, text=True, encoding='utf-8', timeout=30, env=os.environ.copy())
        require(decision_run.returncode == 0, 'Decision logger failed: '+decision_run.stderr)
        decision = Path(decision_run.stdout.strip().split('-> ', 1)[1].strip())
        receipt = {**identity, 'profile': 'experiment_first', 'authorization': auth, 'native_smoke': ref(paths['smoke']),
            'decision': ref(decision), 'created_at': now, 'independent_review': ref(Path(args.independent_review)),
            'gates': {name: {'passed': True, 'evidence': [ref(paths[kind]), ref(Path(args.independent_review))]}
                      for name, kind in [('native_backward', 'smoke'), ('resources', 'resources'), ('independence', 'constraints'), ('constraints', 'constraints')]},
            'efficacy': 'UNKNOWN until actual original formal training; admission is not accuracy gain.'}
        task = {'id': EXP, 'label': 'PSNC parent spectral nonlinear token coupling', 'config': CONFIG, 'code_commit': COMMIT,
            'admission_receipt': receipt_path.relative_to(ROOT).as_posix(), 'status': 'waiting', 'gpu': '0', 'server': 'server-4',
            'profile': 'experiment_first', 'requires_exclusive_ownership': True, 'added_at': now,
            'note': 'Original byte-identical native YAML/seed1999/epochs50/maxiters70; actual paired diagnostic TRAIN2 and resources reviewed. GPU0 only. Diagnostic admission is not efficacy.'}
        current_owner()
        save(receipt_path, receipt, exclusive=True)
        closure.admission(ROOT, task)
        prospective = copy.deepcopy(queue); prospective['gpu_queues']['server-4'].append(task)
        closure.validate_foreground_dispatch_budget(ROOT, prospective, task)
        candidate.setdefault('execution_preparation_history', []).append({
            'recorded_at': now, 'reason': 'Preserve original externally anchored unexecuted preparation state before actual four-arm admission.',
            'current_status_fields': {k: copy.deepcopy(candidate.get(k)) for k in [
                'config_status', 'source_status', 'native_status', 'resource_status', 'native_worker_adapter',
                'implementation_status', 'native_execution_code_commit']},
            'worker_preparation': copy.deepcopy(candidate['worker_preparation']),
            'execution_adapter': copy.deepcopy(candidate['execution_adapter'])})
        candidate.update(stage='deployment', training_status='waiting', native_status='actual_TRAIN2_backward_spectral_path_observed',
            resource_status='actual_original_protocol_pair_passed', experiment_first_admission=True, admission_receipt=ref(receipt_path),
            native_execution=ref(REVIEW), native_execution_code_commit=COMMIT,
            config_status='Exact original YAML is now verified in main Git43 and actual native smoke/resources.',
            source_status='TESTED43_PRESENT_MAIN_ACTUAL_NATIVE_PAIR_VERIFIED',
            native_worker_adapter='ACTUAL_FRESH_BINDING_FOUR_ARMS_TERMINAL_REVIEWED',
            implementation_status='ACTUAL_NATIVE_TRAIN2_AND_RESOURCE_PAIR_VERIFIED',
            next_action='Exact tested PSNC43 admitted waiting on only GPU0. Canonical fresh dispatch must recheck source/runtime/assets/idle/exclusive ownership and actual progress. Do not use GPU1, resume M206 or alter original seed/YAML/schedule.')
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
            provenance='Root used the existing reviewed static catalog with a fresh exact owner/assets/idleGPU0/three-lock binding. Four original M95/PSNC smoke/resource requests completed terminal with independent semantic review. An intermediate busy probe refused before candidate request and was not replayed. The frozen preparation/release remain unchanged historical/static anchors; actual execution is separately bound here. This is diagnostic admission, not formal training or efficacy.')
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
        result = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'token': TOKEN, 'task': task, 'receipt': ref(receipt_path),
            'decision': ref(decision), 'standard_artifacts': {k: ref(v) for k, v in paths.items()},
            'canonical_admission_validated': True, 'canonical_tick_budget_validated': True, 'm206_queue_unchanged': True,
            'training_launched': False, 'source_synced': False}
        save(TICK/'psnc_admission_queue_result.json', result, exclusive=True)
        print(json.dumps({'id': EXP, 'status': 'waiting', 'receipt': ref(receipt_path), 'training_launched': False, 'source_synced': False}, ensure_ascii=False))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
