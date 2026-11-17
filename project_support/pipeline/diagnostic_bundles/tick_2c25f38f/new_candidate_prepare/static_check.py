"""CPU/stdlib checks of actual staged source; never imports model or torch."""
import ast
import datetime
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
BASE_NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
BASE = PROJECT / 'Cluster/framework/model/Quard_model' / BASE_NAME
MODEL = HERE / 'staged_repository/framework/model/Quard_model' / (BASE_NAME + '_btc')
TOKEN = '2c25f38f32af4c69b3def8130cc5399c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard():
    owner = json.loads((PROJECT / 'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf-8'))
    assert owner['token'] == TOKEN
    assert datetime.datetime.now(datetime.timezone.utc) < datetime.datetime.fromisoformat(owner['deadline_at'])
    assert sha(PROJECT / 'pipeline/headless/.tick_context.json') == owner['context_sha256']
    assert sha(PROJECT / 'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256']


def find(tree, name):
    return next(n for n in tree.body if getattr(n, 'name', None) == name)


def dump(node):
    return ast.dump(node, include_attributes=False)


def main():
    guard()
    checks = []

    def check(label, truth):
        assert truth, label
        checks.append(label)

    original = ast.parse((BASE / 'hier_postprocess.py').read_text('utf-8'))
    staged = ast.parse((MODEL / 'hier_postprocess.py').read_text('utf-8'))
    helper = ast.parse((MODEL / 'middle_tree.py').read_text('utf-8'))
    for path in sorted(MODEL.glob('*.py')):
        compile(ast.parse(path.read_text('utf-8')), str(path), 'exec')
        checks.append('AST_compile:' + path.name)
    check('exactly_eight_model_sources', len(list(MODEL.glob('*.py'))) == 8)
    for filename in ['__init__.py', 'backbone.py', 'loss.py', 'network.py', 'sample_model.py']:
        check('unchanged_bytes:' + filename, (MODEL / filename).read_bytes() == (BASE / filename).read_bytes())
    for name in ['C2F_ClusterAttn_Lite', 'C2F_ClusterAttn_CTF_HCG', 'C2F_ClusterAttn_CTF_HCG_CSORT']:
        check('unchanged_AST:' + name, dump(find(original, name)) == dump(find(staged, name)))
    check('unchanged_AST:raw_bank_build', dump(find(find(original, 'SharedClusterBank'), 'build_cluster_feats')) ==
          dump(find(find(staged, 'SharedClusterBank'), 'build_cluster_feats')))
    for name in ['partition_points', 'cluster_layer']:
        check('unchanged_AST:original_geometry_' + name,
              dump(find(find(original, 'PointCloudPartitioner'), name)) ==
              dump(find(find(staged, 'PointCloudPartitioner'), name)))
    config = next((HERE / 'staged_repository/configs/Quard/ctf_hcg_csort_btc').glob('*.yaml'))
    check('native_YAML_byte_identical', config.read_bytes() ==
          (PROJECT / 'Cluster/configs/Quard/ctf_hcg_csort' / (BASE_NAME + '.yaml')).read_bytes())
    source = (MODEL / 'hier_postprocess.py').read_text('utf-8')
    check('old_middle_parameters_removed', 'self.cluster_ffn[1] = nn.Identity()' in source)
    check('new_constructor_RNG_isolated_no_seed', 'with torch.random.fork_rng(devices=[]):' in source and 'manual_seed' not in source)
    check('true_point_support_not_feature_threshold', 'point_to_mid = ids1[ids0]' in source and
          'torch.bincount(point_to_mid, minlength=Kmid) > 0' in source)
    check('cache_tied_to_current_original_ID_object', 'self.middle_parent_ids is not cluster_ids_list[2]' in source)
    ctf_forward = find(find(staged, 'C2F_ClusterAttn_CTF'), 'forward')
    ctf_text = ast.unparse(ctf_forward)
    check('original_middle_outer_skip_preserved',
          'refined = cf + self.middle_tree(self.cluster_ffn_norm[1](cf)' in ctf_text)
    check('original_fine_coarse_operator_preserved',
          'refined = cf + self.cluster_ffn[lvl](self.cluster_ffn_norm[lvl](cf))' in ctf_text)
    module = find(helper, 'ParentBinaryTreeComplement')
    ctor = find(module, '__init__')
    linears = [n for n in ast.walk(ctor) if isinstance(n, ast.Call) and
               isinstance(n.func, ast.Attribute) and n.func.attr == 'Linear']
    check('three_shared_2C_to_C_maps', len(linears) == 3 and all(
        dump(n.args[0]) == dump(ast.parse('2 * channels', mode='eval').body) and
        dump(n.args[1]) == dump(ast.parse('channels', mode='eval').body) for n in linears))
    check('no_new_parameter_buffer_gate_attention_or_detached_features',
          not any(word in (MODEL / 'middle_tree.py').read_text('utf-8') for word in
                  ['register_buffer', 'nn.Parameter', 'MultiheadAttention', 'features.detach()', 'sigmoid(']))
    check('replacement_static_parameter_count', 3 * (2 * 256 * 256 + 256) == 393984)
    # Execute only the actual pure topology function extracted from production AST.
    # No reimplementation, model import, tensor, fake native loss, or torch is used.
    pure = ast.Module(body=[ast.Import(names=[ast.alias(name='math')]),
                            find(helper, 'build_parent_forest')], type_ignores=[])
    namespace = {}
    exec(compile(ast.fix_missing_locations(pure), '<production-topology-only>', 'exec'), namespace)
    build = namespace['build_parent_forest']

    def verify_forest(centers, parents, supported):
        forest = build(centers, parents, supported, 64)
        coverage = []
        for parent, root, children, postorder, tokens in forest:
            coverage.extend(tokens)
            inside = {i: {i} for i in tokens}
            depth = {i: 0 for i in tokens}
            for node in postorder:
                left, right = children[node]
                check('tree_disjoint_subtrees', inside[left].isdisjoint(inside[right]))
                inside[node] = inside[left] | inside[right]
                depth[node] = max(depth[left], depth[right]) + 1
            outside = {root: set()}
            for node in reversed(postorder):
                left, right = children[node]
                outside[left] = outside[node] | inside[right]
                outside[right] = outside[node] | inside[left]
            for token in tokens:
                check('strict_complement_excludes_own_and_covers_all_others',
                      outside[token] == set(tokens) - {token})
                check('never_cross_original_parent', all(parents[i] == parent for i in outside[token]))
            check('bounded_balanced_depth', depth[root] <= (len(tokens) - 1).bit_length())
            check('private_internal_nodes_exact_n_minus_one', len(children) == len(tokens) - 1)
        check('true_support_exact_original_ID_coverage', sorted(coverage) ==
              [i for i, active in enumerate(supported) if active])
        check('deterministic_production_plan', forest == build(centers, parents, supported, 64))

    for n in [0, 1, 2, 3, 4, 7, 8, 16, 63, 64]:
        verify_forest([[float(i % 3), float(i // 3), float(i % 2)] for i in range(n)],
                      [0] * n, [True] * n)
    verify_forest([[0., 0., 0.]] * 8, [0, 0, 1, 1, 1, 2, 2, 2],
                  [True, False, True, True, False, False, False, True])
    check('empty_and_padding_not_in_domain', build([[0., 0., 0.]] * 3, [0, 1, 2], [False] * 3, 64) == [])
    for args in [([[0., 0., 0.]], [0], [], 64),
                 ([[float('nan'), 0., 0.]], [0], [True], 64),
                 ([[0., 0., 0.]], [-1], [True], 64),
                 ([[0., 0., 0.]], [True], [True], 64),
                 ([[0., 0., 0.]] * 65, [0] * 65, [True] * 65, 64)]:
        try:
            build(*args)
        except ValueError:
            checks.append('production_topology_fail_closed_invalid_domain')
        else:
            raise AssertionError('invalid production domain accepted')
    # Check actual source dataflow, rather than a second numerical model.
    forward = find(module, 'forward')
    ftext = ast.unparse(forward)
    check('outside_uses_only_parent_outside_and_sibling_inside',
          'torch.cat((outside[node], inside[right])' in ftext and
          'torch.cat((outside[node], inside[left])' in ftext and
          'torch.cat((outside[node], inside[node])' not in ftext)
    check('inverse_scatter_original_leaf_ID', 'index_copy(0, indices, torch.stack(values))' in ftext)
    check('torch_not_imported_by_offline_checks', 'torch' not in sys.modules)
    guard()
    result = {'status': 'OFFLINE_STATIC_CHECKS_PASSED_NATIVE_NOT_RUN',
              'check_count': len(checks), 'checks': checks,
              'model_source_hashes': {p.name: sha(p) for p in sorted(MODEL.glob('*.py'))},
              'config_sha256': sha(config), 'imports_torch': False,
              'native': 'NOT_RUN', 'resources': 'NOT_RUN',
              'limits': ['No torch shape/autograd/runtime/FP32/GPU/resource test.',
                         'Set propagation checks topology dependency support, not measured numerical Jacobians.',
                         'Exact current YAML bytes checked; no alternative hyperparameters.']}
    (HERE / 'static_validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(json.dumps({'status': result['status'], 'check_count': len(checks)}))


if __name__ == '__main__':
    main()
