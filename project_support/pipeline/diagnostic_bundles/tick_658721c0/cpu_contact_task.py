"""Finite source/graph distinction test; explicitly not a native task-gain test."""
import importlib.util
import json
from pathlib import Path
import numpy as np
import torch
from contact_exchange import contacts, exchange

root = Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
source = root / 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1/fine_exchange.py'
spec = importlib.util.spec_from_file_location('original_fine_exchange', source)
fle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fle)
assert not torch.cuda.is_initialized()
coordinates = np.asarray([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]], dtype=float)
voxels = np.column_stack((np.zeros(4, dtype=int), coordinates.astype(int)))
point_voxels = np.asarray([0, 1, 2, 3, 1])
point_superpoints = np.asarray([0, 1, 2, 3, 2])
edges = contacts(voxels, point_voxels, point_superpoints, [0, 4])[0]
leaves = np.asarray([0, 0, 1, 1])
x = (torch.arange(64, dtype=torch.float32).reshape(4, 16) / 32).requires_grad_()
fallback = torch.zeros_like(x)
actual, degree = exchange(x, coordinates, leaves, edges, fallback)
original_graph = fle.build_graph(coordinates, leaves, k=32)
original = fle.exchange(x, original_graph, heads=8)
old_gradient = torch.autograd.grad(original[1].sum(), x, retain_graph=True)[0][2]
new_gradient = torch.autograd.grad(actual[1].sum(), x, retain_graph=True)[0][2]
assert float(old_gradient.abs().max()) == 0 and float(new_gradient.abs().max()) > 0
permutation = np.asarray([3, 1, 0, 2])
inverse = np.argsort(permutation)
relabel_edges = contacts(voxels, point_voxels, inverse[point_superpoints], [0, 4])[0]
undo_edges = np.sort(permutation[relabel_edges], axis=1)
assert {tuple(e) for e in edges} == {tuple(e) for e in undo_edges}
permuted, _ = exchange(x[permutation], coordinates[permutation], leaves[permutation],
                      relabel_edges, fallback[permutation])
identity, _ = exchange(x, coordinates, leaves, edges, fallback)
deleted, _ = exchange(x, coordinates, leaves, np.empty((0, 2), dtype=int), fallback)
rotated, _ = exchange(x, coordinates, leaves, edges, fallback, rotate_values=True)
identity_error = float((actual - identity).abs().max().detach())
permutation_error = float((actual - permuted[inverse]).abs().max().detach())
assert max(identity_error, permutation_error) <= 1e-6
assert torch.equal(deleted, fallback)
assert float((rotated - actual).abs().max().detach()) > 0
result = {'source_graph_controls_pass': True, 'scope': 'Synthetic source/graph distinction only; zero native captures, task efficacy/admission unproved.',
    'edges': edges.tolist(), 'cross_leaf_edges': edges[leaves[edges[:, 0]] != leaves[edges[:, 1]]].tolist(),
    'degrees': degree, 'identity_error': identity_error, 'row_permutation_error': permutation_error,
    'fle_cross_leaf_donor_gradient_max': float(old_gradient.abs().max()),
    'contact_cross_leaf_donor_gradient_max': float(new_gradient.abs().max()),
    'deleted_contact_equals_fallback': True, 'donor_rotation_changes_message': True,
    'co_occupancy_graph_relabeling_exact': True, 'cuda_initialized': torch.cuda.is_initialized(),
    'new_training': 0, 'scientific_admission': False,
    'history_distinction': 'Direct physical cross-leaf feature delivery, not same-leaf FLE, selected-mask feature contrast readout, named-anchor relation loss or BCCA conditional supervision. This is not a novelty proof.'}
path = Path(__file__).with_name('cpu_contact_result.json')
with path.open('x') as stream:
    json.dump(result, stream, indent=2, allow_nan=False)
print(json.dumps(result))
