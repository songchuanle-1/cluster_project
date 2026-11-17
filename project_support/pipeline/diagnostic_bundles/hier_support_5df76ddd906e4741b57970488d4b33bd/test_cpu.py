"""Frozen constructed controls; no native samples, optimizer or CUDA."""
import json
import torch
from hier_support import coverage, dense_reference, grouped, supports

torch.set_num_threads(1)
assert not torch.cuda.is_initialized()
checks, metrics = {}, {}


def fixture(dtype, large=False):
    generator = torch.Generator().manual_seed(1999)
    sizes = (64, 16, 4) if large else (16, 4, 2)
    valid = 131 if large else 53
    p = torch.randn(valid + 3, 256, generator=generator, dtype=dtype)
    banks = [torch.randn(k + 2, 256, generator=generator, dtype=dtype) for k in sizes]
    # The last two bank rows are padding and are never part of the tree.
    parent1 = torch.arange(sizes[0]) // (sizes[0] // sizes[1])
    parent2 = torch.arange(sizes[1]) // (sizes[1] // sizes[2])
    leaf = torch.arange(valid) % sizes[0]
    logits = torch.randn(valid + 3, 3, generator=generator, dtype=dtype)
    query = torch.randn(3, 256, generator=generator, dtype=dtype)
    return p, banks, leaf, parent1, parent2, logits, query


def run(function, data, **kwargs):
    p, bank, leaf, parent1, parent2, logits, query = data
    variables = [value.detach().clone().requires_grad_() for value in [p, *bank, logits]]
    weights = variables[-1].softmax(dim=-1)
    output = function(variables[0], variables[1:4], leaf, parent1, parent2, weights, **kwargs)
    readout = query @ output.T
    loss = output.square().mean() + readout.square().mean()
    gradients = torch.autograd.grad(loss, variables)
    return output.detach(), [g.detach() for g in gradients], readout.detach()


for dtype, label, tolerance in ((torch.float64, 'float64', 1e-10), (torch.float32, 'float32', 1e-6)):
    for large in (False, True):
        data = fixture(dtype, large)
        name = label + ('_64_16_4' if large else '_16_4_2')
        checks[name + '_cover_once'] = coverage(data[2], data[3], data[4])
        reference, ref_grad, ref_masks = run(dense_reference, data)
        for chunk in (1, 5, 1024):
            for use_checkpoint in (False, True):
                prefix = name + '_chunk' + str(chunk) + '_checkpoint' + str(use_checkpoint)
                output, gradients, masks = run(grouped, data, chunk_size=chunk, checkpoint_chunks=use_checkpoint)
                deltas = {'output': float((output-reference).abs().max()),
                          'fixed_query_logits': float((masks-ref_masks).abs().max()),
                          'input_gradient_max': [float((a-b).abs().max()) for a, b in zip(gradients, ref_grad)]}
                metrics[prefix] = deltas
                checks[prefix] = deltas['output'] <= tolerance and deltas['fixed_query_logits'] <= tolerance and max(deltas['input_gradient_max']) <= tolerance

