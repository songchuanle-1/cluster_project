"""Actual native criterion responses; one readout message changed at a time."""
import argparse
import copy
import importlib
import logging
import numpy as np
from coarse_cross_attention_r1 import coarse_readback
import torch.nn.functional as functional
from native_runtime import acquire, release, verify, observe, setup, save, fingerprint, MANIFEST, NAME
parser = argparse.ArgumentParser()
parser.add_argument('--lease', required=True)
args = parser.parse_args()
r = {'execution_completed': False, 'controls_passed': False, 'native_forwards': 0, 'native_backwards': 0, 'source_interface_forwards': 0, 'suffix_replays': 0, 'criterion_replays': 0, 'optimizer_steps': 0, 'scheduler_steps': 0, 'new_training': False, 'new_VAL': False, 'production_modified': False, 'records': [], 'scope': 'Conditional message diagnostic, not efficacy or admission'}
hooks = []
original_gather = None
try:
    r['before'] = acquire(args.lease)
    torch, gorilla, cfg, model, meta = setup()
    assert meta['epoch'] == MANIFEST['expected_epoch'] == 16
    model.train()
    flags = [p.requires_grad for p in model.parameters()]
    match_trace = []
    positive_trace = []
    original_loss_masks = model.criterion.loss_masks

    def observed_loss_masks(pred_masks, pred_scores, targets, indices, num_boxes):
        match_trace.append(fingerprint(torch, ([target.get('masks') for target in targets], indices, num_boxes)))
        summary = []
        for b, (qi, ti) in enumerate(indices):
            if len(qi) == 0 or targets[b].get('masks') is None:
                summary.append(None)
                continue
            predicted = pred_masks[b][qi].detach() > 0
            target = targets[b]['masks'][ti].detach().bool()
            intersection = (predicted & target).sum(-1).float()
            union = (predicted | target).sum(-1).clamp_min(1).float()
            summary.append({'positive_queries': len(qi), 'mean_mask_iou': float((intersection / union).mean().cpu())})
        positive_trace.append(summary)
        if 'error_support' not in held:
            held['error_support'] = []
            for b, (qi, ti) in enumerate(indices):
                if len(qi) == 0 or targets[b].get('masks') is None:
                    held['error_support'].append(None)
                else:
                    predicted = pred_masks[b][qi].detach() > 0
                    target = targets[b]['masks'][ti].detach().bool()
                    valid = ~held['gather'][3][b]
                    held['error_support'].append(((predicted != target).any(0) & valid).detach().clone())
        return original_loss_masks(pred_masks, pred_scores, targets, indices, num_boxes)
    model.criterion.loss_masks = observed_loss_masks
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader, Subset
    hierarchy = importlib.import_module('framework.model.Quard_model.' + NAME + '.hier_postprocess')
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('task-suffix'))
    cohort = MANIFEST['cohort'][:2]
    for scene in cohort:
        group = dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id'] == scene['scene_id']
        assert [{'object_id': str(x['object_id']), 'ann_id': str(x['ann_id'])} for x in group] == scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch = next(iter(DataLoader(Subset(dataset, [s['group_index'] for s in cohort]), batch_size=2, shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)))
    r['input_sha256'] = fingerprint(torch, batch)
    cluster = model.dec.cluster_att
    active = [layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active) == 1 and active[0] is model.dec.encoder_layers[-1]
    last = model.dec.decoder_layers[-1]
    assert cluster.dropout.p == 0
    for module in (active[0].ila, last):
        assert all((m.p == 0 for m in module.modules() if isinstance(m, torch.nn.Dropout)))
    held = {}

    def clone(value):
        if torch.is_tensor(value):
            return value.detach().clone().requires_grad_(value.requires_grad)
        if isinstance(value, tuple):
            return tuple((clone(v) for v in value))
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
    hooks = [cluster.register_forward_hook(capture_cluster), active[0].ila.register_forward_pre_hook(capture_ila), last.register_forward_hook(capture_decoder), model.criterion.register_forward_pre_hook(capture_criterion)]
    model.zero_grad(set_to_none=True)
    gorilla.set_random_seed(1999)
    try:
        native_loss, native_components = model(copy.deepcopy(batch), mode='loss')
        r['native_forwards'] += 1
        r['native_matching'] = list(match_trace)
        r['native_positive_query_iou'] = list(positive_trace)
        match_trace.clear()
        positive_trace.clear()
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
    assert all((bool(torch.isfinite(p.grad).all()) for p in model.parameters() if p.grad is not None))
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
        held['last_loss'] = loss
        held['last_matching'] = list(match_trace)
        held['last_positive_iou'] = list(positive_trace)
        match_trace.clear()
        positive_trace.clear()
        r['criterion_replays'] += 1
        assert bool(torch.isfinite(loss))
        values = {k: float(v.detach().cpu()) for k, v in components.items() if torch.is_tensor(v) and v.numel() == 1}
        detached = clone(result)
        return (detached, float(loss.detach().cpu()), values)
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
    assert max(controls.values()) <= 1e-06, controls
    r['controls_passed'] = True
    r['baseline_matching_identical'] = held['last_matching'] == r['native_matching']
    assert r['baseline_matching_identical']
    r['coarse_conditions'] = []
    coarse = tokens[-1]
    raw_coarse = held['core_args'][3][-1]
    assert raw_coarse.shape == coarse.shape
    assert coarse.requires_grad
    composed = []
    own = torch.zeros_like(x)
    for b in range(x.shape[0]):
        index = ids[0][b].long()
        for level in range(1, len(ids)):
            index = ids[level][b].long()[index]
        composed.append(index)
        own[b, :len(index)] = coarse[b, index]
    assert isinstance(cluster.point_out_proj, torch.nn.Linear)
    level_weights = cluster.level_gate(torch.cat([x, x.mean(1, keepdim=True).expand_as(x)], -1)).softmax(-1)

    def make_message(mode):
        if mode == 'own_coarse_identity':
            replacement = own
            attention = None
        elif mode == 'uniform_coarse_mean':
            replacement = coarse.mean(1, keepdim=True).expand_as(x).masked_fill(mask.unsqueeze(-1), 0)
            attention = None
        else:
            values = coarse.roll(1, 1) if mode == 'cyclic_key_value_mismatch' else None
            replacement, attention = coarse_readback(x, coarse, mask, heads=cluster.nhead, values=values, key_features=None if mode == 'coarse_attention_refined_key' else raw_coarse)
        delta = (replacement - own) * level_weights[:, :, -1:]
        raw = original_gather(x, tokens, ids, mask)
        r['source_interface_forwards'] += 1
        raw = raw + functional.linear(delta, cluster.point_out_proj.weight, None)
        msg = cluster.message_norm(raw).masked_fill(mask.unsqueeze(-1), 0)
        return (msg, attention)
    for mode in ('own_coarse_identity', 'coarse_attention_refined_key', 'coarse_attention', 'uniform_coarse_mean', 'cyclic_key_value_mismatch'):
        message, attention = make_message(mode)
        output, loss, components = suffix(message)
        condition = {'condition': mode, 'message_max_change': error(message, base), 'mask_max_change': error(output[2], normal[2]), 'score_max_change': error(output[1], normal[1]), 'native_loss': loss, 'native_loss_delta': loss - base_loss, 'components': components, 'matching_identical': held['last_matching'] == r['native_matching'], 'positive_query_iou': held['last_positive_iou']}
        condition['error_group_readouts'] = []
        delta = (message - base).detach()
        for b, error_group in enumerate(held['error_support']):
            if error_group is None:
                condition['error_group_readouts'].append(None)
                continue
            valid = ~mask[b]
            groups = {'original_error': error_group, 'original_correct': valid & ~error_group}
            entry = {}
            for group_name, support in groups.items():
                count = int(support.sum().cpu())
                entry[group_name] = {'points': count, 'native_gradient_dot_message_delta': float((native_gradient[b, support].double() * delta[b, support].double()).sum().cpu()), 'message_delta_norm': float(delta[b, support].norm().cpu()), 'mask_logit_max_change': float((output[2][b, :, support] - normal[2][b, :, support]).abs().max().cpu()) if count else None}
            condition['error_group_readouts'].append(entry)
        assert condition['matching_identical'], 'Native supervision matching changed'
        if mode == 'own_coarse_identity':
            condition['identity_passed'] = max(condition['message_max_change'], condition['mask_max_change'], condition['score_max_change'], abs(condition['native_loss_delta'])) <= 1e-06
            assert condition['identity_passed'], condition
        else:
            message_gradient, coarse_gradient = torch.autograd.grad(held['last_loss'], (message, coarse), retain_graph=True)
            condition['message_gradient_finite'] = bool(torch.isfinite(message_gradient).all())
            condition['coarse_gradient_finite'] = bool(torch.isfinite(coarse_gradient).all())
            condition['message_gradient_norm'] = float(message_gradient.norm().cpu())
            condition['coarse_gradient_norm'] = float(coarse_gradient.norm().cpu())
            assert condition['message_gradient_finite'] and condition['coarse_gradient_finite']
            assert condition['message_gradient_norm'] > 0 and condition['coarse_gradient_norm'] > 0
            r['suffix_gradient_probes'] = r.get('suffix_gradient_probes', 0) + 1
        if attention is not None:
            entropy = -(attention.clamp_min(1e-30).log() * attention).sum(-1)
            own_probability = []
            for b, index in enumerate(composed):
                rows = attention[b, :, :len(index)]
                own_probability.append(float(rows.gather(-1, index[None, :, None].expand(rows.shape[0], -1, 1)).mean().cpu()))
            condition['attention_entropy_mean'] = float(entropy.masked_select((~mask)[:, None, :].expand_as(entropy)).mean().cpu())
            condition['own_coarse_probability_per_expression'] = own_probability
            condition['attention_shape'] = list(attention.shape)
        r['coarse_conditions'].append(condition)
    r['new_candidate_full_native_backward_passed'] = False
    r['diagnosis_gate_passed'] = False
    r['task_deficit_status'] = 'Pending task-level interpretation;path activity alone is not proof of a bottleneck'
    assert [p.requires_grad for p in model.parameters()] == flags
    assert fingerprint(torch, [p.grad for p in model.parameters()]) == gradient_hash
    assert fingerprint(torch, batch) == r['input_sha256']
    r.update(execution_completed=True, scene_ids=[s['scene_id'] for s in cohort], expression_count=int(x.shape[0]), fixed_readouts=len(r['records']), parameter_flags_preserved=True, parameter_gradients_unchanged=True, original_null_failures=sum((v['conditions'].get('remote_null', {}).get('original_strict_1e_minus6_message_gate') is False for v in r['records'])), population_uncertainty='UNKNOWN;only2fixedTRAINscenes,not generalization', scientific_admission=False)
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
        save('native_error_readout_result.json', r)
    finally:
        release()
