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
    candidate_name = MANIFEST.get('candidate_name', base_name + '_hap')
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
    """Original native train loop; HAP observers never change model algebra."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger('hap-native-smoke'))
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

    operator = getattr(model.dec.cluster_att, 'affine_prolongation', None)
    if result['target'] == 'candidate':
        assert operator is not None
        assert sum(p.numel() for p in operator.parameters()) == 0
    tracked = {level: dict(model.dec.cluster_att.cluster_ffn[level].named_parameters())
        for level in range(3)}
    initial_hash = {level: fingerprint(torch, {n:p.detach() for n,p in params.items()})
        for level, params in tracked.items()}
    calls, edges, inverses, losses, steps, batches = [], [], [], [], [], []
    hooks = []
    state = {'inside_operator': False}
    original_pinv = torch.linalg.pinv

    def summary(value):
        finite = bool(torch.isfinite(value).all())
        return {'shape': list(value.shape), 'dtype': str(value.dtype),
            'finite': finite, 'nonfinite_count': int((~torch.isfinite(value)).sum()),
            'abs_max': float(value.detach().float().abs().max().cpu())
                if value.numel() and finite else (0.0 if not value.numel() else None)}

    def logvar(value):
        tensor = torch.as_tensor(value).detach()
        info = summary(tensor)
        info['value'] = float(tensor.cpu()) if info['finite'] and tensor.numel() == 1 else None
        return info

    def observed_pinv(*args, **kwargs):
        # Smoke observer only. Preserve exactly one original call and return object.
        entry = None
        if state['inside_operator']:
            gram = args[0]
            entry = {'actual_input_shape': list(gram.shape),
                'actual_input_dtype': str(gram.dtype),
                'positional_arguments_after_input': len(args) - 1,
                'provided_kwargs': {k: v if isinstance(v, (str,int,float,bool,type(None)))
                    else repr(v) for k,v in kwargs.items()},
                'provided_tolerances': 'default; no observer-supplied atol/rtol/rcond',
                'pinv_retained_rank': 'UNOBSERVED; diagnostic matrix_rank is a separate API',
                'original_calls_per_observation': 0, 'native_pinv_completed': False,
                'observer_readout_complete': False}
            inverses.append(entry)
            try:
                entry['actual_input'] = summary(gram)
            except Exception as error:
                entry['observer_input_error'] = {'type':type(error).__name__, 'message':str(error)}
        if entry is not None:
            entry['original_calls_per_observation'] = 1
        try:
            inverse = original_pinv(*args, **kwargs)
        except BaseException as error:
            if entry is not None:
                entry['native_pinv_exception'] = {'type':type(error).__name__, 'message':str(error)}
            raise
        if entry is not None:
            entry['native_pinv_completed'] = True
            try:
                entry['actual_return'] = summary(inverse)
            except Exception as error:
                entry['observer_return_error'] = {'type':type(error).__name__, 'message':str(error)}
            assert gram.shape[-2:] == (3,3)
            if 'actual_input' in entry:
                assert entry['actual_input']['finite']
            if 'actual_return' in entry:
                assert entry['actual_return']['finite']
            try:
                with torch.no_grad():
                    eigen = torch.linalg.eigvalsh(gram)
                    rank = torch.linalg.matrix_rank(gram, hermitian=True)
                    projection = gram @ inverse
                    entry['diagnostic_eigenvalues'] = eigen.detach().cpu().tolist()
                    entry['diagnostic_matrix_rank_default_api'] = rank.detach().cpu().tolist()
                    entry['diagnostic_matrix_rank_counts'] = {
                        str(k): int(rank.eq(k).sum()) for k in range(4)}
                    entry['symmetry_abs_max'] = float((gram - gram.transpose(-2,-1)).abs().max())
                    entry['G_Gplus_trace'] = projection.diagonal(dim1=-2,dim2=-1).sum(-1).cpu().tolist()
                    entry['G_Gplus_idempotence_abs_max'] = float((projection @ projection - projection).abs().max())
                    entry['spectrum_scope'] = 'Additional diagnostic computation on actual G; not backend pinv internals'
            except Exception as error:
                entry['observer_spectrum_error'] = {'type':type(error).__name__, 'message':str(error)}
            entry['observer_readout_complete'] = all(key in entry for key in
                ('actual_input','actual_return','spectrum_scope')) and not any(key in entry for key in
                ('observer_input_error','observer_return_error','observer_spectrum_error'))
        return inverse

    def enter_operator(owner, values):
        state['inside_operator'] = True

    def observe_operator(owner, values, outputs):
        state['inside_operator'] = False
        record = {'inputs': [summary(values[i]) for i in range(3)],
            'outputs': [summary(value) for value in outputs]}
        calls.append(record)
        assert len(outputs) == 2
        assert all(item['finite'] for item in record['inputs'] + record['outputs'])

    def centered_gradient(gradient, level):
        bank = model.dec.cluster_bank
        maximum, eligible_groups = 0.0, 0
        for b in range(gradient.shape[0]):
            ids = bank.cluster_ids_list[level + 1][b].long()
            occupied = bank.affine_occupied[level][b]
            xyz = bank.affine_positions[level][b].detach().float()
            rows = ids.numel()
            parent_count = bank.affine_positions[level + 1][b].shape[0]
            count = xyz.new_zeros(parent_count)
            count.index_add_(0, ids, occupied.to(xyz.dtype))
            center = xyz.new_zeros(parent_count, 3)
            center.index_add_(0, ids, xyz * occupied.unsqueeze(-1))
            center = center / count.clamp_min(1).unsqueeze(-1)
            delta = (xyz - center[ids]) * occupied.unsqueeze(-1)
            energy = xyz.new_zeros(parent_count)
            energy.index_add_(0, ids, delta.square().sum(-1))
            eligible = count.gt(1) & energy.gt(0)
            eligible_groups += int(eligible.sum())
            g = gradient[b, :rows]
            sums = g.new_zeros(parent_count, g.shape[-1])
            sums.index_add_(0, ids, g * occupied.unsqueeze(-1))
            mean = sums / count.clamp_min(1).unsqueeze(-1)
            selected = occupied & eligible[ids]
            if bool(selected.any()):
                maximum = max(maximum, float((g - mean[ids])[selected].abs().max()))
        return {'eligible_nonconstant_geometry_groups': eligible_groups,
            'group_centered_gradient_abs_max': maximum,
            'scope': 'Only occupied groups with >1 child and nonzero geometric energy; zero-rank groups may be zero'}

    def operator_backward(owner, grad_input, grad_output):
        record = {'inputs': [summary(grad_input[i]) if grad_input[i] is not None else None
                for i in range(3)],
            'outputs': [summary(g) for g in grad_output if g is not None]}
        edges.append(record)
        assert len(record['outputs']) == 2 and all(g['finite'] for g in record['outputs'])
        assert all(g is not None and g['finite'] for g in record['inputs'])
        for level, name in [(0,'fine'), (1,'middle')]:
            info = centered_gradient(grad_input[level], level)
            record[name + '_nonconstant_readout'] = info
            assert info['eligible_nonconstant_geometry_groups'] > 0
            assert info['group_centered_gradient_abs_max'] > 0
        assert record['inputs'][2]['abs_max'] > 0, 'No native-loss gradient through new parent path'
        assert all(g['abs_max'] > 0 for g in record['outputs'])

    def native_input(owner, values):
        batch = values[0]
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

    def before_step(owner, args, kwargs):
        observed = {n:p.grad for n,p in model.named_parameters() if p.grad is not None}
        bad = [n for n,g in observed.items() if not bool(torch.isfinite(g).all())]
        record = {'gradient_tensor_count': len(observed), 'nonfinite_parameter_names': bad,
            'all_observed_gradients_finite': bool(observed) and not bad,
            'ffn_by_level': {}, 'optimizer_step_completed': False}
        steps.append(record)
        assert observed and not bad
        for level, params in tracked.items():
            weights = {n:summary(p.grad) if p.grad is not None else None
                for n,p in params.items() if n.endswith('weight')}
            record['ffn_by_level'][str(level)] = weights
            assert weights and all(g is not None and g['finite'] for g in weights.values())
            assert any(g['abs_max'] > 0 for g in weights.values())
            # Centered fine/middle output-bias gradients may legitimately be zero.
        result['native_criterion_backwards'] += 1

    def after_step(owner, args, kwargs):
        steps[-1]['optimizer_step_completed'] = True
        result['optimizer_steps'] += 1

    if operator is not None:
        hooks.extend([operator.register_forward_pre_hook(enter_operator),
            operator.register_forward_hook(observe_operator),
            operator.register_full_backward_hook(operator_backward)])
    hooks.extend([model.register_forward_pre_hook(native_input),
        model.register_forward_hook(native_output), optimizer.register_step_pre_hook(before_step),
        optimizer.register_step_post_hook(after_step)])
    result.update(actual_train_command='tools.train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)',
        native_train_cli_reference=['python','tools/train.py',result['runtime_config_path'],'--num_gpus','1','--skip_validate'],
        native_data_loaded=False, losses=losses, steps=steps, batches=batches,
        affine_operator_calls=calls, affine_operator_backward_edges=edges,
        actual_pinv_observations=inverses, native_dataloader_config=dict(cfg.dataloader.train),
        pinv_observer_scope='Smoke only; original function called once with unchanged args/kwargs and original Tensor returned; never used in resource mode')
    logger = logging.getLogger('hap-native-smoke')
    logger.addHandler(logging.StreamHandler(sys.stderr)) if not logger.handlers else None
    writer = train.SummaryWriter(cfg.work_dir)
    torch.cuda.reset_peak_memory_stats()
    try:
        if operator is not None:
            torch.linalg.pinv = observed_pinv
        train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)
        torch.cuda.synchronize()
    finally:
        torch.linalg.pinv = original_pinv
        state['inside_operator'] = False
        for hook in hooks:
            hook.remove()
        writer.flush()
        writer.close()
    assert torch.linalg.pinv is original_pinv
    assert len(losses) == len(steps) == len(batches) == result['optimizer_steps'] == 2
    final_hash = {level:fingerprint(torch, {n:p.detach() for n,p in params.items()})
        for level,params in tracked.items()}
    assert all(final_hash[level] != initial_hash[level] for level in range(3))
    if operator is not None:
        assert len(calls) == len(edges) == 2 and inverses
        assert all(item['original_calls_per_observation'] == 1 and
            item['native_pinv_completed'] for item in inverses)
    result['native_smoke_checks_passed'] = True
    result['observer_readout_complete'] = operator is None or all(
        item['observer_readout_complete'] for item in inverses)
    result['observer_failure_count'] = sum(not item['observer_readout_complete'] for item in inverses)
    if not result['observer_readout_complete']:
        result['failure_scope'] = 'diagnostic_observer'
        raise RuntimeError('HAP observer readout incomplete after native two-step checks; not a native pinv failure')
    verify()
    result.update(execution_completed=True, native_data_loaded=True,
        native_train_function_executed=True, backward_finite=True,
        intended_path_observed=operator is not None and len(edges) == 2,
        new_operator_parameters=0 if operator is not None else None,
        native_ffn_initial_hash_by_level=initial_hash, native_ffn_after_hash_by_level=final_hash,
        native_ffn_each_level_updated=True, pinv_original_restored=True,
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
        'native_model_and_yaml_unchanged':True,'source_scope':'Exact native HAP or original M95, original backbone pretrain and native train loop'}
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
