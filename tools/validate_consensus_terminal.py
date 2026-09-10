"""Independent consensus oracle and CUDA terminal-readout graph checks."""
import argparse
import importlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from tools.validate_terminal_readout import BASE, decoder_test, pooling_test


def oracle_test(module):
    device = "cuda"
    maps = [[0, 0, 1, 2, 3], [0, 0, 1, 1], [0, 0]]
    bank = module.SharedClusterBank([4, 2, 1], d_model=3).cuda()
    bank.cluster_ids_list = [[torch.tensor(ids, device=device)] for ids in maps]
    points = torch.tensor([[[1., 2., 3.], [3., 4., 5.], [9., 1., 0.],
                            [0., 8., 1.], [2., 0., 7.]]], device=device)
    probs = torch.tensor([[[.9, .7, .2, .6, .1],
                           [.1, .2, .3, .8, .9]]], device=device)
    point_mask = torch.zeros(1, 5, dtype=torch.bool, device=device)
    refiner = module.MaskConditionedQueryRefiner(3, mode="hierarchy_consensus").cuda()
    paths = [maps[0]]
    for ids in maps[1:]:
        paths.append([ids[c] for c in paths[-1]])

    def scalar_oracle(probabilities):
        results = []
        for qi in range(probabilities.shape[1]):
            occupancy = []
            for ids in paths:
                occupancy.append([
                    sum(float(probabilities[0, qi, j]) for j in range(5) if ids[j] == ids[i])
                    / ids.count(ids[i]) for i in range(5)
                ])
            weights = [min(scale[i] for scale in occupancy) for i in range(5)]
            context = [
                sum(w * float(points[0, i, dim]) for i, w in enumerate(weights))
                / max(sum(weights), 1e-6) for dim in range(points.shape[-1])
            ]
            results.append(context)
        return torch.tensor([results], device=device, dtype=points.dtype)

    def pool(probabilities):
        return refiner._hierarchy_consensus_pool(probabilities, points, point_mask, bank)

    actual = pool(probs)
    torch.testing.assert_close(actual, scalar_oracle(probs), atol=2e-6, rtol=2e-6)
    switched = probs.flip(-1)
    changed = pool(switched)
    torch.testing.assert_close(changed, scalar_oracle(switched), atol=2e-6, rtol=2e-6)
    assert not torch.allclose(actual, changed)
    for value in (0., .5, 1.):
        tied = torch.full_like(probs, value)
        expected = torch.zeros_like(actual) if value == 0 else points.mean(1, keepdim=True).expand_as(actual)
        torch.testing.assert_close(pool(tied), scalar_oracle(tied), atol=2e-6, rtol=2e-6)
        torch.testing.assert_close(pool(tied), expected, atol=2e-6, rtol=2e-6)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()
    report = Path(args.report_dir)
    report.mkdir(parents=True, exist_ok=True)
    name = BASE + "_mqhc_tr"
    config = f"configs/Quard/ctf_hcg_csort_mqhc_tr/{name}.yaml"
    module = importlib.import_module(f"framework.model.Quard_model.{name}.dec")
    oracle_test(module)
    pooling_test(module, "hierarchy_consensus")
    events = decoder_test(module, config)
    from framework import resolve_network
    network = resolve_network(config)
    assert network.__module__ == f"framework.model.Quard_model.{name}.network"
    result = dict(variant=name, passed=True, decoder_events=events,
                  resolver=network.__module__,
                  tests=["independent scalar oracle", "mask switch", "zero and uniform ties",
                         "input gradients", "padding exclusion", "batch isolation",
                         "padded versus unpadded", "exact terminal mask identity",
                         "full decoder backward", "all auxiliary predictions"])
    (report / f"{name}_tests.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
