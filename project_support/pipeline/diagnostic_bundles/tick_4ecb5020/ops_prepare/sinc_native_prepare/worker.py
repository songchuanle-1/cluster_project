"""Default NOP. Original native TRAIN2 and unchanged full resource handler for SINC."""
import argparse
import os
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
    comparison = copy.deepcopy(candidate_values)
    assert comparison['model']['dec']['cluster_mode'] == 'sinc_csort'
    comparison['model']['dec']['cluster_mode'] = parent_values['model']['dec']['cluster_mode']
    assert comparison == parent_values, 'Only fixed cluster_mode may differ from native M95'
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
    check_values['model']['dec']['cluster_mode'] = parent_values['model']['dec']['cluster_mode']
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
    assert cfg.model.dec.cluster_att_num_layers == 1, 'SINC retains original final hierarchy injection'
    # Original-source common initialization preflight. The reference-only
    # construction is observational: restore its entry RNG, never candidate
    # weights or the post-M95 stream. Any mismatch stops before native TRAIN.
    import random
    import numpy as np
    excluded = ('dec.cluster_att.cluster_ffn.0.', 'dec.cluster_att.cluster_ffn_norm.0.', 'dec.cluster_att.fine_simplex.')
    reference_common = None
    if target == 'candidate' and mode == 'smoke':
        entry_rng = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone(), torch.cuda.get_rng_state_all())
        # Identical source constructor-only loss alias avoids re-registering
        # Criterion; no registry/class mutation and no baseline loss execution.
        baseline_package = 'framework.model.Quard_model.' + base_name
        baseline_loss_path = ROOT / 'framework/model/Quard_model' / base_name / 'loss.py'
        candidate_loss_path = STAGE / 'candidate_model/loss.py'
        expected_loss_sha = 'c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5'
        assert sha(baseline_loss_path) == sha(candidate_loss_path) == expected_loss_sha
        candidate_loss_key, baseline_loss_key = qualified + '.loss', baseline_package + '.loss'
        assert candidate_loss_key in sys.modules
        candidate_loss_module = sys.modules[candidate_loss_key]
        assert Path(candidate_loss_module.__file__).resolve() == candidate_loss_path.resolve()
        alias_preexisted = baseline_loss_key in sys.modules
        if alias_preexisted:
            assert sys.modules[baseline_loss_key] is candidate_loss_module
        else:
            sys.modules[baseline_loss_key] = candidate_loss_module
        assert sys.modules[baseline_loss_key] is sys.modules[candidate_loss_key]
        result['baseline_constructor_loss_alias'] = {
            'candidate_module_key':candidate_loss_key,'baseline_module_key':baseline_loss_key,
            'candidate_loss_sha256':sha(candidate_loss_path),'baseline_loss_sha256':sha(baseline_loss_path),
            'identical_source_verified':True,'alias_preexisted':alias_preexisted,
            'actual_same_module_object':True,'module_identity':id(candidate_loss_module),
            'registry_force_clear_or_edit':False,'class_mutation':False,
            'scope':'Baseline common-init constructor only; no baseline criterion forward/backward; actual candidate Criterion unchanged'}
        baseline_module = importlib.import_module(baseline_package)
        baseline_network_module = importlib.import_module(baseline_package + '.network')
        assert sys.modules[baseline_loss_key] is candidate_loss_module
        assert baseline_network_module.Criterion is candidate_loss_module.Criterion
        result['baseline_constructor_loss_alias']['actual_same_Criterion_class'] = True
        baseline_cfg = gorilla.Config.fromfile(str(original_config))
        baseline_model = baseline_module.Network(**baseline_cfg.model).cuda()
        gorilla.load_checkpoint(baseline_model, str(baseline_cfg.train.pretrain), strict=False, map_location='cpu')
        reference_common = {name:p.detach().cpu().clone() for name,p in baseline_model.named_parameters() if not name.startswith(excluded)}
        result['original_common_reference'] = {'names':list(reference_common), 'shapes':{n:list(p.shape) for n,p in reference_common.items()},
            'dtypes':{n:str(p.dtype) for n,p in reference_common.items()},'tensor_count':len(reference_common), 'sha256':fingerprint(torch,reference_common),
            'source':'actual unchanged M95 seed1999 constructor plus original native backbone pretrain; no trained checkpoint'}
        del baseline_model
        random.setstate(entry_rng[0]);np.random.set_state(entry_rng[1])
        torch.set_rng_state(entry_rng[2]);torch.cuda.set_rng_state_all(entry_rng[3])
        assert random.getstate() == entry_rng[0] and np.array_equal(np.random.get_state()[1],entry_rng[1][1])
        assert torch.equal(torch.get_rng_state(),entry_rng[2])
        assert all(torch.equal(a,b) for a,b in zip(torch.cuda.get_rng_state_all(),entry_rng[3]))
        result['original_common_reference']['reference_measurement_entry_RNG_restored_exact'] = True
        del entry_rng
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
    if reference_common is not None:
        common_actual = {name:p.detach() for name,p in model.named_parameters() if not name.startswith(excluded)}
        same_names = set(common_actual) == set(reference_common)
        same_shapes = same_names and all(tuple(common_actual[n].shape)==tuple(reference_common[n].shape) for n in common_actual)
        same_dtypes = same_names and all(common_actual[n].dtype==reference_common[n].dtype for n in common_actual)
        candidate_hash = fingerprint(torch,common_actual)
        differences = [name for name in sorted(set(common_actual)&set(reference_common))
            if tuple(common_actual[name].shape)!=tuple(reference_common[name].shape)
            or common_actual[name].dtype!=reference_common[name].dtype
            or not torch.equal(common_actual[name].cpu(),reference_common[name])]
        result['original_common_initialization_comparison'] = {
            'same_names':same_names,'same_shapes':same_shapes,'same_dtypes':same_dtypes,
            'candidate_names':list(common_actual),'candidate_shapes':{n:list(p.shape) for n,p in common_actual.items()},
            'candidate_dtypes':{n:str(p.dtype) for n,p in common_actual.items()},
            'candidate_tensor_count':len(common_actual),'reference_tensor_count':len(reference_common),
            'candidate_sha256':candidate_hash,'reference_sha256':result['original_common_reference']['sha256'],
            'different_parameter_names':differences,'only_candidate_names':sorted(set(common_actual)-set(reference_common)),
            'only_reference_names':sorted(set(reference_common)-set(common_actual)),
            'candidate_source_initialization_untouched':True,'copied_common_weights':False,
            'post_reference_rng_substituted':False,'derived_expected_count_only':841,
            'passed':same_names and same_shapes and same_dtypes and not differences
                and candidate_hash==result['original_common_reference']['sha256']}
        passed = result['original_common_initialization_comparison']['passed']
        del reference_common
        if not passed:
            result['native_gate_failure'] = 'ACTUAL_ORIGINAL_COMMON_INITIALIZATION_MISMATCH_BEFORE_TRAIN'
            result['native_data_loaded'] = False
            result['native_train_function_executed'] = False
            raise RuntimeError('Original common initialization differs; preserve true measured failure before TRAIN, no copy/reseed/substitution')
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
    if mode == 'smoke':
        excluded = ('dec.cluster_att.cluster_ffn.0.', 'dec.cluster_att.cluster_ffn_norm.0.', 'dec.cluster_att.fine_simplex.')
        common = {name:p.detach() for name,p in model.named_parameters() if not name.startswith(excluded)}
        result['common_initialized_parameters'] = {
            'scope': 'Actual native initialized named parameters; exclude only replaced fine FFN0/norm0 and new fine_simplex; retain middle/coarse FFNs and norms',
            'excluded_name_prefixes':list(excluded), 'names':list(common), 'shapes':{n:list(p.shape) for n,p in common.items()},
            'tensor_count':len(common), 'parameter_count':sum(p.numel() for p in common.values()), 'sha256':fingerprint(torch,common),
            'derived_expected_tensor_count':841, 'expected_count_is_not_a_measured_PASS':True,
            'paired_equality':'NOT_VALIDATED_BY_SINGLE_TARGET_WORKER; names/shapes/hash must actually match retained comparator'}
    return torch, gorilla, cfg, model, qualified, train, optimizer, scheduler

