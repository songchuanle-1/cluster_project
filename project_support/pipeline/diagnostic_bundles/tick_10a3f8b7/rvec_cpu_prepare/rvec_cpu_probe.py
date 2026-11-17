"""Default NOP. Fixed source-bound RVE operator CPU implementation tests."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pickle
import random
import socket
import subprocess
import sys
import traceback
import types

EXPECTED_OWNER = {
    "token": "10a3f8b7d1bc4c5083b9b476c4d6fb94",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-08T21:09:22.656483+00:00",
    "deadline_at": "2026-11-08T22:09:22.656483+00:00",
    "context_sha256": "96ccdaba46f448a2c295d1407b3e782b9f9d1052825fe18b2e4f967a458d3d71",
    "pending_sha256": "a5a8fe814217e681000a6efca7eaeca7999792c27b10345892113ebb4f31ef9f",
}
SOURCE = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"
GPU_UUID_PROVENANCE_ONLY = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
SOURCE_BINDING_SHA = "f33a05f577c2da4da91636af9124b21c433ba3933030c917b6b4c9d028c9e60f"
OPERATOR_RELATIVE = "framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rvec/receiver_vector_exchange.py"
CASE_NAMES = (
    "singleton", "small_padded_batch", "K_minus_one", "K_exactly",
    "K_plus_one", "cutoff_ties_and_other_leaf", "all_valid_multileaf",
    "float32_K_plus_one",
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_TORCH_IMPORT_OR_EXTERNAL_ACTION"}))
        return
    assert sys.flags.isolated and sys.dont_write_bytecode
    assert socket.gethostname() == "dl04-MS-7E06"
    assert os.getuid() == os.geteuid() == 1001
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert Path.cwd() == Path("/") and str(Path(sys.executable)) == PYTHON
    request = globals()["BOUND_REQUEST"]
    assert request["owner"] == EXPECTED_OWNER and request["execution_authorized"] is True
    assert request["producer_sha256"] == globals()["ACTUAL_PRODUCER_SHA256"]
    assert request["source_commit"] == SOURCE and request["runtime_root"] == RUNTIME
    assert request["source_binding_sha256"] == SOURCE_BINDING_SHA
    assert request["gpu_uuid_provenance_only"] == GPU_UUID_PROVENANCE_ONLY
    assert request["GPU_use_authorized"] is False and request["training_launch_authorized"] is False
    assert request["candidate_id"] == "fine-leaf-receiver-conditioned-vector-exchange"
    assert request["experiment_id"] == "M234-RVE" and request["admission_receipt_required"] is False
    assert datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED_OWNER["deadline_at"])
    binding_raw = base64.b64decode(request["source_binding_bytes_base64"], validate=True)
    assert digest(binding_raw) == SOURCE_BINDING_SHA
    binding = json.loads(binding_raw)
    assert binding["owner"] == EXPECTED_OWNER and len(binding["source_files"]) == 9
    operator_raw = globals()["BOUND_OPERATOR_BYTES"]
    legacy_raw = globals()["BOUND_LEGACY_BYTES"]
    assert digest(operator_raw) == binding["source_files"][OPERATOR_RELATIVE]
    assert digest(legacy_raw) == binding["legacy_graph_reference"]["sha256"]
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(PATH="/usr/bin:/bin", GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1",
               GIT_CONFIG_SYSTEM="/dev/null", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_COUNT="0")
    head = subprocess.check_output(
        ["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", RUNTIME,
         "rev-parse", "--verify", "HEAD"], env=env, text=True, timeout=15).strip()
    assert head == SOURCE
    result = {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "owner": EXPECTED_OWNER,
        "producer_sha256": globals()["ACTUAL_PRODUCER_SHA256"],
        "request_sha256": globals()["ACTUAL_REQUEST_SHA256"],
        "source_binding_sha256": SOURCE_BINDING_SHA, "source_files": binding["source_files"],
        "operator_sha256": digest(operator_raw), "legacy_graph_source_sha256": digest(legacy_raw),
        "candidate_id": request["candidate_id"], "experiment_id": request["experiment_id"],
        "source_commit": SOURCE, "runtime_root": RUNTIME, "runtime_HEAD": head,
        "gpu_uuid_provenance_only": GPU_UUID_PROVENANCE_ONLY, "python": sys.executable,
        "GPU_use": False, "native_model_imported": False, "data_or_checkpoint_loaded": False,
        "native_task_loss": "NOT_RUN", "native_two_steps": "NOT_RUN", "resources": "NOT_RUN",
        "admission_granted": False, "efficacy": "UNKNOWN", "novelty": "UNKNOWN", "cases": [],
    }
    python_state = random.getstate()
    torch = None
    torch_state = None
    numpy_rng = None
    numpy_state = None
    failure = None
    try:
        import torch
        import numpy as np
        import scipy
        result["cuda_initialized_before"] = torch.cuda.is_initialized()
        assert result["cuda_initialized_before"] is False
        torch_state = torch.get_rng_state().clone()
        numpy_rng = np.random
        numpy_state = pickle.dumps(numpy_rng.get_state())
        torch.set_num_threads(1)
        torch.manual_seed(1999)
        result["libraries"] = {
            "torch": torch.__version__, "torch_file": torch.__file__,
            "numpy": np.__version__, "scipy": scipy.__version__,
        }

        def load_source(raw, name):
            module = types.ModuleType(name)
            module.__file__ = "<hash-bound-" + name + ">"
            exec(compile(raw, module.__file__, "exec"), module.__dict__)
            return module

        actual = load_source(operator_raw, "actual_receiver_vector_exchange")
        legacy = load_source(legacy_raw, "historical_fle_graph_reference")
        cls = actual.FineLeafReceiverVectorExchange
        model = cls(channels=256, k=32, heads=8).double()
        with torch.no_grad():
            for offset, parameter in enumerate(model.parameters()):
                values = torch.arange(parameter.numel(), dtype=parameter.dtype).reshape_as(parameter)
                parameter.copy_(0.12 * torch.sin(values * 0.017 + offset * 0.31 + 0.2))
        result["operator"] = {
            "class": cls.__name__, "parameters": {n: list(p.shape) for n, p in model.named_parameters()},
            "parameter_count": sum(p.numel() for p in model.parameters()),
            "fixture_parameters": "fixed sine-filled parameters; no search or selected model initialization change",
            "heads": 8, "per_head_dimension": 32, "K": 32, "activation": "source GELU unchanged",
        }

        def fixture(name, dtype):
            if name == "singleton":
                labels = [[5]]
            elif name == "small_padded_batch":
                labels = [[7, 7, 8, 8], [11, 11]]
            elif name in ("K_minus_one", "K_exactly", "K_plus_one", "float32_K_plus_one"):
                labels = [[5] * {"K_minus_one": 31, "K_exactly": 32,
                                "K_plus_one": 33, "float32_K_plus_one": 33}[name]]
            elif name == "cutoff_ties_and_other_leaf":
                labels = [[5] * 33 + [9, 9]]
            elif name == "all_valid_multileaf":
                labels = [[3, 3, 3, 8, 8]]
            else:
                raise AssertionError("Unregistered fixture")
            width = max(map(len, labels)) + (2 if name == "small_padded_batch" else 0)
            count = len(labels) * width * 256
            a = torch.arange(count, dtype=dtype).reshape(len(labels), width, 256)
            features = torch.sin(a * 0.013 + 0.1) / 5 + torch.cos(a * 0.007) / 7
            padding = torch.ones(len(labels), width, dtype=torch.bool)
            positions = torch.zeros(len(labels), width, 3, dtype=torch.float64)
            ids = []
            for batch, values in enumerate(labels):
                n = len(values)
                padding[batch, :n] = False
                ids.append(torch.tensor(values, dtype=torch.long))
                t = torch.arange(n, dtype=torch.float64)
                positions[batch, :n] = torch.stack(
                    (t + 0.013 * t * t, 0.031 * t * t, 0.007 * t * t * t), -1)
            if name == "cutoff_ties_and_other_leaf":
                positions[0, :33] = 0
                positions[0, 33:] = torch.tensor([[100., 0., 0.], [102., 0., 0.]], dtype=torch.float64)
            return features, padding, positions, ids

        def tolerances(dtype):
            return (2e-10, 2e-8) if dtype == torch.float64 else (5e-5, 5e-4)

        def close(a, b, dtype):
            atol, rtol = tolerances(dtype)
            torch.testing.assert_close(a, b, atol=atol, rtol=rtol)
            return float((a - b).abs().max()) if a.numel() else 0.0

        def support_checks(features, padding, positions, ids):
            metadata = []
            for batch, leaves_tensor in enumerate(ids):
                leaves = leaves_tensor.numpy()
                coords = positions[batch, :len(leaves)].numpy()
                graph = actual.build_graph(coords, leaves, k=32)
                old = legacy.build_graph(coords, leaves, k=32)
                for key in ("indices", "allowed", "fallback", "group_ids"):
                    assert torch.equal(graph[key], old[key]), "Inherited FLE support changed: " + key
                for i, leaf in enumerate(leaves):
                    members = np.flatnonzero(leaves == leaf)
                    chosen = graph["indices"][i][graph["allowed"][i]].numpy()
                    assert len(chosen) == min(32, len(members))
                    assert len(set(chosen.tolist())) == len(chosen)
                    assert np.all(leaves[chosen] == leaf)
                    distances = ((coords[members] - coords[i]) ** 2).sum(-1)
                    ordered = np.sort(distances)
                    expected_tie = len(members) > 32 and ordered[31] == ordered[32]
                    assert bool(graph["fallback"][i]) == expected_tie
                    if not expected_tie:
                        chosen_distances = ((coords[chosen] - coords[i]) ** 2).sum(-1)
                        assert chosen_distances.max() <= ordered[min(32, len(members)) - 1] + 1e-10
                metadata.append({"valid_points": len(leaves), "fallback_rows": int(graph["fallback"].sum()),
                                 "support_matches_frozen_FLE": True, "cross_leaf_edges": 0})
            return metadata

        def values_and_grads(module, x, padding, positions, ids, reference, own_only=False):
            x = x.detach().clone().requires_grad_(True)
            if reference:
                y = module.forward_reference(x, padding, positions, ids, donor_cut=own_only)
            elif own_only:
                y = module.forward_own_only(x, padding, positions, ids)
            else:
                y = module(x, padding, positions, ids)
            weight = torch.linspace(0.2, 1.1, y.numel(), dtype=y.dtype).reshape_as(y)
            scalar = (y * weight).sum() + 0.07 * y.square().sum()
            named = list(module.named_parameters())
            gradients = torch.autograd.grad(scalar, [x] + [p for _, p in named], allow_unused=True)
            names = ["features"] + [name for name, _ in named]
            return y.detach(), dict(zip(names, gradients))

        def compare_gradients(left, right, dtype):
            errors = {}
            assert set(left) == set(right)
            for name in left:
                a, b = left[name], right[name]
                assert (a is None) == (b is None), "Unused-gradient mismatch: " + name
                if a is None:
                    errors[name] = {"both_unused": True}
                else:
                    assert torch.isfinite(a).all() and torch.isfinite(b).all()
                    errors[name] = {"max_abs_error": close(a, b, dtype)}
            return errors

        for name in CASE_NAMES:
            dtype = torch.float32 if name.startswith("float32") else torch.float64
            current = model.float() if dtype == torch.float32 else model
            features, padding, positions, ids = fixture(name, dtype)
            entry = {"name": name, "dtype": str(dtype)}
            result["cases"].append(entry)
            entry["support"] = support_checks(features, padding, positions, ids)
            a, ga = values_and_grads(current, features, padding, positions, ids, False)
            b, gb = values_and_grads(current, features, padding, positions, ids, True)
            entry["output_max_abs_error"] = close(a, b, dtype)
            entry["all_differentiable_input_and_parameter_gradients"] = compare_gradients(ga, gb, dtype)
            assert torch.isfinite(a).all() and torch.count_nonzero(a[padding]) == 0
            assert torch.count_nonzero(ga["features"][padding]) == 0
            own, go = values_and_grads(current, features, padding, positions, ids, False, True)
            own_ref, gor = values_and_grads(current, features, padding, positions, ids, True, True)
            entry["own_only_output_max_abs_error"] = close(own, own_ref, dtype)
            entry["own_only_all_gradients"] = compare_gradients(go, gor, dtype)
            # Independent matched own-only formula, including raw-self tie fallback.
            xhead = features.reshape(*features.shape[:-1], 8, 32)
            hidden = torch.nn.functional.gelu(torch.einsum("bnhd,hod->bnho", xhead, current.wr) + current.b1)
            expected = (torch.einsum("bnhd,hod->bnho", hidden, current.w2) + current.b2).reshape_as(features)
            for batch, leaves in enumerate(ids):
                n = len(leaves)
                graph = actual.build_graph(positions[batch, :n].numpy(), leaves.numpy(), k=32)
                mask = graph["fallback"]
                expected[batch, :n] = torch.where(mask[:, None], features[batch, :n], expected[batch, :n])
                if bool(mask.any()):
                    groups = graph["group_ids"]
                    for i in torch.nonzero(mask).flatten().tolist():
                        mean = features[batch, :n][groups == groups[i]].mean(0)
                        close(a[batch, i], mean, dtype)
            expected = expected.masked_fill(padding[:, :, None], 0)
            entry["own_only_independent_formula_error"] = close(own, expected, dtype)
            entry["full_vs_own_only_max_abs_difference"] = float((a - own).abs().max())
            # Geometry and IDs use detached inherited support; only floating feature inputs are differentiable.
            entry["non_differentiable_inputs"] = ["padding bool", "fine IDs long", "geometry detached by inherited builder"]
            # Tie fallback must stay permutation-equivariant rather than choosing tied point identities.
            if name == "cutoff_ties_and_other_leaf":
                order = torch.arange(features.shape[1] - 1, -1, -1)
                reverse_ids = [ids[0][order]]
                permuted = current(features[:, order], padding[:, order], positions[:, order], reverse_ids)
                entry["tie_permutation_max_abs_error"] = close(a[:, order], permuted, dtype)
            entry["passed"] = True

        # Explicit same-leaf donor and own-only cuts on ordinary AND fallback rows.
        model = model.double()
        result["structural_controls"] = []
        for fixture_name in ("all_valid_multileaf", "cutoff_ties_and_other_leaf"):
            features, padding, positions, ids = fixture(fixture_name, torch.float64)
            x = features.detach().clone().requires_grad_(True)
            y = model(x, padding, positions, ids)
            full_grad = torch.autograd.grad(y[0, 0].sum(), x)[0][0]
            xown = features.detach().clone().requires_grad_(True)
            own_y = model.forward_own_only(xown, padding, positions, ids)
            own_grad = torch.autograd.grad(own_y[0, 0].sum(), xown)[0][0]
            same_leaf = ids[0] == ids[0][0]
            offdiag = torch.arange(len(ids[0])) != 0
            assert torch.count_nonzero(full_grad[~same_leaf]) == 0
            assert float(full_grad[same_leaf & offdiag].abs().sum()) > 1e-10
            assert torch.count_nonzero(own_grad[offdiag]) == 0
            assert float(own_grad[0].abs().sum()) > 1e-10
            result["structural_controls"].append({
                "fixture": fixture_name, "recipient": 0, "same_leaf_offdiagonal_gradient_L1":
                float(full_grad[same_leaf & offdiag].abs().sum()),
                "cross_leaf_gradient_nonzeros": int(torch.count_nonzero(full_grad[~same_leaf])),
                "own_only_offdiagonal_gradient_nonzeros": int(torch.count_nonzero(own_grad[offdiag])),
                "own_only_self_gradient_L1": float(own_grad[0].abs().sum()), "passed": True,
            })

        # One fixed toy CPU update of the complete actual operator; no native model, task loss or optimizer.
        features, padding, positions, ids = fixture("small_padded_batch", torch.float64)
        x = features.detach().clone().requires_grad_(True)
        model.zero_grad(set_to_none=True)
        before = {n: p.detach().clone() for n, p in model.named_parameters()}
        output = model(x, padding, positions, ids)
        target = torch.cos(torch.arange(output.numel(), dtype=output.dtype).reshape_as(output) * 0.009) / 10
        toy_loss = (output - target).square().mean()
        toy_loss.backward()
        assert x.grad is not None and torch.isfinite(x.grad).all()
        norms = {}
        for name, parameter in model.named_parameters():
            assert parameter.grad is not None and torch.isfinite(parameter.grad).all(), name
            norms[name] = float(parameter.grad.norm())
            assert norms[name] > 0, "Complete core parameter inactive in ordinary fixture: " + name
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.add_(parameter.grad, alpha=-0.001)
            after_output = model(features, padding, positions, ids)
        changed = {n: float((p.detach() - before[n]).abs().max()) for n, p in model.named_parameters()}
        assert all(value > 0 for value in changed.values()) and torch.isfinite(after_output).all()
        result["complete_operator_toy_update"] = {
            "toy_loss": float(toy_loss.detach()), "gradient_norms": norms, "parameter_max_abs_change": changed,
            "learning_rate_fixed": 0.001, "updates": 1, "finite_after": True, "passed": True,
            "interpretation": "CPU complete isolated operator only; native task loss/native two steps/resources NOT_RUN",
        }
        assert len(result["cases"]) == len(CASE_NAMES) and all(case["passed"] for case in result["cases"])
        result["all_fixed_tests_passed"] = True
    except Exception as error:
        failure = error
        result["all_fixed_tests_passed"] = False
        result["probe_error"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
    finally:
        random.setstate(python_state)
        result["python_rng_restored_exact"] = random.getstate() == python_state
        if torch_state is not None:
            torch.set_rng_state(torch_state)
            result["torch_CPU_rng_restored_exact"] = torch.equal(torch.get_rng_state(), torch_state)
        if numpy_state is not None:
            numpy_rng.set_state(pickle.loads(numpy_state))
            result["numpy_rng_restored_exact"] = pickle.dumps(numpy_rng.get_state()) == numpy_state
        if torch is not None:
            result["cuda_initialized_after"] = torch.cuda.is_initialized()
    result["status"] = "CPU_IMPLEMENTATION_TEST_COMPLETE" if failure is None else "CPU_IMPLEMENTATION_TEST_FAILED"
    result["interpretation_limit"] = "Fixed isolated CPU source tests only; not full native training, efficacy, novelty, resources or scientific admission."
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    assert result["python_rng_restored_exact"] is True
    if torch is not None:
        assert result["cuda_initialized_before"] is False and result["cuda_initialized_after"] is False
    if torch_state is not None:
        assert result["torch_CPU_rng_restored_exact"] is True
    if numpy_state is not None:
        assert result["numpy_rng_restored_exact"] is True
    assert failure is None, "Preserve actual CPU test failure; no replay"


if __name__ == "__main__":
    main()
