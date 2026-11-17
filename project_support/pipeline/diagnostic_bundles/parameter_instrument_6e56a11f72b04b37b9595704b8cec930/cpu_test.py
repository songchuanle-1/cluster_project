"""Test the unchanged diagnostic function, not a production mechanism."""

import ast
import hashlib
import json
from pathlib import Path
import sys

import torch

torch.set_num_threads(1)
source, output = map(Path, sys.argv[1:3])
tree = ast.parse(source.read_text())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "parameter_transport")
namespace = {"TRANSPORT": {"previous": None, "calls": 0}}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)


class FixtureCriterion:
    loss_weight = [0, 0, 0, 0, 0, 0, 1.0]

    def loss_sem_align(self, logits):
        return (logits.square().sum() / 2).reshape(1)


class Fixture(torch.nn.Module):
    def __init__(self, initial):
        super().__init__()
        self.coordinate = torch.nn.Parameter(initial.clone())
        self.unused = torch.nn.Parameter(torch.tensor([7.0]))
        self.criterion = FixtureCriterion()


results = []
task_vector = torch.tensor([-1.0, 1.0])
for label, matrix, initial in (
    ("identity_jacobian", torch.eye(2), torch.tensor([1.0, 2.0])),
    ("anisotropic_jacobian", torch.diag(torch.tensor([3.0, 1.0])), torch.tensor([1.0 / 3, 2.0])),
):
    previous = None
    trials = []
    for repeat in range(2):
        model = Fixture(initial)
        logits = matrix @ model.coordinate
        semantic_gradient = logits.detach()
        subsets = {
            "main_secondary": torch.tensor([True, False]),
            "relation_other": torch.tensor([False, True]),
            "fractional_secondary": torch.tensor([True, True]),
            "fractional_repelling": torch.tensor([False, True]),
        }
        task_loss = (logits * task_vector).sum().reshape(1)
        row = namespace["parameter_transport"](
            model, logits, semantic_gradient, subsets,
            {"mask_plus_indicator": task_loss}, (logits,), torch,
        )
        expected_task = matrix.T @ task_vector
        differences = []
        for condition, readout in row["conditions"].items():
            direction = semantic_gradient
            if condition not in ("original", "identity"):
                direction = direction * subsets[condition]
            expected_gradient = matrix.T @ direction
            differences.extend((
                abs(readout["task_dot"] - float((expected_gradient.double() * expected_task.double()).sum())),
                abs(readout["gradient_norm"] - float(expected_gradient.double().norm())),
            ))
            assert readout["nonzero_parameter_tensors"] == 1
            assert readout["unused_parameter_tensors"] == 1
        assert max(differences) <= 1e-6
        assert row["pass_original_native_identity1e6"]
        assert row["requested_parameter_gradient_calls_this_forward"] == 7
        assert not row["parameter_grad_accumulated"]
        assert model.coordinate.grad is None and model.unused.grad is None
        if repeat:
            assert row["parameter_repeat_max_delta"] == 0
            assert row["pass_parameter_repeat1e6"]
        trials.append(row)
    query_dot = float((semantic_gradient * task_vector).sum())
    parameter_dot = trials[0]["conditions"]["original"]["task_dot"]
    results.append({"fixture": label, "query_dot": query_dot, "parameter_dot": parameter_dot,
                    "trials": trials, "analytic_max_delta": max(differences)})
assert results[0]["query_dot"] == results[0]["parameter_dot"] == 1.0
assert results[1]["query_dot"] == 1.0 and results[1]["parameter_dot"] == -7.0
assert namespace["TRANSPORT"]["calls"] == 28
assert namespace["TRANSPORT"]["previous"] is None
report = {
    "status": "PASS", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "fixtures": results, "function_calls": 4, "parameter_gradient_requests": 28,
    "optimizer_steps": 0, "gpu_forwards": 0, "native_cohort_forwards": 0,
    "known_wrong_identity_jacobian_detected": True,
    "scope": "Synthetic CPU instrument validation only. Quadratic fixture is not native semantic supervision; no original scene/model parameter gradient, source-hypothesis result, core admission, trained gain or FD/native-repeat repair is claimed.",
}
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"status": "PASS", "query_dot": 1, "anisotropic_parameter_dot": -7,
                  "calls": 4, "gradient_requests": 28, "gpu_forwards": 0, "optimizer_steps": 0}))
