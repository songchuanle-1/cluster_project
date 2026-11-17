"""Independent production-helper equality against explicit component factorization."""
import importlib.util
import json
import sys
import torch

spec = importlib.util.spec_from_file_location("candidate", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checks = []
for device in ("cpu", "cuda"):
    torch.manual_seed(1999)
    z = torch.randn(3, 6, device=device, dtype=torch.double, requires_grad=True)
    y = torch.tensor([1, 0, 1, 0, 1, 0], device=device, dtype=torch.bool)
    edges = [[0, 1], [2, 3], [4, 5]]
    assert module.boundary_components(edges, y) == [[0, 1], [2, 3], [4, 5]]
    args = ([z], [{"masks": y[None]}],
            [(torch.arange(3, device=device), torch.zeros(3, device=device, dtype=torch.long))],
            [edges], [1], torch.tensor(1., device=device))
    actual, stats = module.boundary_loss(*args)
    expected = sum(module.conditional_assignment(z[:, group], y[group]).mean() / 3
                   for group in [[0, 1], [2, 3], [4, 5]])
    torch.testing.assert_close(actual, expected)
    torch.testing.assert_close(torch.autograd.grad(actual, z, retain_graph=True)[0],
                               torch.autograd.grad(expected, z, retain_graph=True)[0])
    assert torch.autograd.gradcheck(lambda v: module.boundary_loss(
        [v], *args[1:])[0], (z,))
    assert module.boundary_components(edges + [[1, 2], [3, 4]], y) == [list(range(6))]
    assert module.boundary_components([], y) == []
    checks.append(dict(device=device, equality=True, gradients=True, gradcheck=True,
                       induced_graph=True, empty=True, stats=stats))
print(json.dumps(checks))
