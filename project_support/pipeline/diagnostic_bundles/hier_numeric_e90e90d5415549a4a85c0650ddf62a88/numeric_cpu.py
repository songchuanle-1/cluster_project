"""Decompose frozen arithmetic; never revise its original verdict."""
import ast
import json
import math
import torch
from torch.nn.attention import SDPBackend, sdpa_kernel
import hier_support as hs

torch.set_num_threads(1)
assert not torch.cuda.is_initialized()
functions = [n for n in ast.parse(FROZEN_TEST_SOURCE).body
             if isinstance(n, ast.FunctionDef) and n.name in ('fixture', 'run')]
assert len(functions) == 2
scope = {'torch': torch}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])),
             '<unchanged-fixture-functions>', 'exec'), scope)
fixture, run = scope['fixture'], scope['run']
original_attend = hs._attend


def explicit_selected(q, k, heads):
    if not k.shape[0]:
        return q * 0
    dim = q.shape[-1] // heads
    query = q.reshape(-1, heads, dim).transpose(0, 1)
    key = k.reshape(-1, heads, dim).transpose(0, 1)
    probability = ((query @ key.transpose(-1, -2)) / math.sqrt(dim)).softmax(-1)
    return (probability @ key).transpose(0, 1).reshape_as(q)


def math_selected(q, k, heads):
    with sdpa_kernel([SDPBackend.MATH]):
        return original_attend(q, k, heads)


def delta(a, b):
    return float((a - b).abs().max()) if a.numel() else 0.0


def decompose(data):
    p, banks, leaf, parent1, parent2, logits, _ = data
    valid, channels, heads = leaf.numel(), p.shape[-1], 8
    dim = channels // heads
    weights = logits.softmax(-1)
    query = p[:valid].reshape(valid, heads, dim).transpose(0, 1)
    tree = hs.supports(leaf, parent1, parent2)
    fused = p[:valid] * 0
    records = []
    for level, bank in enumerate(banks):
        key = bank.reshape(-1, heads, dim).transpose(0, 1)
        allowed = torch.zeros(valid, len(bank), dtype=torch.bool)
        for node, selections in tree.items():
            row = torch.nonzero(leaf == node, as_tuple=False).flatten()
            col = selections[level]
            if col.numel():
                allowed[row[:, None], col[None, :]] = True
        scores = (query @ key.transpose(-1, -2)) / math.sqrt(dim)
        nonempty = allowed.any(-1)
        masked = scores.masked_fill(~allowed.unsqueeze(0), -torch.inf)
        masked = torch.where(nonempty[None, :, None], masked, torch.zeros_like(masked))
        probability = masked.softmax(-1) * allowed.unsqueeze(0)
        dense_values = probability @ key
        dense_features = dense_values.transpose(0, 1).reshape(valid, channels)
        fused = fused + dense_features * weights[:valid, level:level + 1]
        deltas = dict.fromkeys(('qk_selected_vs_full', 'probability_selected_vs_full',
            'value_same_probability_different_reduction',
            'explicit_selected_vs_dense_level',
            'default_sdpa_vs_explicit_selected_level'), 0.0)
        for node, selections in tree.items():
            rows = torch.nonzero(leaf == node, as_tuple=False).flatten()
            columns = selections[level]
            if not columns.numel():
                continue
            keys = key.index_select(1, columns)
            qs = query.index_select(1, rows)
            selected_scores = (qs @ keys.transpose(-1, -2)) / math.sqrt(dim)
            full_scores = scores.index_select(1, rows).index_select(2, columns)
            full_probability = probability.index_select(1, rows).index_select(2, columns)
            selected_probability = selected_scores.softmax(-1)
            same_probability_values = full_probability @ keys
            selected_values = selected_probability @ keys
            full_values = dense_values.index_select(1, rows)
            point_rows = p.index_select(0, rows)
            selected_features = selected_values.transpose(0, 1).reshape_as(point_rows)
            sdpa_features = original_attend(point_rows, bank.index_select(0, columns), heads)
            observations = {
                'qk_selected_vs_full': delta(selected_scores, full_scores),
                'probability_selected_vs_full': delta(selected_probability, full_probability),
                'value_same_probability_different_reduction': delta(same_probability_values, full_values),
                'explicit_selected_vs_dense_level': delta(selected_values, full_values),
                'default_sdpa_vs_explicit_selected_level': delta(sdpa_features, selected_features)}
            for name, value in observations.items():
                deltas[name] = max(deltas[name], value)
        records.append({'level': level, **deltas})
    return torch.cat([fused, p[valid:] * 0], dim=0), records


