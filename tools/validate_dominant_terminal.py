"""Check hard branch semantics and terminal-only graph without relaxing argmax."""
import argparse
import importlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from tools.validate_terminal_readout import decoder_test


NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqb_tr"
CONFIG = f"configs/Quard/ctf_hcg_csort_mqb_tr/{NAME}.yaml"


def branch_test(module):
    torch.manual_seed(1999)
    device = "cuda"
    bank = module.SharedClusterBank([4, 2, 1], d_model=8).cuda()
    bank.cluster_ids_list = [
        [torch.tensor([0, 0, 1, 2, 3], device=device),
         torch.tensor([0, 1, 2], device=device)],
        [torch.tensor([0, 0, 1, 1], device=device),
         torch.tensor([0, 0, 1], device=device)],
        [torch.tensor([0, 0], device=device),
         torch.tensor([0, 0], device=device)],
    ]
    padding = torch.tensor([[False]*5, [False]*3+[True]*2], device=device)
    offsets = torch.tensor([0, 5, 8], device=device)
    points = torch.randn(2, 5, 8, device=device, requires_grad=True)
    query = torch.randn(2, 3, 8, device=device, requires_grad=True)
    # First query distinguishes mean occupancy from sum; last query tests ties.
    masks = torch.tensor(
        [[[0., 0., .5, -4., -4.], [-4., -4., -4., 4., -4.], [0.]*5],
         [[-4., -4., 4., 100., 100.], [4., -4., -4., 100., 100.], [0.]*5]],
        device=device, requires_grad=True)
    chosen = [[1, 2, 0], [2, 0, 0]]
    refiner = module.MaskConditionedQueryRefiner(8, mode="dominant_branch").cuda()
    probabilities = masks.sigmoid().masked_fill(padding.unsqueeze(1), 0)
    actual = refiner._dominant_branch_pool(
        probabilities, points, padding, bank, offsets)
    # Scalar grouping oracle does not reuse the production cluster aggregation.
    expected = []
    for b, valid in enumerate((5, 3)):
        levels = []
        features = points[b, :valid]
        for ids in (level[b] for level in bank.cluster_ids_list):
            features = torch.stack([
                features[ids == index].mean(dim=0)
                for index in range(int(ids.max().item()) + 1)])
            levels.append(features)
        branches = []
        for selected in chosen[b]:
            ancestry = [levels[0][selected]]
            for level in range(1, len(levels)):
                selected = int(bank.cluster_ids_list[level][b][selected].item())
                ancestry.append(levels[level][selected])
            branches.append(torch.stack(ancestry).mean(dim=0))
        expected.append(torch.stack(branches))
    torch.testing.assert_close(actual, torch.stack(expected))
    result = refiner(query, masks, points, padding, bank, offsets)
    assert result.shape == query.shape and torch.isfinite(result).all()
    (result * torch.randn_like(result)).sum().backward()
    for tensor in (query, points, refiner.out_proj[0].weight):
        assert tensor.grad is not None and torch.isfinite(tensor.grad).all()
        assert tensor.grad.abs().sum() > 0
    assert masks.grad is None, "Hard argmax must not gain a surrogate gradient"
    assert points.grad[1, 3:].abs().sum() == 0

    changed_points = points.detach().clone()
    changed_points[1] += 1000
    changed_masks = masks.detach().clone()
    changed_masks[1] *= -1
    other = refiner(query.detach(), changed_masks, changed_points,
                    padding, bank, offsets)
    torch.testing.assert_close(other[0], result.detach()[0])
    single = module.SharedClusterBank([4, 2, 1], d_model=8).cuda()
    single.cluster_ids_list = [[level[1]] for level in bank.cluster_ids_list]
    alone = refiner(query.detach()[1:2], masks.detach()[1:2, :, :3],
                    points.detach()[1:2, :3], padding[1:2, :3], single,
                    torch.tensor([0, 3], device=device))
    torch.testing.assert_close(alone[0], result.detach()[1])

    switched = masks.detach().clone()
    switched[0, 0] = torch.tensor([-4., -4., -4., -4., 4.], device=device)
    changed = refiner._dominant_branch_pool(
        switched.sigmoid(), points.detach(), padding, bank, offsets)
    assert not torch.allclose(changed[0, 0], actual.detach()[0, 0])
    torch.testing.assert_close(changed[0, 1:], actual.detach()[0, 1:])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()
    from framework import resolve_network
    package = importlib.import_module(f"framework.model.Quard_model.{NAME}")
    assert resolve_network(CONFIG) is package.Network
    module = importlib.import_module(f"framework.model.Quard_model.{NAME}.dec")
    branch_test(module)
    events = decoder_test(module, CONFIG)
    result = {
        "variant": NAME, "passed": True, "decoder_events": events,
        "mask_selection_gradient": "absent by hard argmax design",
        "tests": ["resolver identity", "scalar ancestry oracle",
                  "mean occupancy not sum", "deterministic first-index tie",
                  "mask-dependent branch switching", "padded mask exclusion",
                  "zero padded point gradient", "batch isolation",
                  "batched versus unpadded", "query/point/projection gradients",
                  "no straight-through mask gradient", "exact terminal boundary",
                  "penultimate mask identity", "all auxiliary outputs", "backward"],
    }
    directory = Path(args.report_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{NAME}_tests.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