def smoke(torch, gorilla, cfg, model, qualified, train, optimizer, scheduler, result):
    """Two original natural TRAIN batches; transparent observations only."""
    from framework.dataset import build_dataset, build_dataloader
    dataset = build_dataset(cfg.data.train, logging.getLogger("sinc-native-smoke"))
    loader = build_dataloader(dataset, dist=cfg.dist, **cfg.dataloader.train)
    assert loader.batch_size == 2 and loader.num_workers == 4 and loader.persistent_workers and loader.drop_last
    class TwoNativeBatches:
        def __init__(self, native):
            self.native, self.sampler = native, native.sampler
        def __len__(self):
            return 2
        def __iter__(self):
            yield from itertools.islice(iter(self.native), 2)
    candidate = result["target"] == "candidate"
    att, bank = model.dec.cluster_att, model.dec.cluster_bank
    encoder = model.dec.encoder_layers[-1]
    assert sum(bool(layer.use_cluster) for layer in model.dec.encoder_layers) == 1
    assert encoder.use_cluster and encoder.cluster_gate_type == "sigmoid"
    assert encoder.cluster_message_type == "context"
    core = att.fine_simplex if candidate else None
    tracked = dict(core.named_parameters()) if candidate else {
        "ffn" + str(i) + "." + name: p for i in range(3)
        for name, p in att.cluster_ffn[i].named_parameters()}
    if candidate:
        assert set(tracked) == {"point_weight", "factor_weight", "receiver_weight", "output_weight", "point_bias", "message_bias", "output_bias"}
        assert sum(p.numel() for p in tracked.values()) == 33536
    hooks, replacements, globals_restore = [], [], []
    state = {"forward": 0}
    result.update(batches=[], losses=[], steps=[], core_calls=[], graph_support_observations=[],
                  inst_to_mask_path_observations=[], raw_bank_observations=[], csort_observations=[])
    initial = {name: fingerprint(torch, p.detach()) for name, p in tracked.items()}
    def summary(value):
        value = torch.as_tensor(value)
        finite = bool(torch.isfinite(value).all())
        return {"shape": list(value.shape), "dtype": str(value.dtype), "finite": finite,
                "abs_max": float(value.detach().float().abs().max().cpu()) if value.numel() and finite else 0.0}
    def watch(value, record, key):
        assert value.requires_grad, key
        def receive(gradient):
            info = summary(gradient)
            record.setdefault(key, []).append(info)
            assert info["finite"]
        hooks.append(value.register_hook(receive))
    def replace(owner, name, function):
        assert name not in vars(owner)
        setattr(owner, name, function)
        replacements.append((owner, name))
    def input_hook(owner, values):
        state.clear()
        state["forward"] = len(result["batches"]) + 1
        batch = values[0]
        result["batches"].append({"sha256": fingerprint(torch, batch),
            "scan_ids": [str(x) for x in batch.get("scan_ids", [])],
            "ann_ids": [int(x) for x in batch.get("ann_ids", [])],
            "scenes_len": [int(x) for x in batch.get("scenes_len", [])]})
    original_build = bank.build_cluster_feats
    def observed_build(*args, **kwargs):
        output = original_build(*args, **kwargs)
        state["raw"] = output
        state["raw_ids"] = bank.cluster_ids_list
        state["raw_maps"] = bank.child_cluster_maps
        record = {"forward": state["forward"], "raw_sha256": fingerprint(torch, output),
                  "ids_sha256": fingerprint(torch, bank.cluster_ids_list),
                  "maps_sha256": fingerprint(torch, bank.child_cluster_maps),
                  "outputs": [summary(x) for x in output], "original_calls": 1}
        state["raw_record"] = record
        result["raw_bank_observations"].append(record)
        return output
    replace(bank, "build_cluster_feats", observed_build)
    if candidate:
        graph_module = importlib.import_module(qualified + ".simplex_incidence")
        original_graph = graph_module.build_graph
        def observed_graph(coordinates, leaves):
            started = time.perf_counter()
            graph = original_graph(coordinates, leaves)
            leaf = torch.as_tensor(leaves, dtype=torch.long)
            vertices, factors = graph["vertices"], graph["factor_ids"]
            assert vertices.ndim == factors.ndim == 1 and len(vertices) == len(factors)
            assert graph["point_count"] == len(leaf) and bool((vertices >= 0).all()) and bool((vertices < len(leaf)).all())
            assert bool((factors >= 0).all()) and bool((factors < graph["factor_count"]).all())
            assert bool((torch.bincount(vertices, minlength=len(leaf)) > 0).all())
            factor_leaves = torch.empty(graph["factor_count"], dtype=leaf.dtype)
            factor_leaves[factors] = leaf[vertices]
            assert bool((factor_leaves[factors] == leaf[vertices]).all())
            degree = torch.bincount(factors, minlength=graph["factor_count"])
            record = {"forward": state["forward"], "point_count": len(leaf),
                "support_sha256": fingerprint(torch, graph), "leaf_ids_sha256": fingerprint(torch, leaf),
                "cross_leaf_edges": 0, "allowed_edges": int((degree * degree).sum()),
                "offdiagonal_edges": int((degree * (degree - 1)).sum()),
                "fallback_rows": graph["summary"]["qhull_fallback_leaves"], "original_calls": 1,
                "factor_count": graph["factor_count"], "incidence_count": len(vertices),
                "actual_graph_and_support_observation_ms": (time.perf_counter() - started) * 1000,
                "original_graph_summary": graph["summary"], "returned_original_graph": True}
            result["graph_support_observations"].append(record)
            return graph
        graph_module.build_graph = observed_graph
        globals_restore.append((graph_module, "build_graph", original_graph))
        def core_pre(owner, values):
            features, padding, positions, fine_ids = values
            assert positions.shape[-1] == 3 and fine_ids is bank.cluster_ids_list[0]
            record = {"forward": state["forward"], "input": summary(features),
                "padding_sha256": fingerprint(torch, padding),
                "positions_sha256": fingerprint(torch, positions),
                "fine_ids_sha256": fingerprint(torch, fine_ids), "actual_source_forward": True}
            state["core_record"] = record
            result["core_calls"].append(record)
            watch(features, record, "native_input_gradients")
        def core_post(owner, values, output):
            record = state["core_record"]
            record["output"] = summary(output)
            assert record["output"]["finite"] and torch.count_nonzero(output[values[1]]) == 0
            state["fine_output"] = output
            watch(output, record, "native_output_gradients")
        hooks += [core.register_forward_pre_hook(core_pre), core.register_forward_hook(core_post)]
        original_read = att._cluster_to_points
        def observed_read(*args, **kwargs):
            assert kwargs.get("fine_message") is state["fine_output"]
            assert args[2] is bank.cluster_ids_list
            state["core_record"]["actual_fine_message_delivered_to_HCG"] = True
            output = original_read(*args, **kwargs)
            watch(output, state["core_record"], "native_HCG_output_gradients")
            return output
        replace(att, "_cluster_to_points", observed_read)
    original_csort = att._cross_scale_orth_loss
    def observed_csort(coarse, fine, maps):
        raw = state["raw"]
        pair = next((i for i in range(2) if coarse is raw[i+1] and fine is raw[i]), None)
        assert pair is not None and maps is bank.child_cluster_maps[pair]
        before = fingerprint(torch, (coarse, fine))
        value = original_csort(coarse, fine, maps)
        assert fingerprint(torch, (coarse, fine)) == before
        result["csort_observations"].append({"forward": state["forward"], "pair": pair,
            "raw_object_identity_preserved": True, "output": summary(value), "original_calls": 1})
        return value
    replace(att, "_cross_scale_orth_loss", observed_csort)
    def encoder_pre(owner, values):
        state["inst_before"] = values[2].detach().clone()
        state["gate"] = torch.sigmoid(owner.cluster_att_gate).detach().clone()
    def attention_post(owner, values, output):
        state["cluster_message"] = output["point"].detach().clone()
    def ila_pre(owner, values):
        expected = state["inst_before"] + state["gate"] * state["cluster_message"]
        exact = fingerprint(torch, values[1]) == fingerprint(torch, expected)
        assert exact
        record = {"forward": state["forward"], "single_original_inst_writeback_exact": True,
                  "extra_injection": False, "query_sha256": fingerprint(torch, values[1])}
        result["inst_to_mask_path_observations"].append(record)
        watch(values[1], record, "native_post_cluster_inst_gradients")
    def encoder_post(owner, values, output):
        watch(output[1], result["inst_to_mask_path_observations"][-1], "native_post_ILA_inst_gradients")
    def decoder_post(owner, values, output):
        watch(output["masks"], result["inst_to_mask_path_observations"][-1], "native_final_mask_gradients")
    def model_output(owner, values, output):
        loss, variables = output
        assert loss.numel() == 1 and bool(torch.isfinite(loss).all())
        result["losses"].append({"forward": state["forward"], "loss": float(loss.detach().cpu()),
                                "components": {key: summary(value) for key, value in variables.items()}})
        result["native_loss_forwards"] += 1
        def backward(gradient):
            assert bool(torch.isfinite(gradient).all())
            result["native_criterion_backwards"] += 1
        hooks.append(loss.register_hook(backward))
        raw_record = state["raw_record"]
        raw_record["raw_unchanged"] = fingerprint(torch, state["raw"]) == raw_record["raw_sha256"]
        raw_record["ids_unchanged"] = fingerprint(torch, bank.cluster_ids_list) == raw_record["ids_sha256"]
        raw_record["maps_unchanged"] = fingerprint(torch, bank.child_cluster_maps) == raw_record["maps_sha256"]
        assert raw_record["raw_unchanged"] and raw_record["ids_unchanged"] and raw_record["maps_unchanged"]
    def step_pre(owner, args, kwargs):
        assert result["native_criterion_backwards"] == state["forward"]
        all_gradients = {name: p.grad for name, p in model.named_parameters() if p.grad is not None}
        bad = [name for name, grad in all_gradients.items() if not bool(torch.isfinite(grad).all())]
        assert all_gradients and not bad
        gradients = {name: summary(p.grad) if p.grad is not None else None for name, p in tracked.items()}
        assert all(value is not None and value["finite"] for value in gradients.values())
        record = {"forward": state["forward"], "all_observed_parameter_gradients_finite": True,
            "nonfinite_parameter_names": bad, "tracked_gradients": gradients,
            "before_hash": {name: fingerprint(torch, p.detach()) for name, p in tracked.items()}}
        if candidate:
            assert any(gradients[name]["abs_max"] > 0 for name in ("point_weight","factor_weight","receiver_weight","output_weight")), "INCONCLUSIVE whole-core actual criterion gradient is zero"
            actual_edges = sum(r["offdiagonal_edges"] for r in result["graph_support_observations"] if r["forward"] == state["forward"])
            assert actual_edges > 0, "INCONCLUSIVE natural TRAIN batch has no offdiagonal support; no replacement/resampling"
            record["actual_offdiagonal_supported_edges"] = actual_edges
        result["steps"].append(record)
    def step_post(owner, args, kwargs):
        record = result["steps"][-1]
        record["after_hash"] = {name: fingerprint(torch, p.detach()) for name, p in tracked.items()}
        record["actual_parameter_updated"] = {name: record["before_hash"][name] != record["after_hash"][name] for name in tracked}
        assert all(record["actual_parameter_updated"].values()), "INCONCLUSIVE inactive actual core parameter; preserve natural batch"
        record["original_optimizer_step_completed"] = True
        result["optimizer_steps"] += 1
    hooks += [model.register_forward_pre_hook(input_hook), model.register_forward_hook(model_output),
        encoder.register_forward_pre_hook(encoder_pre), att.register_forward_hook(attention_post),
        encoder.ila.register_forward_pre_hook(ila_pre), encoder.register_forward_hook(encoder_post),
        model.dec.register_forward_hook(decoder_post),
        optimizer.register_step_pre_hook(step_pre), optimizer.register_step_post_hook(step_post)]
    logger = logging.getLogger("sinc-native-smoke")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler(sys.stderr))
    writer = train.SummaryWriter(cfg.work_dir)
    torch.cuda.reset_peak_memory_stats()
    try:
        train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)
        torch.cuda.synchronize()
    finally:
        for owner, name, original in reversed(globals_restore):
            setattr(owner, name, original)
        for owner, name in reversed(replacements):
            delattr(owner, name)
        for handle in hooks:
            handle.remove()
        writer.flush()
        writer.close()
        state.clear()
    assert len(result["batches"]) == len(result["losses"]) == len(result["steps"]) == 2
    assert result["optimizer_steps"] == result["native_criterion_backwards"] == result["native_loss_forwards"] == 2
    assert len(result["raw_bank_observations"]) == len(result["inst_to_mask_path_observations"]) == 2
    assert len(result["csort_observations"]) == 4
    if candidate:
        assert len(result["core_calls"]) == 2
        for record in result["core_calls"]:
            assert record["actual_fine_message_delivered_to_HCG"]
            for key in ("native_input_gradients", "native_output_gradients", "native_HCG_output_gradients"):
                assert record.get(key) and all(value["finite"] for value in record[key])
    for record in result["inst_to_mask_path_observations"]:
        for key in ("native_post_cluster_inst_gradients", "native_post_ILA_inst_gradients", "native_final_mask_gradients"):
            assert record.get(key) and all(value["finite"] for value in record[key])
    final = {name: fingerprint(torch, p.detach()) for name, p in tracked.items()}
    assert all(final[name] != initial[name] for name in tracked)
    verify()
    result.update(execution_completed=True, native_data_loaded=True, native_train_function_executed=True,
        intended_path_observed=True, backward_finite=True, observer_readout_complete=True,
        native_smoke_checks_passed=True, wrappers_and_hooks_restored=True,
        native_tracked_initial_hash=initial, native_tracked_after_hash=final,
        native_tracked_each_parameter_updated=True, training_checkpoint_saved=False,
        native_smoke_training=True, new_training=0, auxiliary_autograd_grad_or_backward_used=False,
        actual_train_command="tools.train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer)",
        native_dataloader_config=dict(cfg.dataloader.train), optimizer_type=type(optimizer).__name__,
        scheduler_type=type(scheduler).__name__, smoke_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        smoke_peak_reserved_bytes=torch.cuda.max_memory_reserved(),
        pure_training_peak_memory="UNKNOWN; hooks active, separate resource arm required",
        paired_initialization_and_batch_equality="NOT_ESTABLISHED_BY_SINGLE_TARGET_RESULT",
        efficacy="UNKNOWN", novelty="UNKNOWN", after=observe())

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

