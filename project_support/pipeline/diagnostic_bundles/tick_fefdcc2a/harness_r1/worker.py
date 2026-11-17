"""Independent PCE full-model resources and unfrozen full-source controls."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1')
import argparse
import copy
import importlib
import importlib.util
import logging
from pathlib import Path
import sys
import time
from native_runtime import acquire, release, save, sha, verify, observe, fingerprint, MANIFEST, STAGE, ROOT, NAME


def setup(target):
    sys.path[:0] = [str(ROOT), str(ROOT / 'framework/lib')]
    from tools import train
    import torch
    import gorilla
    import yaml
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.75, 0)
    parent_cfg = yaml.safe_load(Path(MANIFEST['assets']['config_path']).read_text())
    candidate_cfg = yaml.safe_load((STAGE / 'candidate.yaml').read_text())
    assert parent_cfg == candidate_cfg, 'Candidate config differs from frozen parent settings'
    config_path = STAGE / 'candidate.yaml' if target == 'candidate' else Path(MANIFEST['assets']['config_path'])
    cfg = gorilla.Config.fromfile(str(config_path))
    assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
    gorilla.set_random_seed(1999)
    qualified = 'framework.model.Quard_model.' + NAME
    if target == 'candidate':
        qualified += '_pce'
        directory = STAGE / 'candidate_model'
        for name, expected in MANIFEST['candidate_source_hashes'].items():
            assert sha(directory / name) == expected
        spec = importlib.util.spec_from_file_location(qualified, directory / '__init__.py',
            submodule_search_locations=[str(directory)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(qualified)
    model = module.Network(**cfg.model)
    checkpoint = torch.load(MANIFEST['assets']['checkpoint'], map_location='cpu', weights_only=False, mmap=True)
    state = checkpoint['model']
    extra = set(state) - set(model.state_dict())
    assert extra <= {'text_encoder.embeddings.position_ids', 'text_encoder.embeddings.token_type_ids'}
    model.load_state_dict({key: value for key, value in state.items() if key not in extra}, strict=True)
    assert checkpoint['meta']['epoch'] == 16
    del state, checkpoint
    model.cuda().eval()
    return torch, gorilla, cfg, model, qualified


def resources(torch, gorilla, cfg, model, result):
    import numpy as np
    from framework.dataset import build_dataset, build_dataloader
    import fvcore
    from fvcore.nn import FlopCountAnalysis
    cfg.data.val.lang_num_max = 1
    dataset = build_dataset(copy.deepcopy(cfg.data.val), logging.getLogger('pce-resource-only'))
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
        full_optimizer_training_peak='UNKNOWN; no optimizer or scheduler steps',
        original_no_cluster_resource_delta='UNKNOWN; original baseline package/config not verified',
        validation_accuracy_evaluated_for_selection=False, parameter_flags_preserved=True,
        source_body_executed_without_replacement=True, after=observe())


def controls(torch, gorilla, cfg, model, qualified, result):
    import numpy as np
    from torch.utils.data import DataLoader, Subset
    from framework.dataset import build_dataset
    hierarchy = importlib.import_module(qualified + '.hier_postprocess')
    active = [layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active) == 1
    encoder = active[0]
    attention, bank = model.dec.cluster_att, model.dec.cluster_bank
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('pce-source-controls'))
    for scene in MANIFEST['cohort']:
        group = dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id'] == scene['scene_id']
        assert [{'object_id': str(value['object_id']), 'ann_id': str(value['ann_id'])}
            for value in group] == scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch = next(iter(DataLoader(Subset(dataset, [scene['group_index'] for scene in MANIFEST['cohort']]),
        batch_size=2, shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)))
    held = {}

    def clone(value):
        if torch.is_tensor(value):
            return value.detach().clone()
        if isinstance(value, dict):
            return {key: clone(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return type(value)(clone(item) for item in value)
        return copy.deepcopy(value)

    def capture_input(owner, values, keywords):
        held['args'], held['kwargs'] = clone(values), clone(keywords)
        held['contact_positions'] = clone(attention.physical_contact_positions)
        held['contact_edges'] = copy.deepcopy(attention.physical_contact_edges)

    def capture_output(owner, values, output):
        held['output'] = clone(output)

    hooks = [encoder.register_forward_pre_hook(capture_input, with_kwargs=True),
        encoder.register_forward_hook(capture_output)]
    gorilla.set_random_seed(1999)
    try:
        with torch.no_grad():
            loss, _ = model(copy.deepcopy(batch), mode='loss')
        result['native_loss_forwards'] += 1
        result['native_loss'] = float(loss.cpu())
    finally:
        for hook in hooks:
            hook.remove()
    args, kwargs = held['args'], held['kwargs']
    signature = fingerprint(torch, (args, kwargs))
    original_ids = clone(bank.cluster_ids_list)
    original_maps = clone(bank.child_cluster_maps)
    edges = copy.deepcopy(held['contact_edges'])
    positions = held['contact_positions'].detach().clone()
    result['source_input_sha256'] = signature
    result['distinct_train_scenes'] = len(MANIFEST['cohort'])
    result['unique_expressions'] = sum(len(scene['expression_ids']) for scene in MANIFEST['cohort'])
    result['frozen_bank_replacements'] = 0
    result['controls'] = {}

    def error(left, right):
        return float((left - right).abs().max().cpu())

    def execute(values=args, keywords=kwargs):
        hierarchy.reset_orth_accum()
        output = encoder(*values, **keywords)
        result['full_source_encoder_calls'] += 1
        return output

    with torch.no_grad():
        repetitions = []
        for _ in range(3):
            bank.cluster_ids_list, bank.child_cluster_maps = clone(original_ids), clone(original_maps)
            attention.physical_contact_edges, attention.physical_contact_positions = copy.deepcopy(edges), positions
            output = execute()
            repetitions.append({'language_max_abs': error(output[0], held['output'][0]),
                'inst_feats_max_abs': error(output[1], held['output'][1])})
        result['controls']['full_source_identity_repeats'] = repetitions
        width = args[2].shape[1]
        permutations, inverses = [], []
        for mask in args[3]:
            n = int((~mask).sum())
            permutation = torch.cat((torch.arange(n - 1, -1, -1, device=mask.device),
                torch.arange(n, width, device=mask.device)))
            permutations.append(permutation)
            inverses.append(torch.argsort(permutation))
        permuted_args = list(clone(args))
        for index in (2, 3, 5):
            permuted_args[index] = torch.stack([value[permutation] for value, permutation in zip(args[index], permutations)])
        bank.cluster_ids_list = clone(original_ids)
        for b, ids in enumerate(original_ids[0]):
            bank.cluster_ids_list[0][b] = ids[permutations[b][:len(ids)]]
        bank.child_cluster_maps = clone(original_maps)
        attention.physical_contact_positions = torch.stack([value[permutation] for value, permutation in zip(positions, permutations)])
        attention.physical_contact_edges = [inverses[b].cpu().numpy()[value] for b, value in enumerate(edges)]
        permuted = execute(tuple(permuted_args))
        restored = torch.stack([value[inverse] for value, inverse in zip(permuted[1], inverses)])
        result['controls']['full_source_row_permutation'] = {
            'language_max_abs': error(permuted[0], held['output'][0]),
            'inst_feats_max_abs': error(restored, held['output'][1])}
        bank.cluster_ids_list, bank.child_cluster_maps = clone(original_ids), clone(original_maps)
        attention.physical_contact_positions = positions
        attention.physical_contact_edges = [np.empty((0, 2), dtype=np.int64) for _ in edges]
        deleted = execute()
        original_gather = attention._cluster_to_points
        parent_path = ROOT / 'framework/model/Quard_model' / NAME / 'hier_postprocess.py'
        assert sha(parent_path) == MANIFEST['assets']['source_hashes']['hier_postprocess.py']
        spec = importlib.util.spec_from_file_location('verified_parent_hierarchy_control', parent_path)
        parent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(parent)
        import types
        attention._cluster_to_points = types.MethodType(parent.C2F_ClusterAttn_CTF_HCG._cluster_to_points, attention)
        try:
            parent_result = execute()
        finally:
            attention._cluster_to_points = original_gather
        result['controls']['deleted_contacts_vs_original_parent_gather'] = {
            'language_max_abs': error(deleted[0], parent_result[0]),
            'inst_feats_max_abs': error(deleted[1], parent_result[1])}
        attention.physical_contact_edges = copy.deepcopy(edges)
        assert fingerprint(torch, (args, kwargs)) == signature
        values = [item for record in repetitions for item in record.values()]
        values += list(result['controls']['full_source_row_permutation'].values())
        values += list(result['controls']['deleted_contacts_vs_original_parent_gather'].values())
        result['control_tolerance'] = MANIFEST['tolerance']
        result['all_full_source_controls_passed'] = max(values) <= MANIFEST['tolerance']
        result['maximum_full_source_control_error'] = max(values)
        result['native_feature_path_change_vs_deleted'] = error(held['output'][1], deleted[1])
    hierarchy.reset_orth_accum()
    model.train()
    model.zero_grad(set_to_none=True)
    gorilla.set_random_seed(1999)
    loss, _ = model(copy.deepcopy(batch), mode='loss')
    result['native_loss_forwards'] += 1
    assert bool(torch.isfinite(loss))
    loss.backward()
    result['native_criterion_backwards'] += 1
    gradients = [value.grad for value in model.parameters() if value.grad is not None]
    result['gradient_tensor_count'] = len(gradients)
    result['all_observed_gradients_finite'] = bool(gradients) and all(bool(torch.isfinite(value).all()) for value in gradients)
    verify()
    result.update(execution_completed=True, optimizer_steps=0, full_model_point_renumbering_tested=False,
        original_numeric_threshold_preserved=True, failure_scope='none' if result['all_full_source_controls_passed'] else 'implementation',
        source_scope='Full original hierarchy-bank reduction plus complete active encoder; upstream backbone not relabeled and FPS membership transported, not recomputed.',
        after=observe())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lease', required=True)
    parser.add_argument('--mode', choices=('resources', 'controls'), required=True)
    parser.add_argument('--target', choices=('champion', 'candidate'), required=True)
    args = parser.parse_args()
    result = {'execution_completed': False, 'mode': args.mode, 'target': args.target,
        'scientific_admission': False, 'new_training': 0, 'optimizer_steps': 0,
        'native_predict_calls': 0, 'native_loss_forwards': 0, 'native_criterion_backwards': 0,
        'full_source_encoder_calls': 0}
    try:
        result['before'] = acquire(args.lease)
        torch, gorilla, cfg, model, qualified = setup(args.target)
        if args.mode == 'resources':
            resources(torch, gorilla, cfg, model, result)
        else:
            assert args.target == 'candidate'
            controls(torch, gorilla, cfg, model, qualified, result)
    except BaseException as error:
        result.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        try:
            save(args.mode + '_' + args.target + '_result.json', result)
        finally:
            release()


if __name__ == '__main__':
    main()
