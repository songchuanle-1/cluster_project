from runtime import get_native
TRANSPORT = {'previous': None, 'calls': 0}

def parameter_transport(model, logits, original_gradient, subsets, objectives, native_values, torch):
    named = [(name, p) for name, p in model.named_parameters() if p.requires_grad]
    parameters = tuple((p for _, p in named))
    task = torch.autograd.grad(objectives['mask_plus_indicator'].sum(), parameters, retain_graph=True, allow_unused=True)
    TRANSPORT['calls'] += 1
    conditions = {}
    cpu = {}
    weight = model.criterion.loss_weight[6]
    for name in ('original', 'identity', 'main_secondary', 'relation_other', 'fractional_secondary', 'fractional_repelling'):
        if name == 'identity':
            scalar = weight * type(model.criterion).loss_sem_align(model.criterion, *native_values)
            gradient = torch.autograd.grad(scalar.sum(), parameters, retain_graph=True, allow_unused=True)
        else:
            direction = original_gradient * weight
            if name != 'original':
                direction = direction * subsets[name]
            gradient = torch.autograd.grad(logits, parameters, grad_outputs=direction, retain_graph=True, allow_unused=True)
        TRANSPORT['calls'] += 1
        assert all((g is None or bool(torch.isfinite(g).all()) for g in gradient))
        cpu[name] = [None if g is None else g.detach().cpu() for g in gradient]
        norm2 = sum((float(g.double().square().sum()) for g in gradient if g is not None))
        dot = sum((float((g.double() * t.double()).sum()) for g, t in zip(gradient, task) if g is not None and t is not None))
        conditions[name] = {'gradient_norm': norm2 ** 0.5, 'task_dot': dot, 'nonzero_parameter_tensors': sum((g is not None and bool((g != 0).any()) for g in gradient)), 'unused_parameter_tensors': sum((g is None for g in gradient))}
    assert all((p.grad is None for p in parameters))
    identity = 0.0
    for a, b in zip(cpu['original'], cpu['identity']):
        if a is None or b is None:
            assert a is b
        else:
            identity = max(identity, float((a - b).abs().max()))
    result = {'trainable_parameter_tensors': len(parameters), 'task_nonzero_parameter_tensors': sum((t is not None and bool((t != 0).any()) for t in task)), 'conditions': conditions, 'original_native_identity_max_delta': identity, 'pass_original_native_identity1e6': identity <= 1e-06, 'requested_parameter_gradient_calls_this_forward': 7, 'parameter_grad_accumulated': False}
    if TRANSPORT['previous'] is None:
        TRANSPORT['previous'] = cpu
    else:
        maximum = 0.0
        for name, gradients in cpu.items():
            for a, b in zip(TRANSPORT['previous'][name], gradients):
                if a is None or b is None:
                    assert a is b
                else:
                    maximum = max(maximum, float((a - b).abs().max()))
        result['parameter_repeat_max_delta'] = maximum
        result['pass_parameter_repeat1e6'] = maximum <= 1e-06
        TRANSPORT['previous'] = None
    return result

def install_capture(model):
    state = {'masks': [], 'indicators': [], 'query': None}
    original_masks = model.criterion.loss_masks
    original_indi = model.criterion.loss_indi

    def masks(*args):
        result = original_masks(*args)
        state['masks'].append((args, result))
        return result

    def indi(*args):
        result = original_indi(*args)
        state['indicators'].append((args, result))
        return result
    model.criterion.loss_masks = masks
    model.criterion.loss_indi = indi
    state['hook'] = model.dec.decoder_layers[-1].register_forward_hook(lambda module, inputs, output: state.update(query=output[0], inst_feats=inputs[2], batch_mask=inputs[3]))
    state.update(original_masks=original_masks, original_indi=original_indi)
    return state

