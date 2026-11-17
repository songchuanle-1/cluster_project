import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import torch
from hier_support import dense_reference, grouped

torch.set_num_threads(1)
tree = ast.parse(FROZEN_TEST_SOURCE)
scope = {'torch': torch}
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('fixture', 'run')]
assert len(functions) == 2
exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), '<unchanged-fixture-functions>', 'exec'), scope)
fixture, run = scope['fixture'], scope['run']
records = []
for large in (False, True):
    data = fixture(torch.float32, large)
    ref, ref_grad, ref_masks = run(dense_reference, data)
    reference_repeat, _, _ = run(dense_reference, data)
    out, grad, masks = run(grouped, data, chunk_size=5, checkpoint_chunks=False)
    repeated, repeat_grad, repeated_masks = run(grouped, data, chunk_size=5, checkpoint_chunks=False)
    checkpointed, checkpoint_grad, checkpoint_masks = run(grouped, data, chunk_size=5, checkpoint_chunks=True)
    query = data[-1].double()
    reference_double_readout = query @ ref.double().T
    grouped_double_readout = query @ out.double().T
    propagation_bound = query.abs() @ (out.double()-ref.double()).abs().T
    records.append({'tree': '64/16/4' if large else '16/4/2',
        'dense_repeat_delta': float((ref-reference_repeat).abs().max()),
        'grouped_repeat_delta': float((out-repeated).abs().max()),
        'checkpoint_same_shape_output_delta': float((out-checkpointed).abs().max()),
        'checkpoint_same_shape_gradient_delta': max(float((a-b).abs().max()) for a,b in zip(grad, checkpoint_grad)),
        'checkpoint_same_shape_logit_delta': float((masks-checkpoint_masks).abs().max()),
        'dense_vs_grouped_feature_delta': float((out-ref).abs().max()),
        'original_float32_logit_delta': float((masks-ref_masks).abs().max()),
        'conditional_double_readout_delta': float((grouped_double_readout-reference_double_readout).abs().max()),
        'conditional_propagation_bound_max': float(propagation_bound.max()),
        'dense_float32_readout_rounding': float((reference_double_readout-ref_masks.double()).abs().max()),
        'grouped_float32_readout_rounding': float((grouped_double_readout-masks.double()).abs().max())})

root = Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
name = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
sys.path[:0] = [str(root), str(root/'framework/lib')]
source = root/'framework/model/Quard_model'/name/'hier_postprocess.py'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
spec = importlib.util.spec_from_file_location('unchanged_m95_source', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
torch.manual_seed(1999)
model = module.C2F_ClusterAttn_CTF_HCG_CSORT(d_model=256, nhead=8, cluster_layer_nums=[256,64,8], per_layer_topk_list=[32,16,8], dropout=0.0).eval()
checkpoint = root.parent/'Cluster_checkpoints'/name/'20260815_101011/best.pth'
digest = hashlib.sha256()
with checkpoint.open('rb') as handle:
    for block in iter(lambda: handle.read(8*1024*1024), b''):
        digest.update(block)
assert digest.hexdigest() == 'fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
saved = torch.load(checkpoint, map_location='cpu', weights_only=False, mmap=True)
weights = {key[len('dec.cluster_att.'):]:value for key,value in saved['model'].items() if key.startswith('dec.cluster_att.')}
model.load_state_dict(weights, strict=True)
state_count = len(weights)
del saved, weights
p, banks, leaf, parent1, parent2, logits, query = fixture(torch.float32, True)
mask = torch.arange(p.shape[0])[None,:] >= leaf.numel()
ids = [[leaf], [parent1], [parent2]]
original_banks = [bank.unsqueeze(0) for bank in banks]
changed = [bank.clone() for bank in banks]
changed[2][parent2[parent1[leaf[0]]]] += 100
with torch.no_grad():
    original = model._cluster_to_points(p.unsqueeze(0), original_banks, ids, mask)
    intervened = model._cluster_to_points(p.unsqueeze(0), [bank.unsqueeze(0) for bank in changed], ids, mask)
original_delta = float((original[0,0]-intervened[0,0]).abs().max())
checks = {'dense_and_grouped_repeat_exact': all(r['dense_repeat_delta']==r['grouped_repeat_delta']==0 for r in records),
          'same_shape_checkpoint_exact': all(r['checkpoint_same_shape_output_delta']==r['checkpoint_same_shape_gradient_delta']==r['checkpoint_same_shape_logit_delta']==0 for r in records),
          'original_hcg_own_coarse_path_active': original_delta > 1e-6,
          'cuda_not_initialized': not torch.cuda.is_initialized()}
print('HIER_CALIBRATION_JSON='+json.dumps({'status':'DIAGNOSTIC_ONLY_ORIGINAL_FAIL_RETAINED',
    'checks':checks,'records':records,'original_m95_own_coarse_point0_delta':original_delta,
    'module_state_count':state_count,'original_strict_control_reclassified':False,
    'native_network_forwards':0,'optimizer_steps':0,'cuda_initialized':torch.cuda.is_initialized(),
    'scope':'Unchanged constructed inputs; double readout is a diagnostic, not changed precision or admission.'}))
