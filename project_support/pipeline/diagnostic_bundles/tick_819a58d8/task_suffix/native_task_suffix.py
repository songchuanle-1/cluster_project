"""Actual native criterion responses; one readout message changed at a time."""
import argparse
import copy
import importlib
import logging
import numpy as np
from native_runtime import (acquire, release, verify, observe, setup, save,
                            fingerprint, MANIFEST, NAME)

parser = argparse.ArgumentParser()
parser.add_argument('--lease', required=True)
args = parser.parse_args()
r = {'execution_completed': False, 'controls_passed': False, 'native_forwards': 0,
     'native_backwards': 0, 'source_interface_forwards': 0, 'suffix_replays': 0,
     'criterion_replays': 0, 'optimizer_steps': 0, 'scheduler_steps': 0,
     'new_training': False, 'new_VAL': False, 'production_modified': False,
     'records': [], 'scope': 'Conditional message diagnostic, not efficacy or admission'}
hooks = []
original_gather = None
try:
    r['before'] = acquire(args.lease)
    torch, gorilla, cfg, model, meta = setup()
    assert meta['epoch'] == MANIFEST['expected_epoch'] == 16
    model.train()
    flags = [p.requires_grad for p in model.parameters()]
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader, Subset
    hierarchy = importlib.import_module('framework.model.Quard_model.' + NAME + '.hier_postprocess')
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('task-suffix'))
    cohort = MANIFEST['cohort'][:2]
    for scene in cohort:
        group = dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id'] == scene['scene_id']
        assert [{'object_id': str(x['object_id']), 'ann_id': str(x['ann_id'])}
                for x in group] == scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch = next(iter(DataLoader(Subset(dataset, [s['group_index'] for s in cohort]),
                                batch_size=2, shuffle=False, num_workers=0,
                                collate_fn=dataset.collate_fn)))
    r['input_sha256'] = fingerprint(torch, batch)
    cluster = model.dec.cluster_att
    active = [layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active) == 1 and active[0] is model.dec.encoder_layers[-1]
    last = model.dec.decoder_layers[-1]
    assert cluster.dropout.p == 0
    for module in (active[0].ila, last):
        assert all(m.p == 0 for m in module.modules() if isinstance(m, torch.nn.Dropout))
    held = {}

    def clone(value):
        if torch.is_tensor(value):
            return value.detach().clone().requires_grad_(value.requires_grad)
        if isinstance(value, tuple):
            return tuple(clone(v) for v in value)
        if isinstance(value, list):
            return [clone(v) for v in value]
        if isinstance(value, dict):
            return {k: clone(v) for k, v in value.items()}
        return value

    def error(left, right):
        return float((left.detach() - right.detach()).abs().max().cpu())

    original_gather = cluster._cluster_to_points

    def capture_gather(*values, **keywords):
        assert not keywords
        result = original_gather(*values)
        held['gather'] = clone(values)
        return result

    def capture_cluster(module, values, output):
        held['core_args'] = clone(values)
        held['message'] = clone(output['point'])
        held['native_message'] = output['point']
        output['point'].retain_grad()

    def capture_ila(module, values):
        held['ila'] = clone(values)

    def capture_decoder(module, values, output):
        held['decoder_args'] = clone(values)
        held['decoder_output'] = clone(output)

    def capture_criterion(module, values):
        held['criterion'] = clone(values)

    cluster._cluster_to_points = capture_gather
    hooks = [cluster.register_forward_hook(capture_cluster),
             active[0].ila.register_forward_pre_hook(capture_ila),
             last.register_forward_hook(capture_decoder),
             model.criterion.register_forward_pre_hook(capture_criterion)]
    model.zero_grad(set_to_none=True)
    gorilla.set_random_seed(1999)
    try:
        native_loss, native_components = model(copy.deepcopy(batch), mode='loss')
        r['native_forwards'] += 1
        assert bool(torch.isfinite(native_loss))
        r['native_loss'] = float(native_loss.detach().cpu())
        native_loss.backward()
        r['native_backwards'] += 1
    finally:
        cluster._cluster_to_points = original_gather
        for handle in hooks:
            handle.remove()
        hooks.clear()
    native_gradient = held['native_message'].grad.detach().clone()
    assert bool(torch.isfinite(native_gradient).all()) and bool((native_gradient != 0).any())
    assert all(bool(torch.isfinite(p.grad).all()) for p in model.parameters() if p.grad is not None)
    gradient_hash = fingerprint(torch, [p.grad for p in model.parameters()])
    x, tokens, ids, mask = held['gather']
    r['prefix_sha256'] = fingerprint(torch, held['gather'])
    r['native_gradient_sha256'] = fingerprint(torch, native_gradient)

    def source_message(points, values):
        value = cluster.message_norm(original_gather(points, values, ids, mask))
        r['source_interface_forwards'] += 1
        return value.masked_fill(mask.unsqueeze(-1), 0)

    def suffix(message):
        iargs = list(clone(held['ila']))
        iargs[1] = held['core_args'][0] + torch.sigmoid(active[0].cluster_att_gate) * message
        features = active[0].ila(*iargs)[0]
        dargs = list(clone(held['decoder_args']))
        dargs[2] = features
        result = last(*dargs)
        r['suffix_replays'] += 1
        cargs = list(clone(held['criterion']))
        for field, output in zip(('scores', 'masks', 'indis', 'proj_queries', 'proj_tokens'), result[1:]):
            cargs[0][field] = output
        loss, components = model.criterion(*cargs)
        r['criterion_replays'] += 1
        assert bool(torch.isfinite(loss))
        values = {k: float(v.detach().cpu()) for k, v in components.items() if torch.is_tensor(v) and v.numel() == 1}
        detached = clone(result)
        return detached, float(loss.detach().cpu()), values

    base = source_message(x, tokens)
    controls = {'message_reconstruction': error(base, held['message'])}
    normal, base_loss, base_components = suffix(base)
    for i, (actual, expected) in enumerate(zip(normal, held['decoder_output'])):
        if actual is not None:
            controls['native_suffix_' + str(i)] = error(actual, expected)
    controls['native_criterion_loss'] = abs(base_loss - r['native_loss'])
    identity, identity_loss, _ = suffix(base + torch.zeros_like(base))
    controls['identity_criterion_loss'] = abs(identity_loss - base_loss)
    for i, (actual, expected) in enumerate(zip(identity, normal)):
        if actual is not None:
            controls['identity_suffix_' + str(i)] = error(actual, expected)
    r.update(controls=controls, baseline_loss=base_loss, baseline_components=base_components)
    assert max(controls.values()) <= 1e-6, controls
    r['controls_passed'] = True
    weight = cluster.level_gate.weight.detach().cpu().double()[:, x.shape[-1]:]
    centered = weight - weight.mean(0, keepdim=True)
    _, singular, vh = torch.linalg.svd(centered, full_matrices=False)
    rank = int((singular > torch.finfo(torch.float64).eps * max(centered.shape) * singular.max()).sum())
    assert rank <= 2
    basis = vh[:rank]
    for b in range(x.shape[0]):
        valid = int((~mask[b]).sum().cpu())
        coarse = ids[0][b].long()
        for level in (1, 2):
            coarse = ids[level][b].long()[coarse]
        for index in (0, valid // 2, valid - 1):
            record = {'expression': b, 'point': index, 'conditions': {}}
            r['records'].append(record)
            remote_ids = (coarse != coarse[index]).nonzero().flatten()
            if not len(remote_ids):
                record['status'] = 'UNKNOWN no remote coarse cluster'
                continue
            remote = int(remote_ids[0].cpu())
            d = x[b, remote].detach().cpu().double() - x[b, index].detach().cpu().double()
            row = basis.T @ (basis @ d)
            null = d - row
            norm = x[b, remote].detach().cpu().double().norm()
            if min(float(row.norm()), float(null.norm()), float(norm)) <= 1e-12:
                record['status'] = 'UNKNOWN degenerate direction'
                continue
            row, null = row / row.norm() * norm, null / null.norm() * norm
            residual = float((centered @ null).abs().max())
            record.update(remote_point=remote, direction_norm=float(norm), ideal_null_residual=residual)
            assert residual <= 1e-12
            for label, direction in zip(('remote_null', 'remote_row', 'own_coarse_null'), (null, row, null)):
                px, values = clone(x), clone(tokens)
                if label == 'own_coarse_null':
                    changed = values[-1].clone()
                    changed[b, coarse[index]] = changed[b, coarse[index]] + direction.to(changed)
                    values[-1] = changed
                else:
                    px = px.clone()
                    px[b, remote] = px[b, remote] + direction.to(px)
                message = source_message(px, values)
                isolated = base.clone()
                isolated[b, index] = message[b, index]
                delta = (isolated[b, index] - base[b, index]).detach()
                output, loss, components = suffix(isolated)
                condition = {'message_max_absolute_change': float(delta.abs().max().cpu()),
                             'message_l2_change': float(delta.norm().cpu()),
                             'mask_logits_max_change': error(output[2][b], normal[2][b]),
                             'score_max_change': error(output[1][b], normal[1][b]),
                             'indicator_max_change': error(output[3][b], normal[3][b]),
                             'native_loss': loss, 'native_loss_delta': loss - base_loss,
                             'components': components,
                             'native_cotangent_linear_surrogate': float((native_gradient[b, index].double() * delta.double()).sum().cpu())}
                if label == 'remote_null':
                    condition['original_strict_1e_minus6_message_gate'] = bool(delta.abs().max() <= 1e-6)
                record['conditions'][label] = condition
                del output, isolated, message, px, values
    assert [p.requires_grad for p in model.parameters()] == flags
    assert fingerprint(torch, [p.grad for p in model.parameters()]) == gradient_hash
    assert fingerprint(torch, batch) == r['input_sha256']
    r.update(execution_completed=True, scene_ids=[s['scene_id'] for s in cohort],
             expression_count=int(x.shape[0]), fixed_readouts=len(r['records']),
             parameter_flags_preserved=True, parameter_gradients_unchanged=True,
             original_null_failures=sum(v['conditions'].get('remote_null', {}).get(
                 'original_strict_1e_minus6_message_gate') is False for v in r['records']),
             population_uncertainty='UNKNOWN;only2fixedTRAINscenes,not generalization',
             scientific_admission=False)
    hierarchy.reset_orth_accum()
    verify()
    r['after'] = observe()
except BaseException as error_value:
    r.update(error_type=type(error_value).__name__, error=str(error_value))
    raise
finally:
    if original_gather is not None:
        cluster._cluster_to_points = original_gather
    for handle in hooks:
        handle.remove()
    try:
        save('native_task_suffix_result.json', r)
    finally:
        release()
