"""Frozen native hierarchy padding diagnostic; no model/mean replacement."""
import argparse
import copy
import importlib
import logging
import numpy as np
from native_runtime import acquire, release, verify, observe, setup, save, fingerprint, MANIFEST, NAME

p = argparse.ArgumentParser()
p.add_argument('--lease', required=True)
args = p.parse_args()
r = {'passed': False, 'native_forwards': 0, 'native_backwards': 0, 'optimizer_steps': 0,
     'suffix_replays': 0, 'scenes': [], 'model_changed': False,
     'scope': 'Exact gather-interface invariance on2TRAINscenes;not taskimprovement or nativebatch2harm'}
try:
    r['before'] = acquire(args.lease)
    torch, gorilla, cfg, model, meta = setup()
    assert meta['epoch'] == 13
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader, Subset
    hierarchy = importlib.import_module('framework.model.Quard_model.' + NAME + '.hier_postprocess')
    get_iou = importlib.import_module('framework.model.Quard_model.' + NAME + '.loss').get_iou
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('padding-invariance'))
    cohort = MANIFEST['cohort'][:2]
    for s in cohort:
        group = dataset.scene_inputs[s['group_index']]
        assert group[0]['scene_id'] == s['scene_id']
        assert [{'object_id': str(x['object_id']), 'ann_id': str(x['ann_id'])} for x in group] == s['expression_ids']
    gorilla.set_random_seed(1999)
    loader = DataLoader(Subset(dataset, [s['group_index'] for s in cohort]), batch_size=1,
                        shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)
    cluster = model.dec.cluster_att
    active = [x for x in model.dec.encoder_layers if x.use_cluster]
    assert len(active) == 1 and active[0] is model.dec.encoder_layers[-1]

    def clone(v):
        if torch.is_tensor(v): return v.detach().clone()
        if isinstance(v, tuple): return tuple(clone(x) for x in v)
        if isinstance(v, list): return [clone(x) for x in v]
        if isinstance(v, dict): return {k: clone(x) for k, x in v.items()}
        return v

    def error(a, b): return float((a - b).abs().max().cpu())

    with torch.no_grad():
        for scene_number, (scene, batch) in enumerate(zip(cohort, loader)):
            observe()
            held = {}
            before = fingerprint(torch, batch)
            original_gather = cluster._cluster_to_points

            def gather(*arguments, **keywords):
                value = original_gather(*arguments, **keywords)
                held.update(gather_args=clone(arguments), gather_kwargs=clone(keywords), gather_output=clone(value))
                return value

            def core(module, arguments, value):
                held.update(core_args=clone(arguments), message=clone(value['point']))

            def ila(module, arguments): held['ila'] = clone(arguments)

            def dec(module, arguments, value): held.update(decoder=clone(arguments), decoder_output=clone(value))

            hooks = [cluster.register_forward_hook(core), active[0].ila.register_forward_pre_hook(ila),
                     model.dec.decoder_layers[-1].register_forward_hook(dec)]
            gorilla.set_random_seed(1999)
            try:
                cluster._cluster_to_points = gather
                loss, components = model(copy.deepcopy(batch), mode='loss')
                r['native_forwards'] += 1
                assert bool(torch.isfinite(loss))
            finally:
                cluster._cluster_to_points = original_gather
                for hook in hooks: hook.remove()
            assert fingerprint(torch, batch) == before
            a, kw = held['gather_args'], held['gather_kwargs']
            assert len(a) == 4 and 'fine_message' in kw
            features, tokens, ids, mask = a
            B, N, C = features.shape

            def replay(f, t, m, fine):
                gates = []
                hook = cluster.level_gate.register_forward_hook(lambda module, args, output: gates.append(clone(output)))
                try: value = original_gather(f, t, ids, m, fine_message=fine)
                finally: hook.remove()
                assert len(gates) == 1
                return value, gates[0]

            base, base_gate = replay(features, tokens, mask, kw['fine_message'])
            base_message = cluster.message_norm(base).masked_fill(mask.unsqueeze(-1), 0)
            controls = {'gather_replay': error(base, held['gather_output']),
                        'message_reconstruction': error(base_message, held['message'])}

            def suffix(message):
                ila_args = list(clone(held['ila']))
                ila_args[1] = held['core_args'][0] + torch.sigmoid(active[0].cluster_att_gate) * message
                output_features = active[0].ila(*ila_args)[0]
                decoder_args = list(clone(held['decoder']))
                decoder_args[2] = output_features
                r['suffix_replays'] += 1
                return model.dec.decoder_layers[-1](*decoder_args)

            normal = suffix(base_message)
            for i in (2, 3): controls['native_suffix_' + str(i)] = error(normal[i], held['decoder_output'][i])
            zero_tokens = [torch.zeros_like(x) for x in tokens]
            zero_base, _ = replay(features, zero_tokens, mask, torch.zeros_like(kw['fine_message']))
            rows = []
            for label, extra, sentinel in [('pad7zero', 7, 0.), ('padNzero', N, 0.), ('padNone', N, 1.)]:
                f = torch.cat([features, features.new_full((B, extra, C), sentinel)], dim=1)
                m = torch.cat([mask, torch.ones((B, extra), device=mask.device, dtype=torch.bool)], dim=1)
                fine = torch.cat([kw['fine_message'], features.new_zeros((B, extra, C))], dim=1)
                value, gate = replay(f, tokens, m, fine)
                assert bool((value[:, N:] == 0).all())
                changed_message = cluster.message_norm(value[:, :N]).masked_fill(mask.unsqueeze(-1), 0)
                changed = suffix(changed_message)
                zero_changed, _ = replay(f, zero_tokens, m, torch.zeros_like(fine))
                null_error = error(zero_base, zero_changed[:, :N])
                controls['zero_scale_' + label] = null_error
                sp = batch['superpoints'].to(normal[2].device).long()
                expressions = []
                for e in range(len(batch['ann_ids'])):
                    q = int(normal[3][e].softmax(-1)[:, 1].argmax())
                    gt = batch['gt_pmasks'][e].to(normal[2].device).float()
                    expressions.append({'ann_id': int(batch['ann_ids'][e]), 'original_query': q,
                        'normal_piou': float(get_iou(normal[2][e, q][sp], gt).cpu()),
                        'padding_piou': float(get_iou(changed[2][e, q][sp], gt).cpu())})
                rows.append({'case': label, 'extra_masked_positions': extra, 'masked_feature_value': sentinel,
                    'valid_gather_max_change': error(base, value[:, :N]),
                    'valid_gate_logits_max_change': error(base_gate, gate[:, :N]),
                    'valid_message_max_change': error(base_message, changed_message),
                    'mask_logits_max_change': error(normal[2], changed[2]), 'expressions': expressions})
            assert max(controls.values()) <= 1e-6, controls
            row = {'scene': scene['scene_id'], 'group_index': scene['group_index'], 'input_sha256': before,
                   'original_superpoints': N, 'native_loss': float(loss.cpu()), 'controls': controls, 'cases': rows}
            save('padding_scene_' + str(scene_number) + '.json', row)
            r['scenes'].append(row)
            hierarchy.reset_orth_accum()
            del held, loss, components, normal
            torch.cuda.empty_cache()
    verify()
    r['after'] = observe()
    assert len(r['scenes']) == 2
    r.update(passed=True, padding_invariance_pass=all(c['valid_gather_max_change'] <= 1e-6 for s in r['scenes'] for c in s['cases']),
             model_or_baseline_corrected=False, task_improvement='UNKNOWN', native_training_batch2_incidence='UNKNOWN')
except BaseException as e:
    r.update(error_type=type(e).__name__, error=str(e))
    raise
finally:
    save('native_padding_result.json', r)
    release()
