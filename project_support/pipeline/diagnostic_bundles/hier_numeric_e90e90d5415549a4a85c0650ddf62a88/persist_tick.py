"""Persist actual evidence without granting any new scientific or GPU authority."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from run_numeric import BUNDLE, ROOT, TOKEN, guard, tick

PRIMARY = 'm95-hierarchical-mask-feature-path-audit'
AUXILIARY = ('m95-native-relation-other-sign-conflict',
    'm95-native-main-role-weight-precedence', 'm95-native-secondary-positive-mass',
    'm95-native-between-pair-support')
RESOURCE = ROOT / ('pipeline/diagnostic_bundles/resource_recheck_' + TOKEN)


def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': tick.digest(path)}


def main():
    guard()
    assert not (BUNDLE / 'persistence.json').exists()
    context = tick.load(ROOT / 'pipeline/headless/.tick_model_view.json')
    assert context['research']['due_count'] == 5
    assert context['queue']['candidate_budget'] == 1
    assert context['research']['reserve_budget'] == 0
    work_path = ROOT / 'pipeline/research_work.json'
    before = tick.load(RESOURCE / 'work_before.json')
    assert tick.load(work_path) == before
    before_hash = tick.digest(work_path)
    original = {c['id']: c for c in before['candidates']}
    assert len(original) == 100
    resource = tick.load(RESOURCE / 'resource_result.json')
    assert resource['token'] == TOKEN
    assert resource['probe_flocks_released'] and not resource['ready_for_original_capture_guards']
    assert resource['cuda_allocations'] == resource['native_network_forwards'] == resource['optimizer_steps'] == 0
    assert resource['foreign_process_signals'] == resource['gpu_resets'] == resource['lock_deletions'] == 0
    result = tick.load(BUNDLE / 'result.json')
    assert result['token'] == TOKEN and result['check_count'] == 7
    assert all(result['checks'].values())
    assert not result['prior_float32_failures_reclassified']
    assert not result['production_precision_or_backend_changed']
    assert not result['cuda_initialized']
    assert all(not values['original_float32_bound_met_for_this_pair_only']
               for record in result['records'] for values in record['variants'].values())
    observed = datetime.fromisoformat(resource['observed_at'])
    assert observed >= datetime.fromisoformat(original[PRIMARY]['retry_after'])
    primary_retry = observed + timedelta(hours=1)
    now = datetime.now(timezone.utc)
    auxiliary_retry = now + timedelta(hours=4)
    goal = tick.load(ROOT / 'pipeline/goal.json')
    assert goal['research_mainline']['primary_axis'] == 'hierarchical_attention_point_feature_update'
    for cid in AUXILIARY:
        c = original[cid]
        assert c['stage'] == 'blocked' and c['research_role'] == 'auxiliary_scope_hold'
        assert c['blocker_kind'] == 'human_authorization'
        assert now >= datetime.fromisoformat(c['retry_after'])
    scope = {'token': TOKEN, 'observed_at': now.isoformat(),
        'test': 'Rebind four due auxiliary holds to the unchanged latest goal and user mainline scope.',
        'goal': ref(ROOT / 'pipeline/goal.json'), 'ids': list(AUXILIARY),
        'result': 'Scope holds remain; no new authorization, scientific rejection, restart or gate change.',
        'original_gate_sets_preserved': True, 'retry_after': auxiliary_retry.isoformat(),
        'native_tests': 0, 'm201_restarted': False}
    tick.save(BUNDLE / 'auxiliary_scope_check.json', scope)
    decision = ROOT / 'pipeline/decisions/20261016-021757_other.md'
    numeric_evidence = [ref(BUNDLE / name) for name in (
        'prereg.md', 'numeric_cpu.py', 'run_numeric.py', 'frozen_sources.json',
        'attempt.json', 'result.json', 'remote_numeric.py')]
    resource_evidence = [ref(RESOURCE / name) for name in (
        'remote_probe.py', 'attempt.json', 'resource_result.json')]
    common_evidence = [ref(Path(__file__).resolve())]
    primary_evidence = numeric_evidence + resource_evidence + common_evidence + [ref(decision)]
    work = copy.deepcopy(before)
    current = {c['id']: c for c in work['candidates']}
    primary = current[PRIMARY]
    assert all(not g['passed'] for g in primary['gates'].values())
    primary['evidence'].extend(primary_evidence)
    primary['retry_after'] = primary_retry.isoformat()
    primary['blocker'] = (
        'Pinned server4 GPU0 at ' + resource['observed_at'] +
        ' free139MiB/util95; NVML2634704uses20016MiB and4093981uses11848MiB; '
        'original training flock held, diagnostic flocks released. All original guards fail. '
        'New seven-check CPU arithmetic localization is diagnostic only: dense reconstruction exact, '
        'same-float32-input double implementations agree, but all six float32 comparison pairs '
        'still fail unchanged1e-6 fixed-query criterion. Original12FAIL and native/model gates remain. '
        'Actual learned feature capture requires exclusive GPU; no further backend/precision sweep.')
    primary['findings']['latest_resource_guard'] = {
        'observed_at': resource['observed_at'], 'evidence': ref(RESOURCE / 'resource_result.json'),
        'ready': False, 'native_network_forwards_this_tick': 0,
        'scope': 'Live original guards only, no GPU allocation.'}
    primary['findings']['numeric_localization'] = {
        'observed_at': result['observed_at'], 'evidence': ref(BUNDLE / 'result.json'),
        'constructed_checks': 7, 'passed': 7,
        'float32_backend_comparison_pairs': 6, 'float32_pairs_within_original_bound': 0,
        'original_failures_reclassified': False, 'native_network_forwards': 0,
        'scope': 'Evidence consistent with arithmetic-path sensitivity, not unique-root-cause proof or admission.'}
    primary['next_action'] = (
        'Run prepared unchanged M95 native TRAIN feature capture for groups0,60,101,124 only after '
        'fresh pinned identity/NVML/30000MiB/three-flock guards pass. Diagnose learned-scale redundancy '
        'and apply same-capture ancestor/uniform/support controls before choosing conditional core. '
        'CPU arithmetic localization is complete for this question; do not repeat it, select backend, '
        'raise tolerance, change production precision or call it new trained gain. Preserve strictFAILs; '
        'full native backward/resources/independent model/config/constraints remain unpassed.')
    for cid in AUXILIARY:
        current[cid]['evidence'].extend([ref(BUNDLE / 'auxiliary_scope_check.json'), *common_evidence])
        current[cid]['retry_after'] = auxiliary_retry.isoformat()
    changed = {PRIMARY, *AUXILIARY}
    assert all(c == original[c['id']] for c in work['candidates'] if c['id'] not in changed)
    assert all(current[cid]['gates'] == original[cid]['gates'] for cid in changed)
    assert all(current[cid]['stage'] == original[cid]['stage'] for cid in changed)
    work['design_cycle'] = {'stop_reason': 'external_resource_blocked',
        'attempted_ids': [PRIMARY, *AUXILIARY],
        'evidence': [*primary_evidence, ref(BUNDLE / 'auxiliary_scope_check.json')],
        'resume_condition': primary['unblock_condition'], 'retry_after': primary_retry.isoformat(),
        'scope': 'One fresh original resource probe; one new CPU numerical decomposition, not duplicated '
                 'whole controls. Four auxiliary authorization holds reconfirmed, not hypothesis tests. '
                 'Non-GPU preparation complete for the next frozen native diagnosis. No exhaustion claim, '
                 'new core selection, admission or training. Timers confer no GPU/science permission.'}
    guard()
    assert tick.digest(work_path) == before_hash
    tick.save(work_path, work)
    outcome = {'token': TOKEN, 'changed_candidate_ids': sorted(changed),
        'other95_unchanged': True, 'all_original_gate_sets_unchanged': True,
        'stages_unchanged': True, 'primary_evidence_added': len(primary_evidence),
        'auxiliary_evidence_added': 2 * len(AUXILIARY), 'new_candidates': 0,
        'new_admissions': 0, 'native_forwards': 0, 'optimizer_steps': 0, 'new_training': 0,
        'primary_retry_after': primary_retry.isoformat(),
        'auxiliary_retry_after': auxiliary_retry.isoformat()}
    tick.save(BUNDLE / 'persistence.json', outcome)
    print(json.dumps(outcome, indent=2))


if __name__ == '__main__':
    main()
