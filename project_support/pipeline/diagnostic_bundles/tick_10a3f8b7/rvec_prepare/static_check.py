"""Read-only stdlib source checks. Does not import Torch or the candidate."""
from pathlib import Path
from fractions import Fraction as Q
import ast
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def dump(node):
    return ast.dump(node, include_attributes=False)


def main():
    version = json.loads((HERE / 'source_version.json').read_text(encoding='utf8'))
    source = HERE / 'source'
    model = source / version['model_dir']
    references = HERE / 'references'
    checks = []
    def check(name, value):
        assert value, name
        checks.append(name)
    actual = {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
    check('exact_nine_source_hash_map', actual == version['source_files_exact9'])
    check('eight_python_one_yaml', len(list(source.rglob('*.py'))) == 8 and len(list(source.rglob('*.yaml'))) == 1)
    for path in source.rglob('*.py'):
        compile(path.read_bytes(), str(path), 'exec')
    check('all_eight_compile_without_import', True)
    check('M95_common5_byte_exact', all(sha(model / n) == digest for n, digest in version['M95_common5_byte_exact'].items()))
    check('plain_M95_init_no_startup_guard', (model / '__init__.py').read_text(encoding='utf8') == 'from .network import Network\n\n__all__ = ["Network"]\n' and not (model / 'startup_guard.py').exists())
    legacy_dec = (references / 'fle_dec.py').read_text(encoding='utf8')
    current_dec = (model / 'dec.py').read_text(encoding='utf8')
    check('decoder_only_class_and_mode_projection', current_dec == legacy_dec.replace('C2F_ClusterAttn_FLE_CSORT', 'C2F_ClusterAttn_RVEC_CSORT').replace("'fle_csort'", "'rvec_csort'"))
    legacy_hier = (references / 'fle_hier_postprocess.py').read_text(encoding='utf8')
    expected_hier = legacy_hier.replace('C2F_ClusterAttn_FLE_CSORT', 'C2F_ClusterAttn_RVEC_CSORT').replace('"""Fine point exchange, with the unchanged middle/coarse M95 context."""', '"""Receiver vector exchange, with unchanged middle/coarse M95 context."""').replace('from .fine_exchange import FineLeafExchange', 'from .receiver_vector_exchange import FineLeafReceiverVectorExchange').replace('self.fine_exchange = FineLeafExchange(\n            k=self.per_layer_topk_list[0], heads=self.nhead)', 'self.fine_exchange = FineLeafReceiverVectorExchange(\n            channels=self.d_model, k=self.per_layer_topk_list[0], heads=self.nhead)')
    current_hier = (model / 'hier_postprocess.py').read_text(encoding='utf8')
    check('hierarchy_only_operator_constructor_and_class_projection', current_hier == expected_hier)
    old_config = (references / 'fle_config.yaml').read_text(encoding='utf8')
    config = (source / version['config']).read_text(encoding='utf8')
    check('config_only_mode_change', config == old_config.replace('cluster_mode: fle_csort', 'cluster_mode: rvec_csort', 1))
    check('actual_YAML_GELU_H8_C256_K32_inherited', all(x in config for x in ['activation_fn: gelu', 'nhead: 8', 'd_model: 256', 'per_layer_topk_list: [32, 16, 8]']))
    text = (model / 'receiver_vector_exchange.py').read_text(encoding='utf8')
    tree = ast.parse(text)
    legacy = ast.parse((references / 'fle_fine_exchange.py').read_text(encoding='utf8'))
    check('build_graph_AST_exact_inherited', dump(function(tree, 'build_graph')) == dump(function(legacy, 'build_graph')))
    check('no_new_softmax_gate_routing_environment_or_cuda', not any(x in text for x in ['softmax(', 'os.environ', '.cuda(', 'getenv(', 'topk(', 'level_gate']))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'FineLeafReceiverVectorExchange')
    methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    check('actual_forward_fixed_optimized_control_false', ast.unparse(methods['forward'].body[0].value).endswith('exchange_optimized, False)'))
    check('own_only_fixed_optimized_control_true', ast.unparse(methods['forward_own_only'].body[0].value).endswith('exchange_optimized, True)'))
    fallback = ast.unparse(function(tree, '_fallback'))
    check('actual_fallback_raw_leaf_mean_and_control_rawself', 'fallback_value = features' in fallback and 'fallback_value = means[groups]' in fallback and 'torch.bincount(groups)' in fallback)
    ref = ast.unparse(function(tree, 'exchange_reference'))
    opt = ast.unparse(function(tree, 'exchange_optimized'))
    check('reference_joint_relative_affine_then_edge_GELU_then_second_affine', 'relative = x[indices] - x.unsqueeze(1)' in ref and "torch.einsum('nkhd,hod->nkho', relative, wd)" in ref and 'F.gelu(affine)' in ref)
    check('optimized_Wr_minus_Wd_and_Wd_precomputed', "torch.einsum('nhd,hod->nho', x, wr - wd)" in opt and "torch.einsum('nhd,hod->nho', x, wd)" in opt)
    check('GELU_before_masked_mean_second_affine_after_mean', opt.index('F.gelu(affine)') < opt.index('mean_hidden =') < opt.index("torch.einsum('nhd,hod->nho', mean_hidden, w2)"))
    check('allowed_edges_only_both_forms', 'masked_fill(~allowed[:, :, None, None], 0)' in ref and 'masked_fill(~allowed[:, :, None, None], 0)' in opt)
    check('own_only_affine_no_donor_in_both_forms', 'receiver.expand(-1, indices.shape[1], -1, -1) + b1' in ref and 'receiver.unsqueeze(1).expand(-1, indices.shape[1], -1, -1) + b1' in opt)
    check('parameter_count_25088', 3 * 8 * 32 * 32 + 2 * 8 * 32 == 25088)
    # Exact rational identities: no Torch tensors, approximate GELU or gradient claims.
    x = [Q(2, 3), Q(-4, 5)]
    donors = [[Q(1, 7), Q(8, 3)], [Q(-2, 9), Q(5, 11)]]
    wr = [[Q(1, 2), Q(-2, 3)], [Q(4, 7), Q(3, 5)]]
    wd = [[Q(-5, 13), Q(7, 17)], [Q(2, 19), Q(-3, 23)]]
    w2 = [[Q(3, 4), Q(-2, 5)], [Q(5, 7), Q(7, 9)]]
    b1 = [Q(1, 31), Q(-3, 37)]
    b2 = [Q(1, 41), Q(2, 43)]
    def mv(weight, value):
        return [sum(a * b for a, b in zip(row, value)) for row in weight]
    for donor in donors:
        direct = [a + b + c for a, b, c in zip(mv(wr, x), mv(wd, [j-i for i,j in zip(x, donor)]), b1)]
        optimized = [a + b + c for a,b,c in zip(mv([[a-b for a,b in zip(ar,br)] for ar,br in zip(wr,wd)], x), mv(wd, donor), b1)]
        check('rational_endpoint_affine_identity_' + str(len(checks)), direct == optimized)
    arbitrary_hidden = [[Q(2, 47), Q(7, 53)], [Q(-4, 59), Q(11, 61)]]
    per_edge = [[a+b for a,b in zip(mv(w2, h), b2)] for h in arbitrary_hidden]
    left = [sum(row[j] for row in per_edge) / len(per_edge) for j in range(2)]
    right = [a+b for a,b in zip(mv(w2, [sum(h[j] for h in arbitrary_hidden)/len(arbitrary_hidden) for j in range(2)]), b2)]
    check('rational_second_affine_mean_commutation_any_hidden', left == right)
    gelu = lambda z: z * (1 + math.erf(z / math.sqrt(2))) / 2
    check('negative_control_mean_cannot_cross_GELU', abs((gelu(1) + gelu(-1))/2 - gelu(0)) > 0.1)
    print(json.dumps({'schema_version': 1, 'passed': True, 'scope': 'STDLIB_STATIC_AND_EXACT_RATIONAL_AFFINE_IDENTITIES_ONLY',
                      'checks_passed': len(checks), 'checks': checks, 'Torch_imported': False,
                      'actual_reference_optimized_tensor_equivalence': 'NOT_RUN', 'autograd': 'NOT_RUN',
                      'native_backward': 'NOT_RUN', 'resources': 'NOT_RUN', 'efficacy': 'UNKNOWN', 'novelty': 'UNKNOWN'}, indent=2))


if __name__ == '__main__':
    main()
