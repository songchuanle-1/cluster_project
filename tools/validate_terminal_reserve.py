"""Independent scalar oracles and decoder-boundary checks for the reserve."""
import argparse
import importlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from tools.validate_terminal_readout import pooling_test, decoder_test, BASE

MODES = {"mqbc": "bottleneck_branch", "mqtd": "topdown_branch",
         "mqsd": "sibling_discrimination"}


def oracle_test(module, suffix):
    device = "cuda"
    bank = module.SharedClusterBank([4, 2, 1], d_model=3).cuda()
    maps = [[0, 0, 1, 2, 3], [0, 0, 1, 1], [0, 0]]
    bank.cluster_ids_list = [[torch.tensor(m, device=device)] for m in maps]
    points = torch.tensor([[[1., 2., 3.], [3., 4., 5.], [9., 1., 0.],
                            [0., 8., 1.], [2., 0., 7.]]], device=device)
    probs = torch.tensor([[[.9, .7, .2, .6, .1],
                           [.1, .2, .3, .8, .9]]], device=device)
    mask = torch.zeros(1, 5, dtype=torch.bool, device=device)
    offsets = torch.tensor([0, 5], device=device)
    refiner = module.MaskConditionedQueryRefiner(3, mode=MODES[suffix]).cuda()
    path = [maps[0]]
    for mapping in maps[1:]:
        path.append([mapping[i] for i in path[-1]])
    occupancy = []
    for ids in path:
        occupancy.append([
            [sum(float(probs[0, q, i]) for i, c in enumerate(ids) if c == k)
             / ids.count(k) for k in range(max(ids) + 1)]
            for q in range(probs.shape[1])
        ])
    # Feature hierarchy averages children, rather than directly weighting points.
    features = [points[0]]
    for mapping in maps:
        features.append(torch.stack([
            torch.stack([features[-1][i] for i, c in enumerate(mapping) if c == k]).mean(0)
            for k in range(max(mapping) + 1)
        ]))
    expected = []
    for qi in range(probs.shape[1]):
        if suffix in ("mqbc", "mqtd"):
            if suffix == "mqbc":
                branches = [[f, maps[1][f], maps[2][maps[1][f]]] for f in range(4)]
                scores = [min(occupancy[l][qi][ids[l]] for l in range(3)) for ids in branches]
                selected = branches[max(range(4), key=lambda f: scores[f])]
            else:
                selected = [None] * 3
                selected[2] = max(range(len(occupancy[2][qi])), key=lambda k: occupancy[2][qi][k])
                for level in (1, 0):
                    children = [k for k, parent in enumerate(maps[level + 1])
                                if parent == selected[level + 1]]
                    selected[level] = max(children, key=lambda k: occupancy[level][qi][k])
            expected.append(torch.stack([features[l + 1][selected[l]] for l in range(3)]).mean(0))
        else:
            weights = []
            for i in range(5):
                advantages = []
                for level in (0, 1):
                    child = path[level][i]
                    siblings = [k for k, parent in enumerate(maps[level + 1])
                                if parent == maps[level + 1][child] and k != child]
                    advantage = (max(0., occupancy[level][qi][child] -
                                     sum(occupancy[level][qi][k] for k in siblings) / len(siblings))
                                 if siblings else 0.)
                    advantages.append(advantage)
                weights.append(sum(advantages) / len(advantages))
            weight = points.new_tensor(weights)
            expected.append((weight[:, None] * points[0]).sum(0) / weight.sum().clamp_min(1e-6))
    method = getattr(refiner, "_" + MODES[suffix] + "_pool")
    args = (probs, points, mask, bank)
    result = method(*args) if suffix == "mqsd" else method(*args, offsets)
    torch.testing.assert_close(result[0], torch.stack(expected))
    assert not torch.allclose(result[0, 0], result[0, 1]), "Masks must select different evidence"
    # Uniform masks exercise deterministic ties / zero sibling advantage.
    uniform = torch.full_like(probs, .5)
    tied = method(uniform, points, mask, bank) if suffix == "mqsd" else method(
        uniform, points, mask, bank, offsets)
    assert torch.isfinite(tied).all()
    if suffix == "mqsd":
        torch.testing.assert_close(tied, torch.zeros_like(tied))
    else:
        torch.testing.assert_close(tied[0, 0], torch.stack([f[0] for f in features[1:]]).mean(0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suffix", choices=MODES, required=True)
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()
    name = f"{BASE}_{args.suffix}_tr"
    module = importlib.import_module(f"framework.model.Quard_model.{name}.dec")
    oracle_test(module, args.suffix)
    pooling_test(module, MODES[args.suffix])
    config = f"configs/Quard/ctf_hcg_csort_{args.suffix}_tr/{name}.yaml"
    events = decoder_test(module, config)
    output = Path(args.report_dir)
    output.mkdir(parents=True, exist_ok=True)
    result = {"variant": name, "passed": True, "decoder_events": events,
              "tests": ["scalar topology oracle", "mask-dependent evidence",
                        "ties or zero-advantage", "finite nonzero input gradients",
                        "padding exclusion", "batch isolation", "padded vs unpadded",
                        "exact terminal boundary", "penultimate mask identity",
                        "decoder backward", "all auxiliary outputs"]}
    (output / f"{name}_tests.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
