"""Frozen within-cell moment controls on a single native TRAIN prefix."""
import argparse
import copy
import importlib
import logging
from native_runtime import (acquire, release, verify, observe, setup, save, fingerprint, MANIFEST, NAME)

parser = argparse.ArgumentParser()
parser.add_argument('--lease', required=True)
args = parser.parse_args()
r = {'execution_completed': False, 'controls_passed': False, 'native_forwards': 0,
     'native_backwards': 0, 'bank_forwards': 0, 'cluster_forwards': 0,
     'suffix_replays': 0, 'criterion_replays': 0, 'optimizer_steps': 0,
     'scheduler_steps': 0, 'new_training': False, 'new_VAL': False,
     'production_modified': False, 'conditions': [], 'scientific_admission': False}
hooks = []
try:
    r['before'] = acquire(args.lease)
    torch, gorilla, cfg, model, meta = setup()
    assert meta['epoch'] == MANIFEST['expected_epoch'] == 16
    model.train()
    flags = [p.requires_grad for p in model.parameters()]
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader, Subset
    hierarchy = importlib.import_module('framework.model.Quard_model.' + NAME + '.hier_postprocess')
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('moment'))
    cohort = MANIFEST['cohort'][:2]
    for scene in cohort:
        group = dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id'] == scene['scene_id']
        assert [{'object_id': str(x['object_id']), 'ann_id': str(x['ann_id'])} for x in group] == scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch = next(iter(DataLoader(Subset(dataset, [s['group_index'] for s in cohort]), batch_size=2,
                                shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)))
    r['input_sha256'] = fingerprint(torch, batch)
    cluster = model.dec.cluster_att
    bank = model.dec.cluster_bank
    active = [layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active) == 1 and active[0] is model.dec.encoder_layers[-1]
    assert bank.cluster_pool_type == 'mean'
    last = model.dec.decoder_layers[-1]
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

    def capture_encoder(module, values, keywords):
        held['encoder_args'] = clone(values)
        held['offsets'] = clone(keywords['batch_offsets'])

    def capture_cluster(module, values, output):
        held['cluster_args'] = clone(values)
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

    hooks = [active[0].register_forward_pre_hook(capture_encoder, with_kwargs=True),
             cluster.register_forward_hook(capture_cluster),
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
        for handle in hooks:
            handle.remove()
        hooks.clear()
    native_gradient = held['native_message'].grad.detach().clone()
    assert bool(torch.isfinite(native_gradient).all()) and bool((native_gradient != 0).any())
    gradient_hash = fingerprint(torch, [p.grad for p in model.parameters()])
    x, query, mask, tokens, child_maps, ids = held['cluster_args']
    pos = held['encoder_args'][5]
    r['prefix_sha256'] = fingerprint(torch, (held['cluster_args'], pos))
    r['shapes'] = {'points': list(x.shape), 'positions': list(pos.shape), 'tokens': [list(t.shape) for t in tokens]}
    assert pos.shape[:2] == x.shape[:2]

    @torch.no_grad()
    def source(points):
        values = bank.build_cluster_feats(hierarchy.batch2flatten(points, mask), held['offsets'])
        r['bank_forwards'] += 1
        return values

    @torch.no_grad()
    def message(points, values):
        output = cluster(points, query, mask, values, child_maps, ids)['point']
        r['cluster_forwards'] += 1
        return output

    @torch.no_grad()
    def suffix(points, msg):
        iargs = list(clone(held['ila']))
        iargs[1] = points + torch.sigmoid(active[0].cluster_att_gate) * msg
        features = active[0].ila(*iargs)[0]
        dargs = list(clone(held['decoder_args']))
        dargs[2] = features
        output = last(*dargs)
        r['suffix_replays'] += 1
        cargs = list(clone(held['criterion']))
        for field, value in zip(('scores', 'masks', 'indis', 'proj_queries', 'proj_tokens'), output[1:]):
            cargs[0][field] = value
        loss, components = model.criterion(*cargs)
        r['criterion_replays'] += 1
        assert bool(torch.isfinite(loss))
        return clone(output), float(loss.cpu())

    @torch.no_grad()
    def moment(points):
        result = []
        for b in range(points.shape[0]):
            cid = ids[0][b].long()
            n = len(cid)
            center = hierarchy.aggregate_cluster(pos[b, :n], cid)
            dp = pos[b, :n] - center[cid]
            mf = hierarchy.aggregate_cluster(dp[:, :, None] * points[b, :n, None, :], cid)
            result.append(mf)
        return result

    base_tokens = source(x)
    base_message = message(x, base_tokens)
    base_output, base_loss = suffix(x, base_message)
    identity_output, identity_loss = suffix(x + torch.zeros_like(x), base_message + torch.zeros_like(base_message))
    controls = {'token_reconstruction': max(error(a, b) for a, b in zip(base_tokens, tokens)),
                'message_reconstruction': error(base_message, held['message']),
                'criterion_reconstruction': abs(base_loss - r['native_loss']),
                'identity_criterion': abs(identity_loss - base_loss)}
    for i, (actual, expected) in enumerate(zip(base_output, held['decoder_output'])):
        if actual is not None:
            controls['suffix_reconstruction_' + str(i)] = error(actual, expected)
            controls['identity_suffix_' + str(i)] = error(actual, identity_output[i])
    r.update(controls=controls, baseline_loss=base_loss)
    assert max(controls.values()) <= 1e-6, controls
    r['controls_passed'] = True
    baseline_moments = moment(x)
    for permutation in ('reverse', 'cycle_one'):
        perm = x.detach().clone()
        moved = []
        for b in range(x.shape[0]):
            cid = ids[0][b].long()
            count = 0
            for cell in range(int(cid.max().cpu()) + 1):
                members = (cid == cell).nonzero().flatten()
                if len(members) > 1:
                    sender = members.flip(0) if permutation == 'reverse' else members.roll(1)
                    perm[b, members] = x[b, sender]
                    count += int((sender != members).sum().cpu())
            moved.append(count)
        perm_tokens = source(perm)
        pm = moment(perm)
        fixed_msg = message(x, perm_tokens)
        whole_msg = message(perm, perm_tokens)
        record = {'permutation': permutation, 'moved_points_per_expression': moved,
                  'feature_position_moment_max_change': [error(a, b) for a, b in zip(pm, baseline_moments)],
                  'per_level_token_max_change': [error(a, b) for a, b in zip(perm_tokens, base_tokens)],
                  'hierarchy_only_message_max_change': error(fixed_msg, base_message),
                  'strict_1e_minus6_invariance': error(fixed_msg, base_message) <= 1e-6,
                  'task_conditions': {}}
        for label, points, msg in (('hierarchy_source_only', x, fixed_msg),
                                   ('point_path_only', perm, base_message),
                                   ('whole_feature_path', perm, whole_msg)):
            output, loss = suffix(points, msg)
            record['task_conditions'][label] = {'native_loss': loss, 'native_loss_delta': loss - base_loss,
                'mask_logit_max_change_per_expression': [error(output[2][b], base_output[2][b]) for b in range(x.shape[0])],
                'score_max_change': error(output[1], base_output[1])}
        r['conditions'].append(record)
    assert [p.requires_grad for p in model.parameters()] == flags
    assert fingerprint(torch, [p.grad for p in model.parameters()]) == gradient_hash
    assert fingerprint(torch, batch) == r['input_sha256']
    r.update(execution_completed=True, parameter_flags_preserved=True, parameter_gradients_unchanged=True,
             scene_ids=[s['scene_id'] for s in cohort], expression_count=int(x.shape[0]),
             population_uncertainty='UNKNOWN;2fixedTRAINscenes,not generalization',
             task_deficit_established=False)
    hierarchy.reset_orth_accum()
    verify()
    r['after'] = observe()
except BaseException as error:
    r.update(error_type=type(error).__name__, error=str(error))
    raise
finally:
    for handle in hooks:
        handle.remove()
    try:
        save('native_moment_result.json', r)
    finally:
        release()
