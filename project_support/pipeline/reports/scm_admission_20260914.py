"""Offline admission checks. Never starts a trainer or writes model checkpoints."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import torch
import torch.distributed as dist
import torch.multiprocessing as mp


def load_helper(path):
    spec = importlib.util.spec_from_file_location("scm_helper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ddp_worker(rank, rendezvous, helper, output):
    torch.set_num_threads(1)
    dist.init_process_group("gloo", init_method="file://" + rendezvous,
                            rank=rank, world_size=2)
    fn = load_helper(helper)
    results = []
    for counts in ((1, 3), (0, 4), (0, 0)):
        weight = torch.tensor(2., requires_grad=True)
        count = counts[rank]
        numerator = weight * count
        matches = torch.tensor(float(count * 2))
        dist.all_reduce(matches)
        loss, valid = fn.parent_reduction(numerator, matches, count)
        loss.backward()
        gradient = weight.grad.clone()
        dist.all_reduce(gradient)
        gradient /= 2
        expected = .25 if sum(counts) else 0.
        torch.testing.assert_close(gradient, torch.tensor(expected))
        assert valid.item() == sum(counts)
        results.append(dict(counts=counts, gradient=gradient.item(),
                            global_valid=valid.item(), expected=expected))
    if rank == 0:
        Path(output).write_text(json.dumps(results, indent=2))
    dist.destroy_process_group()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--helper", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    fn = load_helper(args.helper)
    torch.set_num_threads(1)
    torch.manual_seed(1999)
    results = {}
    for device in ("cpu", "cuda"):
        masks = torch.randn(4, 11, device=device, requires_grad=True)
        scores = torch.randn(4, device=device, requires_grad=True)
        xyz = torch.randn(11, 3, device=device)
        target = (torch.arange(11, device=device) < 3).float()
        loss, status = fn.spatial_transport(masks, scores, xyz, target)
        assert status == "valid"
        for dtype in ([torch.bfloat16] if device == "cpu"
                      else [torch.float16, torch.bfloat16]):
            with torch.autocast(device, dtype=dtype):
                got, _ = fn.spatial_transport(
                    masks.to(dtype), scores.to(dtype), xyz, target)
            assert got.dtype == torch.float32 and torch.isfinite(got)
            grads = torch.autograd.grad(got, (masks, scores))
            assert all(torch.isfinite(g).all() and g.abs().sum() > 0 for g in grads)
            results[f"{device}_{dtype}"] = dict(loss=got.item(), finite_gradient=True)
        for label, m, s, x, y in [
            ("no_queries", masks[:0], scores[:0], xyz, target),
            ("no_superpoints", masks[:, :0], scores, xyz[:0], target[:0]),
            ("no_target", masks, scores, xyz, target * 0),
            ("zero_extent", masks, scores, xyz * 0, target),
        ]:
            val, why = fn.spatial_transport(m, s, x, y)
            assert why == label and val.item() == 0 and val.requires_grad
        double_m = masks.detach().double().requires_grad_()
        double_s = scores.detach().double().requires_grad_()
        assert torch.autograd.gradcheck(
            lambda m, s: fn.spatial_transport(m, s, xyz.double(), target.double())[0],
            (double_m, double_s))
        results[device + "_gradcheck_empty"] = "PASS"
    mp.spawn(ddp_worker, args=(str(out / "rendezvous"), args.helper,
                              str(out / "ddp.json")), nprocs=2, join=True)
    results["ddp"] = json.loads((out / "ddp.json").read_text())
    results["torch"] = torch.__version__
    results["device"] = torch.cuda.get_device_name()
    (out / "unit_results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
