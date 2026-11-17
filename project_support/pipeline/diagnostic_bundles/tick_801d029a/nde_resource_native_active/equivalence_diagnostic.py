"""Bounded revision1 equivalence diagnostic, separate from native TRAIN2.

This entry point has no active binding in the preparation bundle. Its import
hits the same default-disabled native runtime before Torch or CUDA is imported.
A newly reviewed operational copy, actual manifest and lease are required.
It never calls worker.setup/smoke/resources and never uses native TRAIN data.
"""
import argparse
import copy
import importlib.util
import math
import pickle
import random
import sys
from pathlib import Path

from native_runtime import (
    MANIFEST, ROOT, STAGE, acquire, fingerprint, observe, release, save, sha,
    verify,
)


def load_private(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.HierarchicalDistributionEmbedding


def compare_revision1(torch, numpy, original_type, revision_type, channels,
                      optimizer_factory):
    """Compare a fixed constructed core fixture; no native training claims."""
    assert torch.cuda.is_initialized() and torch.cuda.device_count() == 1
    assert torch.cuda.current_device() == 0

    def rng_state():
        return {
            'python': random.getstate(), 'numpy': numpy.random.get_state(),
            'torch_cpu': torch.get_rng_state().clone(),
            'torch_visible_gpu0': torch.cuda.get_rng_state(0).clone(),
        }

    def restore_rng(value):
        random.setstate(value['python'])
        numpy.random.set_state(value['numpy'])
        torch.set_rng_state(value['torch_cpu'])
        torch.cuda.set_rng_state(value['torch_visible_gpu0'], 0)

    def rng_equal(left, right):
        return {
            key: (torch.equal(left[key], right[key]) if key.startswith('torch_')
                  else pickle.dumps(left[key]) == pickle.dumps(right[key]))
            for key in left
        }

    def seed():
        random.seed(1999)
        numpy.random.seed(1999)
        torch.manual_seed(1999)
        torch.cuda.manual_seed(1999)

    def tensor_record(name, left, right):
        record = {'name': name, 'left_is_None': left is None,
                  'right_is_None': right is None}
        if left is None or right is None:
            record['passed'] = left is None and right is None
            return record
        left, right = left.detach(), right.detach()
        record.update(shape=list(left.shape), dtype=str(left.dtype),
                      shape_equal=left.shape == right.shape,
                      dtype_equal=left.dtype == right.dtype,
                      both_finite=bool(torch.isfinite(left).all())
                      and bool(torch.isfinite(right).all()))
        if record['shape_equal'] and record['dtype_equal']:
            difference = (left - right).abs()
            record['max_abs_error'] = float(difference.max().item()) if difference.numel() else 0.0
            relative = difference / left.abs().clamp_min(torch.finfo(left.dtype).tiny)
            metric = float(relative.max().item()) if relative.numel() else 0.0
            record['max_relative_error_descriptive'] = metric if math.isfinite(metric) else None
        try:
            # Use Torch's dtype-default tolerance unchanged: no rtol/atol override.
            torch.testing.assert_close(left, right)
            record['passed'] = record['both_finite']
        except AssertionError as error:
            record.update(passed=False, assertion=str(error)[:1800])
        return record

    def fixture(core, kind):
        parameter = next(core.parameters())
        device, dtype = parameter.device, parameter.dtype
        def values(shape, offset):
            count = math.prod(shape)
            value = torch.arange(count, device=device, dtype=dtype)
            return ((value.remainder(29) - 14 + offset) / 29).reshape(shape)
        points = values((2, 9, channels), 0)
        normalized = [values((2, width, channels), level + 1)
                      for level, width in enumerate((5, 4, 3))]
        if kind == 'unequal_repeated_unsorted_support_and_empty_scene':
            mask = [[False, True, False, False, True, False, False, False, True],
                    [True] * 9]
            members = [[[3, 1, 3, 4, 1, 3], []],
                       [[0, 2, 0, 2, 1], []], [[0, 2, 1, 0], []]]
        else:
            assert kind == 'singleton_support_and_empty_scene'
            mask = [[True, False, True, True, True, True, True, True, True],
                    [True] * 9]
            members = [[[2], []], [[0, 0, 1, 0, 0], []], [[0, 2, 0, 0], []]]
        return {
            'points': points,
            'point_mask': torch.tensor(mask, device=device, dtype=torch.bool),
            'normalized': normalized,
            'cluster_ids_list': [
                [torch.tensor(scene, device=device, dtype=torch.long)
                 for scene in level] for level in members],
        }

    def run(core, data):
        points = data['points'].detach().clone().requires_grad_(True)
        banks = [value.detach().clone().requires_grad_(True)
                 for value in data['normalized']]
        analyses = []
        def analysis_hook(owner, args, output):
            analyses.append(output.detach().clone())
        hook = core.analysis.register_forward_hook(analysis_hook)
        try:
            outputs = core(points, data['point_mask'], banks,
                           data['cluster_ids_list'])
        finally:
            hook.remove()
        # Fixed identical vector cotangents; no random draws or task-loss claim.
        cotangents = [
            ((torch.arange(value.numel(), device=value.device, dtype=value.dtype)
              .remainder(17) - 8) / 17).reshape_as(value)
            for value in outputs]
        scalar = sum((value * cotangent).sum()
                     for value, cotangent in zip(outputs, cotangents))
        scalar.backward()
        return {
            'outputs': [value.detach().clone() for value in outputs],
            'analysis_outputs': analyses,
            'input_gradients': {'points': points.grad,
                                **{'normalized_' + str(i): value.grad
                                   for i, value in enumerate(banks)}},
            'parameter_gradients': {name: None if value.grad is None else
                                    value.grad.detach().clone()
                                    for name, value in core.named_parameters()},
            'scalar': float(scalar.detach().item()),
        }

    initial_rng = rng_state()
    cases = []
    try:
        for kind in ('unequal_repeated_unsorted_support_and_empty_scene',
                     'singleton_support_and_empty_scene'):
            seed()
            original = original_type(channels).cuda()
            original_rng = rng_state()
            seed()
            revision = revision_type(channels).cuda()
            revision_rng = rng_state()
            init_original, init_revision = original.state_dict(), revision.state_dict()
            assert list(init_original) == list(init_revision)
            assert list(dict(original.named_parameters())) == list(dict(revision.named_parameters()))
            assert all(init_original[name].shape == init_revision[name].shape
                       and init_original[name].dtype == init_revision[name].dtype
                       and torch.equal(init_original[name], init_revision[name])
                       for name in init_original)
            consumption = rng_equal(original_rng, revision_rng)
            assert all(consumption.values())
            revision.load_state_dict(init_original, strict=True)
            initial_state = {name: value.detach().clone()
                             for name, value in init_original.items()}
            data = fixture(original, kind)
            left, right = run(original, data), run(revision, data)
            comparisons = [
                tensor_record('output_' + str(i), a, b)
                for i, (a, b) in enumerate(zip(left['outputs'], right['outputs']))]
            assert len(left['outputs']) == len(right['outputs']) == 3
            assert len(left['analysis_outputs']) == len(right['analysis_outputs']) == 3
            comparisons.extend(
                tensor_record('analysis_output_' + str(i), a, b)
                for i, (a, b) in enumerate(zip(left['analysis_outputs'],
                                             right['analysis_outputs'])))
            for scope in ('input_gradients', 'parameter_gradients'):
                assert list(left[scope]) == list(right[scope])
                comparisons.extend(tensor_record(scope + '.' + name,
                                                  left[scope][name],
                                                  right[scope][name])
                                   for name in left[scope])
            # An identical native YAML AdamW configuration on both private cores.
            original_optimizer = optimizer_factory(original)
            revision_optimizer = optimizer_factory(revision)
            assert type(original_optimizer).__name__ == type(revision_optimizer).__name__ == 'AdamW'
            assert [{key: value for key, value in group.items() if key != 'params'}
                    for group in original_optimizer.param_groups] == [
                        {key: value for key, value in group.items() if key != 'params'}
                        for group in revision_optimizer.param_groups]
            original_optimizer.step()
            revision_optimizer.step()
            updated_original, updated_revision = (dict(original.named_parameters()),
                                                  dict(revision.named_parameters()))
            comparisons.extend(tensor_record('after_identical_AdamW.' + name,
                                              updated_original[name],
                                              updated_revision[name])
                               for name in updated_original)
            # Distinguishing control: fixed wrong fine-parent tokens, same IDs.
            # Restore the SAME initial revision state; do not select a new seed.
            revision.load_state_dict(initial_state, strict=True)
            wrong_banks = [value.detach().clone() for value in data['normalized']]
            wrong_banks[0] = wrong_banks[0].roll(1, dims=1)
            with torch.no_grad():
                wrong_outputs = revision(data['points'], data['point_mask'],
                                         wrong_banks, data['cluster_ids_list'])
            negative_comparisons = [
                tensor_record('wrong_parent_output_' + str(i), a, b)
                for i, (a, b) in enumerate(zip(right['outputs'], wrong_outputs))]
            rejected = any(not item['passed'] for item in negative_comparisons)
            cases.append({
                'case': kind, 'dtype': str(next(original.parameters()).dtype),
                'same_initial_state_exact': True,
                'same_parameter_names_shapes_and_registration_order': True,
                'constructor_rng_consumption_equal': consumption,
                'original_initial_state_strictly_loaded_into_revision': True,
                'fixture_sha256': fingerprint(torch, data),
                'positive_comparisons': comparisons,
                'positive_equivalence_passed': all(item['passed'] for item in comparisons),
                'negative_wrong_parent_control': {
                    'status': 'REJECTED_AS_EXPECTED' if rejected else
                              'INCONCLUSIVE_FIXED_FIXTURE_INSENSITIVE',
                    'fixed_transformation': 'roll normalized fine-bank rows by1; IDs unchanged',
                    'comparisons': negative_comparisons,
                    'no_seed_sample_tolerance_or_effect_threshold_selection': True},
                'original_scalar': left['scalar'], 'revision_scalar': right['scalar'],
                'optimizer_config': 'Unchanged candidate YAML AdamW, gorilla.build_optimizer',
            })
            del original, revision, original_optimizer, revision_optimizer
    finally:
        restore_rng(initial_rng)
    restored = rng_equal(initial_rng, rng_state())
    assert all(restored.values())
    return {
        'cases': cases,
        'equivalence_passed': all(case['positive_equivalence_passed'] for case in cases),
        'distinguishing_control_passed': all(
            case['negative_wrong_parent_control']['status'] == 'REJECTED_AS_EXPECTED'
            for case in cases),
        'caller_RNG_restored': restored,
        'comparison_tolerances': 'torch.testing.assert_close dtype defaults, no overrides',
        'precision': 'Original constructed core parameter dtype; no dtype cast or autocast',
        'native_task_loss_or_full_model_equivalence': 'NOT_RUN_NOT_ESTABLISHED',
        'constructed_fixture_is_native_TRAIN_data': False,
        'auxiliary_autograd_grad_or_backward_used': True,
        'auxiliary_scope': 'Only this separate bounded constructed-core diagnostic process',
        'native_TRAIN2_implementation_changed': False,
    }


def optimizer_carrier_for_core(torch, core):
    """Expose the existing core as native dec group; other YAML groups are empty."""
    carrier = torch.nn.Module()
    for name in ('text_encoder', 'input_conv', 'unet', 'output_layer'):
        carrier.add_module(name, torch.nn.Module())
    carrier.add_module('dec', core)
    return carrier


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lease', required=True)
    args = parser.parse_args()
    result = {
        'execution_completed': False, 'mode': 'revision1_equivalence',
        'candidate_id': MANIFEST['candidate_id'],
        'experiment_id': MANIFEST['experiment_id'],
        'code_commit': MANIFEST['code_commit'],
        'implementation_revision': MANIFEST['implementation_revision'],
        'goal_sha256': MANIFEST['goal_sha256'],
        'runtime_code_commit': MANIFEST['runtime_code_commit'],
        'source_preparation_sha256': MANIFEST['source_preparation_sha256'],
        'native_manifest_sha256': sha(STAGE / 'native_manifest.json'),
        'diagnostic_worker_sha256': sha(Path(__file__)),
        'runtime_sha256': sha(STAGE / 'native_runtime.py'),
        **{key: MANIFEST[key] for key in (
            'stage', 'physical_gpu', 'gpu_uuid', 'current_token',
            'tick_generated_at', 'deadline_at', 'context_sha256', 'pending_sha256')},
        'native_data_loaded': False, 'native_TRAIN_steps': 0,
        'new_training': 0, 'scientific_admission': False,
    }
    try:
        result['before'] = acquire(args.lease)
        sys.path[:0] = [str(ROOT), str(ROOT / 'framework/lib')]
        import torch
        import numpy
        import gorilla
        import yaml
        assert not torch.cuda.is_initialized()
        torch.set_num_threads(1)
        torch.cuda.set_per_process_memory_fraction(0.75, 0)
        candidate_values = yaml.safe_load((STAGE / 'candidate.yaml').read_text())
        original_values = yaml.safe_load(Path(MANIFEST['assets']['config_path']).read_text())
        assert candidate_values == original_values
        assert candidate_values['train']['seed'] == 1999
        original_type = load_private(STAGE / 'reference_distribution_embedding.py',
                                     '_nde_original46_equivalence')
        revision_type = load_private(STAGE / 'candidate_model/distribution_embedding.py',
                                     '_nde_revision1_equivalence')
        cfg = gorilla.Config.fromfile(str(STAGE / 'candidate.yaml'))
        result.update(compare_revision1(
            torch, numpy, original_type, revision_type, cfg.model.dec.d_model,
            lambda core: gorilla.build_optimizer(optimizer_carrier_for_core(torch, core), copy.deepcopy(cfg.optimizer))))
        torch.cuda.synchronize()
        verify()
        result.update(execution_completed=True, after=observe())
        assert result['equivalence_passed'], 'Revision1 equivalence failed; preserve results without tolerance relaxation'
        assert result['distinguishing_control_passed'], 'Fixed wrong-parent control inconclusive; do not resample'
    except BaseException as error:
        result.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        try:
            save('equivalence_result.json', result)
        finally:
            release()


if __name__ == '__main__':
    main()
