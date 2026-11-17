"""Pure JSON boundary checks against copies of the four completed BTC results."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import statistics

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/project/cluster_project')
EXECUTION = HERE.parent / 'btc_execution'
spec = importlib.util.spec_from_file_location('btc_pure_json_reviewer', HERE / 'review_btc.py')
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)
manifest = reviewer.read(EXECUTION / 'native_manifest.json')
actual = {mode+'_'+target: reviewer.read(EXECUTION / (mode+'_'+target+'_execution.json'))['result']
          for mode, target in reviewer.PAIRS}
checks = []


def check(label, mutation, expected='refused'):
    value = copy.deepcopy(actual)
    mutation(value)
    try:
        result = reviewer.review_payloads(value, manifest)
    except (reviewer.Refused, KeyError, TypeError, ValueError):
        assert expected == 'refused', label
        checks.append({'label': label, 'outcome': 'REFUSED_AS_EXPECTED'})
    else:
        assert expected != 'refused', label
        if expected == 'retention':
            assert result['existing_memory_condition_needs_separate_retention_decision'] is True
        checks.append({'label': label, 'outcome': 'ACCEPTED_WITH_RECORDED_SCOPE'})


def candidate(value):
    return value['smoke_candidate']


def erase_proper_gradient(value):
    for record in candidate(value)['BTC_tree_observations']:
        for call in record['map_calls']:
            if call['map'] == 'inside':
                for gradient in call['native_output_gradients']:
                    gradient['abs_max'] = 0.0


def zero_one_call(value):
    call = next(c for c in candidate(value)['BTC_tree_observations'][0]['map_calls']
                if c['map'] == 'inside')
    for key in ('native_input_gradients', 'native_output_gradients', 'native_linear_output_gradients'):
        for gradient in call[key]:
            gradient['abs_max'] = 0.0


def omit_middle_ln(value):
    for key in ('smoke_candidate', 'smoke_champion'):
        common = value[key]['common_initialized_parameters']
        common['names'] = [n for n in common['names'] if not n.startswith('dec.cluster_att.cluster_ffn_norm.1.')]
        common['tensor_count'] = len(common['names'])


def slower(value):
    result = value['resources_candidate']
    times = [t * 1.5 for t in result['measurements_ms']]
    ordered = sorted(times)
    result.update(measurements_ms=times, median_ms=statistics.median(times),
                  p90_ms=ordered[89] + (ordered[90]-ordered[89]) * 0.1)


reviewer.review_payloads(actual, manifest)
checks.append({'label': 'actual_four_payload_semantics', 'outcome': 'ACTUAL_ACCEPTED_NOT_ADMISSION'})
check('missing_proper_inside_original_batch_coverage', lambda v: candidate(v)['BTC_tree_observations'][0].update(actual_n_ge3_supported_parent_groups=0))
check('all_proper_inside_loss_gradients_zero', erase_proper_gradient)
check('root_inside_must_remain_unused', lambda v: candidate(v)['BTC_tree_observations'][0].update(root_inside_actual_calls=1))
check('wrong_actual_map_sources', lambda v: candidate(v)['BTC_tree_observations'][0]['map_calls'][0].update(actual_input_sources_exact=False))
check('missing_actual_map_loss_hook', lambda v: candidate(v)['BTC_tree_observations'][0]['map_calls'][0].update(native_output_gradients=[]))
check('map_weight_gradient_zero', lambda v: candidate(v)['steps'][0]['tracked_module_gradients']['tree_inside']['weight'].update(abs_max=0.0))
check('map_weight_not_updated', lambda v: candidate(v)['steps'][0]['weight_after_step_hash'].update(tree_inside=candidate(v)['steps'][0]['weight_before_step_hash']['tree_inside']))
check('extra_native_backward', lambda v: candidate(v).update(native_criterion_backwards=3))
check('wrong_remaining_ffn_level', lambda v: candidate(v)['ffn_calls'][0].update(level=1))
check('mismatched_original_train_batch', lambda v: candidate(v)['batches'][0].update(sha256='0'*64))
check('common_exclusion_scope_changed', lambda v: candidate(v)['common_initialized_parameters'].update(excluded_name_prefixes=[]))
check('middle_layernorm_omitted_from_common_pair', omit_middle_ln)
check('foreign_candidate_source_hash', lambda v: candidate(v)['source_hashes'].update({'middle_tree.py': '0'*64}))
check('incorrect_replacement_parameter_inventory', lambda v: candidate(v)['dynamic_parameter_inventory'].update(new_declared_parameters=0))
check('resource_repeat_not100', lambda v: v['resources_candidate'].update(repeat=99))
check('resource_prediction_contains_training', lambda v: v['resources_candidate'].update(optimizer_steps=1))
check('timing_contains_nonfinite_value', lambda v: v['resources_candidate']['measurements_ms'].__setitem__(0, float('nan')))
check('same_resource_input_required', lambda v: v['resources_candidate'].update(input_sha256='0'*64))
check('every_map_call_nonzero_is_not_required', zero_one_call, 'accepted')
check('slower_actual_timing_is_reported_without_new_latency_gate', slower, 'accepted')
check('existing_memory_condition_is_observed_not_auto_passed', lambda v: v['resources_candidate'].update(peak_allocated_bytes=2*v['resources_champion']['peak_allocated_bytes']), 'retention')

result = {
    'status': 'PURE_JSON_ACTUAL_PAYLOAD_AND_REFUSAL_BOUNDARIES_CHECKED_NOT_NATIVE_EXECUTION',
    'reviewer_sha256': hashlib.sha256((HERE/'review_btc.py').read_bytes()).hexdigest(),
    'checks': checks,
    'count': len(checks),
    'native_or_GPU_or_SSH_execution': False,
    'standard_or_receipt_or_shared_write': False,
    'scope': 'Only copies of actual completed JSON payloads were mutated in memory. Original results and frozen packet remain unchanged. Accepted altered payloads are scope tests, not additional native experiments or usable evidence.',
}
output = HERE / 'reviewer_refusal_checks.json'
with output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write('\n')
print(json.dumps({'path': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                  'count': len(checks)}, ensure_ascii=False))
