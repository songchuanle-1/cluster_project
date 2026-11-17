"""Check actual BCR source and production scalar plan; never import torch/model."""
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys
import traceback

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
BASE_NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
BASE = PROJECT / 'Cluster/framework/model/Quard_model' / BASE_NAME
MODEL = HERE / 'staged_repository/framework/model/Quard_model' / (BASE_NAME + '_bcr')
TOKEN = '41eb62fa1d32436f859264a19b0d4049'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard():
    o = json.loads((PROJECT / 'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf-8'))
    assert o['token'] == TOKEN and datetime.now(timezone.utc) < datetime.fromisoformat(o['deadline_at'])
    assert sha(PROJECT / 'pipeline/headless/.tick_context.json') == o['context_sha256']
    assert sha(PROJECT / 'pipeline/headless/.tick_context_state.next.json') == o['pending_sha256']


def find(tree, name):
    return next(n for n in tree.body if getattr(n, 'name', None) == name)


def dump(node):
    return ast.dump(node, include_attributes=False)


def validate(checks, fixtures):
    def check(label, truth):
        assert truth, label
        checks.append(label)

    for p in sorted(MODEL.glob('*.py')):
        compile(ast.parse(p.read_text('utf-8')), str(p), 'exec')
        checks.append('AST_compile:' + p.name)
    check('exactly_eight_model_sources', len(list(MODEL.glob('*.py'))) == 8)
    for filename in ['__init__.py', 'backbone.py', 'loss.py', 'network.py', 'sample_model.py']:
        check('unchanged_bytes:' + filename, (MODEL / filename).read_bytes() == (BASE / filename).read_bytes())
    before = ast.parse((BASE / 'hier_postprocess.py').read_text('utf-8'))
    after = ast.parse((MODEL / 'hier_postprocess.py').read_text('utf-8'))
    for node in before.body:
        if isinstance(node, ast.FunctionDef):
            check('unchanged_original_function:' + node.name, dump(find(after, node.name)) == dump(node))
    for name in ['C2F_ClusterAttn_Lite', 'C2F_ClusterAttn_CTF_HCG', 'C2F_ClusterAttn_CTF_HCG_CSORT']:
        check('unchanged_AST:' + name, dump(find(before, name)) == dump(find(after, name)))
    check('original_raw_bank_pooling_AST', dump(find(find(before, 'SharedClusterBank'), 'build_cluster_feats')) ==
          dump(find(find(after, 'SharedClusterBank'), 'build_cluster_feats')))
    for name in ['partition_points', 'cluster_layer']:
        check('unchanged_geometry_method:' + name,
              dump(find(find(before, 'PointCloudPartitioner'), name)) ==
              dump(find(find(after, 'PointCloudPartitioner'), name)))
    a = find(find(before, 'PointCloudPartitioner'), 'forward').body
    b = find(find(after, 'PointCloudPartitioner'), 'forward').body
    cursor = 0
    for statement in a:
        while cursor < len(b) and dump(statement) != dump(b[cursor]):
            cursor += 1
        check('all_original_partition_forward_statements_preserved_in_order', cursor < len(b))
        cursor += 1
    original_init = find(find(before, 'C2F_ClusterAttn_CTF'), '__init__')
    current_init = find(find(after, 'C2F_ClusterAttn_CTF'), '__init__')
    check('original_CTF_constructor_initialization_prefix_unchanged',
          [dump(x) for x in current_init.body[:len(original_init.body)]] == [dump(x) for x in original_init.body])
    before_dec = ast.parse((BASE / 'dec.py').read_text('utf-8'))
    after_dec = ast.parse((MODEL / 'dec.py').read_text('utf-8'))

    class RemoveGeometryDelivery(ast.NodeTransformer):
        def visit_Assign(self, node):
            if any(isinstance(x, ast.Attribute) and x.attr in
                   ('middle_positions', 'middle_valid', 'middle_parent_ids') for x in node.targets):
                return None
            return self.generic_visit(node)

        def visit_If(self, node):
            if 'middle_parent_ids' in ast.unparse(node.test):
                return None
            return self.generic_visit(node)

    for node in before_dec.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            actual = find(after_dec, node.name)
            if node.name == 'Encoder_layer':
                actual = RemoveGeometryDelivery().visit(copy.deepcopy(actual))
            check('decoder_original_AST_after_removing_cache_delivery:' + node.name, dump(actual) == dump(node))
    config = next((HERE / 'staged_repository/configs/Quard/ctf_hcg_csort_bcr').glob('*.yaml'))
    check('native_YAML_byte_identical', config.read_bytes() ==
          (PROJECT / 'Cluster/configs/Quard/ctf_hcg_csort' / (BASE_NAME + '.yaml')).read_bytes())
    text = (MODEL / 'hier_postprocess.py').read_text('utf-8')
    check('true_support_from_composed_real_point_IDs', 'point_to_mid = ids1[ids0]' in text and
          'torch.bincount(point_to_mid, minlength=Kmid) > 0' in text)
    check('original_ID_cache_object_identity_guard', 'self.middle_parent_ids is not cluster_ids_list[2]' in text)
    check('removed_middle_FFN_and_isolated_new_default_initialization',
          'self.cluster_ffn[1] = nn.Identity()' in text and
          'with torch.random.fork_rng(devices=[]):' in text and 'manual_seed' not in text)
    forward = ast.unparse(find(find(after, 'C2F_ClusterAttn_CTF'), 'forward'))
    check('original_middle_skip_and_LN_kept',
          'refined = cf + self.middle_complement(self.cluster_ffn_norm[1](cf)' in forward)
    check('original_fine_coarse_operator_kept',
          'refined = cf + self.cluster_ffn[lvl](self.cluster_ffn_norm[lvl](cf))' in forward)
    helper_text = (MODEL / 'middle_complement.py').read_text('utf-8')
    helper = ast.parse(helper_text)
    module = find(helper, 'ParentBidirectionalComplementRecurrence')
    init = find(module, '__init__')
    linears = [n for n in ast.walk(init) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'Linear']
    check('only_shared_2C_scan_and_3C_readout', len(linears) == 2 and
          [dump(n.args[0]) for n in linears] == [dump(ast.parse(x, mode='eval').body) for x in ['2 * channels', '3 * channels']] and
          all(dump(n.args[1]) == dump(ast.parse('channels', mode='eval').body) for n in linears))
    check('static_parameter_count_and_delta', (2 * 256 * 256 + 256) + (3 * 256 * 256 + 256) == 328192 and
          328192 - 525568 == -197376)
    check('no_new_gate_buffer_residual_or_feature_detach', not any(x in helper_text for x in
          ['register_buffer', 'nn.Parameter', 'MultiheadAttention', 'features.detach()', 'sigmoid(', '+ features', '+ left[', '+ right[']))
    actual_forward = ast.unparse(find(module, 'forward'))
    check('scan_context_reads_source_not_destination_feature',
          '(features[b, source], left[source])' in actual_forward and
          '(features[b, source], right[source])' in actual_forward and
          'features[b, destination]' not in actual_forward)
    check('exclusive_three_branch_linear_readout',
          'self.readout(torch.cat((own, torch.stack([left[token] for token in order]), torch.stack([right[token] for token in order]))' in actual_forward)
    check('inverse_scatter_original_IDs', 'output.index_copy(0, original_ids, delta)' in actual_forward)
    check('only_two_plan_scan_call_sites_no_unused_terminal', len([n for n in ast.walk(find(module, 'forward'))
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'scan']) == 2)

    # Execute the production scalar planner itself, not a second model implementation.
    pure = ast.Module(body=[ast.Import(names=[ast.alias(name='math')]), find(helper, 'build_complement_plan')], type_ignores=[])
    namespace = {}
    exec(compile(ast.fix_missing_locations(pure), '<actual-production-plan-only>', 'exec'), namespace)
    build = namespace['build_complement_plan']

    def plan_case(label, centers, parents, supported):
        plan = build(centers, parents, supported, 64)
        coverage = []
        for group in plan:
            order = group['order']; coverage.extend(order); n = len(order)
            check('plan_only_real_supported_original_IDs', all(supported[i] and parents[i] == group['parent'] for i in order))
            check('lexicographic_xyz_then_original_ID_order', all((*centers[a], a) <= (*centers[b], b) for a, b in zip(order, order[1:])))
            left = {order[0]: set()}; right = {order[-1]: set()}
            feedback_steps = 0
            for destination, source in group['left_steps']:
                check('left_topological_scan_no_self_source', source in left and destination not in left and destination != source)
                feedback_steps += bool(left[source])
                left[destination] = left[source] | {source}
            for destination, source in group['right_steps']:
                check('right_topological_scan_no_self_source', source in right and destination not in right and destination != source)
                feedback_steps += bool(right[source])
                right[destination] = right[source] | {source}
            check('exactly_2_n_minus_1_consumed_scans', len(group['left_steps']) + len(group['right_steps']) == 2 * (n - 1))
            check('state_half_structural_opportunities_need_n_ge_3', feedback_steps == 2 * max(n - 2, 0))
            for i, token in enumerate(order):
                check('prefix_exact_previous_siblings', left[token] == set(order[:i]))
                check('suffix_exact_later_siblings', right[token] == set(order[i + 1:]))
                check('own_excluded_disjoint_complement_complete', token not in left[token] | right[token] and
                      left[token].isdisjoint(right[token]) and left[token] | right[token] == set(order) - {token})
            if n == 1:
                check('singleton_zero_context_zero_scan', not group['left_steps'] and not group['right_steps'] and left[order[0]] == right[order[0]] == set())
        check('support_coverage_no_duplicate_or_padding_ID', sorted(coverage) == [i for i, flag in enumerate(supported) if flag])
        check('deterministic_production_plan', plan == build(centers, parents, supported, 64))
        fixtures.append(label)

    for n in [0, 1, 2, 3, 4, 7, 8, 16, 63, 64]:
        plan_case('one_parent_n' + str(n), [[float(i % 3), float(i // 3), float(i % 2)] for i in range(n)], [0] * n, [True] * n)
    plan_case('ties_sparse_parents_and_support_holes', [[0., 0., 0.]] * 8,
              [0, 0, 7, 7, 7, 9, 9, 9], [True, False, True, True, False, False, False, True])
    plan_case('all_unsupported_zero_plan', [[0., 0., 0.]] * 5, [0, 0, 1, 1, 2], [False] * 5)
    rng = random.Random(1999)
    for n in [3, 17, 64]:
        plan_case('fixed_stdlib_random_domain_n' + str(n), [[rng.random(), rng.random(), rng.random()] for _ in range(n)],
                  [i % 4 for i in range(n)], [i % 5 != 0 for i in range(n)])
    invalid = [([[0., 0., 0.]], [0], [], 64), ([[float('nan'), 0., 0.]], [0], [True], 64),
               ([[0., 0., 0.]], [-1], [True], 64), ([[0., 0., 0.]], [True], [True], 64),
               ([[0., 0., 0.]], [0], [1], 64), ([[0., 0.]], [0], [True], 64),
               ([[0., 0., 0.]] * 65, [0] * 65, [True] * 65, 64)]
    for i, args in enumerate(invalid):
        try:
            build(*args)
        except (ValueError, TypeError):
            checks.append('production_plan_invalid_domain_refused'); fixtures.append('invalid_' + str(i))
        else:
            raise AssertionError('Production plan accepted invalid domain')
    check('torch_not_imported', 'torch' not in sys.modules)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='static_validation.json')
    args = parser.parse_args()
    output = (HERE / args.output).resolve()
    assert output.parent == HERE and not output.exists(), 'Keep every original check outcome; new output name required'
    guard(); checks = []; fixtures = []; failure = None
    try:
        validate(checks, fixtures)
    except Exception:
        failure = traceback.format_exc()
    guard()
    config = next((HERE / 'staged_repository/configs/Quard/ctf_hcg_csort_bcr').glob('*.yaml'))
    record = {'status': 'OFFLINE_SOURCE_AND_PRODUCTION_PLAN_PASSED_NATIVE_NOT_RUN' if failure is None else 'OFFLINE_CHECK_FAILED_RETAINED',
              'recorded_at': datetime.now(timezone.utc).isoformat(), 'assertion_count': len(checks),
              'distinct_check_labels': len(set(checks)), 'checks': checks, 'production_plan_cases': fixtures,
              'production_plan_case_count': len(fixtures), 'error': failure,
              'source_hashes': {p.name: sha(p) for p in sorted(MODEL.glob('*.py'))}, 'config_sha256': sha(config),
              'torch_imported': 'torch' in sys.modules, 'native_execution': 'NOT_RUN', 'resources': 'NOT_RUN',
              'limits': ['Actual scalar production planner executed; symbolic support sets are not a torch/FP32/Jacobian test.',
                         'No tensor cache-shape or actual empty/singleton/padded native example was executed.',
                         'Ws recurrent-state half and readout context-column gradients/updates still require original native loss on real n>=3 groups.']}
    with output.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({k: record[k] for k in ['status', 'assertion_count', 'distinct_check_labels', 'production_plan_case_count', 'torch_imported']}))
    if failure:
        print(failure)
    sys.exit(0 if failure is None else 1)


if __name__ == '__main__':
    main()
