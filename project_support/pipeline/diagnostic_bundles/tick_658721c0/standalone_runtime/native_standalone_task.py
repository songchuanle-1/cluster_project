"""Run the independent contact package, without a forward-replacement hook."""
import argparse
import copy
import gc
import importlib.util
import logging
from pathlib import Path
import sys
from native_runtime import acquire, release, setup, save, sha, MANIFEST, NAME, STAGE

parser = argparse.ArgumentParser()
parser.add_argument('--lease', required=True)
args = parser.parse_args()
result = {'execution_completed': False, 'scientific_admission': False, 'new_training': 0, 'optimizer_steps': 0}
try:
    result['before'] = acquire(args.lease)
    torch, gorilla, cfg, parent, metadata = setup()
    parent_parameter_count = sum(p.numel() for p in parent.parameters())
    del parent
    gc.collect()
    torch.cuda.empty_cache()
    directory = STAGE / 'candidate_model'
    for name, expected in MANIFEST['candidate_source_hashes'].items():
        assert sha(directory / name) == expected
    name = 'framework.model.Quard_model.' + NAME + '_pce'
    spec = importlib.util.spec_from_file_location(name, directory / '__init__.py', submodule_search_locations=[str(directory)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[name] = package
    spec.loader.exec_module(package)
    gorilla.set_random_seed(1999)
    model = package.Network(**cfg.model)
    state = torch.load(MANIFEST['assets']['checkpoint'], map_location='cpu', weights_only=False, mmap=True)['model']
    expected = model.state_dict()
    extra = set(state) - set(expected)
    assert extra <= {'text_encoder.embeddings.position_ids', 'text_encoder.embeddings.token_type_ids'}
    model.load_state_dict({key: value for key, value in state.items() if key not in extra}, strict=True)
    del state, expected
    model.cuda().train()
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader, Subset
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('standalone-contact'))
    for scene in MANIFEST['cohort']:
        group = dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id'] == scene['scene_id']
        assert [{'object_id': str(r['object_id']), 'ann_id': str(r['ann_id'])} for r in group] == scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch = next(iter(DataLoader(Subset(dataset, [s['group_index'] for s in MANIFEST['cohort']]),
        batch_size=2, shuffle=False, num_workers=0, collate_fn=dataset.collate_fn)))
    gorilla.set_random_seed(1999)
    loss, _ = model(copy.deepcopy(batch), mode='loss')
    assert bool(torch.isfinite(loss))
    loss.backward()
    gradients = [p.grad for p in model.parameters() if p.grad is not None]
    assert gradients and all(bool(torch.isfinite(g).all()) for g in gradients)
    parameter_count = sum(p.numel() for p in model.parameters())
    assert parameter_count == parent_parameter_count
    result.update(execution_completed=True, native_loss=float(loss.detach().cpu()),
        native_loss_forwards=1, native_criterion_backwards=1,
        gradient_tensor_count=len(gradients), all_observed_gradients_finite=True,
        parent_parameter_count=parent_parameter_count, candidate_parameter_count=parameter_count,
        new_learned_parameters=0, forward_replacement_hooks=0,
        independent_model_body_executed=True, inference_graph_wiring='static only; native loss path tested',
        diagnostic_checkpoint='Frozen M95 epoch16 for feasibility, not a trained candidate or launch initialization decision',
        remaining='Formal total FLOPs/latency/Pareto, full-source permutation/numerical evidence, broader scene task uncertainty and publication novelty')
except BaseException as error_value:
    result.update(error_type=type(error_value).__name__, error=str(error_value))
    raise
finally:
    try:
        save('native_standalone_result.json', result)
    finally:
        release()
