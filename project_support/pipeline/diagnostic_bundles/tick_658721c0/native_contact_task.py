"""Frozen TRAIN capture and point-feature-only counterfactual readout."""
import argparse
import copy
import hashlib
import importlib
import logging
from pathlib import Path
from native_runtime import acquire, release, setup, save, sha, MANIFEST, ROOT, NAME

parser = argparse.ArgumentParser()
parser.add_argument('--lease', required=True)
args = parser.parse_args()
result = {'execution_completed': False, 'scientific_admission': False, 'new_training': 0,
          'native_loss_forwards': 0, 'full_native_loss_backwards': 0, 'cut_path_backward_calls': 0,
          'scope': 'Frozen-bank, fixed-query point-feature counterfactual. This does not repair or pass the historical full-source numerical/permutation gates.'}
hooks, bank, attention, module = [], None, None, None
original_build, original_gather = None, None
try:
    result['before'] = acquire(args.lease)
    torch, gorilla, cfg, model, metadata = setup()
    import numpy as np
    from torch.utils.data import DataLoader, Subset
    from framework.dataset import build_dataset
    from contact_exchange import contacts, exchange, readback
    assert sha(MANIFEST['assets']['operator_path']) == MANIFEST['assets']['operator_sha256']
    module = importlib.import_module('framework.model.Quard_model.' + NAME + '.hier_postprocess')
    bank, attention = model.dec.cluster_bank, model.dec.cluster_att
    original_build, original_gather = bank.build_cluster_feats, attention._cluster_to_points
    active = [layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active) == 1 and active[0] is model.dec.encoder_layers[-1]
    encoder, decoder = active[0], model.dec.decoder_layers[-1]
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('contact-native'))
    cohort = MANIFEST['cohort']
    for scene in cohort:
        group = dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id'] == scene['scene_id']
        assert [{'object_id': str(row['object_id']), 'ann_id': str(row['ann_id'])} for row in group] == scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch = next(iter(DataLoader(Subset(dataset, [s['group_index'] for s in cohort]),
        batch_size=2, shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)))
    lengths = [int(v) for v in batch['scenes_len']]
    assert lengths == [4, 4]
    raw_offsets = batch['batch_offsets'].cpu().numpy()
    edge_arrays = contacts(batch['voxel_coords'].cpu().numpy(), batch['p2v_map'].cpu().numpy(),
                           batch['superpoints'].cpu().numpy(), raw_offsets)
    expanded_edges = [edges for edges, size in zip(edge_arrays, lengths) for _ in range(size)]
    held = {}

    def clone(value):
        if torch.is_tensor(value):
            return value.detach().clone()
        if isinstance(value, (list, tuple)):
            return type(value)(clone(v) for v in value)
        if isinstance(value, dict):
            return {key: clone(v) for key, v in value.items()}
        return value

    def error(a, b):
        return float((a - b).abs().max().detach().cpu())

    def capture_build(*values):
        output = original_build(*values)
        held['raw_banks'] = clone(output)
        return output

    def capture_gather(*values):
        output = original_gather(*values)
        held['gather_args'], held['gather_output'] = clone(values), clone(output)
        return output

    def capture_encoder_input(owner, values, keywords):
        held['encoder_args'], held['encoder_kwargs'] = clone(values), clone(keywords)

    def capture_encoder_output(owner, values, output):
        held['encoder_output'] = clone(output)

    def capture_decoder(owner, values, output):
        held['final_query'], held['native_masks'], held['native_indis'] = clone(output[0]), clone(output[2]), clone(output[3])
        held['final_features'], held['padding'] = clone(values[2]), clone(values[3])

    bank.build_cluster_feats, attention._cluster_to_points = capture_build, capture_gather
    hooks.append(encoder.register_forward_pre_hook(capture_encoder_input, with_kwargs=True))
    hooks.append(encoder.register_forward_hook(capture_encoder_output))
    hooks.append(decoder.register_forward_hook(capture_decoder))
    with torch.no_grad():
        loss, _ = model(copy.deepcopy(batch), mode='loss')
    result['native_loss_forwards'] = 1
    result['native_loss'] = float(loss.cpu())
    for hook in hooks:
        hook.remove()
    hooks.clear()
    bank.build_cluster_feats = lambda *values: held['raw_banks']
    attention._cluster_to_points = original_gather
    positions = held['encoder_args'][5]
    features, refined, identifiers, padding = held['gather_args']
    with torch.no_grad():
        reconstruction = readback(attention, features, refined, identifiers, padding)
        _, head_identity = decoder.prediction_head(held['final_query'], held['final_features'], held['padding'])
        module.reset_orth_accum()
        _, identity_features = encoder(*held['encoder_args'], **held['encoder_kwargs'])
    result['controls'] = {
        'readback_replica_max_error': error(reconstruction, held['gather_output']),
        'native_head_identity_max_error': error(head_identity, held['native_masks']),
        'frozen_bank_encoder_identity_max_error': error(identity_features, held['final_features'])}
    assert max(result['controls'].values()) <= MANIFEST['tolerance'], 'Original strict identity control failed before intervention'
    degrees, fine_messages, rotations, operator_errors = [], [], [], []
    incidence = []
    with torch.no_grad():
        for b, ids in enumerate(identifiers[0]):
            n = len(ids)
            assert n == int((~padding[b]).sum())
            xyz, leaves = positions[b, :n].cpu().numpy(), ids.cpu().numpy()
            fallback = refined[0][b, ids.long()]
            message, degree = exchange(features[b, :n], xyz, leaves, expanded_edges[b], fallback, heads=attention.nhead)
            rotated, _ = exchange(features[b, :n], xyz, leaves, expanded_edges[b], fallback, heads=attention.nhead, rotate_values=True)
            permutation = np.arange(n - 1, -1, -1)
            inverse = np.argsort(permutation)
            renamed, _ = exchange(features[b, :n][permutation.copy()], xyz[permutation], leaves[permutation],
                inverse[expanded_edges[b]], fallback[permutation.copy()], heads=attention.nhead)
            operator_errors.append(error(message, renamed[inverse.copy()]))
            assert operator_errors[-1] <= MANIFEST['tolerance'], 'Native-feature operator relabeling control failed'
            fine_messages.append(message)
            rotations.append(rotated)
            degrees.append(degree)
            edges = expanded_edges[b]
            cross = leaves[edges[:, 0]] != leaves[edges[:, 1]]
            target = torch.as_tensor(batch['gt_spmasks'][b], device=features.device).reshape(-1).float()
            assert target.numel() == n and bool(((target >= 0) & (target <= 1)).all())
            labels = target.cpu().numpy() > .5
            same_target = labels[edges[:, 0]] == labels[edges[:, 1]]
            incidence.append({'expression': b, 'supports': n, 'physical_edges': len(edges),
                'cross_leaf_edges': int(cross.sum()), 'cross_leaf_receivers': sum(d > 0 for d in degree),
                'cross_leaf_target_boundary_edges': int((cross & ~same_target).sum()),
                'cross_leaf_same_target_label_edges': int((cross & same_target).sum())})
        result['controls']['operator_row_permutation_max_error'] = max(operator_errors)
        arm_masks, arm_feature_changes = {}, {}
        for arm, messages in (('deleted', None), ('physical_contact', fine_messages), ('rotated_values', rotations)):
            attention._cluster_to_points = lambda *values, override=messages: readback(attention, *values, fine_override=override)
            module.reset_orth_accum()
            _, updated_features = encoder(*held['encoder_args'], **held['encoder_kwargs'])
            _, masks = decoder.prediction_head(held['final_query'], updated_features, held['padding'])
            arm_masks[arm] = masks
            arm_feature_changes[arm] = error(updated_features, held['final_features'])
        result['controls']['deleted_contact_mask_max_error'] = error(arm_masks['deleted'], held['native_masks'])
        assert result['controls']['deleted_contact_mask_max_error'] <= MANIFEST['tolerance']
        selected = held['native_indis'].softmax(-1)[..., 1].argmax(-1)
        readouts = []
        for b, ids in enumerate(identifiers[0]):
            n = len(ids)
            target = torch.as_tensor(batch['gt_spmasks'][b], device=features.device).reshape(-1).float()
            query = int(selected[b])
            native = held['native_masks'][b, query, :n].sigmoid()
            changed = arm_masks['physical_contact'][b, query, :n].sigmoid()
            rotated = arm_masks['rotated_values'][b, query, :n].sigmoid()
            receivers = torch.tensor(degrees[b], device=features.device) > 0
            original_error = (native - target).abs()
            changed_error, rotated_error = (changed - target).abs(), (rotated - target).abs()
            readouts.append({'expression': b, 'scene_id': cohort[0 if b < lengths[0] else 1]['scene_id'],
                'frozen_deployed_query': query, 'supports': n, 'contact_receivers': int(receivers.sum()),
                'baseline_probability_mae': float(original_error.mean()),
                'contact_minus_baseline_probability_mae': float((changed_error - original_error).mean()),
                'contact_minus_rotated_probability_mae': float((changed_error - rotated_error).mean()),
                'receiver_contact_minus_baseline_probability_mae': float((changed_error - original_error)[receivers].mean()) if bool(receivers.any()) else None})
    with torch.enable_grad():
        b = next(b for b, ds in enumerate(degrees) if any(ds))
        n = len(identifiers[0][b])
        differentiated = features[b, :n].detach().clone().requires_grad_()
        message, _ = exchange(differentiated, positions[b, :n].cpu().numpy(),
            identifiers[0][b].cpu().numpy(), expanded_edges[b], refined[0][b, identifiers[0][b].long()], heads=attention.nhead)
        receiver = next(i for i, degree in enumerate(degrees[b]) if degree)
        gradient = torch.autograd.grad(message[receiver].sum(), differentiated)[0]
        off_leaf = identifiers[0][b] != identifiers[0][b][receiver]
        result['native_cut_path_off_leaf_gradient_max'] = float(gradient[off_leaf].abs().max().cpu())
        assert result['native_cut_path_off_leaf_gradient_max'] > 0
        result['cut_path_backward_calls'] = 1
    result.update(incidence=incidence, readouts=readouts, feature_changes=arm_feature_changes,
        scene_ids=[s['scene_id'] for s in cohort], native_expressions=8, distinct_scenes=2,
        original_numeric_gates_preserved=True, full_source_permutation_admission='unproved',
        execution_completed=True)
    fixture = Path(__file__).with_name('native_contact_fixture.pt')
    with fixture.open('xb') as stream:
        torch.save({'features': features.cpu(), 'positions': positions.cpu(), 'refined_banks': [v.cpu() for v in refined],
            'fine_ids': [v.cpu() for v in identifiers[0]], 'physical_edges': edge_arrays,
            'targets': batch['gt_spmasks'], 'cohort': cohort, 'scope': 'Captured native tensors, not model weights.'}, stream)
    result['fixture'] = {'path': str(fixture), 'sha256': sha(fixture), 'bytes': fixture.stat().st_size}
    result['after'] = __import__('native_runtime').observe()
except BaseException as error_value:
    result.update(error_type=type(error_value).__name__, error=str(error_value))
    raise
finally:
    for hook in hooks:
        hook.remove()
    if bank is not None and original_build is not None:
        bank.build_cluster_feats = original_build
    if attention is not None and original_gather is not None:
        attention._cluster_to_points = original_gather
    if module is not None:
        module.reset_orth_accum()
    try:
        save('native_contact_result.json', result)
    finally:
        release()
