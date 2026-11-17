"""Native two-step MDC training smoke and unchanged-handler resource comparison."""
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
    base_name = NAME[:-4] if NAME.endswith('_mdc') else NAME
    candidate_name = MANIFEST.get('candidate_name', base_name + '_mdc')
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
    from framework.dataset import build_dataset, build_dataloader
    logger = logging.getLogger('mdc-native-smoke')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler(sys.stderr))
    dataset = build_dataset(cfg.data.train, logger)
    # Preserve native batch size, four workers, shuffle, drop_last, augmentation and collation.
    loader = build_dataloader(dataset, dist=cfg.dist, **cfg.dataloader.train)
    assert loader.batch_size == 2 and loader.num_workers == 4 and loader.drop_last
    assert loader.persistent_workers

    class TwoNativeBatches:
        def __init__(self, native):
            self.native = native
            self.sampler = native.sampler
        def __len__(self):
            return 2
        def __iter__(self):
            yield from itertools.islice(iter(self.native), 2)

    convolution = getattr(model.dec.cluster_att, 'coarse_channel_attention', None)
    new_parameters = {str(level)+'.'+name:p for level in (0,2) for name,p in model.dec.cluster_att.cluster_ffn[level].named_parameters()} if convolution is not None else {}
    initial_module_hash = fingerprint(torch, {name: p.detach() for name, p in new_parameters.items()})
    calls = []
    edge_backwards = []
    result['operator_backward_edges'] = edge_backwards
    losses = []
    batches = []
    steps = []
    hooks = []

    def tensors(value):
        if torch.is_tensor(value):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from tensors(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                yield from tensors(item)

    def tensor_summary(value):
        finite = bool(torch.isfinite(value).all())
        return {'shape': list(value.shape), 'dtype': str(value.dtype),
            'requires_grad': bool(value.requires_grad),
            'finite': finite,
            'abs_max': (float(value.detach().float().abs().max().cpu()) if value.numel() else 0.0) if finite else None}

    def module_call(owner, values, output):
        inputs = list(tensors(values))
        outputs = list(tensors(output))
        record = {'input': [tensor_summary(x) for x in inputs],
            'output': [tensor_summary(x) for x in outputs], 'input_gradients': [], 'output_gradients': []}
        calls.append(record)
        assert all(x['finite'] for x in record['input'] + record['output'])
        for direction, values_list in [('input_gradients', inputs), ('output_gradients', outputs)]:
            for value in values_list:
                if value.requires_grad:
                    def capture_gradient(gradient, record=record, direction=direction):
                        record[direction].append(tensor_summary(gradient))
                        return None
                    value.register_hook(capture_gradient)

    def operator_backward(owner, grad_input, grad_output):
        record = {'fine_input': tensor_summary(grad_input[0]) if grad_input[0] is not None else None,
            'coarse_input': tensor_summary(grad_input[1]) if grad_input[1] is not None else None,
            'output': [tensor_summary(g) for g in grad_output if g is not None]}
        edge_backwards.append(record)
        assert record['fine_input'] and record['coarse_input']
        assert all(record[k]['finite'] and record[k]['abs_max'] > 0 for k in ('fine_input','coarse_input'))
        assert record['output'] and all(g['finite'] and g['abs_max'] > 0 for g in record['output'])

    def native_input(owner, values):
        batch = values[0]
        batches.append({'sha256': fingerprint(torch, batch),
            'scan_ids': [str(x) for x in batch.get('scan_ids', [])],
            'ann_ids': [int(x) for x in batch.get('ann_ids', [])],
            'scenes_len': [int(x) for x in batch.get('scenes_len', [])]})

    def native_output(owner, values, output):
        loss = output[0]
        result.setdefault('loss_component_observations', []).append({str(k): {'finite': bool(torch.isfinite(torch.as_tensor(v)).all()), 'value': float(v.detach()) if torch.is_tensor(v) else float(v) if bool(torch.isfinite(torch.as_tensor(v)).all()) else str(v)} for k,v in output[1].items()})
        result.setdefault('loss_tensor_observations', []).append({'shape':list(loss.shape),'numel':loss.numel(),'finite':bool(torch.isfinite(loss).all()),'value':float(loss.detach().cpu()) if bool(torch.isfinite(loss).all()) else None})
        assert loss.numel() == 1 and bool(torch.isfinite(loss).all()), 'Native loss must be one finite element'
        losses.append(float(loss.detach().cpu()))
        result['native_loss_forwards'] += 1

    def before_step(owner, args, kwargs):
        observed = {name: p.grad for name, p in model.named_parameters() if p.grad is not None}
        nonfinite = [name for name, grad in observed.items() if not bool(torch.isfinite(grad).all())]
        new = {name: {'present': p.grad is not None,
            'finite': bool(torch.isfinite(p.grad).all()) if p.grad is not None else False,
            'abs_max': float(p.grad.detach().abs().max().cpu())
                if p.grad is not None and bool(torch.isfinite(p.grad).all()) else None}
            for name, p in new_parameters.items()}
        steps.append({'gradient_tensor_count': len(observed), 'nonfinite_parameter_names': nonfinite,
            'all_observed_gradients_finite': bool(observed) and not nonfinite,
            'affected_native_ffn_gradients': new, 'optimizer_step_completed': False})
        result['native_criterion_backwards'] += 1
        assert observed and not nonfinite, 'Native backward produced nonfinite gradients'
        assert all(x['present'] and x['finite'] for x in new.values()), 'New-module gradients absent/nonfinite'
        assert not new or any(x['abs_max'] > 0 for x in new.values()), 'New module is disconnected from native loss'

    def after_step(owner, args, kwargs):
        steps[-1]['optimizer_step_completed'] = True
        result['optimizer_steps'] += 1

    if convolution is not None:
        hooks.append(convolution.register_forward_hook(module_call))
        hooks.append(convolution.register_full_backward_hook(operator_backward))
    hooks.extend([model.register_forward_pre_hook(native_input), model.register_forward_hook(native_output),
        optimizer.register_step_pre_hook(before_step), optimizer.register_step_post_hook(after_step)])
    writer = train.SummaryWriter(cfg.work_dir)
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), '
        'optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python', 'tools/train.py', str(result['runtime_config_path']),
            '--num_gpus', '1', '--skip_validate'],
        smoke_bound='Only the first two batches of the native loader; not a full epoch or formal training run',
        native_dataloader_config=dict(cfg.dataloader.train),
        native_data_loaded=False, losses=losses, steps=steps, batches=batches, coarse_channel_calls=calls)
    torch.cuda.reset_peak_memory_stats()
    try:
        # The original native train function performs zero_grad, loss.backward, clipping and optimizer.step.
        train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)
        torch.cuda.synchronize()
    finally:
        for hook in hooks:
            hook.remove()
        writer.flush()
        writer.close()
    assert len(batches) == len(losses) == len(steps) == result['optimizer_steps'] == 2
    gradients = [g for call in calls for key in ('input_gradients', 'output_gradients') for g in call[key]]
    assert convolution is None or (calls and len(calls) == 2 and len(edge_backwards) == 2)
    assert convolution is None or (gradients and all(g['finite'] for g in gradients))
    assert convolution is None or all(call['output_gradients'] and any(g['abs_max'] > 0 for g in call['output_gradients']) for call in calls)
    final_module_hash = fingerprint(torch, {name: p.detach() for name, p in new_parameters.items()})
    assert convolution is None or final_module_hash != initial_module_hash, 'Native optimizer did not update the new module'
    verify()
    result.update(execution_completed=True, new_training=0, native_smoke_training=True,
        native_data_loaded=True, native_train_function_executed=True,
        backward_finite=all(x['all_observed_gradients_finite'] for x in steps),
        intended_path_observed=True, affected_native_ffn_parameters_updated=True,
        affected_ffn_initial_sha256=initial_module_hash, affected_ffn_after_two_steps_sha256=final_module_hash,
        new_operator_parameters=sum(p.numel() for p in convolution.parameters()),
        parameter_tracking_scope='Existing fine/coarse FFNs; zero new CGCA parameters',
        optimizer_type=type(optimizer).__name__, scheduler_type=type(scheduler).__name__,
        scheduler_epoch_end_calls=1, validation_forwards=0, training_checkpoint_saved=False,
        smoke_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        smoke_peak_reserved_bytes=torch.cuda.max_memory_reserved(), after=observe())
    # Drop the iterator owner so native persistent workers exit with this bounded process.
    del loader


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lease', required=True)
    parser.add_argument('--mode', choices=('resources', 'smoke'), required=True)
    parser.add_argument('--target', choices=('champion', 'candidate'), required=True)
    args = parser.parse_args()
    result = {'execution_completed': False, 'mode': args.mode, 'target': args.target,
        'candidate_id': MANIFEST.get('candidate_id'), 'goal_sha256': MANIFEST.get('goal_sha256'),
        'code_commit': MANIFEST.get('code_commit'),
        'scientific_admission': False, 'new_training': 0, 'optimizer_steps': 0,
        'native_predict_calls': 0, 'native_loss_forwards': 0, 'native_criterion_backwards': 0,
        'source_scope': 'Native backbone-pretrain initialization and complete unmodified native train function; no trained M95 checkpoint'}
    try:
        result['before'] = acquire(args.lease)
        values = setup(args.target, args.mode, result)
        torch, gorilla, cfg, model, qualified, train, optimizer, scheduler = values
        if args.mode == 'resources':
            resources(torch, gorilla, cfg, model, result)
        else:
            smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result)
    except BaseException as error:
        import traceback
        traceback.print_exc()
        result.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        try:
            save(args.mode + '_' + args.target + '_result.json', result)
        finally:
            release()
            print(json.dumps({'execution_completed': result['execution_completed'],
                'mode': args.mode, 'target': args.target, 'optimizer_steps': result['optimizer_steps'],
                'result_file': str(STAGE / (args.mode + '_' + args.target + '_result.json'))}), flush=True)


if __name__ == '__main__':
    main()
