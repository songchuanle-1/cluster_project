"""Default NOP. Exact-source CPU-only SINC core tests, never native admission."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import socket
import sys
import time
import traceback

OWNER = {
    "token": "1aa2d994ab004c93b2ea069c90ef9356",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-10T05:07:20.849412+00:00",
    "deadline_at": "2026-11-10T06:07:20.849412+00:00",
    "context_sha256": "eff960250947a7e168ea5f144742d7a877fd810d38f3f958cca86ab058cc9a93",
    "pending_sha256": "d7e6661624a7282adbfadedf6e35e015206fb97cb7ab4add04a79974af7a6f58"
}
STAGE = Path("/data/songcl/Project/Cluster_project/pipeline/cpu_core_1aa2d994")
SOURCE_SHA = "4dfac3788bc9cdff3f312b2c04ea4e320b66bd24cdd43e67a343ea50c3a6c619"
PARAMETERS = {"point_weight", "factor_weight", "receiver_weight", "output_weight",
              "point_bias", "message_bias", "output_bias"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_TORCH_OR_EXTERNAL_ACTION"}))
        return
    assert socket.gethostname() == "dl04-MS-7E06" and os.getuid() == os.geteuid() == 1001
    assert Path.cwd() == STAGE and Path(__file__).resolve().parent == STAGE
    assert sys.dont_write_bytecode and not sys.flags.isolated and not sys.flags.optimize
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "" and os.environ["PYTHONDONTWRITEBYTECODE"] == "1"
    assert str(Path(sys.executable)) == "/home/songcl/.conda/envs/project_cluster/bin/python"
    assert sha(sys.executable) == "61ae9cdb79cb325d09a903fc05610369ee6488e954b19e165aad9dd6ba0e72f5"
    assert datetime.now(timezone.utc) < datetime.fromisoformat(OWNER["deadline_at"])
    request = json.loads((STAGE / "request.json").read_text())
    assert request["owner"] == OWNER and request["GPU_use"] is False
    assert sha(STAGE / "simplex_incidence.py") == SOURCE_SHA
    assert sha(__file__) == request["producer_sha256"]
    result = {"owner": OWNER, "candidate_id": "fine-leaf-geometric-simplex-incidence-composition",
              "experiment_id": "M235-SINC", "recorded_at": datetime.now(timezone.utc).isoformat(),
              "producer_sha256": sha(__file__), "source_sha256": SOURCE_SHA,
              "request_sha256": sha(STAGE / "request.json"), "GPU_use": False,
              "CUDA_API_called": False, "native_TRAIN": "NOT_RUN", "resources": "NOT_RUN",
              "native_model_or_dataset_imported": False, "native_task_loss": "NOT_RUN",
              "admission_granted": False, "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
              "all_fixed_tests_passed": False, "cases": []}
    python_state, torch_state, numpy_state = random.getstate(), None, None
    started = time.monotonic()
    torch = np = None
    error = None
    try:
        import torch
        import numpy as np
        import scipy
        torch_state, numpy_state = torch.get_rng_state().clone(), np.random.get_state()
        assert not getattr(sys.modules.get("torch.cuda"), "_initialized", False)
        torch.set_num_threads(1)
        # Seed the CPU generator directly; never call torch.manual_seed/CUDA APIs.
        torch.random.default_generator.manual_seed(1999)
        spec = importlib.util.spec_from_file_location("hash_bound_sinc_core", STAGE / "simplex_incidence.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        model = module.FineLeafSimplexIncidence(channels=256, heads=8).double()
        assert set(dict(model.named_parameters())) == PARAMETERS
        assert sum(p.numel() for p in model.parameters()) == 33536
        assert all(p.device.type == "cpu" for p in model.parameters())
        result["libraries"] = {"torch": torch.__version__, "numpy": np.__version__, "scipy": scipy.__version__}
        result["parameter_shapes"] = {name: list(p.shape) for name, p in model.named_parameters()}
        result["parameter_count"] = 33536
        points = {
            "singleton": [[0, 0, 0]],
            "coincident": [[1, 2, 3]] * 5,
            "collinear": [[0, 0, 0], [1, 0, 0], [2.3, 0, 0], [4.1, 0, 0], [6.4, 0, 0]],
            "planar": [[0, 0, 0], [2, 0, 0], [0, 3, 0], [0.4, 0.7, 0], [1.7, 1.1, 0], [1.1, 2.6, 0]],
            "tetrahedron": [[0, 0, 0], [2, 0, 0], [0, 3, 0], [0, 0, 4]],
            "delaunay": [[0, 0, 0], [2, 0, 0], [0, 3, 0], [0, 0, 4],
                         [0.3, 0.7, 0.9], [1.1, 0.4, 1.7], [0.4, 1.8, 1.2], [1.6, 1.3, 0.3]],
        }
        points["duplicates"] = points["delaunay"] + [points["delaunay"][0], points["delaunay"][4]]

        def budget():
            assert time.monotonic() - started < 100, "SOFT_CPU_BUDGET_NO_RETRY"
            assert datetime.now(timezone.utc) < datetime.fromisoformat(OWNER["deadline_at"])

        def fixture(name, dtype):
            if name == "padded_multiscene":
                scenes = [points["tetrahedron"] + [[10, 0, 0], [11, 0, 0], [12.5, 0, 0]],
                          points["singleton"] + [[10, 0, 0], [12, 0, 0], [10, 3, 0]]]
                labels = [[3] * 4 + [8] * 3, [11] + [17] * 3]
            else:
                scenes, labels = [points[name]], [[3] * len(points[name])]
            width = max(map(len, scenes)) + 2
            a = torch.arange(len(scenes) * width * 256, dtype=dtype).reshape(len(scenes), width, 256)
            x = torch.sin(a * 0.013 + 0.1) / 5 + torch.cos(a * 0.007) / 7
            pad = torch.ones(len(scenes), width, dtype=torch.bool)
            pos = torch.zeros(len(scenes), width, 3, dtype=torch.float64)
            ids = []
            for batch, scene in enumerate(scenes):
                pos[batch, :len(scene)] = torch.tensor(scene, dtype=torch.float64)
                pad[batch, :len(scene)] = False
                ids.append(torch.tensor(labels[batch], dtype=torch.long))
            return x, pad, pos, ids

        def close(a, b):
            atol, rtol = (2e-10, 2e-8) if a.dtype == torch.float64 else (5e-5, 5e-4)
            torch.testing.assert_close(a, b, atol=atol, rtol=rtol)
            return float((a - b).abs().max()) if a.numel() else 0.0

        def values_grads(current, x, pad, pos, ids, reference=False, own=False):
            current.zero_grad(set_to_none=True)
            x = x.detach().clone().requires_grad_()
            if reference:
                y = current.forward_reference(x, pad, pos, ids, own_only=own)
            else:
                y = current.forward_own_only(x, pad, pos, ids) if own else current(x, pad, pos, ids)
            weights = torch.cos(torch.arange(y.numel(), dtype=y.dtype).reshape_as(y) * 0.019 + 0.23)
            loss = (y * weights).sum() / y.numel()
            grads = torch.autograd.grad(loss, [x] + list(current.parameters()), allow_unused=False)
            assert all(bool(torch.isfinite(g).all()) and g.device.type == "cpu" for g in grads)
            assert bool(torch.isfinite(y).all()) and int(torch.count_nonzero(y[pad])) == 0
            assert int(torch.count_nonzero(grads[0][pad])) == 0
            return y.detach(), [g.detach() for g in grads]

        names = ["singleton", "coincident", "collinear", "planar", "tetrahedron",
                 "delaunay", "duplicates", "padded_multiscene"]
        for name, dtype in [(n, torch.float64) for n in names] + [("delaunay", torch.float32)]:
            budget()
            current = copy.deepcopy(model).to(dtype=dtype)
            x, pad, pos, ids = fixture(name, dtype)
            y, gradients = values_grads(current, x, pad, pos, ids)
            yr, reference_gradients = values_grads(current, x, pad, pos, ids, reference=True)
            own, own_gradients = values_grads(current, x, pad, pos, ids, own=True)
            ownr, own_reference_gradients = values_grads(current, x, pad, pos, ids, reference=True, own=True)
            summaries = []
            for batch, leaf in enumerate(ids):
                coords = pos[batch, :len(leaf)].numpy()
                graph, repeated = module.build_graph(coords, leaf.numpy()), module.build_graph(coords, leaf.numpy())
                assert torch.equal(graph["vertices"], repeated["vertices"])
                assert torch.equal(graph["factor_ids"], repeated["factor_ids"])
                vertices, factors = graph["vertices"], graph["factor_ids"]
                assert bool((torch.bincount(vertices, minlength=len(leaf)) > 0).all())
                for factor in range(graph["factor_count"]):
                    assert len(torch.unique(leaf[vertices[factors == factor]])) == 1
                expected_ranks = ([3, 1] if batch == 0 else [0, 2]) if name == "padded_multiscene" else {
                    "singleton": [0], "coincident": [0], "collinear": [1], "planar": [2],
                    "tetrahedron": [3], "delaunay": [3], "duplicates": [3]}[name]
                assert graph["summary"]["affine_ranks"] == expected_ranks
                summaries.append(graph["summary"])
            result["cases"].append({"name": name, "dtype": str(dtype), "output_error": close(y, yr),
                "gradient_errors": [close(a, b) for a, b in zip(gradients, reference_gradients)],
                "own_only_output_error": close(own, ownr),
                "own_only_gradient_errors": [close(a, b) for a, b in zip(own_gradients, own_reference_gradients)],
                "graph_summaries": summaries, "repeated_support_exact": True, "padding_output_and_gradient_zero": True,
                "all_input_and_seven_parameter_gradients_finite": True})
        # Actual autograd -> actual CPU optimizer step, no fixture weight override.
        budget()
        update_model = copy.deepcopy(model)
        x, pad, pos, ids = fixture("delaunay", torch.float64)
        optimizer = torch.optim.SGD(update_model.parameters(), lr=0.01)
        before = {n: p.detach().clone() for n, p in update_model.named_parameters()}
        out = update_model(x, pad, pos, ids)
        weights = torch.cos(torch.arange(out.numel(), dtype=out.dtype).reshape_as(out) * 0.019 + 0.23)
        ((out * weights).sum() / out.numel()).backward()
        result["update_gradients"] = {n: {"finite": bool(torch.isfinite(p.grad).all()),
            "abs_max": float(p.grad.abs().max()) if bool(torch.isfinite(p.grad).all()) else None}
            for n, p in update_model.named_parameters()}
        assert all(g["finite"] and g["abs_max"] > 0 for g in result["update_gradients"].values())
        optimizer.step()
        result["parameter_updated"] = {n: not torch.equal(before[n], p) for n, p in update_model.named_parameters()}
        assert all(result["parameter_updated"].values())
        # Geometry permutation/relabeling and padding/scene/leaf isolation.
        budget()
        x, pad, pos, ids = fixture("duplicates", torch.float64)
        n = len(ids[0])
        permutation = torch.tensor([4, 1, 8, 3, 0, 7, 2, 9, 6, 5])
        xp, pp = x.clone(), pos.clone()
        xp[0, :n], pp[0, :n] = x[0, permutation], pos[0, permutation]
        original, permuted = model(x, pad, pos, ids), model(xp, pad, pp, [ids[0][permutation] + 101])
        result["permutation_equivariance_error"] = close(permuted[0, :n], original[0, permutation])
        x, pad, pos, ids = fixture("padded_multiscene", torch.float64)
        base = model(x, pad, pos, ids)
        changed = x.clone()
        changed[pad] = 999
        result["padding_input_independence_error"] = close(model(changed, pad, pos, ids), base)
        changed = x.clone()
        changed[1] += 0.4
        changed[0, 4:7] -= 0.7
        result["scene_and_crossleaf_isolation_error"] = close(model(changed, pad, pos, ids)[0, :4], base[0, :4])
        # Same factor incidence/weights; own_only cuts every nonself feature dependency.
        x = x.detach().clone().requires_grad_()
        full, own = model(x, pad, pos, ids), model.forward_own_only(x, pad, pos, ids)
        full_grad = torch.autograd.grad(full[0, 0].sum(), x, retain_graph=True)[0]
        own_grad = torch.autograd.grad(own[0, 0].sum(), x)[0]
        nonself = own_grad.clone()
        nonself[0, 0] = 0
        assert int(torch.count_nonzero(nonself)) == 0
        assert float(full_grad[0, 1:4].abs().sum()) > 0
        assert int(torch.count_nonzero(full_grad[0, 4:])) == int(torch.count_nonzero(full_grad[1])) == 0
        changed = x.detach().clone()
        changed[0, 1] += 0.2
        full_delta = float((model(changed, pad, pos, ids)[0, 0] - full[0, 0]).abs().max())
        own_delta = close(model.forward_own_only(changed, pad, pos, ids)[0, 0], own[0, 0])
        assert full_delta > 1e-12
        result["nonself_control"] = {"full_nonself_gradient_L1": float(full_grad[0, 1:4].abs().sum()),
            "own_only_nonself_gradient_nonzeros": 0, "full_donor_perturbation_delta": full_delta,
            "own_only_donor_perturbation_delta": own_delta, "crossleaf_and_scene_gradient_nonzeros": 0}
        assert sha(STAGE / "simplex_incidence.py") == SOURCE_SHA
        assert not getattr(sys.modules.get("torch.cuda"), "_initialized", False)
        budget()
        result.update(all_fixed_tests_passed=True, status="CPU_CORE_IMPLEMENTATION_TEST_COMPLETE",
                      native_TRAIN="NOT_RUN", resources="NOT_RUN")
    except BaseException as caught:
        error = caught
        result.update(status="CPU_CORE_IMPLEMENTATION_TEST_FAILED_OR_INCONCLUSIVE",
                      error_type=type(caught).__name__, error=str(caught)[:1000])
        traceback.print_exc()
    finally:
        random.setstate(python_state)
        if torch_state is not None:
            torch.set_rng_state(torch_state)
        if numpy_state is not None:
            np.random.set_state(numpy_state)
        numpy_restored = None
        if numpy_state is not None:
            restored = np.random.get_state()
            numpy_restored = (restored[0] == numpy_state[0] and np.array_equal(restored[1], numpy_state[1])
                              and restored[2:] == numpy_state[2:])
        result.update(python_rng_restored_exact=random.getstate() == python_state,
                      torch_CPU_rng_restored_exact=bool(torch.equal(torch.get_rng_state(), torch_state))
                          if torch_state is not None else None,
                      numpy_rng_restored_exact=numpy_restored,
                      elapsed_seconds=time.monotonic() - started,
                      finished_at=datetime.now(timezone.utc).isoformat())
        encoded = json.dumps(result, ensure_ascii=True, allow_nan=False)
        assert len(encoded.encode()) <= 65536
        with (STAGE / "result.json").open("x", encoding="utf-8") as stream:
            stream.write(encoded + "\n")
        print(encoded, flush=True)
    if error is not None:
        raise error


if __name__ == "__main__":
    main()