records, checks = [], {}
for large in (False, True):
    name = '64/16/4' if large else '16/4/2'
    data = fixture(torch.float32, large)
    reference, reference_gradients, reference_masks = run(hs.dense_reference, data)
    with torch.no_grad():
        reconstructed, stages = decompose(data)
    checks[name + '_dense_reconstruction_exact'] = delta(reconstructed, reference) == 0
    p, banks, leaf, parent1, parent2, logits, query = data
    with torch.no_grad():
        double_args = (p.double(), [bank.double() for bank in banks], leaf,
                       parent1, parent2, logits.softmax(-1).double())
        oracle = hs.dense_reference(*double_args)
        oracle_masks = query.double() @ oracle.T
        oracle_grouped = hs.grouped(*double_args, chunk_size=5)
    checks[name + '_same_float32_input_float64_agreement'] = (
        delta(oracle_grouped, oracle) <= 1e-10
        and delta(query.double() @ oracle_grouped.T, oracle_masks) <= 1e-10)
    variants = {}
    try:
        for label, attend in (('original_default', original_attend),
                ('diagnostic_explicit_selected', explicit_selected),
                ('diagnostic_sdpa_math', math_selected)):
            hs._attend = attend
            output, gradients, masks = run(hs.grouped, data,
                                         chunk_size=5, checkpoint_chunks=False)
            deltas = {'output': delta(output, reference),
                'fixed_query_logits': delta(masks, reference_masks),
                'gradient_max': max(delta(a, b) for a, b in zip(gradients, reference_gradients)),
                'vs_same_input_float64_feature': delta(output.double(), oracle),
                'vs_same_input_float64_fixed_query': delta(masks.double(), oracle_masks)}
            deltas['original_float32_bound_met_for_this_pair_only'] = (
                max(deltas['output'], deltas['fixed_query_logits'], deltas['gradient_max']) <= 1e-6)
            variants[label] = deltas
    finally:
        hs._attend = original_attend
    checks[name + '_stage_metrics_finite'] = all(math.isfinite(v)
        for row in stages for k, v in row.items() if k != 'level')
    records.append({'tree': name, 'dtype': 'float32', 'chunk_size': 5,
        'dense_reconstruction_delta': delta(reconstructed, reference),
        'dense_vs_same_input_float64_fixed_query': delta(reference_masks.double(), oracle_masks),
        'same_input_float64_dense_vs_grouped': delta(oracle_grouped, oracle),
        'stage_deltas': stages, 'variants': variants})
checks['cuda_not_initialized'] = not torch.cuda.is_initialized()
print('HIER_NUMERIC_JSON=' + json.dumps({
    'status': 'NUMERICAL_DIAGNOSTIC_ONLY_ORIGINAL_FAIL_RETAINED',
    'torch_version': torch.__version__, 'num_threads': torch.get_num_threads(),
    'checks': checks, 'check_count': len(checks),
    'failures': [k for k, v in checks.items() if not v], 'records': records,
    'prior_float32_failures_reclassified': False,
    'production_precision_or_backend_changed': False,
    'native_network_forwards': 0, 'optimizer_steps': 0,
    'cuda_initialized': torch.cuda.is_initialized(),
    'scope': 'Same constructed inputs only; not native correctness, resources or task efficacy.'}))
raise SystemExit(0 if all(checks.values()) else 1)
