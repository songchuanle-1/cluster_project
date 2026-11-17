"""Natural batch2 padding incidence, with unchanged source gather calls."""
import argparse
import copy
import importlib
import logging
from native_runtime import acquire, release, verify, observe, setup, save, fingerprint, MANIFEST, NAME

p = argparse.ArgumentParser()
p.add_argument('--lease', required=True)
args = p.parse_args()
r = {'passed': False, 'native_forwards': 0, 'native_backwards': 0, 'optimizer_steps': 0,
     'suffix_replays': 0, 'production_modified': False, 'scope': 'One naturalTRAINbatch2,padding interface diagnosis only'}
try:
    r['before'] = acquire(args.lease)
    torch, gorilla, cfg, model, meta = setup()
    assert meta['epoch'] == 13 and cfg.dataloader.train.batch_size == 2
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader, Subset
    hierarchy = importlib.import_module('framework.model.Quard_model.' + NAME + '.hier_postprocess')
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('native-batch2'))
    cohort = MANIFEST['cohort'][:2]
    for s in cohort:
        group = dataset.scene_inputs[s['group_index']]
        assert group[0]['scene_id'] == s['scene_id']
        assert [{'object_id': str(x['object_id']), 'ann_id': str(x['ann_id'])} for x in group] == s['expression_ids']
    gorilla.set_random_seed(1999)
    loader = DataLoader(Subset(dataset, [s['group_index'] for s in cohort]), batch_size=2,
                        shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)
    batch = next(iter(loader))
    before = fingerprint(torch, batch)
    cluster = model.dec.cluster_att
    active = [x for x in model.dec.encoder_layers if x.use_cluster]
    assert len(active) == 1 and active[0] is model.dec.encoder_layers[-1]
    held = {}
    def clone(v):
        if torch.is_tensor(v): return v.detach().clone()
        if isinstance(v, tuple): return tuple(clone(x) for x in v)
        if isinstance(v, list): return [clone(x) for x in v]
        if isinstance(v, dict): return {k: clone(x) for k, x in v.items()}
        return v
    def error(a, b): return float((a-b).abs().max().cpu())
    original = cluster._cluster_to_points
    def gather(*arguments, **keywords):
        value = original(*arguments, **keywords)
        held.update(gather_args=clone(arguments), gather_kwargs=clone(keywords), gather_output=clone(value))
        return value
    def core(module, arguments, value): held.update(core_args=clone(arguments), message=clone(value['point']))
    def ila(module, arguments): held['ila'] = clone(arguments)
    def dec(module, arguments, value): held.update(decoder=clone(arguments), decoder_output=clone(value))
    with torch.no_grad():
        hooks = [cluster.register_forward_hook(core), active[0].ila.register_forward_pre_hook(ila),
                 model.dec.decoder_layers[-1].register_forward_hook(dec)]
        gorilla.set_random_seed(1999)
        try:
            cluster._cluster_to_points = gather
            loss, components = model(copy.deepcopy(batch), mode='loss')
            r['native_forwards'] += 1
            assert bool(torch.isfinite(loss))
        finally:
            cluster._cluster_to_points = original
            for h in hooks: h.remove()
        assert fingerprint(torch, batch) == before
        a, kw = held['gather_args'], held['gather_kwargs']
        features, tokens, ids, mask = a
        B, N, C = features.shape
        lengths = (~mask).sum(1).tolist()
        assert len(set(lengths)) > 1 and bool(mask.any()), 'No natural heterogeneous padding in frozen batch'
        base = original(*a, **kw)
        base_message = cluster.message_norm(base).masked_fill(mask.unsqueeze(-1), 0)
        controls = {'gather_replay': error(base, held['gather_output']),
                    'message_reconstruction': error(base_message, held['message'])}
        cropped = torch.zeros_like(base)
        zero_tokens = [torch.zeros_like(x) for x in tokens]
        zero_base = original(features, zero_tokens, ids, mask, fine_message=torch.zeros_like(kw['fine_message']))
        zero_cropped = torch.zeros_like(zero_base)
        rows = []
        for b, n in enumerate(lengths):
            row_tokens = [x[b:b+1] for x in tokens]
            row_ids = [[level[b]] for level in ids]
            row_mask = mask[b:b+1, :n]
            value = original(features[b:b+1, :n], row_tokens, row_ids, row_mask,
                             fine_message=kw['fine_message'][b:b+1, :n])
            cropped[b, :n] = value[0]
            null = original(features[b:b+1, :n], [torch.zeros_like(x) for x in row_tokens], row_ids, row_mask,
                            fine_message=torch.zeros_like(kw['fine_message'][b:b+1, :n]))
            zero_cropped[b, :n] = null[0]
            masked = features[b, n:]
            rows.append({'row': b, 'valid_points': n, 'padded_points': N-n,
                         'padding_fraction': (N-n)/N,
                         'native_masked_feature_max_abs': float(masked.abs().max().cpu()) if masked.numel() else 0.,
                         'valid_gather_max_change': error(base[b, :n], value[0])})
        controls['zero_scale_null'] = error(zero_base, zero_cropped)
        cropped_message = cluster.message_norm(cropped).masked_fill(mask.unsqueeze(-1), 0)
        def suffix(message):
            iargs = list(clone(held['ila']))
            iargs[1] = held['core_args'][0] + torch.sigmoid(active[0].cluster_att_gate)*message
            f = active[0].ila(*iargs)[0]
            dargs = list(clone(held['decoder']))
            dargs[2] = f
            r['suffix_replays'] += 1
            return model.dec.decoder_layers[-1](*dargs)
        normal, changed = suffix(base_message), suffix(cropped_message)
        for i in (2, 3): controls['native_suffix_'+str(i)] = error(normal[i], held['decoder_output'][i])
        assert max(controls.values()) <= 1e-6, controls
        r.update(passed=True, input_sha256=before, scene_ids=[s['scene_id'] for s in cohort],
                 native_loss=float(loss.cpu()), rows=rows, controls=controls,
                 natural_padding_present=True, valid_message_max_change=error(base_message, cropped_message),
                 final_mask_logits_max_change=error(normal[2], changed[2]),
                 padding_invariance_pass=all(x['valid_gather_max_change'] <= 1e-6 for x in rows),
                 efficacy='UNKNOWN', shared_baseline_incidence='UNKNOWN', uniform_fix_authorized=False)
        hierarchy.reset_orth_accum()
    verify()
    r['after'] = observe()
except BaseException as e:
    r.update(error_type=type(e).__name__, error=str(e))
    raise
finally:
    save('native_batch2_result.json', r)
    release()
