"""Native same-scene expression-message transplant with fixed original query."""
import argparse
import copy
import logging
from native_runtime import acquire, release, setup, save, fingerprint, MANIFEST
from expression_metrics import select_donors, summarize
parser = argparse.ArgumentParser()
parser.add_argument('--lease', required=True)
parser.add_argument('--pair', type=int, choices=range(4), required=True)
args = parser.parse_args()
result = {'execution_completed': False, 'controls_passed': False, 'scientific_diagnosis_passed': False, 'native_task_mask_replays': 0, 'new_training': 0, 'native_backwards': 0, 'optimizer_steps': 0, 'records': [], 'scope': 'Conditionalexpressioninformationdiagnosis,not a newmodel or efficacy/admission'}
hooks = []
original_gather = None
try:
    result['before'] = acquire(args.lease)
    torch, gorilla, cfg, model, meta = setup()
    assert meta['epoch'] == 16
    model.eval()
    from torch.utils.data import DataLoader, Subset
    from framework.dataset import build_dataset
    cohort = MANIFEST['cohort'][2 * args.pair:2 * args.pair + 2]
    assert len(cohort) == 2
    expressions, donors = select_donors(cohort)
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('native-expression'))
    for scene in cohort:
        group = dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id'] == scene['scene_id']
        assert [{'object_id': str(x['object_id']), 'ann_id': str(x['ann_id'])} for x in group] == scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch = next(iter(DataLoader(Subset(dataset, [s['group_index'] for s in cohort]), batch_size=2, shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)))
    cluster = model.dec.cluster_att
    active = [layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active) == 1 and active[0] is model.dec.encoder_layers[-1]
    assert active[0].cluster_message_type == 'context' and active[0].cluster_gate_type == 'sigmoid'
    last = model.dec.decoder_layers[-1]

    def clone(value):
        if torch.is_tensor(value):
            return value.detach().clone()
        if isinstance(value, tuple):
            return tuple((clone(x) for x in value))
        if isinstance(value, list):
            return [clone(x) for x in value]
        if isinstance(value, dict):
            return {k: clone(v) for k, v in value.items()}
        return value

    def error(left, right):
        return float((left - right).abs().max().cpu())
    held = {}
    original_gather = cluster._cluster_to_points

    def capture_gather(*values):
        held['gather'] = clone(values)
        return original_gather(*values)

    def capture_cluster(module, values, output):
        held['core'] = clone(values)
        held['message'] = clone(output['point'])

    def capture_ila(module, values):
        held['ila'] = clone(values)

    def capture_last(module, values, output):
        held['last_args'] = clone(values)
        held['last'] = clone(output)

    def capture_criterion(module, values):
        held['criterion'] = clone(values)
    cluster._cluster_to_points = capture_gather
    hooks = [cluster.register_forward_hook(capture_cluster), active[0].ila.register_forward_pre_hook(capture_ila), last.register_forward_hook(capture_last), model.criterion.register_forward_pre_hook(capture_criterion)]
    with torch.no_grad():
        native_loss, _ = model(copy.deepcopy(batch), mode='loss')
    cluster._cluster_to_points = original_gather
    for handle in hooks:
        handle.remove()
    hooks = []
    x, tokens, ids, mask = held['gather']
    assert len(x) == len(expressions) == 8
    output = held['criterion'][0]
    assert torch.equal(output['masks'], held['last'][2])
    query = held['last'][0]
    query_hash = fingerprint(torch, query)
    message = held['message']
    message_hash = fingerprint(torch, message)
    matches = []
    original_loss_masks = model.criterion.loss_masks

    def collect_masks(pred_masks, pred_scores, targets, indices, num_boxes):
        if all((torch.equal(pred_masks[b], output['masks'][b, :, ~mask[b]]) for b in range(len(pred_masks)))):
            matches.append(clone((targets, indices)))
        return original_loss_masks(pred_masks, pred_scores, targets, indices, num_boxes)
    model.criterion.loss_masks = collect_masks
    try:
        with torch.no_grad():
            model.criterion(*held['criterion'])
    finally:
        model.criterion.loss_masks = original_loss_masks
    assert len(matches) == 1
    targets, indices = matches[0]

    def suffix(value):
        values = list(clone(held['ila']))
        values[1] = held['core'][0] + torch.sigmoid(active[0].cluster_att_gate) * value
        features = active[0].ila(*values)[0]
        scores, logits = last.prediction_head(query, features, mask)
        assert fingerprint(torch, query) == query_hash
        result['native_task_mask_replays'] += 1
        return (scores, logits, features)
    with torch.no_grad():
        scores, logits, features = suffix(message)
        identity = suffix(message.clone())
        controls = {'own_native_features': error(features, held['last_args'][2]), 'own_native_mask': error(logits, held['last'][2]), 'own_native_score': error(scores, held['last'][1]), 'own_identity_mask': error(identity[1], logits)}
        transplanted = message.clone()
        for b, donor in donors.items():
            if donor is None:
                continue
            assert expressions[b]['scene_id'] == expressions[donor]['scene_id'] and expressions[b]['object_id'] != expressions[donor]['object_id']
            assert torch.equal(mask[b], mask[donor])
            assert torch.equal(held['last_args'][5][b], held['last_args'][5][donor]), 'Physicalsuperpointcoordinates/orderdonotmatch'
            assert all((torch.equal(ids[s][b], ids[s][donor]) for s in range(3)))
            transplanted[b] = message[donor]
        restored = transplanted.clone()
        for b in donors:
            restored[b] = message[b]
        assert fingerprint(torch, restored) == message_hash
        restore_result = suffix(restored)
        controls['transplant_then_restore_mask'] = error(restore_result[1], logits)
        result['controls'] = controls
        assert max(controls.values()) <= 1e-06, controls
        result['controls_passed'] = True
        donor_logits = suffix(transplanted)[1]
        for b, (qi, ti) in enumerate(indices):
            donor = donors[b]
            n = int((~mask[b]).sum())
            target_object = int(expressions[b]['object_id'])
            assert target_object in [int(v) for v in held['criterion'][3][b]]
            original_instance_labels = held['criterion'][4][b][:n]
            original_main_target = original_instance_labels == target_object
            recorded = 0
            for q, t in zip(qi.tolist(), ti.tolist()):
                target = targets[b]['masks'][t]
                assert len(target) == n and bool(((target == 0) | (target == 1)).all())
                if not torch.equal(target.bool(), original_main_target):
                    continue
                own_error = float((logits[b, q, :n].sigmoid() - target.to(dtype=logits.dtype)).abs().mean().cpu())
                donor_error = float((donor_logits[b, q, :n].sigmoid() - target.to(dtype=logits.dtype)).abs().mean().cpu()) if donor is not None else None
                result['records'].append({'scene_id': expressions[b]['scene_id'], 'expression_index': b, 'native_query': q, 'native_target': t, 'object_id': expressions[b]['object_id'], 'donor': donor, 'valid_receivers': n, 'positive_receivers': int(original_main_target.sum()), 'own_probability_error': own_error, 'donor_probability_error': donor_error, 'donor_minus_own_probability_error': donor_error - own_error if donor_error is not None else None})
                recorded += 1
            if not recorded:
                result['records'].append({'scene_id': expressions[b]['scene_id'], 'expression_index': b, 'native_query': None, 'donor_minus_own_probability_error': None, 'reason': 'Nooriginalnativequerymatchedprimarytarget;notreselected'})
        assert fingerprint(torch, query) == query_hash and fingerprint(torch, message) == message_hash
    result.update(execution_completed=True, scene_ids=[s['scene_id'] for s in cohort], expression_count=len(x), fixed_query_sha256=query_hash, original_message_sha256=message_hash, matching_sha256=fingerprint(torch, matches), input_sha256=fingerprint(torch, batch), summary=summarize(result['records']), native_loss=float(native_loss.cpu()), population_uncertainty='UNKNOWN;fixedTRAINcohort,correlatedqueries/expressions,sceneunit')
except BaseException as exc:
    result.update(error_type=type(exc).__name__, error=str(exc))
    raise
finally:
    if original_gather is not None:
        cluster._cluster_to_points = original_gather
    for handle in hooks:
        handle.remove()
    try:
        save('native_expression_task_pair_' + str(args.pair) + '.json', result)
    finally:
        release()