def head_effects(model, state, pred, mask_calls, indicator_calls, native, logits, role_grad, task_grad, query, torch):
    weights = model.criterion.loss_weight
    _, _, _, targets, indices, _ = native
    layer = model.dec.decoder_layers[-1]
    loss_module = __import__(type(model.criterion).__module__, fromlist=['get_iou'])

    def evaluate(counter_query):
        with torch.no_grad():
            scores, padded = layer.prediction_head(counter_query, state['inst_feats'], state['batch_mask'])
            unpadded = [mask.masked_select((~padding).unsqueeze(0)).view(mask.shape[0], -1) for mask, padding in zip(padded, pred['batch_mask'])]
            mask_args = list(mask_calls[0][0])
            mask_args[0], mask_args[1] = (unpadded, scores)
            bce, dice, _ = state['original_masks'](*mask_args)
            indi = layer.indi_embedding(counter_query)
            indi_args = list(indicator_calls[0][0])
            indi_args[0] = indi
            indicator = weights[4] * state['original_indi'](*indi_args)
            mask = weights[0] * bce + weights[1] * dice
            expressions = []
            for bi, (src, tgt) in enumerate(indices):
                indication = indi[bi].softmax(-1)[:, 1]
                selected = int(indication.argmax())
                is_matched = torch.zeros_like(indication, dtype=torch.bool)
                is_matched[src] = True
                margin = float(indication[is_matched].max() - indication[~is_matched].max())
                expressions.append({'batch': bi, 'selected': selected, 'selected_support_iou': float(loss_module.get_iou(unpadded[bi][selected], targets[bi]['masks'][0])), 'indicator_matched_unmatched_margin': margin})
            return {'losses': {'mask': float(mask), 'indicator': float(indicator), 'mask_plus_indicator': float(mask + indicator)}, 'expressions': expressions}
    baseline = evaluate(query.detach())
    assert baseline == evaluate(query.detach()), 'Exact fixed-head repeat'
    expected_mask = weights[0] * mask_calls[0][1][0] + weights[1] * mask_calls[0][1][1]
    expected_indi = weights[4] * indicator_calls[0][1]
    identity_delta = max(abs(baseline['losses']['mask'] - float(expected_mask.detach())), abs(baseline['losses']['indicator'] - float(expected_indi.detach())))
    assert identity_delta <= 1e-06
    original_semantic = type(model.criterion).loss_sem_align.__get__(model.criterion)
    original = torch.autograd.grad((weights[6] * original_semantic(*native)).sum(), query, retain_graph=True)[0].detach()
    directions = {'original': original, 'identity': original.clone()}
    directions.update(role_grad)
    for name, gradient in role_grad.items():
        directions['complement_' + name] = original - gradient
    readouts = {}
    epsilon = 0.001
    for name, gradient in directions.items():
        norm = float(gradient.double().norm())
        if norm == 0:
            readouts[name] = {'gradient_norm': 0, 'effects': None}
            continue
        direction = gradient / norm
        descent = evaluate(query.detach() - epsilon * direction)
        ascent = evaluate(query.detach() + epsilon * direction)
        assert descent == evaluate(query.detach() - epsilon * direction)
        assert ascent == evaluate(query.detach() + epsilon * direction)
        effects = {}
        for objective, reference in task_grad.items():
            predicted = -float((gradient.double() * reference.double()).sum()) / norm
            central = (descent['losses'][objective] - ascent['losses'][objective]) / (2 * epsilon)
            effects[objective] = {'descent_loss_delta': descent['losses'][objective] - baseline['losses'][objective], 'ascent_loss_delta': ascent['losses'][objective] - baseline['losses'][objective], 'central_derivative': central, 'analytic_unit_descent_derivative': predicted, 'central_absolute_error': abs(central - predicted)}
        readouts[name] = {'gradient_norm': norm, 'effects': effects, 'descent_expression_readouts': descent['expressions'], 'ascent_expression_readouts': ascent['expressions']}
    assert readouts['original'] == readouts['identity']
    return {'epsilon': epsilon, 'head_identity_max_loss_delta': identity_delta, 'same_capture_head_repeat_exact': True, 'baseline': baseline, 'conditions': readouts, 'scope': 'Fixed-head readout only; no optimizer, parameter update, full-network intervention, strict derivative certification or trained efficacy.'}