def exception_frame_metadata(error):
    """Bounded failure-only type/identity evidence; never records tensor data."""
    import builtins
    import hashlib
    import types
    def describe(value):
        cls=builtins.type(value)
        out={'type_module':cls.__module__,'type_qualname':cls.__qualname__,
            'identity':builtins.id(value),'callable':builtins.callable(value)}
        if isinstance(value,(types.FunctionType,types.BuiltinFunctionType,types.MethodType,types.BuiltinMethodType)):
            out['callable_module']=getattr(value,'__module__',None)
            out['callable_qualname']=getattr(value,'__qualname__',None)
            bound=getattr(value,'__self__',None);function=getattr(value,'__func__',None)
            if bound is not None:
                bound_cls=builtins.type(bound)
                out['bound_self_identity']=builtins.id(bound)
                out['bound_self_type']=bound_cls.__module__+'.'+bound_cls.__qualname__
            if function is not None:out['bound_function_identity']=builtins.id(function)
        return out
    trace=[];current=error.__traceback__
    while current is not None:
        trace.append(current);current=current.tb_next
    selected=trace[-16:];torch_module=sys.modules.get('torch');frames=[];file_hashes={}
    for tb in selected:
        frame=tb.tb_frame;filename=frame.f_code.co_filename
        item={'file':filename,'function':frame.f_code.co_name,'line':tb.tb_lineno,
            'locals_selected_types':{name:describe(frame.f_locals[name]) for name in
                ('torch','memo','fn','func','wrapper','t','param','param_applied','param_grad','grad','self','module','FakeTensor','op','operator') if name in frame.f_locals}}
        item['resolved_global_binding_types'] = {}
        for binding_name in ('isinstance','type','is_traceable_wrapper_subclass','FakeTensor'):
            if binding_name in frame.f_globals:
                item['resolved_global_binding_types'][binding_name] = describe(frame.f_globals[binding_name])
            elif binding_name in frame.f_builtins:
                item['resolved_global_binding_types'][binding_name] = describe(frame.f_builtins[binding_name])
        if 'torch' in frame.f_globals:
            item['globals_torch']=describe(frame.f_globals['torch'])
            item['globals_torch_is_sys_modules_torch']=frame.f_globals['torch'] is torch_module
        path=Path(filename)
        if filename not in file_hashes:
            try:
                if path.is_file() and path.stat().st_size<=1048576:
                    file_hashes[filename]=hashlib.sha256(path.read_bytes()).hexdigest()
            except (OSError,ValueError):pass
        frames.append(item)
    return {'pid':os.getpid(),'frame_count_total':len(trace),'frame_limit':16,
        'frames':frames,'selected_source_sha256':file_hashes,
        'sys_modules_torch':describe(torch_module),
        'scope':'Actual exception frames, types/identities/source hashes only; no tensor values/full locals; original exception re-raised',
        'no_success_gate_or_training_math_change':True}

