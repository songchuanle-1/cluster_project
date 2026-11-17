"""Default NOP; real frozen CSO core checks run only in the remote CPU stage."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

PARAMETER_SHAPES = {
    "input_norm.weight": [256],
    "input_norm.bias": [256],
    "project.weight": [8, 256],
    "readout.0.weight": [128, 44],
    "readout.0.bias": [128],
    "readout.2.weight": [256, 128],
    "readout.2.bias": [256],
    "readout.3.weight": [256],
    "readout.3.bias": [256],
}


def run_checks(result, environment):
    import torch
    import yaml
    assert str(Path(torch.__file__).resolve()) == environment["torch"]["module"]["realpath"]
    assert torch.__version__ == environment["torch"]["version"]
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    # CPU generator only: no torch.manual_seed()/CUDA seed or device API.
    torch.random.default_generator.manual_seed(1999)
    generator = torch.Generator(device="cpu").manual_seed(3017)
    core_path = Path(__file__).resolve().parent / "covariance_shape.py"
    spec = importlib.util.spec_from_file_location("cso_frozen_cpu_core", core_path)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    assert core.FineLeafCovarianceShape.__module__ == "cso_frozen_cpu_core"
    native_config = yaml.safe_load((core_path.parent / "candidate.yaml").read_text())
    native_optimizer = native_config["optimizer"]
    assert native_optimizer["type"] == "AdamW"
    assert native_optimizer["lr"] == 1e-4 and native_optimizer["weight_decay"] == 5e-4
    assert native_optimizer["paramwise_cfg"]["dec"]["lr_mult"] == 1.0
    native_grad_clip = native_config["train"]["grad_clip"]
    assert native_grad_clip == 0.1
    assert native_config["train"]["seed"] == 1999
    template = core.FineLeafCovarianceShape(channels=256)
    assert {name: list(p.shape) for name, p in template.named_parameters()} == PARAMETER_SHAPES
    assert sum(p.numel() for p in template.parameters()) == 41856
    assert all(p.device.type == "cpu" for p in template.parameters())
    assert all(b.device.type == "cpu" for b in template.buffers())
    result["runtime"] = {
        "torch_version": torch.__version__, "torch_module": torch.__file__,
        "python": sys.executable, "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
        "device": "cpu", "intraop_threads": torch.get_num_threads(),
        "interop_threads": torch.get_num_interop_threads(),
        "core_parameter_shapes": PARAMETER_SHAPES, "parameter_tensors": 9,
        "parameter_count": 41856, "cpu_default_seed": 1999, "fixture_generator_seed": 3017,
    }

    def random(shape, dtype):
        return torch.randn(shape, dtype=dtype, device="cpu", generator=generator)

    def finite(tensor, label):
        assert tensor.device.type == "cpu", label + ": device"
        assert bool(torch.isfinite(tensor).all()), label + ": nonfinite"

    def compare(actual, expected, dtype, label):
        finite(actual, label + " actual")
        finite(expected, label + " expected")
        atol, rtol = (2e-8, 2e-6) if dtype == torch.float64 else (3e-5, 3e-4)
        error = float((actual - expected).abs().max()) if actual.numel() else 0.0
        assert torch.allclose(actual, expected, atol=atol, rtol=rtol), (label, error, atol, rtol)
        return {"max_abs_error": error, "atol": atol, "rtol": rtol}

    mask = torch.ones((2, 13), dtype=torch.bool)
    valid_indices = ([0, 1, 3, 4, 6, 8, 9, 11, 12], [0, 2, 3, 5, 7, 10, 12])
    for batch, indices in enumerate(valid_indices):
        mask[batch, list(indices)] = False
    groups = [
        torch.tensor([0, 0, 2, 2, 2, 5, 5, 8, 8], dtype=torch.long),
        torch.tensor([0, 1, 1, 4, 4, 4, 9], dtype=torch.long),
    ]

    def backward_observation(model, x, positions, target, method, diagonal=False):
        if method == "reference":
            output = model.forward_reference(x, mask, positions, groups, diagonal_only=diagonal)
        elif diagonal:
            output = model.forward_diagonal_only(x, mask, positions, groups)
        else:
            output = model(x, mask, positions, groups)
        finite(output, "output")
        assert torch.count_nonzero(output[mask]) == 0
        loss = (output[~mask] - target[~mask]).square().mean()
        finite(loss, "loss")
        loss.backward()
        finite(x.grad, "input gradient")
        assert torch.count_nonzero(x.grad[mask]) == 0
        grads = {}
        for name, parameter in model.named_parameters():
            assert parameter.grad is not None, name
            finite(parameter.grad, name + " gradient")
            grads[name] = parameter.grad.detach().clone()
        return output.detach(), x.grad.detach(), grads, float(loss.detach()), model.last_observation

    for dtype in (torch.float64, torch.float32):
        features = random((2, 13, 256), dtype)
        positions = random((2, 13, 3), dtype)
        target = random((2, 13, 256), dtype)
        for diagonal in (False, True):
            left = copy.deepcopy(template).to(dtype=dtype)
            right = copy.deepcopy(template).to(dtype=dtype)
            fast = backward_observation(left, features.clone().requires_grad_(), positions, target, "fast", diagonal)
            reference = backward_observation(right, features.clone().requires_grad_(), positions, target, "reference", diagonal)
            observations = {
                "name": "fast_reference_output_and_backward",
                "dtype": str(dtype), "diagonal_only": diagonal,
                "output": compare(fast[0], reference[0], dtype, "output"),
                "input_gradient": compare(fast[1], reference[1], dtype, "input gradient"),
                "parameter_gradients": {
                    name: compare(fast[2][name], reference[2][name], dtype, name)
                    for name in PARAMETER_SHAPES
                },
                "loss_fast": fast[3], "loss_reference": reference[3],
                "fast_observation": fast[4], "reference_observation": reference[4],
                "all_nine_gradients_finite": True,
                "padding_output_and_input_gradient_exact_zero": True, "passed": True,
            }
            assert fast[4]["points"] == 16 and fast[4]["occupied_leaves"] == 8
            assert fast[4]["receiver_donor_edges"] == 0 and fast[4]["uses_positions"] is False
            result["checks"].append(observations)

        model = copy.deepcopy(template).to(dtype=dtype)
        with torch.no_grad():
            expected = model(features, mask, positions, groups).clone()
            poisoned = features.clone()
            poisoned[mask] = float("nan")
            padding_output = model(poisoned, mask, torch.full_like(positions, float("nan")), groups)
            padding = compare(padding_output, expected, dtype, "padding/unused positions")
            assert torch.count_nonzero(padding_output[mask]) == 0
            permutations = [torch.randperm(13, generator=generator) for _ in range(2)]
            perm_features, perm_mask, perm_positions, perm_groups, perm_expected = [], [], [], [], []
            for batch, permutation in enumerate(permutations):
                per_point_ids = torch.full((13,), -1, dtype=torch.long)
                per_point_ids[~mask[batch]] = groups[batch]
                perm_features.append(features[batch, permutation])
                perm_mask.append(mask[batch, permutation])
                perm_positions.append(positions[batch, permutation])
                perm_groups.append(per_point_ids[permutation][~mask[batch, permutation]])
                perm_expected.append(expected[batch, permutation])
            permuted = model(torch.stack(perm_features), torch.stack(perm_mask), torch.stack(perm_positions), perm_groups)
            permutation = compare(permuted, torch.stack(perm_expected), dtype, "point permutation")
            relabeled_groups = []
            for ids in groups:
                labels = sorted(set(ids.tolist()))
                mapping = {old: (len(labels) - 1 - index) * 3 + 1 for index, old in enumerate(labels)}
                relabeled_groups.append(torch.tensor([mapping[int(x)] for x in ids], dtype=torch.long))
            relabeled = model(features, mask, positions, relabeled_groups)
            relabel = compare(relabeled, expected, dtype, "fine ID relabeling with gaps")
            changed = features.clone()
            changed[1, ~mask[1]] += random((7, 256), dtype) * 20
            other_scene = model(changed, mask, positions, groups)
            assert torch.equal(other_scene[0], expected[0]), "Cross-scene leakage"
            compact = model(features[0:1, ~mask[0]], torch.zeros((1, 9), dtype=torch.bool),
                            positions[0:1, ~mask[0]], [groups[0]])
            compact_check = compare(compact[0], expected[0, ~mask[0]], dtype, "compact/padded valid inputs")
        result["checks"].append({
            "name": "padding_permutation_id_relabel_cross_scene", "dtype": str(dtype),
            "padding": padding, "permutation": permutation, "id_relabeling": relabel,
            "compact": compact_check, "cross_scene_exact": True, "passed": True,
        })

        singleton = random((1, 4, 256), dtype).requires_grad_()
        singleton_mask = torch.tensor([[True, False, True, True]])
        singleton_ids = [torch.tensor([3], dtype=torch.long)]
        singleton_model = copy.deepcopy(template).to(dtype=dtype)
        singleton_out = singleton_model(singleton, singleton_mask, None, singleton_ids)
        finite(singleton_out, "singleton output")
        singleton_ref = singleton_model.forward_reference(singleton, singleton_mask, None, singleton_ids)
        singleton_error = compare(singleton_out, singleton_ref, dtype, "singleton reference")
        singleton_out[~singleton_mask].square().mean().backward()
        finite(singleton.grad, "singleton input gradient")
        assert torch.count_nonzero(singleton_out[singleton_mask]) == 0
        assert torch.count_nonzero(singleton.grad[singleton_mask]) == 0
        for name, parameter in singleton_model.named_parameters():
            assert parameter.grad is not None
            finite(parameter.grad, "singleton " + name)
        result["checks"].append({
            "name": "singleton_and_unoccupied_leaf_slots", "dtype": str(dtype),
            "reference": singleton_error, "occupied_leaves": singleton_model.last_observation["occupied_leaves"],
            "all_nine_gradients_finite": True, "padding_exact_zero": True, "passed": True,
        })

        for scale in (0.0, 1e-9, 1e-6, 1e-3):
            degenerate_model = copy.deepcopy(template).to(dtype=dtype)
            base = random((1, 1, 256), dtype)
            x = (base.expand(1, 6, 256) + scale * random((1, 6, 256), dtype)).clone().requires_grad_()
            m = torch.zeros((1, 6), dtype=torch.bool)
            ids = [torch.tensor([0, 0, 0, 2, 2, 5], dtype=torch.long)]
            output = degenerate_model(x, m, None, ids)
            finite(output, "near-degenerate output")
            reference = degenerate_model.forward_reference(x, m, None, ids)
            error = compare(output, reference, dtype, "near-degenerate reference")
            (output * random(output.shape, dtype)).mean().backward()
            finite(x.grad, "near-degenerate input gradient")
            for name, parameter in degenerate_model.named_parameters():
                assert parameter.grad is not None
                finite(parameter.grad, "near-degenerate " + name)
            z = (random((1, 8), dtype).expand(6, 8) + scale * random((6, 8), dtype)).clone().requires_grad_()
            means, covariance, counts = core.covariance_statistics(z, ids[0], 6)
            root = core.matrix_square_root(covariance)
            finite(root, "near-degenerate matrix root")
            symmetry = float((root - root.transpose(-1, -2)).abs().max())
            assert symmetry <= (1e-10 if dtype == torch.float64 else 1e-5)
            positive = covariance + torch.finfo(dtype).eps * torch.eye(8, dtype=dtype)[None]
            residual = float((root.bmm(root) - positive).norm() / positive.norm().clamp_min(torch.finfo(dtype).eps))
            (root * random(root.shape, dtype)).mean().add(means.square().mean()).backward()
            finite(z.grad, "near-degenerate projected gradient")
            result["checks"].append({
                "name": "near_degenerate_finite_backward", "dtype": str(dtype), "noise_scale": scale,
                "reference": error, "root_symmetry_max_abs": symmetry,
                "fixed_six_step_relative_square_residual_observed": residual,
                "residual_is_not_an_exact_square_root_accuracy_claim": True,
                "all_nine_gradients_and_inputs_finite": True, "passed": True,
            })

        constant_model = copy.deepcopy(template).to(dtype=dtype)
        constant = torch.full((1, 3, 256), 7.0, dtype=dtype, requires_grad=True)
        constant_output = constant_model(constant, torch.zeros((1, 3), dtype=torch.bool), None,
                                         [torch.zeros(3, dtype=torch.long)])
        finite(constant_output, "constant-channel zero-LayerNorm variance")
        (constant_output * random(constant_output.shape, dtype)).mean().backward()
        finite(constant.grad, "constant-channel input gradient")
        for name, parameter in constant_model.named_parameters():
            assert parameter.grad is not None
            finite(parameter.grad, "constant-channel " + name)
        result["checks"].append({
            "name": "zero_channel_variance_finite_backward", "dtype": str(dtype), "passed": True,
        })

    # Matched projected means/diagonal variances isolate the actual off-diagonal mechanism.
    dtype = torch.float64
    a = torch.zeros((2, 8), dtype=dtype)
    a[0, :2] = torch.tensor([1.0, 1.0], dtype=dtype)
    a[1] = -a[0]
    b = a.clone()
    b[:, 1] *= -1
    zero_ids = torch.zeros(2, dtype=torch.long)
    ma, ca, _ = core.covariance_statistics(a, zero_ids, 1)
    mb, cb, _ = core.covariance_statistics(b, zero_ids, 1)
    assert torch.equal(ma, mb) and torch.equal(ca.diagonal(dim1=-2, dim2=-1), cb.diagonal(dim1=-2, dim2=-1))
    ra, rb = core.matrix_square_root(ca), core.matrix_square_root(cb)
    da = core.matrix_square_root(torch.diag_embed(ca.diagonal(dim1=-2, dim2=-1)))
    db = core.matrix_square_root(torch.diag_embed(cb.diagonal(dim1=-2, dim2=-1)))
    assert torch.equal(da, db) and float(ra[0, 0, 1]) > 0 and float(rb[0, 0, 1]) < 0
    diagnostic = copy.deepcopy(template).double()
    # Declared parameter fixture only; exact source and all readout weights stay unchanged.
    with torch.no_grad():
        diagnostic.project.weight.zero_()
        diagnostic.project.weight[0, 0] = 1.0
        diagnostic.project.weight[1, 1] = 1.0
    input_a = torch.zeros((1, 2, 256), dtype=dtype)
    input_a[0, 0, :4] = torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=dtype)
    input_a[0, 1] = -input_a[0, 0]
    input_b = torch.zeros_like(input_a)
    input_b[0, 0, :4] = torch.tensor([1.0, -1.0, 1.0, -1.0], dtype=dtype)
    input_b[0, 1] = -input_b[0, 0]
    cmask, cids = torch.zeros((1, 2), dtype=torch.bool), [zero_ids]
    with torch.no_grad():
        full_a, full_b = diagnostic(input_a, cmask, None, cids), diagnostic(input_b, cmask, None, cids)
        diagonal_a = diagnostic.forward_diagonal_only(input_a, cmask, None, cids)
        diagonal_b = diagnostic.forward_diagonal_only(input_b, cmask, None, cids)
        full_difference = float((full_a - full_b).abs().max())
        diagonal_difference = float((diagonal_a - diagonal_b).abs().max())
        assert full_difference > 1e-8 and diagonal_difference <= 1e-12
        compare(full_a, diagnostic.forward_reference(input_a, cmask, None, cids), dtype, "correlation full/reference")
        compare(diagonal_a, diagnostic.forward_reference(input_a, cmask, None, cids, diagonal_only=True),
                dtype, "correlation diagonal/reference")
    result["checks"].append({
        "name": "matched_diagonal_opposite_correlation_discriminant",
        "projected_means_and_diagonal_variances_exact_equal": True,
        "actual_six_step_root_offdiagonals": [float(ra[0, 0, 1]), float(rb[0, 0, 1])],
        "full_forward_max_abs_difference": full_difference,
        "diagonal_forward_max_abs_difference": diagonal_difference,
        "declared_fixture": "Separate diagnostic instance: project first two channels to latent first two; other projection entries zero; default LayerNorm/readout retained",
        "frozen_source_modified": False, "passed": True,
    })

    model = copy.deepcopy(template)
    optimizer = torch.optim.AdamW(model.parameters(), lr=native_optimizer["lr"],
                                 weight_decay=native_optimizer["weight_decay"])
    assert optimizer.defaults["betas"] == (0.9, 0.999) and optimizer.defaults["eps"] == 1e-8
    updates = []
    for step in range(2):
        optimizer.zero_grad(set_to_none=True)
        x = random((2, 13, 256), torch.float32).requires_grad_()
        target = random((2, 13, 256), torch.float32)
        output = model(x, mask, None, groups)
        loss = (output[~mask] - target[~mask]).square().mean()
        finite(loss, "optimizer loss")
        loss.backward()
        gradient_norms, before = {}, {}
        for name, parameter in model.named_parameters():
            assert parameter.grad is not None
            finite(parameter.grad, name + " optimizer gradient")
            norm = float(parameter.grad.norm())
            assert norm > 0, name + ": zero gradient on registered training fixture"
            gradient_norms[name] = norm
            before[name] = parameter.detach().clone()
        finite(x.grad, "optimizer input gradient")
        assert torch.count_nonzero(x.grad[mask]) == 0
        total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), native_grad_clip)
        finite(total_norm, "native grad_clip norm")
        optimizer.step()
        parameter_updates = {}
        for name, parameter in model.named_parameters():
            finite(parameter, name + " updated")
            delta = float((parameter.detach() - before[name]).abs().max())
            assert delta > 0, name + ": parameter not updated"
            parameter_updates[name] = delta
            state = optimizer.state[parameter]
            finite(state["exp_avg"], name + " first moment")
            finite(state["exp_avg_sq"], name + " second moment")
            assert float(state["step"]) == step + 1
        updates.append({
            "step": step + 1, "synthetic_loss": float(loss.detach()),
            "all_nine_gradient_norms_before_clip": gradient_norms,
            "native_grad_clip": native_grad_clip, "total_gradient_norm_before_clip": float(total_norm),
            "all_nine_max_abs_parameter_updates": parameter_updates,
            "intended_core_observation": model.last_observation,
        })
    result["checks"].append({
        "name": "native_yaml_adamw_hyperparameters_two_synthetic_core_steps",
        "optimizer": "torch.optim.AdamW", "lr": 1e-4, "weight_decay": 5e-4,
        "betas": [0.9, 0.999], "eps": 1e-8, "steps": updates,
        "native_task_loss_or_training_claimed": False,
        "all_nine_parameters_finite_nonzero_gradients_and_updated": True, "passed": True,
    })
    invalid_inputs = [
        (torch.ones((1, 2), dtype=torch.bool), [torch.empty(0, dtype=torch.long)]),
        (torch.zeros((1, 2), dtype=torch.bool), [torch.tensor([0], dtype=torch.long)]),
        (torch.zeros((1, 2), dtype=torch.bool), [torch.tensor([0, -1], dtype=torch.long)]),
    ]
    for invalid_mask, invalid_ids in invalid_inputs:
        try:
            template(torch.zeros((1, 2, 256)), invalid_mask, None, invalid_ids)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed/empty fine incidence was accepted")
    forbidden = [name for name in sys.modules if name == "framework" or name.startswith(
        ("framework.", "tools.train", "spconv", "gorilla"))]
    assert not forbidden, forbidden
    result["checks"].append({"name": "invalid_incidence_rejected_and_no_project_import", "passed": True})
    result["all_required_checks_passed"] = all(item["passed"] for item in result["checks"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--lease")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_TORCH_SSH_GPU_OR_MUTATION"}))
        return
    assert args.lease
    from cso_runtime import OWNER, STAGE, sha, verify, save_result
    started = time.monotonic()
    signal.alarm(95)  # Only this private synthetic worker; no external process signaling.
    result = {
        "owner": OWNER, "experiment_id": "M236-CSO",
        "candidate_id": "fine-leaf-full-covariance-shape-composition",
        "scope": "REMOTE_CPU_ONLY_SYNTHETIC_EXACT_CORE_CHECK",
        "passed": False, "execution_completed": False, "checks": [],
        "native_data_loaded": False, "native_train_function_executed": False,
        "full_model_imported": False, "cuda_device_requested": False,
        "native_backward": "NOT_RUN", "resources": "NOT_RUN",
        "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
        "command": sys.argv, "core_sha256": sha(STAGE / "covariance_shape.py"),
    }
    try:
        source, environment = verify(args.lease)
        result["source_binding_sha256"] = sha(STAGE / "source_binding.json")
        result["pre_torch_guards_passed"] = True
        run_checks(result, environment)
        assert sha(STAGE / "covariance_shape.py") == source["source_core_sha256"]
        result.update(passed=True, execution_completed=True, status="SYNTHETIC_CORE_CHECKS_PASSED")
    except BaseException as error:
        result.update(execution_completed=True, status="SYNTHETIC_CORE_CHECK_FAILED",
                      error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    result["elapsed_seconds"] = time.monotonic() - started
    save_result(result)
    print(json.dumps({"status": result["status"], "passed": result["passed"],
                      "result_sha256": sha(STAGE / "core_result.json"),
                      "elapsed_seconds": result["elapsed_seconds"]}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
