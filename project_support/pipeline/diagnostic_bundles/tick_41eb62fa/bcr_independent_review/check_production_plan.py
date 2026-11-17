"""Actual stdlib BCR plan versus independent ordered-set/complement oracle.

No torch/model import, tensor execution, gradient observation or remote action.
"""
from pathlib import Path
from datetime import datetime, timezone
import ast
import copy
import hashlib
import json
import math

ROOT = Path('D:/project/cluster_project')
TICK = ROOT / 'pipeline/diagnostic_bundles/tick_41eb62fa'
SOURCE = TICK / 'new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


hashes_before = {n: digest(SOURCE/n) for n in ('middle_complement.py', 'hier_postprocess.py', 'dec.py')}
module = ast.parse((SOURCE/'middle_complement.py').read_text(encoding='utf-8'))
production = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'build_complement_plan')
environment = {'math': math}
exec(compile(ast.Module(body=[production], type_ignores=[]), str(SOURCE/'middle_complement.py'), 'exec'), environment)
build = environment['build_complement_plan']
results = []
production_calls = 0


def validate(label, centers, parents, support, width=None):
    """Oracle orders all IDs first, then filters each parent and slices contexts."""
    global production_calls
    k = len(parents)
    slots = k if width is None else width
    args = (copy.deepcopy(centers), copy.deepcopy(parents), copy.deepcopy(support), slots)
    original = copy.deepcopy(args)
    actual = build(*args)
    production_calls += 1
    assert args == original, 'Production plan mutated original metadata'
    globally_ordered = sorted(range(k), key=lambda j: (centers[j][0], centers[j][1], centers[j][2], j))
    active_parents = sorted({parents[j] for j in range(k) if support[j]})
    assert [group['parent'] for group in actual] == active_parents
    symbolic_scatter = [None] * slots
    total_steps = 0
    for parent, group in zip(active_parents, actual):
        order = [j for j in globally_ordered if support[j] and parents[j] == parent]
        assert tuple(order) == group['order'] and order
        all_members = set(order)
        # Execute the actual emitted program using sets as dependency values.
        left = {order[0]: set()}
        right = {order[-1]: set()}
        for direction, memory in [('left', left), ('right', right)]:
            steps = group[direction+'_steps']
            assert len(steps) == len(order)-1
            for destination, source in steps:
                assert source in memory and destination not in memory
                assert parents[destination] == parents[source] == parent
                memory[destination] = memory[source] | {source}
                assert destination not in memory[destination]
            # No unconsumed inclusive terminal state is emitted.
            assert set(memory) == all_members
        assert set(source for _, source in group['left_steps']) == all_members-{order[-1]}
        assert set(source for _, source in group['right_steps']) == all_members-{order[0]}
        assert len(group['left_steps'])+len(group['right_steps']) == 2*(len(order)-1)
        total_steps += 2*(len(order)-1)
        for position, token in enumerate(order):
            expected_left = set(order[:position])
            expected_right = set(order[position+1:])
            assert left[token] == expected_left and right[token] == expected_right
            assert not left[token] & right[token]
            assert left[token] | right[token] == all_members-{token}
            assert token not in left[token] | right[token]
            # Simulate only the emitted original-ID write addresses, not tensors.
            assert symbolic_scatter[token] is None
            symbolic_scatter[token] = {'own': token, 'left': sorted(left[token]), 'right': sorted(right[token])}
    assert {j for j, value in enumerate(symbolic_scatter) if value is not None} == {j for j in range(k) if support[j]}
    assert all(value is None for value in symbolic_scatter[k:])
    results.append({'label': label, 'status': 'ACTUAL_STDLIB_PLAN_MATCHES_INDEPENDENT_ORACLE',
                    'prefix': k, 'padded_width': slots, 'supported_tokens': sum(support),
                    'parents': len(actual), 'consumed_scan_steps': total_steps})


valid = [
    ('empty_prefix', [], [], [], 0),
    ('nonempty_prefix_all_unsupported', [[0., 0., 0.], [1., 0., 0.]], [2, 2], [False, False], 5),
    ('singleton', [[2., 1., 0.]], [7], [True], 1),
    ('two_reverse_geometry', [[2., 0., 0.], [-1., 0., 0.]], [0, 0], [True, True], 2),
    ('three_irregular_geometry', [[2., 3., 1.], [0., 9., 0.], [1., -2., 4.]], [0, 0, 0], [True]*3, 3),
    ('five_duplicate_centers_ID_tie_break', [[0., 0., 0.]]*5, [4]*5, [True]*5, 5),
    ('multiple_parent_ID_gaps_support_holes_padding', [[4., 0., 0.], [3., 1., 0.], [0., 2., 0.], [1., 0., 0.], [2., 0., 0.], [-1., 0., 0.]], [9, 2, 9, 2, 9, 2], [True, False, True, True, False, True], 9),
    ('all_parent_singletons', [[2., 0., 0.], [1., 0., 0.], [0., 0., 0.]], [8, 1, 5], [True]*3, 5),
    ('secondary_y_z_lexicographic_order', [[0., 2., 1.], [0., 1., 2.], [0., 1., 1.], [0., 2., 0.]], [0]*4, [True]*4, 4),
    ('negative_coordinates_and_position_ties', [[-1., -2., 0.], [-1., -3., 2.], [-1., -3., 2.], [2., 0., -1.]], [3]*4, [True]*4, 8),
    ('nonconsecutive_supported_original_IDs', [[float(i), 0., 0.] for i in range(8)], [0]*8, [False, True, False, True, False, False, True, False], 10),
    ('max64_one_parent', [[float(63-i), float(i%3), 0.] for i in range(64)], [6]*64, [True]*64, 64),
    ('batch_reuse_same_parent_reset_A', [[0., 0., 0.], [2., 0., 0.], [1., 0., 0.]], [0]*3, [True]*3, 3),
    ('batch_reuse_same_parent_reset_B', [[5., 0., 0.], [4., 0., 0.]], [0]*2, [True]*2, 5),
]
for row in valid:
    validate(*row)

