"""Test whether the proposed read transports relation evidence or only values."""
import hashlib
import json
from pathlib import Path

import torch

from instance_distribution_prototype_20260916 import read


def main():
    torch.manual_seed(1999)
    device, dtype = "cuda", torch.float64
    z = torch.tensor([-2., -1., 1., 2.], device=device, dtype=dtype)
    a = torch.tensor([[8., 8., -8., -8.], [-8., -8., 8., 8.]],
                     device=device, dtype=dtype, requires_grad=True)
    b = torch.tensor([[-8., 8., 8., -8.]], device=device, dtype=dtype,
                     requires_grad=True)
    q = torch.tensor([[1., .5, -.2, .7]], device=device, dtype=dtype)
    w = torch.randn(4, 2, device=device, dtype=dtype, requires_grad=True)
    same = torch.tensor([[1., 2., 3., 4.]], device=device, dtype=dtype).repeat(4, 1)
    y, r = read(q, same, a, b, z, w)
    y_flip, r_flip = read(q, same, a, b, -z, w)
    geometry_delta = float((r-r_flip).abs().max())
    output_delta = float((y-y_flip).abs().max())
    grad = torch.autograd.grad(y.square().sum(), w)[0]
    assert geometry_delta > .1
    torch.testing.assert_close(y, y_flip, atol=1e-12, rtol=1e-12)
    assert float(grad.abs().max()) < 1e-12

    # This sweep is a diagnostic limit, not model/config hyperparameter selection.
    direction = torch.tensor([[1., 0., 0., 0.], [1., 0., 0., 0.],
                              [-1., 0., 0., 0.], [-1., 0., 0., 0.]],
                             device=device, dtype=dtype)
    rows = []
    for epsilon in (1., .1, .01, .001, 0.):
        features = same + epsilon * direction
        original, _ = read(q, features, a, b, z, w)
        reflected, _ = read(q, features, a, b, -z, w)
        value = a.sigmoid()
        value = (value/value.sum(-1, keepdim=True)) @ features
        diameter = float((value[0]-value[1]).abs().max())
        delta = float((original-reflected).abs().max())
        assert delta <= diameter + 1e-12
        rows.append(dict(feature_contrast=epsilon, output_delta=delta,
                         instance_value_diameter=diameter))
    # One instance has a unit softmax weight: its relation never reaches the read.
    one, one_r = read(q, same+direction, a[:1], b, z, w)
    one_flip, one_r_flip = read(q, same+direction, a[:1], b, -z, w)
    torch.testing.assert_close(one, one_flip, atol=1e-12, rtol=1e-12)
    assert float((one_r-one_r_flip).abs().max()) > .1
    result = dict(
        checks=dict(equal_values_erase_geometry=True,
                    relation_projection_gradient_zero_with_equal_values=True,
                    output_change_bounded_by_value_diameter=True,
                    singleton_erases_geometry=True),
        geometry_delta=geometry_delta, output_delta=output_delta,
        relation_projection_gradient_max=float(grad.abs().max()),
        limiting_cases=rows,
        conclusion="The proposed value-only read cannot guarantee transport of "
                   "distributional relations. This is a constructive expressivity "
                   "counterexample, not evidence that native descriptors are equal, "
                   "nor proof of training failure or a ban on all attention.",
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    path = Path("/data3/songcl/Project/Cluster_project/pipeline/"
                "instance_relation_readout_contract_20260916")
    path.mkdir(exist_ok=True)
    (path/"result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
