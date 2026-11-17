"""HRC native two-step smoke and original-handler resources; fresh lease required."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1')
import argparse
import copy
import importlib
import importlib.util
import itertools
import json
import logging
from pathlib import Path
import sys
import time
from native_runtime import acquire, release, save, sha, verify, observe, fingerprint, MANIFEST, STAGE, ROOT, NAME


def setup(target, mode, result):
    sys.path[:0] = [str(ROOT), str(ROOT / 'framework/lib')]
    # Importing this module installs the project's native torch.load compatibility.
    from tools import train
    import torch
    import gorilla
    import yaml
    from framework import resolve_network
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.75, 0)
    base_name = NAME
    candidate_name = MANIFEST['candidate_name']
    selected_name = candidate_name if target == 'candidate' else base_name
    qualified = 'framework.model.Quard_model.' + selected_name
    original_config = Path(MANIFEST['assets']['config_path'])
    candidate_config = STAGE / 'candidate.yaml'
    parent_values = yaml.safe_load(original_config.read_text())
    candidate_values = yaml.safe_load(candidate_config.read_text())
    assert parent_values == candidate_values, 'Only the config filename may identify the independent model'
    source_config = candidate_config if target == 'candidate' else original_config
    values = copy.deepcopy(candidate_values if target == 'candidate' else parent_values)
    original_work_dir = values.get('work_dir')
    # Approved private output-path adaptation only. All data and training values stay native.
    values['work_dir'] = str(STAGE / ('native_' + mode + '_' + target))
    Path(values['work_dir']).mkdir(exist_ok=False)
    config_dir = STAGE / ('runtime_config_' + mode + '_' + target)
    config_dir.mkdir(exist_ok=False)
    config_path = config_dir / (selected_name + '.yaml')
    with config_path.open('x') as stream:
        yaml.safe_dump(values, stream, sort_keys=False)
    check_values = copy.deepcopy(values)
    check_values['work_dir'] = original_work_dir
    assert check_values == parent_values
    cfg = gorilla.Config.fromfile(str(config_path))
    cfg.dist = False  # tools/train.py main's default single-GPU CLI state.
    assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
    assert cfg.dataloader.train.batch_size == 2 and cfg.dataloader.train.num_workers == 4
    assert cfg.dataloader.train.persistent_workers is True
    gorilla.set_random_seed(1999)
    source_hashes = {}
    if target == 'candidate':
        directory = STAGE / 'candidate_model'
        for name, expected in MANIFEST['candidate_source_hashes'].items():
            observed = sha(directory / name)
            assert observed == expected, name
            source_hashes[name] = observed
        importlib.import_module('framework.model.Quard_model')
        spec = importlib.util.spec_from_file_location(qualified, directory / '__init__.py',
            submodule_search_locations=[str(directory)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(qualified)
        for name, expected in MANIFEST['assets']['source_hashes'].items():
            observed = sha(ROOT / 'framework/model/Quard_model' / base_name / name)
            assert observed == expected, name
            source_hashes[name] = observed
    network = resolve_network(str(config_path))
    assert network is module.Network, 'Native YAML resolver silently selected another model'
    assert network.__module__ == qualified + '.network', 'Unexpected/fallback native Network module'
    assert cfg.model.dec.cluster_att_num_layers == 1, 'Dependency control requires only the original final hierarchy injection'
    model = network(**cfg.model).cuda()
    # Match tools.train.main: native optimizer/scheduler construction precedes pretrain loading.
    optimizer = gorilla.build_optimizer(model, cfg.optimizer) if mode == 'smoke' else None
    scheduler = gorilla.build_lr_scheduler(optimizer, cfg.lr_scheduler) if optimizer is not None else None
    assert cfg.train.pretrain, 'Native backbone pretrain is required'
    pretrain = Path(cfg.train.pretrain)
    assert pretrain.is_file()
    full_checkpoint = MANIFEST['assets'].get('checkpoint')
    if full_checkpoint:
        assert pretrain.resolve() != Path(full_checkpoint).resolve(), 'No trained M95 full-model checkpoint initialization'
    gorilla.load_checkpoint(model, str(pretrain), strict=False, map_location='cpu')
    model.eval()
    result.update(source_hashes=source_hashes,
        config_sha256=sha(source_config), runtime_config_sha256=sha(config_path),
        original_config_sha256=sha(original_config), model_package=qualified,
        config_source=str(source_config), runtime_config_path=str(config_path),
        configuration_adaptations={'work_dir': {'from': original_work_dir, 'to': cfg.work_dir},
            'dist': 'False, native single-GPU CLI default'},
        initialization={'kind': 'native_train_pretrain', 'path': str(pretrain),
            'sha256': sha(pretrain), 'loader': 'gorilla.load_checkpoint(strict=False,map_location=cpu)',
            'trained_m95_checkpoint_loaded': False, 'seed': 1999},
        native_train_source_sha256=sha(ROOT / 'tools/train.py'),
        data_source={key: {'data_root': value.get('data_root'), 'prefix': value.get('prefix'),
            'type': value.get('type'), 'training': value.get('training')}
            for key, value in cfg.data.items()})
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler


def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Original train.train; read-only graph observations never enter optimizer.grad."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('hrc-native-smoke'))
    loader = build_dataloader(dataset, dist=cfg.dist, **cfg.dataloader.train)
    assert loader.batch_size == 2 and loader.num_workers == 4 and loader.persistent_workers
    assert loader.drop_last

    class TwoNativeBatches:
        def __init__(self, native):
            self.native, self.sampler = native, native.sampler
        def __len__(self):
            return 2
        def __iter__(self):
            yield from itertools.islice(iter(self.native), 2)

    att = model.dec.cluster_att
    bank = model.dec.cluster_bank
    hierarchy = importlib.import_module(qualified + '.hier_postprocess')
    candidate = result['target'] == 'candidate'
    original_mean = getattr(hierarchy, 'refined_parent_mean', None)
    assert (original_mean is not None) == candidate
    tracked = {level: dict(att.cluster_ffn[level].named_parameters()) for level in range(3)}
    initial_hash = {level: fingerprint(torch, {n:p.detach() for n,p in ps.items()}) for level,ps in tracked.items()}
    calls, means, rawbanks, csort, readbacks, probes, losses, steps, batches = [], [], [], [], [], [], [], [], []
    hooks = []
    state = {'probe_active': False, 'forward_index': 0}
    replacements = []

    def summary(value):
        finite = bool(torch.isfinite(value).all())
        return {'shape': list(value.shape), 'dtype': str(value.dtype), 'finite': finite,
            'nonfinite_count': int((~torch.isfinite(value)).sum()),
            'abs_max': float(value.detach().float().abs().max().cpu()) if value.numel() and finite
                else (0.0 if not value.numel() else None)}

    def logvar(value):
        tensor = torch.as_tensor(value).detach()
        info = summary(tensor)
        info['value'] = float(tensor.cpu()) if info['finite'] and tensor.numel() == 1 else None
        return info

    def gradient_hook(record, key):
        def receive(gradient):
            # autograd.grad probes traverse some of these same nodes. Never count
            # or assert them as native criterion backward observations.
            if state['probe_active']:
                return None
            info = summary(gradient)
            record.setdefault(key, []).append(info)
            assert info['finite']
            return None
        return receive

    def watch(value, record, key):
        assert value.requires_grad, key
        hooks.append(value.register_hook(gradient_hook(record, key)))

    def replace(owner, name, replacement):
        assert name not in vars(owner), 'Diagnostic expects original inherited methods'
        setattr(owner, name, replacement)
        replacements.append((owner, name))

    original_build = bank.build_cluster_feats
    def observed_build(sp_feats, batch_offsets):
        output = original_build(sp_feats, batch_offsets)
        record = {'forward': state['forward_index'],
            'raw_sha256': fingerprint(torch, [x.detach().clone() for x in output]),
            'id_sha256': fingerprint(torch, bank.cluster_ids_list),
            'map_sha256': fingerprint(torch, bank.child_cluster_maps),
            'levels': [summary(x) for x in output]}
        rawbanks.append(record)
        state['raw_refs'] = output
        state['raw_record'] = record
        return output
    replace(bank, 'build_cluster_feats', observed_build)

    def ffn_hook(level):
        def observe_ffn(owner, values, output):
            record = {'forward': state['forward_index'], 'level': level,
                'input': summary(values[0]), 'output': summary(output)}
            assert record['input']['finite'] and record['output']['finite']
            calls.append(record)
            state.setdefault('ffn_output_snapshots', {})[level] = output.detach().clone()
            watch(values[0], record, 'native_input_gradients')
            watch(output, record, 'native_output_gradients')
        return observe_ffn
    for level in range(3):
        hooks.append(att.cluster_ffn[level].register_forward_hook(ffn_hook(level)))

    def observed_mean(child_feats, parent_ids_list, parent_template):
        record = {'forward': state['forward_index'], 'index': len(means),
            'child': summary(child_feats), 'raw_parent_template': summary(parent_template),
            'ids_sha256': fingerprint(torch, parent_ids_list), 'batches': [],
            'original_call_count': 1, 'reference_scope': 'detached CPU float64 fixed-slot sum/count; never fed into model'}
        output = original_mean(child_feats, parent_ids_list, parent_template)
        record['output'] = summary(output)
        assert record['child']['finite'] and record['output']['finite']
        reference = torch.zeros(output.shape, dtype=torch.float64, device='cpu')
        mean_level = 1 + sum(x['forward'] == state['forward_index'] for x in means)
        assert mean_level in (1, 2)
        record['level'] = mean_level
        for b, ids in enumerate(parent_ids_list):
            ids_cpu = ids.detach().long().cpu()
            rows = ids_cpu.numel()
            parent_width = parent_template.shape[1]
            source = child_feats[b, :rows].detach().cpu().double()
            counts = torch.zeros(parent_width, dtype=torch.float64)
            reference[b].index_add_(0, ids_cpu, source)
            counts.index_add_(0, ids_cpu, torch.ones(rows, dtype=torch.float64))
            reference[b] /= counts.clamp_min(1).unsqueeze(-1)
            parent_real_width = int(ids_cpu.max()) + 1 if rows else 0
            adjacent_ids = bank.cluster_ids_list[mean_level-1][b].detach().long().cpu()
            adjacent_counts = torch.bincount(adjacent_ids, minlength=rows)
            real_point_child_ids = bank.cluster_ids_list[0][b].detach().long().cpu()
            if mean_level == 2:
                real_point_child_ids = adjacent_ids[real_point_child_ids]
            real_point_counts = torch.bincount(real_point_child_ids, minlength=rows)
            empty_parent = counts[:parent_real_width].eq(0)
            empty_zero = bool(output[b, :parent_real_width].detach().cpu()[empty_parent].eq(0).all())
            pad_zero = bool(output[b, parent_real_width:].detach().cpu().eq(0).all())
            record['batches'].append({'batch': b, 'child_prefix': rows,
                'child_padded_width': child_feats.shape[1], 'parent_real_width': parent_real_width,
                'parent_padded_width': parent_width,
                'id_min': int(ids_cpu.min()) if rows else None,
                'id_max': int(ids_cpu.max()) if rows else None,
                'parent_unique_count': int(ids_cpu.unique().numel()),
                'empty_child_id_slots_from_adjacent_ids': int(adjacent_counts.eq(0).sum()),
                'child_slots_without_real_point_support': int(real_point_counts.eq(0).sum()),
                'empty_parent_id_slots': int(empty_parent.sum()),
                'empty_parent_zero_before_ffn': empty_zero, 'parent_padding_zero_before_ffn': pad_zero,
                'semantics': 'All original child slots counted; internal empty FFN bias preserved; padding prefix excluded'})
            assert rows <= child_feats.shape[1] and empty_zero and pad_zero
        delta = (output.detach().cpu().double() - reference).abs()
        record['reference_abs_max'] = float(delta.max()) if delta.numel() else 0.0
        record['reference_tolerance'] = MANIFEST['tolerance']
        assert record['reference_abs_max'] <= MANIFEST['tolerance'], 'Frozen fixed-mean reference tolerance failed; do not relax'
        means.append(record)
        watch(child_feats, record, 'native_child_gradients')
        watch(output, record, 'native_output_gradients')
        return output
    if candidate:
        hierarchy.refined_parent_mean = observed_mean

    original_csort = att._cross_scale_orth_loss
    def observed_csort(coarse_tokens, fine_tokens, child_maps):
        raw = state['raw_refs']
        pair = next((i for i in range(2) if coarse_tokens is raw[i+1] and fine_tokens is raw[i]), None)
        assert pair is not None, 'CSORT must receive the original raw-bank objects'
        before = fingerprint(torch, [coarse_tokens.detach().clone(), fine_tokens.detach().clone()])
        value = original_csort(coarse_tokens, fine_tokens, child_maps)
        assert fingerprint(torch, [coarse_tokens, fine_tokens]) == before
        csort.append({'forward': state['forward_index'], 'pair': pair,
            'original_raw_objects': True, 'input_sha256': before, 'output': logvar(value), 'original_calls': 1})
        return value
    replace(att, '_cross_scale_orth_loss', observed_csort)

    original_readback = att._cluster_to_points
    def observed_readback(point_feats, refined, ids_list, point_mask):
        record = {'forward': state['forward_index'], 'levels': [summary(x) for x in refined],
            'refined_sha256': fingerprint(torch, [x.detach().clone() for x in refined]),
            'ids_sha256': fingerprint(torch, ids_list), 'point_padding': summary(point_mask)}
        raw = state['raw_refs']
        expected_fine = raw[0].detach() + state['ffn_output_snapshots'][0]
        record['fine_original_residual_abs_max'] = float((refined[0].detach()-expected_fine).abs().max())
        assert record['fine_original_residual_abs_max'] == 0.0
        state['coarse_graph'] = refined[2]
        state['probe_ids'] = ids_list
        output = original_readback(point_feats, refined, ids_list, point_mask)
        record['output'] = summary(output)
        readbacks.append(record)
        watch(output, record, 'native_point_message_gradients')
        return output
    replace(att, '_cluster_to_points', observed_readback)

    def grad_state():
        return {'sha256': fingerprint(torch, {n:p.grad for n,p in model.named_parameters()}),
            'identities_versions': {n:None if p.grad is None else [id(p.grad), p.grad._version]
                for n,p in model.named_parameters()}}

    def dependency_probe():
        h2 = state.pop('coarse_graph')
        ids_list = state.pop('probe_ids')
        cpu_rng = torch.get_rng_state().clone()
        cuda_rng = torch.cuda.get_rng_state().clone()
        grads_before = grad_state()
        optimizer_before = fingerprint(torch, optimizer.state_dict())
        scheduler_before = fingerprint(torch, scheduler.state_dict())
        terms, supports = [], []
        channels = torch.arange(1, h2.shape[-1]+1, device=h2.device, dtype=h2.dtype)/(h2.shape[-1]+1)
        for b in range(h2.shape[0]):
            ids0 = ids_list[0][b].long()
            ids1 = ids_list[1][b].long()
            ids2 = ids_list[2][b].long()
            supported = torch.unique(ids2[ids1[ids0]], sorted=True)
            assert supported.numel() > 0
            weights = ((supported.to(h2.dtype)+1)/(h2.shape[1]+1)).unsqueeze(-1)*channels.unsqueeze(0)
            terms.append((h2[b, supported]*weights).sum()*((b+1)/(h2.shape[0]+1)))
            supports.append({'batch': b, 'coarse_ids_reached_by_real_points': supported.detach().cpu().tolist()})
        scalar = sum(terms)
        parameters = (att.cluster_ffn[0][0].weight, att.cluster_ffn[1][0].weight)
        previous_flag = state['probe_active']
        try:
            state['probe_active'] = True
            derivatives = torch.autograd.grad(scalar, parameters, retain_graph=True,
                allow_unused=True, create_graph=False)
        finally:
            state['probe_active'] = previous_flag
        grads_after = grad_state()
        record = {'forward': state['forward_index'], 'scope': 'Fixed nonconstant token-channel probe of coarse tokens actually reached by composed point IDs',
            'support': supports, 'scalar': logvar(scalar),
            'fine_ffn_first_weight_gradient': summary(derivatives[0]) if derivatives[0] is not None else None,
            'middle_ffn_first_weight_gradient': summary(derivatives[1]) if derivatives[1] is not None else None,
            'parameter_grad_state_unchanged': grads_before == grads_after,
            'parameter_grad_sha256_before': grads_before['sha256'], 'parameter_grad_sha256_after': grads_after['sha256'],
            'optimizer_state_unchanged': optimizer_before == fingerprint(torch, optimizer.state_dict()),
            'scheduler_state_unchanged': scheduler_before == fingerprint(torch, scheduler.state_dict()),
            'cpu_rng_unchanged': bool(torch.equal(cpu_rng, torch.get_rng_state())),
            'cuda_rng_unchanged': bool(torch.equal(cuda_rng, torch.cuda.get_rng_state())),
            'mechanism_expectation': 'candidate finite nonzero; control both structurally unused',
            'autograd_grad_only': True, 'retain_graph': True, 'probe_backward_or_step_called': False}
        probes.append(record)
        assert all(record[key] for key in ('parameter_grad_state_unchanged','optimizer_state_unchanged',
            'scheduler_state_unchanged','cpu_rng_unchanged','cuda_rng_unchanged'))
        if candidate:
            assert all(g is not None and bool(torch.isfinite(g).all()) and bool(g.abs().max()>0) for g in derivatives), 'Frozen dependency probe failed; no probe/seed selection'
        else:
            assert all(g is None for g in derivatives), 'M95 control unexpectedly depends on fine/middle FFNs'
        del derivatives, scalar, h2

    def native_input(owner, values):
        batch = values[0]
        state['forward_index'] += 1
        state['ffn_output_snapshots'] = {}
        batches.append({'sha256': fingerprint(torch, batch),
            'scan_ids': [str(x) for x in batch.get('scan_ids', [])],
            'ann_ids': [int(x) for x in batch.get('ann_ids', [])],
            'scenes_len': [int(x) for x in batch.get('scenes_len', [])]})

    def native_output(owner, values, output):
        loss, variables = output
        result.setdefault('loss_tensor_observations', []).append(logvar(loss))
        result.setdefault('loss_component_observations', []).append({k:logvar(v) for k,v in variables.items()})
        assert loss.numel() == 1 and bool(torch.isfinite(loss).all())
        losses.append(float(loss.detach().cpu()))
        result['native_loss_forwards'] += 1
        raw_record = state['raw_record']
        raw_record['unchanged_after_full_forward'] = fingerprint(torch, state['raw_refs']) == raw_record['raw_sha256']
        raw_record['ids_unchanged_after_full_forward'] = fingerprint(torch, bank.cluster_ids_list) == raw_record['id_sha256']
        raw_record['maps_unchanged_after_full_forward'] = fingerprint(torch, bank.child_cluster_maps) == raw_record['map_sha256']
        assert raw_record['unchanged_after_full_forward'] and raw_record['ids_unchanged_after_full_forward'] and raw_record['maps_unchanged_after_full_forward']
        dependency_probe()
        state.pop('raw_refs', None)
        state.pop('raw_record', None)
        state['ffn_output_snapshots'].clear()

    def before_step(owner, args, kwargs):
        assert not state['probe_active']
        observed = {n:p.grad for n,p in model.named_parameters() if p.grad is not None}
        bad = [n for n,g in observed.items() if not bool(torch.isfinite(g).all())]
        record = {'gradient_tensor_count': len(observed), 'nonfinite_parameter_names': bad,
            'all_observed_gradients_finite': bool(observed) and not bad,
            'ffn_by_level': {}, 'optimizer_step_completed': False,
            'ffn_before_step_hash': {level:fingerprint(torch, {n:p.detach() for n,p in ps.items()}) for level,ps in tracked.items()}}
        steps.append(record)
        assert observed and not bad
        for level, parameters in tracked.items():
            weights = {n:summary(p.grad) if p.grad is not None else None for n,p in parameters.items() if n.endswith('weight')}
            record['ffn_by_level'][str(level)] = weights
            assert weights and all(g is not None and g['finite'] for g in weights.values())
            assert any(g['abs_max'] > 0 for g in weights.values())
        result['native_criterion_backwards'] += 1

    def after_step(owner, args, kwargs):
        record = steps[-1]
        record['optimizer_step_completed'] = True
        record['ffn_after_step_hash'] = {level:fingerprint(torch, {n:p.detach() for n,p in ps.items()}) for level,ps in tracked.items()}
        assert all(record['ffn_before_step_hash'][level] != record['ffn_after_step_hash'][level] for level in range(3))
        result['optimizer_steps'] += 1

    hooks.extend([model.register_forward_pre_hook(native_input), model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step), optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False, losses=losses, steps=steps, batches=batches,
        ffn_calls=calls, refined_parent_mean_calls=means, raw_bank_observations=rawbanks,
        csort_raw_input_observations=csort, hcg_readbacks=readbacks, coarse_dependency_probes=probes,
        native_dataloader_config=dict(cfg.dataloader.train),
        smoke_memory_scope='Two-step native train including diagnostic hooks, fixed-mean reference and autograd.grad dependency probes; not pure TRAIN memory',
        pure_training_peak_memory='UNKNOWN; requires a separate no-observer/no-probe native training process pair',
        dependency_probe_scope='Smoke only; never installed in resource mode; does not change model inputs, loss, .grad, optimizer or RNG')
    logger = logging.getLogger('hrc-native-smoke')
    logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
    writer = train.SummaryWriter(cfg.work_dir)
    torch.cuda.reset_peak_memory_stats()
    try:
        train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)
        torch.cuda.synchronize()
    finally:
        if candidate:
            hierarchy.refined_parent_mean = original_mean
        for owner, name in reversed(replacements):
            delattr(owner, name)
        for hook in hooks:
            hook.remove()
        state.clear()
        writer.flush(); writer.close()
    assert len(losses) == len(steps) == len(batches) == len(probes) == result['optimizer_steps'] == 2
    assert len(calls) == 6 and len(rawbanks) == len(readbacks) == 2 and len(csort) == 4
    for forward in (1, 2):
        assert [entry['level'] for entry in calls if entry['forward']==forward] == [0,1,2]
        assert sum(entry['forward']==forward for entry in means) == (2 if candidate else 0)
    for record in calls:
        for key in ('native_input_gradients','native_output_gradients'):
            assert record.get(key) and all(g['finite'] for g in record[key])
    for record in means:
        for key in ('native_child_gradients','native_output_gradients'):
            assert record.get(key) and all(g['finite'] and g['abs_max']>0 for g in record[key])
    assert all(record.get('native_point_message_gradients') and all(g['finite'] and g['abs_max']>0 for g in record['native_point_message_gradients']) for record in readbacks)
    final_hash = {level:fingerprint(torch, {n:p.detach() for n,p in parameters.items()}) for level,parameters in tracked.items()}
    assert all(final_hash[level] != initial_hash[level] for level in range(3))
    verify()
    result.update(execution_completed=True, native_data_loaded=True,
        native_train_function_executed=True, backward_finite=True,
        intended_path_observed=candidate and len(means)==4,
        new_operator_parameters=0 if candidate else None,
        native_ffn_initial_hash_by_level=initial_hash, native_ffn_after_hash_by_level=final_hash,
        native_ffn_each_level_updated=True, observer_readout_complete=True,
        native_smoke_checks_passed=True, wrappers_and_hooks_restored=True,
        training_checkpoint_saved=False, native_smoke_training=True, new_training=0,
        optimizer_type=type(optimizer).__name__, scheduler_type=type(scheduler).__name__,
        smoke_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        smoke_peak_reserved_bytes=torch.cuda.max_memory_reserved(), after=observe())


def resources(torch, gorilla, cfg, model, result):
    import numpy as np
    from framework.dataset import build_dataset, build_dataloader
    import fvcore
    from fvcore.nn import FlopCountAnalysis
    profile_cfg = copy.deepcopy(cfg.data.val)
    profile_cfg.lang_num_max = 1
    dataset = build_dataset(profile_cfg, logging.getLogger('mdc-resource-only'))
    loader_cfg = copy.deepcopy(cfg.dataloader.val)
    loader_cfg.batch_size = 1
    loader_cfg.num_workers = 0
    loader_cfg.persistent_workers = False
    gorilla.set_random_seed(1999)
    sample = next(iter(build_dataloader(dataset, training=False, **loader_cfg)))
    assert len(sample['ann_ids']) == len(sample['scan_ids']) == 1
    signature = fingerprint(torch, sample)
    handlers = {name: sha(Path(importlib.import_module('fvcore.nn.' + name).__file__))
        for name in ('flop_count', 'jit_analysis', 'jit_handles')}
    expected = {'flop_count': 'b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba',
        'jit_analysis': '110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31',
        'jit_handles': 'ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129'}
    assert handlers == expected, 'Historical profiler handlers must not change'
    model.eval()
    flags = {key: value.requires_grad for key, value in model.named_parameters()}
    with torch.no_grad():
        analysis = FlopCountAnalysis(model, (sample, 'predict'))
        analysis.unsupported_ops_warnings(False)
        analysis.uncalled_modules_warnings(False)
        total = analysis.total()
        result['native_predict_calls'] += 1
        result['profile'] = {'flops': float(total), 'flops_g': float(total / 1e9),
            'within10G': bool(total <= 10e9), 'fvcore_version': fvcore.__version__,
            'profiler_file_sha256': handlers, 'by_operator': {key: float(value) for key, value in analysis.by_operator().items()},
            'unsupported_ops': dict(analysis.unsupported_ops())}
        for _ in range(20):
            model(sample, mode='predict')
            result['native_predict_calls'] += 1
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        times = []
        for _ in range(100):
            torch.cuda.synchronize()
            start = time.perf_counter()
            prediction = model(sample, mode='predict')
            torch.cuda.synchronize()
            times.append((time.perf_counter() - start) * 1000)
            result['native_predict_calls'] += 1
        assert prediction['piou'] and all(bool(torch.isfinite(value).all()) for value in prediction['piou'])
    assert fingerprint(torch, sample) == signature
    assert {key: value.requires_grad for key, value in model.named_parameters()} == flags
    verify()
    result.update(execution_completed=True, input_sha256=signature, scan_ids=sample['scan_ids'],
        ann_ids=sample['ann_ids'], parameters=sum(value.numel() for value in model.parameters()),
        batch_size=1, lang_num_max=1, warmup=20, repeat=100, median_ms=float(np.median(times)),
        p90_ms=float(np.percentile(times, 90)), measurements_ms=times,
        peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved(),
        full_optimizer_training_peak='UNKNOWN; separate resource process, no optimizer or scheduler steps',
        original_no_cluster_resource_delta='UNKNOWN; no-cluster baseline not measured',
        validation_accuracy_evaluated_for_selection=False, parameter_flags_preserved=True,
        source_body_executed_without_replacement=True, after=observe())



def json_safe(value):
    import math
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k):json_safe(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [json_safe(v) for v in value]
    return value


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--lease',required=True)
    parser.add_argument('--mode',choices=['smoke','resources'],required=True)
    parser.add_argument('--target',choices=['candidate','champion'],required=True)
    args=parser.parse_args()
    result={'execution_completed':False,'mode':args.mode,'target':args.target,
        'candidate_id':MANIFEST.get('candidate_id'),'code_commit':MANIFEST.get('code_commit'),
        'goal_sha256':MANIFEST.get('goal_sha256'),'optimizer_steps':0,'native_loss_forwards':0,
        'native_criterion_backwards':0,'native_predict_calls':0,'new_training':0,
        'native_model_and_yaml_unchanged':True,'source_scope':'Exact native HRC or original M95, original backbone pretrain and native train loop'}
    try:
        result['before']=acquire(args.lease)
        torch,gorilla,cfg,model,qualified,train,optimizer,scheduler=setup(args.target,args.mode,result)
        if args.mode=='smoke':
            smoke(torch,gorilla,cfg,model,qualified,train,optimizer,scheduler,result)
        else:
            resources(torch,gorilla,cfg,model,result)
    except BaseException as error:
        import traceback
        result.update(error_type=type(error).__name__,error=str(error))
        traceback.print_exc()
        raise
    finally:
        try:
            save(args.mode+'_'+args.target+'_result.json',json_safe(result))
        finally:
            release()
            print(json.dumps({'execution_completed':result['execution_completed'],
                'optimizer_steps':result['optimizer_steps'],'result_mode':args.mode,'target':args.target}),flush=True)


if __name__=='__main__':
    main()
