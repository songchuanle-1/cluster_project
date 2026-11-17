import ast, copy, datetime, hashlib, importlib.util, json, os, pathlib, subprocess, sys, types
os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1')
assert subprocess.check_output(['hostname'], text=True).strip() == 'dl04-MS-7E06'
root = pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
MODEL = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
path = root / 'framework/model/Quard_model' / MODEL / 'hier_postprocess.py'
assert hashlib.sha256(path.read_bytes()).hexdigest() == '7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
sys.path.insert(0, str(root))
resource = {'fresh_this_tick': False, 'scope': 'No resource recheck; keep prior observation timestamp16:24:50+08 and retry17:46:54+08. No allocation permission.'}
import torch
torch.set_num_threads(1)
assert not torch.cuda.is_initialized()
spec = importlib.util.spec_from_file_location('m95_hierarchy_unchanged', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
torch.manual_seed(1999)
model = module.C2F_ClusterAttn_CTF_HCG_CSORT(d_model=256, nhead=8, cluster_layer_nums=[256, 64, 8], per_layer_topk_list=[32, 16, 8], dropout=0.0).eval()
checkpoint = root.parent / 'Cluster_checkpoints' / MODEL / '20260815_101011/best.pth'
checkpoint_expected = 'fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
h = hashlib.sha256()
with checkpoint.open('rb') as handle:
    for block in iter(lambda: handle.read(8 * 1024 * 1024), b''):
        h.update(block)
assert h.hexdigest() == checkpoint_expected
rng_before = torch.get_rng_state().clone()
saved = torch.load(checkpoint, map_location='cpu', weights_only=False, mmap=True)
prefix_key = 'dec.cluster_att.'
weights = {key[len(prefix_key):]: value for key, value in saved['model'].items() if key.startswith(prefix_key)}
assert weights
incompatible = model.load_state_dict(weights, strict=True)
assert not incompatible.missing_keys and (not incompatible.unexpected_keys)
module_state_count = len(weights)
del saved, weights
assert torch.equal(rng_before, torch.get_rng_state()), 'Weight source must not change fixture RNG'
points = torch.randn(1, 6, 256)
query = torch.randn(1, 8, 256)
tokens = [torch.randn(1, k, 256) for k in (4, 2, 1)]
ids = [[torch.tensor([0, 0, 1, 2, 3, 3])], [torch.tensor([0, 0, 1, 1])], [torch.tensor([0, 0])]]
children = [[{0: [0], 1: [0], 2: [1], 3: [1]}], [{0: [0], 1: [0]}]]
mask = torch.zeros(1, 6, dtype=torch.bool)

def call(obj, p, q, t, m):
    module.reset_orth_accum()
    value = obj(p, q, m, t, children, ids)['point']
    module.get_orth_loss()
    return value
with torch.no_grad():
    a = call(model, points, query, tokens, mask)
    repeat = call(model, points, query, tokens, mask)
    query_swap = call(model, points, torch.randn_like(query), tokens, mask)
    padded = torch.cat([points, torch.zeros_like(points)], dim=1)
    padded_mask = torch.cat([mask, torch.ones_like(mask)], dim=1)
    padded_result = call(model, padded, query, tokens, padded_mask)[:, :6]
    changed = [t.clone() for t in tokens]
    changed[0] = changed[0].roll(1, dims=1)
    permuted = call(model, points, query, changed, mask)
    zero_points = torch.zeros_like(points)
    zero_a = call(model, zero_points, query, tokens, mask)
    zero_b = call(model, torch.cat([zero_points, zero_points], dim=1), query, tokens, padded_mask)[:, :6]
tree = ast.parse(path.read_text())
cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'C2F_ClusterAttn_CTF_HCG'))
node = copy.deepcopy(next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_cluster_to_points')))
assignments = [n for n in ast.walk(node) if isinstance(n, ast.Assign) and any((isinstance(t, ast.Name) and t.id == 'global_mean' for t in n.targets))]
assert len(assignments) == 1
assignments[0].value = ast.parse('torch.stack([point_feats[b, ~point_mask[b]].mean(dim=0) if (~point_mask[b]).any() else torch.zeros_like(point_feats[b, 0]) for b in range(point_feats.shape[0])], dim=0).unsqueeze(1).expand_as(point_feats)', mode='eval').body
code = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
scope = {'torch': torch}
exec(compile(code, '<masked-mean-diagnostic-only>', 'exec'), scope)
control = copy.deepcopy(model)
control._cluster_to_points = types.MethodType(scope['_cluster_to_points'], control)
with torch.no_grad():
    corrected_a = call(control, points, query, tokens, mask)
    corrected_b = call(control, padded, query, tokens, padded_mask)[:, :6]
    fixed_query = torch.randn(1, 8, 256)
    fixed_query = torch.nn.functional.normalize(fixed_query, dim=-1)
    logit_gap = (torch.einsum('bnd,bmd->bnm', fixed_query, a) - torch.einsum('bnd,bmd->bnm', fixed_query, padded_result)).abs().max().item()
q = query.clone().requires_grad_()
t = [value.clone().requires_grad_() for value in tokens]
pred = call(model, points, q, t, mask)
grads = torch.autograd.grad((pred * torch.randn_like(pred)).sum(), [q, *t], allow_unused=True)
metrics = {'repeat_delta': (a - repeat).abs().max().item(), 'query_swap_delta': (a - query_swap).abs().max().item(), 'fine_token_permutation_delta': (a - permuted).abs().max().item(), 'padding_valid_feature_delta': (a - padded_result).abs().max().item(), 'padding_fixed_query_logit_delta': logit_gap, 'zero_point_mean_padding_control_delta': (zero_a - zero_b).abs().max().item(), 'masked_mean_padding_control_delta': (corrected_a - corrected_b).abs().max().item(), 'unpadded_counterfactual_delta': (a - corrected_a).abs().max().item(), 'query_gradient_unused': grads[0] is None, 'cluster_token_gradient_norms': [value.norm().item() if value is not None else None for value in grads[1:]]}
checks = {'repeat_exact': metrics['repeat_delta'] == 0, 'query_blind_given_bank': metrics['query_swap_delta'] == 0 and metrics['query_gradient_unused'], 'token_path_active': metrics['fine_token_permutation_delta'] > 1e-06 and all((value and value > 0 for value in metrics['cluster_token_gradient_norms'])), 'zero_mean_negative_control': metrics['zero_point_mean_padding_control_delta'] <= 1e-06, 'masked_mean_control_padding_invariant': metrics['masked_mean_padding_control_delta'] <= 1e-06, 'counterfactual_agrees_unpadded': metrics['unpadded_counterfactual_delta'] <= 1e-06}
captured = {}

def capture_gate(m, i, o):
    captured['input'] = i[0].detach().clone()
    captured['logits'] = o.detach().clone()
hook = model.level_gate.register_forward_hook(capture_gate)
with torch.no_grad():
    same_original = call(model, padded, query, tokens, padded_mask)
hook.remove()
replayed = copy.deepcopy(model)
replayed.level_gate.forward = lambda _x: captured['logits']
blocked = copy.deepcopy(control)
blocked.level_gate.forward = lambda _x: captured['logits']
with torch.no_grad():
    replayed_out = call(replayed, padded, query, tokens, padded_mask)
    blocked_out = call(blocked, padded, query, tokens, padded_mask)
    mean_changed_out = call(control, padded, query, tokens, padded_mask)
same_metrics = {'original_logits_replay_delta': (same_original - replayed_out).abs().max().item(), 'blocked_global_mean_path_delta': (same_original - blocked_out).abs().max().item(), 'same_shape_global_mean_effect': (same_original[:, :6] - mean_changed_out[:, :6]).abs().max().item(), 'observed_mean_matches_padded_mean_delta': (captured['input'][..., 256:] - padded.mean(dim=1, keepdim=True)).abs().max().item()}
same_checks = {'original_path_replay_exact': same_metrics['original_logits_replay_delta'] == 0, 'blocked_path_control': same_metrics['blocked_global_mean_path_delta'] <= 1e-06, 'same_shape_mean_path_active': same_metrics['same_shape_global_mean_effect'] > 1e-06, 'actual_unmasked_mean_confirmed': same_metrics['observed_mean_matches_padded_mean_delta'] == 0}
assert all(same_checks.values()), (same_checks, same_metrics)
assert not torch.cuda.is_initialized()
print(json.dumps({'resource': resource, 'metrics': metrics, 'checks': checks, 'same_shape_metrics': same_metrics, 'same_shape_checks': same_checks, 'overall_control_status': 'PASS_CURRENT_FIXTURE_ONLY' if all(checks.values()) else 'FAIL_CURRENT_STRICT_CROSS_SHAPE_CONTROL', 'cuda_initialized': False, 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'sample_scope': 'One constructed CPU fixture, unchanged seed1999/constructor/input RNG, exact frozen M95 cluster-module weights. NOT native TRAIN features or network capture.', 'counterfactual_scope': 'Exactly one global_mean expression changed in an in-memory method clone, diagnostic only. Not a new model or tuning proposal.', 'optimizer_steps': 0, 'gpu_tests': 0, 'efficacy': 'unknown', 'native_backward_gate': 'not passed', 'checkpoint_sha256': checkpoint_expected, 'module_state_count': module_state_count, 'fixture_rng_unchanged': True}))
