"""Native same-prefix query/point attribution; no training or model revision."""
import argparse
import copy
import importlib
import itertools
import logging
import numpy as np
from native_runtime import acquire, release, verify, observe, setup, save, fingerprint, MANIFEST, NAME
from neighbor_content import padded_intervention

parser = argparse.ArgumentParser()
parser.add_argument('--lease', required=True)
args = parser.parse_args()
result = {'passed': False, 'native_forwards': 0, 'native_backwards': 0,
          'optimizer_steps': 0, 'suffix_replays': 0, 'scenes': [],
          'scientific_status': 'terminal_checkpoint_TRAIN_mechanistic_diagnostic_not_VAL_efficacy',
          'new_model_revision': False, 'norm_helper_revision': 2}
try:
    result['before'] = acquire(args.lease)
    torch, gorilla, cfg, model, meta = setup()
    assert meta['epoch'] == 13
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader, Subset
    operator = importlib.import_module('framework.model.Quard_model.' + NAME + '.fine_exchange')
    hierarchy = importlib.import_module('framework.model.Quard_model.' + NAME + '.hier_postprocess')
    get_iou = importlib.import_module('framework.model.Quard_model.' + NAME + '.loss').get_iou
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('fle-qf'))
    cohort = MANIFEST['cohort']
    for row in cohort:
        group = dataset.scene_inputs[row['group_index']]
        assert group[0]['scene_id'] == row['scene_id']
        assert [{'object_id': str(r['object_id']), 'ann_id': str(r['ann_id'])} for r in group] == row['expression_ids']
    gorilla.set_random_seed(1999)
    loader = DataLoader(Subset(dataset, [r['group_index'] for r in cohort]), batch_size=1,
                        shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)
    active = [layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active) == 1 and active[0] is model.dec.encoder_layers[-1]
    cluster = model.dec.cluster_att
    fine = cluster.fine_exchange
    last = model.dec.decoder_layers[-1]
    assert fine.k == 32 and fine.heads == 8

    def clone(value):
        if torch.is_tensor(value): return value.detach().clone()
        if isinstance(value, list): return [clone(v) for v in value]
        if isinstance(value, tuple): return tuple(clone(v) for v in value)
        if isinstance(value, dict): return {k: clone(v) for k, v in value.items()}
        return value

    def maximum(a, b): return float((a - b).abs().max().cpu())

    result['checkpoint_meta'] = {k: v for k, v in meta.items() if isinstance(v, (int, float, str, bool))}
    with torch.no_grad():
        for scene_number, (scene, batch) in enumerate(zip(cohort, loader)):
            observe()
            before = fingerprint(torch, batch)
            held = {}

            def core(module, arguments, keywords, value):
                held.update(core_args=clone(arguments), core_kwargs=clone(keywords), message=clone(value['point']))

            def ila(module, arguments): held['ila'] = clone(arguments)

            def decoder(module, arguments, value):
                held.update(decoder=clone(arguments), decoder_output=clone(value))

            hooks = [cluster.register_forward_hook(core, with_kwargs=True),
                     active[0].ila.register_forward_pre_hook(ila), last.register_forward_hook(decoder)]
            gorilla.set_random_seed(1999)
            try:
                loss, components = model(copy.deepcopy(batch), mode='loss')
                result['native_forwards'] += 1
                assert bool(torch.isfinite(loss))
                native_loss = float(loss.cpu())
            finally:
                for hook in hooks: hook.remove()
            assert fingerprint(torch, batch) == before
            arguments, keywords = held['core_args'], held['core_kwargs']
            normal = cluster(*arguments, **keywords)['point']
            normal2 = cluster(*arguments, **keywords)['point']
            errors = {'message_replay': maximum(normal, held['message']), 'repeat': maximum(normal, normal2)}
            original_fine = fine.forward
            receipts = []

            def controlled(identity):
                def replace(features, padding, positions, fine_ids):
                    expected = original_fine(features, padding, positions, fine_ids)
                    decomposed, altered, rows = padded_intervention(
                        features, padding, positions, fine_ids, operator.build_graph, identity=identity)
                    source_error = maximum(expected, decomposed)
                    receipt = {'identity': identity, 'source_error': source_error, 'rows': rows}
                    result.setdefault('control_attempts', []).append({'scene': scene['scene_id'], **receipt})
                    assert source_error <= 1e-6
                    assert max(r['norm_max_error'] for r in rows) <= 1e-6
                    assert max(r['true_norm_max_error'] for r in rows) <= 1e-6
                    receipts.append(receipt)
                    return altered
                try:
                    fine.forward = replace
                    return cluster(*arguments, **keywords)['point']
                finally:
                    fine.forward = original_fine

            identity_message, altered_message = controlled(True), controlled(False)
            errors['identity_message'] = maximum(normal, identity_message)
            original_head = last.prediction_head

            def suffix(message):
                ila_args = list(clone(held['ila']))
                ila_args[1] = arguments[0] + torch.sigmoid(active[0].cluster_att_gate) * message
                features = active[0].ila(*ila_args)[0]
                decoder_args = list(clone(held['decoder']))
                decoder_args[2] = features
                captured = []

                def head(query, mask_feats, batch_mask):
                    normalized = []
                    hook = last.out_norm.register_forward_hook(lambda module, args, value: normalized.append(clone(value)))
                    try:
                        scores, masks = original_head(query, mask_feats, batch_mask)
                    finally:
                        hook.remove()
                    assert len(normalized) == 1
                    captured.append({'query': normalized[0], 'features': clone(mask_feats), 'masks': clone(masks)})
                    return scores, masks

                try:
                    last.prediction_head = head
                    value = last(*decoder_args)
                    result['suffix_replays'] += 1
                finally:
                    last.prediction_head = original_head
                assert len(captured) == 1
                return value, captured[0]

            normal_out, base = suffix(normal)
            identity_out, null = suffix(identity_message)
            altered_out, changed = suffix(altered_message)
            for index in (2, 3):
                errors['native_suffix_' + str(index)] = maximum(normal_out[index], held['decoder_output'][index])
                errors['identity_suffix_' + str(index)] = maximum(normal_out[index], identity_out[index])
            for key in ('query', 'features', 'masks'):
                errors['identity_' + key] = maximum(base[key], null[key])
            masks = {'L00': torch.einsum('bnd,bmd->bnm', base['query'], base['features']),
                     'L01': torch.einsum('bnd,bmd->bnm', base['query'], changed['features']),
                     'L10': torch.einsum('bnd,bmd->bnm', changed['query'], base['features']),
                     'L11': torch.einsum('bnd,bmd->bnm', changed['query'], changed['features'])}
            errors['native_L00'] = maximum(masks['L00'], normal_out[2])
            errors['native_L11'] = maximum(masks['L11'], altered_out[2])
            assert max(errors.values()) <= 1e-6, errors
            d = {key: value.double() for key, value in masks.items()}
            point_effect = .5 * ((d['L01'] - d['L00']) + (d['L11'] - d['L10']))
            query_effect = .5 * ((d['L10'] - d['L00']) + (d['L11'] - d['L01']))
            additive_error = maximum(point_effect + query_effect, d['L11'] - d['L00'])
            assert additive_error <= 1e-12
            sp = batch['superpoints'].to(normal_out[2].device).long()
            rows = []
            for expression in range(len(batch['ann_ids'])):
                q = int(normal_out[3][expression].softmax(-1)[:, 1].argmax())
                other = int(altered_out[3][expression].softmax(-1)[:, 1].argmax())
                gt = batch['gt_pmasks'][expression].to(normal_out[2].device).float()
                metrics = {}
                for key, value in masks.items():
                    logits = value[expression, q][sp]
                    metrics[key] = {'piou': float(get_iou(logits, gt).cpu()),
                                    'bce': float(torch.nn.functional.binary_cross_entropy_with_logits(logits, gt).cpu())}
                p = point_effect[expression, q][sp]
                qeffect = query_effect[expression, q][sp]
                rows.append({'ann_id': int(batch['ann_ids'][expression]), 'normal_query': q, 'intervention_query': other,
                             'metrics': metrics, 'point_logit_rms': float(p.square().mean().sqrt().cpu()),
                             'query_logit_rms': float(qeffect.square().mean().sqrt().cpu()),
                             'final_mask_max_change': maximum(masks['L00'][expression], masks['L11'][expression])})
            row = {'scene': scene['scene_id'], 'group_index': scene['group_index'], 'input_sha256': before,
                   'native_loss': native_loss, 'controls': errors, 'additive_logit_error': additive_error,
                   'query_feature_max_change': maximum(base['query'], changed['query']),
                   'point_feature_max_change': maximum(base['features'], changed['features']),
                   'interventions': receipts, 'expressions': rows}
            save('qf_scene_' + str(scene_number).zfill(2) + '.json', row)
            result['scenes'].append(row)
            print('QF_SCENE ' + str(scene_number + 1) + '/32', flush=True)
            hierarchy.reset_orth_accum()
            del held, normal, normal2, identity_message, altered_message, normal_out, identity_out, altered_out
            del base, null, changed, masks, d, point_effect, query_effect, loss, components
            torch.cuda.empty_cache()
    verify()
    result['after'] = observe()
    assert len(result['scenes']) == 32
    metrics = ('piou', 'bce')
    keys = ('L00', 'L01', 'L10', 'L11')
    scene_means = {m: {key: np.array([np.mean([r['metrics'][key][m] for r in s['expressions']])
                                      for s in result['scenes']]) for key in keys} for m in metrics}
    indices = np.random.default_rng(1999).integers(0, 32, (10000, 32))
    result['task_readouts'] = {m: {key: float(v.mean()) for key, v in values.items()}
                               for m, values in scene_means.items()}
    result['paired_scene_contrasts'] = {}
    for m, values in scene_means.items():
        result['paired_scene_contrasts'][m] = {}
        for a, b in itertools.combinations(keys, 2):
            delta = values[a] - values[b]
            result['paired_scene_contrasts'][m][a + '_minus_' + b] = {
                'mean': float(delta.mean()), 'ci95': np.quantile(delta[indices].mean(1), [.025, .975]).tolist()}
    result.update(passed=True, new_training_started=False, efficacy='unknown', material_novelty='unestablished',
                  uncertainty='32 fixed TRAIN scenes only; exploratory contrasts, no generalization or fullVAL')
except BaseException as error:
    result.update(error_type=type(error).__name__, error=str(error))
    raise
finally:
    save('native_diagnostic_result.json', result)
    release()