def json_safe(value):
    import math
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        # Private device flags are normally reduced/popped after successful TRAIN2.
        # On an earlier failure, never synchronize CUDA or mask the original error.
        output={str(k):json_safe(v) for k,v in value.items() if k!='_internal_gradient_flags'}
        if '_internal_gradient_flags' in value:
            output['internal_gradient_finiteness_status']='NOT_REDUCED_ON_FAILURE'
            output['unreduced_internal_gradient_callback_count']=len(value['_internal_gradient_flags'])
        return output
    if isinstance(value, (list,tuple)):
        return [json_safe(v) for v in value]
    return value

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root',action='store_true')
    parser.add_argument('--lease')
    parser.add_argument('--mode',choices=['smoke','resources'])
    parser.add_argument('--target',choices=['candidate','champion'])
    args=parser.parse_args()
    if not args.execute_root:
        print(json.dumps({'status':'DEFAULT_NOP_NO_TORCH_GPU_OR_EXTERNAL_ACTION'}));return
    assert args.lease and args.mode and args.target
    result={'execution_completed':False,'mode':args.mode,'target':args.target,'optimizer_steps':0,
        'native_loss_forwards':0,'native_criterion_backwards':0,'native_predict_calls':0,'new_training':0,
        'exception_frame_capture_status':'NOT_EXERCISED','native_model_and_yaml_unchanged':False,
        'scientific_admission':False,'efficacy':'UNKNOWN','novelty':'UNKNOWN'}
    try:
        result['before']=acquire(args.lease)
        result.update(candidate_id=MANIFEST['candidate_id'],experiment_id=MANIFEST['experiment_id'],
            code_commit=MANIFEST['code_commit'],source_binding_sha256=MANIFEST['source_binding_sha256'],
            owner=MANIFEST['owner'],goal_sha256=MANIFEST['goal_sha256'],config=MANIFEST['config'],
            stage=str(STAGE),native_manifest_sha256=sha(STAGE/'native_manifest.json'),
            diagnostic_worker_sha256=sha(Path(__file__)),runtime_sha256=sha(STAGE/'native_runtime.py'),
            physical_gpu=0,gpu_uuid=MANIFEST['gpu_uuid'],resource_gate_status='PENDING_ACTUAL_COMPARISON')
        torch,gorilla,cfg,model,qualified,train,optimizer,scheduler=setup(args.target,args.mode,result)
        result['native_model_and_yaml_unchanged']=True
        if args.mode=='smoke':smoke(torch,gorilla,cfg,model,qualified,train,optimizer,scheduler,result)
        else:resources(torch,gorilla,cfg,model,result)
    except BaseException as error:
        import traceback
        result.update(error_type=type(error).__name__,error=str(error))
        try:
            result['exception_frame_metadata']=exception_frame_metadata(error)
            result['exception_frame_capture_status']='ACTUAL_FAILURE_CAPTURED'
        except BaseException as capture_error:
            result['exception_frame_capture_status']='CAPTURE_FAILED_ORIGINAL_EXCEPTION_PRESESINCD'
            result['exception_frame_capture_error_type']=type(capture_error).__name__
        traceback.print_exc();raise
    finally:
        try:
            if MANIFEST:save(args.mode+'_'+args.target+'_result.json',json_safe(result))
        finally:
            release()
            print(json.dumps({'execution_completed':result['execution_completed'],'optimizer_steps':result['optimizer_steps'],
                'result_mode':args.mode,'target':args.target}),flush=True)

if __name__=='__main__':main()