invalid = [
    ('mismatched_center_length', [], [0], [True], 1),
    ('mismatched_support_length', [[0., 0., 0.]], [0], [], 1),
    ('center_dimension_not_three', [[0., 0.]], [0], [True], 1),
    ('nonfinite_NaN_geometry', [[math.nan, 0., 0.]], [0], [True], 1),
    ('nonfinite_infinite_geometry', [[0., math.inf, 0.]], [0], [True], 1),
    ('negative_parent_even_if_unsupported', [[0., 0., 0.]], [-1], [False], 1),
    ('boolean_parent_is_not_integer_ID', [[0., 0., 0.]], [True], [True], 1),
    ('floating_parent_is_not_integer_ID', [[0., 0., 0.]], [1.0], [True], 1),
    ('nonboolean_support', [[0., 0., 0.]], [0], [1], 1),
    ('prefix_exceeds_declared_max', [[0., 0., 0.], [1., 0., 0.]], [0, 0], [True, True], 1),
]
for label, *args in invalid:
    try:
        build(*args)
        production_calls += 1
    except ValueError:
        production_calls += 1
        results.append({'label': label, 'status': 'ACTUAL_PRODUCTION_VALUEERROR_AS_EXPECTED'})
    else:
        raise AssertionError('Production plan accepted malformed metadata: '+label)

class_node = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'ParentBidirectionalComplementRecurrence')
forward = next(n for n in class_node.body if isinstance(n, ast.FunctionDef) and n.name == 'forward')
forward_text = ast.unparse(forward)
ast_checks = {
    'single_registered_shared_scan_2C_to_C': 'self.scan = nn.Linear(2 * channels, channels)' in ast.unparse(class_node),
    'single_registered_readout_3C_to_C': 'self.readout = nn.Linear(3 * channels, channels)' in ast.unparse(class_node),
    'actual_forward_consumes_production_plan': 'plan = build_complement_plan' in forward_text,
    'left_uses_source_feature_and_source_context': 'features[b, source], left[source]' in forward_text,
    'right_uses_source_feature_and_source_context': 'features[b, source], right[source]' in forward_text,
    'readout_own_plus_exclusive_left_right': 'torch.cat((own, torch.stack([left[token] for token in order]), torch.stack([right[token] for token in order])), dim=-1)' in forward_text,
    'scatter_uses_original_IDs': 'output = output.index_copy(0, original_ids, delta)' in forward_text,
    'zero_updates_for_unassigned_padding': 'output = features.new_zeros((slots, self.channels))' in forward_text,
    'no_new_residual_inside_helper': 'return torch.stack(outputs, dim=0) if outputs else torch.zeros_like(features)' in forward_text,
}
assert all(ast_checks.values()), ast_checks
assert hashes_before == {n: digest(SOURCE/n) for n in hashes_before}, 'Author sources changed during independent review'
result = {
    'schema_version': 1,
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'status': 'ACTUAL_PRODUCTION_STDLIB_BCR_PLAN_AND_STATIC_CONSUMER_CHECKED_NATIVE_NOT_RUN',
    'candidate_id': 'hierarchy-parent-bidirectional-complement-recurrence',
    'reviewed_source_hashes': hashes_before,
    'valid_cases': len(valid), 'invalid_cases': len(invalid), 'actual_production_function_calls': production_calls,
    'case_results': results, 'static_consumer_checks': ast_checks,
    'material_concerns': [],
    'test_scope': '24 deterministic scalar fixtures directly call the extracted current production build_complement_plan. Independent oracle uses ordered-ID slicing and symbolic set/scatter semantics; no torch or model import. These are logical software cases, not 24 scientific experiments or native tensor behavior tests.',
    'gradients_and_native': 'NOT_RUN_NOT_PROVEN', 'resources_and_efficacy': 'UNKNOWN',
    'limitations': [
        'Python symbolic scatter checks addresses and zero-unassigned slots; actual tensor index_copy/autograd/device/numerics remain untested.',
        'Feature recurrence/GELU/readout values were not executed. Native scan/readout gradients and optimizer updates still require the original actual TRAIN2 protocol; n1-only support would leave shared scan unused.',
        'Full initialization/data pairing, actual empty/pad/singleton native coverage and resource measurement are unknown.',
        'This is a reviewed current draft hash. Final author freeze must rebind exactly these source bytes or review changed files before reuse.',
    ],
}
output = TICK/'bcr_topology_review.json'
with output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write('\n')
print(json.dumps({'path': str(output), 'sha256': digest(output), 'valid_cases': len(valid),
                  'invalid_cases': len(invalid), 'production_calls': production_calls,
                  'material_concerns': result['material_concerns']}, ensure_ascii=False))