def calibration(model, state, native, pred, gradients, batch, torch):
    tokens, queries, lang_masks, targets, indices, num_boxes = native
    logits = queries @ tokens.transpose(-1, -2) / model.criterion.temperature
    z = logits.detach().double()
    positive = torch.zeros_like(z)
    ends = lang_masks.sum(1) - 1
    positive[torch.arange(len(ends)), :, ends] = 0.5
    positive[torch.arange(len(ends)), :, ends - 1] = 0.5
    maps = {name: torch.zeros_like(z) for name in ('modify', 'pron', 'rel', 'other')}
    sources = {'modify': 'modify_positive_map', 'pron': 'pron_positive_map', 'rel': 'rel_positive_map', 'other': 'other_entity_map'}
    mask = torch.full(z.shape[:2], model.criterion.eos_coef, device=z.device, dtype=torch.float64)
    for bi, (src, tgt) in enumerate(indices):
        positive[bi, src] = targets[bi]['positive_map'][tgt, :z.shape[-1]].double()
        mask[bi, src] = 1
        for name, field in sources.items():
            maps[name][bi, src] = targets[bi][field][tgt, :z.shape[-1]].double()
    positive = positive > 0
    supports = {name: value > 0 for name, value in maps.items()}
    attraction = positive.double() / (positive.sum(2, keepdim=True) + 1e-06)
    for name, weight in (('modify', 0.2), ('pron', 0.2), ('rel', 0.1)):
        attraction += weight * supports[name] / (supports[name].sum(2, keepdim=True) + 1e-06)
    amplification = 1 + supports['other'].double()
    effective_probability = (z * amplification).softmax(2)
    q_component = mask.unsqueeze(-1) * (effective_probability * amplification - attraction)
    q_component *= positive.any(2, keepdim=True)
    tmask = torch.full((len(z), z.shape[-1]), model.criterion.eos_coef, device=z.device, dtype=torch.float64)
    tmask[torch.arange(len(ends)), ends] = 1
    tmask[positive.any(1)] = 1
    tmask[supports['modify'].any(1)] = 0.2
    tmask[supports['pron'].any(1)] = 0.2
    tmask[supports['rel'].any(1)] = 0.1
    tmask[torch.arange(len(ends)), ends - 1] = 0.1
    role_count = positive.double()
    mass = positive.sum(1).double()
    for name in ('modify', 'pron', 'rel'):
        role_count = role_count + supports[name]
        mass = mass + maps[name].sum(1)
    mass += 1e-06
    t_component = z.softmax(1) - role_count / mass.unsqueeze(1)
    t_component *= role_count.any(1).unsqueeze(1) * tmask.unsqueeze(1)
    denominator = 2 * float(num_boxes)
    analytic = (q_component + t_component) / denominator
    analytic_error = float((analytic - gradients['original'].double()).abs().max())
    assert analytic_error <= 1e-06, ('analytic_gradient', analytic_error)
    expected_masks = [value.masked_select((~padding).unsqueeze(0)).view(value.shape[0], -1) for value, padding in zip(pred['masks'], pred['batch_mask'])]
    mask_calls = [(args, values) for args, values in state['masks'] if len(args[0]) == len(expected_masks) and all((a.shape == b.shape and torch.equal(a, b) for a, b in zip(args[0], expected_masks)))]
    indicator_calls = [(args, value) for args, value in state['indicators'] if args[0] is pred['indis']]
    assert len(mask_calls) == len(indicator_calls) == 1
    weights = model.criterion.loss_weight
    mask_loss = weights[0] * mask_calls[0][1][0] + weights[1] * mask_calls[0][1][1]
    indi_loss = weights[4] * indicator_calls[0][1]
    query = state['query']
    objectives = {'mask': mask_loss, 'indicator': indi_loss, 'mask_plus_indicator': mask_loss + indi_loss}
    task_grad = {name: torch.autograd.grad(value.sum(), query, retain_graph=True)[0] for name, value in objectives.items()}
    fractional = torch.zeros_like(positive)
    for name in ('modify', 'pron', 'rel'):
        fractional |= (maps[name] > 0) & (maps[name] < 1)
    main_secondary = positive & (supports['modify'] | supports['pron'] | supports['rel'])
    relation_other = supports['rel'] & supports['other']
    subsets = {'main_secondary': main_secondary, 'relation_other': relation_other, 'fractional_secondary': fractional, 'fractional_repelling': fractional & (gradients['original'] > 0), 'fractional_attracting': fractional & (gradients['original'] < 0)}
    role_grad = {}
    for name, subset in subsets.items():
        gradient = torch.autograd.grad(logits, query, grad_outputs=gradients['original'] * subset * weights[6], retain_graph=True)[0]
        assert bool(torch.isfinite(gradient).all())
        role_grad[name] = gradient.detach()
    expressions = []
    from importlib import import_module
    native_iou = import_module(type(model.criterion).__module__).get_iou
    for bi, (src, tgt) in enumerate(indices):
        assert len(batch['object_idss'][bi]) == 1
        assert targets[bi]['masks'].shape[0] == len(tgt)
        assert torch.equal(targets[bi]['masks'], targets[bi]['masks'][:1].expand_as(targets[bi]['masks']))
        ious = native_iou(expected_masks[bi].detach(), targets[bi]['masks'][0]).detach()
        indicate = pred['indis'][bi].detach().softmax(-1)[:, 1]
        selected = int(indicate.argmax())
        alignment = {}
        for name, gradient in role_grad.items():
            own = gradient[bi].double()
            if not bool(subsets[name][bi].any()):
                continue
            alignment[name] = {objective: {'dot': float((own * reference[bi].double()).sum()), 'role_query_gradient_norm': float(own.norm()), 'task_query_gradient_norm': float(reference[bi].double().norm())} for objective, reference in task_grad.items()}
        sites = []
        for qi, ti in zip(src.tolist(), tgt.tolist()):
            union = main_secondary[bi, qi] | fractional[bi, qi] | relation_other[bi, qi]
            for token in union.nonzero().flatten().tolist():
                sites.append({'query': qi, 'target': ti, 'token': token, 'main': bool(positive[bi, qi, token]), 'modify': float(maps['modify'][bi, qi, token]), 'pron': float(maps['pron'][bi, qi, token]), 'rel': float(maps['rel'][bi, qi, token]), 'other': float(maps['other'][bi, qi, token]), 'fractional': bool(fractional[bi, qi, token]), 'query_to_token_probability': float(effective_probability[bi, qi, token]), 'attraction_coefficient': float(attraction[bi, qi, token]), 'calibration_threshold': float((attraction / amplification)[bi, qi, token]), 'query_to_token_derivative': float(q_component[bi, qi, token] / denominator), 'token_to_query_derivative': float(t_component[bi, qi, token] / denominator), 'total_derivative': float(gradients['original'][bi, qi, token]), 'matched_query_support_iou': float(ious[qi])})
        expressions.append({'batch': bi, 'ann_id': int(batch['ann_ids'][bi]), 'selected_query': selected, 'selected_support_iou': float(ious[selected]), 'best_support_iou': float(ious.max()), 'selected_is_matched': selected in src.tolist(), 'matched_queries': src.tolist(), 'matched_support_ious': ious[src].tolist(), 'role_task_alignment': alignment, 'sites': sites})
    head_readout = head_effects(model, state, pred, mask_calls, indicator_calls, native, logits, role_grad, task_grad, query, torch)
    result = {'analytic_autograd_max_delta': analytic_error, 'expressions': expressions, 'weighted_original_task_losses': {name: float(value.detach()) for name, value in objectives.items()}, 'scope': 'TRAIN augmented support IoU and local task directions; not VAL mIoU, causal task harm, optimizer, efficacy or admission.', 'fixed_head': head_readout}
    result['parameter_transport'] = parameter_transport(model, logits, gradients['original'], subsets, objectives, native, torch)
    state['masks'].clear()
    state['indicators'].clear()
    state['query'] = None
    return result
