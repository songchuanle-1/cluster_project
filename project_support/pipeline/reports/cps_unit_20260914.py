"""Standalone helper verification; no imports of production model registries."""
import importlib.util
import json
import sys
import torch

spec = importlib.util.spec_from_file_location("cps_helper", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fn = module.paired_switch
torch.set_num_threads(1)
tests = []
for device in ["cpu"] + (["cuda"] if torch.cuda.is_available() else []):
    z = torch.tensor([[[0., 2.], [0., -1.]], [[0., -2.], [0., 3.]]],
                     dtype=torch.float64, device=device, requires_grad=True)
    seeds = torch.tensor([[0, 1], [0, 1]], device=device)
    labels = [torch.tensor([1, 2], device=device)] * 2
    target = [[1], [2]]
    loss, count = fn(z, seeds, labels, target, [2])
    assert count["eligible_pairs"] == 1
    assert torch.allclose(loss, torch.nn.functional.softplus(z.new_tensor(-8.)))
    assert torch.autograd.gradcheck(lambda zz: fn(zz, seeds, labels, target, [2])[0], (z,))
    # Object and expression biases cancel, but their interaction does not.
    shifted = z.detach().clone()
    shifted[:, :, 1] += z.new_tensor([[10., 20.], [13., 23.]])
    assert torch.allclose(fn(shifted, seeds, labels, target, [2])[0], loss)
    assert torch.allclose(fn(z[:, [1, 0]], seeds[:, [1, 0]], labels, target, [2])[0], loss)
    assert torch.allclose(fn(z.flip(0), seeds.flip(0), labels, target[::-1], [2])[0], loss)
    zero, counters = fn(z, seeds, labels, target, [1, 1])
    assert zero == 0 and counters["eligible_pairs"] == 0
    assert fn(z, seeds, labels, [[1], [1]], [2])[1]["same_target"] == 1
    assert fn(z, seeds, labels, [[1, 2], [2]], [2])[1]["multi_target"] == 1
    assert fn(z, seeds, [torch.tensor([1, 1], device=device)] * 2, target, [2])[1]["missing_shared_target"] == 1
    assert torch.equal(torch.autograd.grad(zero, z)[0], torch.zeros_like(z))
    for dtype in ([torch.bfloat16] if device == "cpu" else [torch.float16, torch.bfloat16]):
        zz = z.detach().to(dtype).requires_grad_(True)
        with torch.autocast(device, dtype=dtype):
            ll = fn(zz, seeds, labels, target, [2])[0]
        assert ll.dtype == torch.float32 and torch.isfinite(torch.autograd.grad(ll, zz)[0]).all()
    bad = z.detach().clone()
    bad[0, 0, 0] = float("nan")
    try:
        fn(bad, seeds, labels, target, [2])
        raise AssertionError("NaN accepted")
    except ValueError:
        pass
    tests.append(dict(device=device, gradcheck=True, invariances=True,
                      scene_isolation=True, exclusions=True, connected_zero=True,
                      amp=True, nan_rejected=True))
print(json.dumps(dict(status="PASS", tests=tests), indent=2))
