"""Matched native criterion backward on an instrumented contact prototype."""
import argparse
import copy
import importlib
import logging
import time
from native_runtime import acquire, release, setup, save, sha, MANIFEST, NAME

parser = argparse.ArgumentParser()
parser.add_argument('--lease', required=True)
args = parser.parse_args()
result = {'execution_completed': False, 'scientific_admission': False, 'new_training': 0,
    'optimizer_steps': 0, 'scope': 'Instrumented original Network and unchanged native criterion; no independently deployed model/config or formal bs1 warmup20/repeat100 efficiency gate.'}
hooks, attention, original_gather = [], None, None
try:
    result['before'] = acquire(args.lease)
    torch, gorilla, cfg, model, metadata = setup()
    from torch.utils.data import DataLoader, Subset
    from framework.dataset import build_dataset
    from contact_exchange import contacts, exchange, readback
    module = importlib.import_module('framework.model.Quard_model.' + NAME + '.hier_postprocess')
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('contact-backward'))
    for scene in MANIFEST['cohort']:
        group = dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id'] == scene['scene_id']
        assert [{'object_id': str(row['object_id']), 'ann_id': str(row['ann_id'])} for row in group] == scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch = next(iter(DataLoader(Subset(dataset, [s['group_index'] for s in MANIFEST['cohort']]),
        batch_size=2, shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)))
    lengths = [int(v) for v in batch['scenes_len']]
    assert lengths == [4, 4]
    physical = contacts(batch['voxel_coords'].numpy(), batch['p2v_map'].numpy(),
                        batch['superpoints'].numpy(), batch['batch_offsets'].numpy())
    expanded = [edges for edges, length in zip(physical, lengths) for _ in range(length)]
    initial = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    attention = model.dec.cluster_att
    original_gather = attention._cluster_to_points
    active = [layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active) == 1
    held = {'message_gradients': []}

    def positions_hook(owner, values):
        held['positions'] = values[5].detach()

    hooks.append(active[0].register_forward_pre_hook(positions_hook))

    def capture_gradient(gradient):
        held['message_gradients'].append({'finite': bool(torch.isfinite(gradient).all()),
            'max_abs': float(gradient.abs().max().cpu()), 'l2': float(gradient.norm().cpu())})

    def candidate_gather(features, banks, identifiers, padding):
        messages = []
        for b, ids in enumerate(identifiers[0]):
            n = len(ids)
            message, _ = exchange(features[b, :n], held['positions'][b, :n].cpu().numpy(),
                ids.cpu().numpy(), expanded[b], banks[0][b, ids.long()], heads=attention.nhead)
            if message.requires_grad:
                message.register_hook(capture_gradient)
            messages.append(message)
        return readback(attention, features, banks, identifiers, padding, fine_override=messages)

    arms = []
    for arm in ('baseline', 'physical_contact'):
        model.zero_grad(set_to_none=True)
        model.load_state_dict(initial, strict=True)
        model.train()
        gorilla.set_random_seed(1999)
        held['message_gradients'] = []
        attention._cluster_to_points = original_gather if arm == 'baseline' else candidate_gather
        module.reset_orth_accum()
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        allocated_before = torch.cuda.memory_allocated()
        started = time.perf_counter()
        loss, _ = model(copy.deepcopy(batch), mode='loss')
        assert bool(torch.isfinite(loss))
        loss.backward()
        torch.cuda.synchronize()
        seconds = time.perf_counter() - started
        gradients = [p.grad for p in model.parameters() if p.grad is not None]
        assert gradients and all(bool(torch.isfinite(g).all()) for g in gradients)
        if arm == 'physical_contact':
            assert len(held['message_gradients']) == 8
            assert all(g['finite'] for g in held['message_gradients'])
            assert any(g['max_abs'] > 0 for g in held['message_gradients'])
        arms.append({'arm': arm, 'native_loss': float(loss.detach().cpu()),
            'native_criterion_backward_completed': True, 'gradient_tensor_count': len(gradients),
            'all_observed_parameter_gradients_finite': True,
            'contact_message_gradients': held['message_gradients'],
            'allocated_before_bytes': allocated_before,
            'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
            'peak_reserved_bytes': torch.cuda.max_memory_reserved(),
            'forward_backward_seconds': seconds,
            'measurement': 'same process/native batch2, eight expressions; single pass, not calibrated latency benchmark or full optimizer training peak'})
        del loss, gradients
    model.zero_grad(set_to_none=True)
    model.load_state_dict(initial, strict=True)
    candidate_peak, baseline_peak = arms[1]['peak_allocated_bytes'], arms[0]['peak_allocated_bytes']
    result.update(execution_completed=True, arms=arms, native_loss_forwards=2,
        native_criterion_backwards=2, new_path_native_criterion_backwards=1,
        candidate_minus_baseline_peak_allocated_bytes=candidate_peak - baseline_peak,
        candidate_to_baseline_peak_allocated_ratio=candidate_peak / baseline_peak,
        parameters_restored_without_optimizer=True,
        original_seed_schedule_criterion_preserved=True,
        missing_admission_gates=['Independent model/config integration', 'Uniform standard FLOPs',
            'bs1 warmup20/repeat100 latency/memory', 'Full-source numerical/permutation evidence',
            'Broader scene-level matched task interpretation and novelty limitations'])
    result['after'] = __import__('native_runtime').observe()
except BaseException as error_value:
    result.update(error_type=type(error_value).__name__, error=str(error_value))
    raise
finally:
    for hook in hooks:
        hook.remove()
    if attention is not None and original_gather is not None:
        attention._cluster_to_points = original_gather
    try:
        save('native_backward_result.json', result)
    finally:
        release()