'Checkpoint-specific, fixed-cohort diagnostics for three existing hypotheses.'
import argparse
import ast
import copy
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import logging
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runner', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--token', required=True)
    args = parser.parse_args()
    native = get_native(args.runner)
    assert native.digest(args.runner) == 'f29e5f8dd8dd70a8cb7428f8facd7f8e37401ced27e01cdf1e0ef2db19c175e9'
    torch = native.torch
    root = Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
    pipe = root.parent / 'pipeline'
    output = Path(args.output)
    old = Path('/data/songcl/Project/Cluster_project/pipeline/transport_port_75d7e1ea35634b1fa29749fcf54163c8/assets')
    locks = []
    rows = []
    try:
        for name in ('/tmp/cluster_project_gpu0_m201_migration.lock', '/tmp/cluster_project_gpu0_exclusive.lock', '/tmp/cluster_project_gpu0_parameter_transport.lock'):
            handle = open(name, 'a+b')
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locks.append(handle)
        first_guard = native.guard(root)
        torch.cuda.set_per_process_memory_fraction(0.25, 0)
        sys.path[:0] = [str(root), str(root / 'framework/lib')]
        import gorilla
        from framework import resolve_network
        from framework.dataset import build_dataset
        config = 'configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml'
        cfg = gorilla.Config.fromfile(str(root / config))
        assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and (cfg.lr_scheduler.max_iters == 70)
        checkpoint = old / 'checkpoint_snapshot.pth'
        assert native.digest(checkpoint) == 'f17f2ec3b08422f033a6683a4030bff1d69a1112514c6ac96dcb38870be735fd'
        saved = torch.load(checkpoint, map_location='cpu', weights_only=False, mmap=True)
        gorilla.set_random_seed(1999)
        model = resolve_network(config)(**cfg.model)
        state = saved['model']
        keys = ('text_encoder.embeddings.position_ids', 'text_encoder.embeddings.token_type_ids')
        assert set(state) - set(model.state_dict()) == set(keys)
        buffers = dict(model.named_buffers())
        buffer_audit = {}
        for key in keys:
            assert key in buffers and key not in model.state_dict()
            left, right = (state[key].detach().cpu(), buffers[key].detach().cpu())
            assert left.shape == right.shape and left.dtype == right.dtype and torch.equal(left, right)
            buffer_audit[key] = native.input_hash(left)
        filtered = {key: value for key, value in state.items() if key not in keys}
        model.load_state_dict(filtered, strict=True)
        model.cuda().train()
        task_capture = install_capture(model)
        manifest = json.loads((old / 'source_manifest.json').read_text())
        folder = root / 'framework/model/Quard_model' / native.PACKAGE
        for name, expected in manifest['package'].items():
            assert native.digest(folder / name) == expected
        dataset = build_dataset(cfg.data.train, logging.getLogger('bps-scalar-checkpoint'))
        generator_path = old / 'native_role_direction_v2_20261014_0010.py'
        assert native.digest(generator_path) == 'c5a9c1157421bd9cc386a2da160ac1cf0ae376948ddff5b7f0c6808be690d749'
        generator = next((node for node in ast.parse(generator_path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == 'logit_functions'))
        namespace = {'ast': ast, 'copy': copy}
        exec(compile(ast.Module(body=[generator], type_ignores=[]), str(generator_path), 'exec'), namespace)
        functions = namespace['logit_functions'](folder / 'loss.py', model.criterion, torch)
        cohort, source_hashes = ({}, {})
        for family, filename, expected in (('role', 'role_gradient_native_20261013_1012.json', 'ca0697d740a4d239dfe4465542ac75beed09a0d95b963022fc7b796ec6368187'), ('relation', 'relation_gradient_native_20261013_0707.json', 'f98351adaf132046fca6ca11158a89a21ca8e0fc5a223d635cf3207b214eb7d4')):
            source = old / filename
            assert native.digest(source) == expected
            source_hashes[filename] = expected
            for row in json.loads(source.read_text())['rows']:
                if row['trial'] != 0:
                    continue
                selection = row['selection']
                group = selection['group']
                if group not in cohort:
                    cohort[group] = dict(group=group, scene=selection['scene'], ann_ids=row['ann_ids'], families=[])
                assert cohort[group]['ann_ids'] == row['ann_ids']
                cohort[group]['families'].append(family)
        semantic = model.criterion.loss_sem_align
        calls, held = ([], {})

        def capture(*values):
            actual = semantic(*values)
            calls.append((values, actual))
            return actual
        model.criterion.loss_sem_align = capture
        hook = model.criterion.register_forward_pre_hook(lambda module, inputs: held.update(pred=inputs[0]))
        try:
            for selection in list(cohort.values())[:4]:
                native.guard(root)
                gorilla.set_random_seed(1999)
                batch = dataset.collate_fn([dataset[selection['group']]])
                assert list(map(int, batch['ann_ids'])) == selection['ann_ids']
                fingerprint = native.input_hash(batch)
                trials, previous_masks, previous_gradients = ([], None, None)
                max_mask_delta = max_gradient_delta = 0.0
                for trial in range(2):
                    model.load_state_dict(filtered, strict=True)
                    model.train()
                    gorilla.set_random_seed(1999)
                    calls.clear()
                    held.clear()
                    with torch.enable_grad():
                        full_loss, _ = model(batch, mode='loss')
                    pred = held['pred']
                    final = [(values, actual) for values, actual in calls if values[0] is pred['proj_tokens'] and values[1] is pred['proj_queries']]
                    assert len(final) == 1, 'Final semantic tensor identity ambiguous'
                    values, actual = final[0]
                    tokens, queries, language, targets, indices, num_boxes = values
                    raw = queries.detach() @ tokens.detach().transpose(-1, -2) / model.criterion.temperature
                    subset = {key: torch.zeros_like(raw, dtype=torch.bool) for key in ('main_secondary', 'relation_other', 'fractional_secondary')}
                    relation_targets = []
                    for bi, (target, (src, tgt)) in enumerate(zip(targets, indices)):
                        maps = {name: target[name][tgt, :raw.shape[-1]] for name in ('positive_map', 'modify_positive_map', 'pron_positive_map', 'rel_positive_map', 'other_entity_map')}
                        secondary = [maps[key] for key in ('modify_positive_map', 'pron_positive_map', 'rel_positive_map')]
                        subset['main_secondary'][bi, src] = (maps['positive_map'] > 0) & ((secondary[0] > 0) | (secondary[1] > 0) | (secondary[2] > 0))
                        subset['relation_other'][bi, src] = (maps['rel_positive_map'] > 0) & (maps['other_entity_map'] > 0)
                        subset['fractional_secondary'][bi, src] = (secondary[0] > 0) & (secondary[0] < 1) | (secondary[1] > 0) & (secondary[1] < 1) | (secondary[2] > 0) & (secondary[2] < 1)
                        edited = dict(target)
                        edited['other_entity_map'] = target['other_entity_map'].clone()
                        edited['other_entity_map'].masked_fill_(target['rel_positive_map'] > 0, 0)
                        relation_targets.append(edited)
                    conditions, gradients = ({}, {})
                    with torch.enable_grad():
                        for name in ('original', 'identity', 'precedence', 'mass', 'relation_overlap_removed'):
                            z = raw.detach().clone().requires_grad_(True)
                            inputs = list(values)
                            if name == 'relation_overlap_removed':
                                inputs[3] = relation_targets
                            operator = functions['original' if name == 'relation_overlap_removed' else name]
                            value = operator(*inputs, z)
                            gradient = torch.autograd.grad(value, z)[0].detach()
                            assert bool(torch.isfinite(value).all() and torch.isfinite(gradient).all())
                            gradients[name] = gradient.cpu()
                            conditions[name] = {'loss': float(value.detach()), 'subsets': {key: {'count': int(mask.sum()), 'attracting': int((gradient[mask] < 0).sum()), 'repelling': int((gradient[mask] > 0).sum()), 'zero': int((gradient[mask] == 0).sum())} for key, mask in subset.items()}}
                    for name in conditions:
                        conditions[name]['loss_delta_from_original'] = conditions[name]['loss'] - conditions['original']['loss']
                        conditions[name]['subset_sign_flips'] = {key: int(((gradients[name].sign() != gradients['original'].sign()) & mask.cpu()).sum()) for key, mask in subset.items()}
                    identity_delta = max(abs(conditions['identity']['loss'] - conditions['original']['loss']), float((gradients['identity'] - gradients['original']).abs().max()))
                    assert identity_delta == 0
                    masks = [value.detach().cpu().clone() for value in pred['masks']]
                    if previous_masks is not None:
                        max_mask_delta = max((float((a - b).abs().max()) for a, b in zip(previous_masks, masks)))
                        max_gradient_delta = max((float((previous_gradients[name] - gradients[name]).abs().max()) for name in gradients))
                    previous_masks, previous_gradients = (masks, gradients)
                    task_calibration = calibration(model, task_capture, values, pred, {name: value.to(raw.device) for name, value in gradients.items()}, batch, torch)
                    assert all((parameter.grad is None for parameter in model.parameters()))
                    trials.append({'full_loss': float(full_loss), 'native_semantic_loss': float(actual), 'source_loss_identity_abs_delta': abs(float(actual) - conditions['original']['loss']), 'conditions': conditions, 'task_calibration': task_calibration})
                    assert native.input_hash(batch) == fingerprint
                row = {'selection': selection, 'input_sha256': fingerprint, 'trials': trials, 'max_mask_repeat_delta': max_mask_delta, 'max_gradient_repeat_delta': max_gradient_delta, 'full_loss_repeat_delta': abs(trials[0]['full_loss'] - trials[1]['full_loss']), 'pass_repeat1e6': max(max_mask_delta, max_gradient_delta, abs(trials[0]['full_loss'] - trials[1]['full_loss'])) <= 1e-06, 'pass_native_identity1e6': max((t['source_loss_identity_abs_delta'] for t in trials)) <= 1e-06}
                rows.append(row)
                native.save(output, {'token': args.token, 'complete': False, 'rows': rows})
                print('completed scalar group ' + str(selection['group']), flush=True)
                torch.cuda.empty_cache()
        finally:
            hook.remove()
            model.criterion.loss_sem_align = semantic
        native.save(output, {'token': args.token, 'complete': True, 'rows': rows, 'recorded_at': datetime.now(timezone.utc).isoformat(), 'script_sha256': native.digest(__file__), 'source_hashes': source_hashes, 'checkpoint_sha256': native.digest(checkpoint), 'checkpoint_meta': saved.get('meta', {}), 'buffer_audit': buffer_audit, 'guard_before': first_guard, 'guard_after': native.guard(root), 'peak_allocated_mib': torch.cuda.max_memory_allocated() / 2 ** 20, 'optimizer_steps': 0, 'model_parameter_backward': 0, 'scope': 'New BPS checkpoint-specific frozen TRAIN logit diagnostics only; not full-model intervention, historical repeat repair, independent core, task harm, efficacy or admission.'})
    finally:
        for handle in reversed(locks):
            fcntl.flock(handle, fcntl.LOCK_UN)
            handle.close()
if __name__ == '__main__':
    main()
    output = Path(sys.argv[sys.argv.index('--output') + 1])
    result = json.loads(output.read_text())
    assert [row['selection']['group'] for row in result['rows']] == [0, 60, 101, 124]
    result['requested_model_parameter_gradient_calls'] = TRANSPORT['calls']
    result['model_parameter_backward'] = 'Explicit autograd.grad requests; no .backward, accumulation or optimizer'
    result['scope'] = 'Fixed four-group local parameter-gradient transport only; no optimizer update, causal training harm, efficacy or new structural admission.'
    output.write_text(json.dumps(result, indent=2) + '\n')