data = fixture(torch.float32, True)
p, banks, leaf, parent1, parent2, logits, query = data
weights = logits.softmax(dim=-1)
with torch.no_grad():
    output = grouped(p, banks, leaf, parent1, parent2, weights)
    changed = [bank.clone() for bank in banks]
    for bank in changed:
        bank[-2:] = 10000
    ppad = p.clone()
    ppad[leaf.numel():] = 10000
    padded = grouped(ppad, changed, leaf, parent1, parent2, weights)
    metrics['padding_delta'] = float((output-padded).abs().max())
    checks['padding_no_effect_and_zero_output'] = metrics['padding_delta'] == 0 and bool((output[leaf.numel():] == 0).all())
    for level in range(3):
        changed = [bank.clone() for bank in banks]
        selected = supports(leaf, parent1, parent2)[int(leaf[0])][level]
        assert selected.numel() > 1
        changed[level][selected[0]] += .25
        intervention = grouped(p, changed, leaf, parent1, parent2, weights)
        metrics['level' + str(level) + '_included_delta'] = float(((query @ intervention.T)[:, 0]-(query @ output.T)[:, 0]).abs().max())
        checks['level' + str(level) + '_included_path_active'] = metrics['level' + str(level) + '_included_delta'] > 1e-6
    changed = [bank.clone() for bank in banks]
    excluded_top = parent2[parent1[leaf[0]]]
    changed[2][excluded_top] += 100
    excluded = grouped(p, changed, leaf, parent1, parent2, weights)
    metrics['excluded_coarse_point0_delta'] = float((excluded[0]-output[0]).abs().max())
    checks['excluded_coarse_point0_no_effect'] = metrics['excluded_coarse_point0_delta'] == 0
    def readout(message, frozen_message=None):
        feature = p + (message if frozen_message is None else frozen_message)
        return query @ feature.T
    checks['blocked_readout_exact'] = bool((readout(excluded, output) == readout(output, output)).all())
    checks['unblocked_readout_changes'] = float((readout(excluded)-readout(output)).abs().max()) > 1e-6
    # Relabel leaf IDs and bank rows without changing their geometric groups.
    perm = torch.arange(parent1.numel()-1, -1, -1)
    relabeled_banks = [torch.cat([banks[0][perm], banks[0][-2:]]), banks[1], banks[2]]
    inverse = torch.argsort(perm)
    relabeled = grouped(p, relabeled_banks, inverse[leaf], parent1[perm], parent2, weights)
    metrics['relabel_delta'] = float((relabeled-output).abs().max())
    checks['leaf_relabel_invariant'] = metrics['relabel_delta'] <= 1e-6
    single = grouped(p[:2], [b[:1] for b in banks], torch.zeros(1, dtype=torch.long),
                     torch.zeros(1, dtype=torch.long), torch.zeros(1, dtype=torch.long), weights[:2])
    checks['single_tree_finite_and_empty_roles_zero'] = bool(torch.isfinite(single).all()) and bool((single[1] == 0).all())
    empty = grouped(p[:2], [b[:1] for b in banks], torch.zeros(0, dtype=torch.long),
                    torch.zeros(1, dtype=torch.long), torch.zeros(1, dtype=torch.long), weights[:2])
    checks['empty_scene_zero'] = bool((empty == 0).all())


def saved_storage(function, checkpointed=False):
    tensors = set()
    def pack(tensor):
        tensors.add((tensor.untyped_storage().data_ptr(), tensor.untyped_storage().nbytes()))
        return tensor
    with torch.autograd.graph.saved_tensors_hooks(pack, lambda value: value):
        run(function, fixture(torch.float32, True), **({'checkpoint_chunks': True} if checkpointed else {}))
    return {'unique_storage_bytes': sum(size for _, size in tensors), 'unique_storages': len(tensors)}


metrics['cpu_saved_tensor_storage'] = {'dense': saved_storage(dense_reference),
    'grouped_checkpoint': saved_storage(grouped, True),
    'scope': 'CPU autograd referenced storage only; NOT peak GPU or whole-model memory; no savings gate.'}
checks['cuda_not_initialized'] = not torch.cuda.is_initialized()
result = {'status': 'PASS_CONSTRUCTED_OPERATOR_ONLY' if all(checks.values()) else 'FAIL_CONSTRUCTED_OPERATOR_CONTROL',
          'torch_version': torch.__version__, 'checks': checks, 'metrics': metrics,
          'check_count': len(checks), 'failures': [key for key, passed in checks.items() if not passed],
          'native_network_forwards': 0, 'optimizer_steps': 0, 'cuda_initialized': torch.cuda.is_initialized(),
          'scope': 'Two constructed trees, frozen seed1999/C256/head8; not native TRAIN or trained efficacy.'}
print('HIER_SUPPORT_JSON=' + json.dumps(result))
raise SystemExit(0 if all(checks.values()) else 1)
