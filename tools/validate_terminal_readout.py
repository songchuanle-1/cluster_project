"""CUDA structural and gradient tests for independent terminal-readout models."""
import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gorilla
import torch


BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
MODES = {"mqst": "subtree_branch", "mqpp": "path_posterior",
         "mqht": "hierarchy_transport", "mqfc": "frontier_cover"}


def pooling_test(module, mode):
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
    point_mask = torch.tensor(
        [[False]*5, [False]*3+[True]*2], device=device)
    offsets = torch.tensor([0, 5, 8], device=device)
    query = torch.randn(2, 3, 8, device=device, requires_grad=True)
    points = torch.randn(2, 5, 8, device=device, requires_grad=True)
    masks = torch.randn(2, 3, 5, device=device, requires_grad=True)
    refiner = module.MaskConditionedQueryRefiner(8, mode=mode).cuda()
    result = refiner(query, masks, points, point_mask, bank, offsets)
    assert result.shape == query.shape and torch.isfinite(result).all()
    (result * torch.randn_like(result)).sum().backward()
    for tensor in (query, points, masks):
        assert torch.isfinite(tensor.grad).all()
        assert tensor.grad.abs().sum() > 0
    assert points.grad[1, 3:].abs().sum() == 0
    assert masks.grad[1, :, 3:].abs().sum() == 0
    changed = points.detach().clone()
    changed[1] += 1000
    other = refiner(query.detach(), masks.detach(), changed,
                    point_mask, bank, offsets)
    torch.testing.assert_close(other[0], result.detach()[0])
    # Batched padded evaluation must equal the unpadded single-scene evaluation.
    single = module.SharedClusterBank([4, 2, 1], d_model=8).cuda()
    single.cluster_ids_list = [[level[1]] for level in bank.cluster_ids_list]
    alone = refiner(query.detach()[1:2], masks.detach()[1:2, :, :3],
                    points.detach()[1:2, :3], point_mask[1:2, :3],
                    single, torch.tensor([0, 3], device=device))
    torch.testing.assert_close(alone[0], result.detach()[1])


def decoder_test(module, config):
    torch.manual_seed(1999)
    cfg = gorilla.Config.fromfile(config)
    dec = module.DEC(in_channel=cfg.model.media,
                     sampling_module=cfg.model.sampling_module,
                     **cfg.model.dec).cuda().eval()
    device = "cuda"
    npoints = 300
    offsets = torch.tensor([0, npoints], device=device)
    points = torch.randn(npoints, cfg.model.media, device=device,
                         requires_grad=True)
    seeds = torch.arange(cfg.model.fps_num, device=device).unsqueeze(0)
    positions = torch.randn(npoints, 3, device=device)
    language = torch.randn(1, 8, 768, device=device)
    lang_mask = torch.ones(1, 8, dtype=torch.bool, device=device)
    events = []
    saved_masks = []
    handles = []
    for index, layer in enumerate(dec.decoder_layers):
        def before(mod, args, index=index):
            events.append(f"decoder{index}")
        handles.append(layer.register_forward_pre_hook(before))

    def refine_before(mod, args):
        events.append("refiner")
        assert args[1] is saved_masks[-1]

    def mask_after(mod, args, output):
        saved_masks.append(output[2])

    handles.append(dec.decoder_layers[-2].register_forward_hook(mask_after))
    handles.append(dec.query_context_refiner.register_forward_pre_hook(refine_before))
    result = dec(points, seeds, offsets, lang_feats=language,
                 lang_masks=lang_mask, sp_pos=positions)
    expected = [f"decoder{i}" for i in range(len(dec.decoder_layers) - 1)]
    expected += ["refiner", f"decoder{len(dec.decoder_layers) - 1}"]
    assert events == expected, events
    assert len(result["aux_outputs"]) == len(dec.decoder_layers) - 1
    assert torch.isfinite(result["masks"]).all()
    loss = result["masks"].square().mean() + result["orth_reg_loss"]
    loss.backward()
    assert torch.isfinite(points.grad).all() and points.grad.abs().sum() > 0
    weight = dec.query_context_refiner.out_proj[0].weight
    assert torch.isfinite(weight.grad).all() and weight.grad.abs().sum() > 0
    for handle in handles:
        handle.remove()
    return events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suffix", choices=tuple(MODES))
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    if args.suffix is None:
        for suffix in MODES:
            subprocess.run([sys.executable, __file__, "--suffix", suffix,
                            "--report-dir", str(report_dir)], check=True)
        return
    name = f"{BASE}_{args.suffix}_tr"
    module = importlib.import_module(f"framework.model.Quard_model.{name}.dec")
    pooling_test(module, MODES[args.suffix])
    events = decoder_test(
        module, f"configs/Quard/ctf_hcg_csort_{args.suffix}_tr/{name}.yaml")
    result = {"variant": name, "passed": True, "decoder_events": events,
              "tests": ["finite pooling", "nonzero input gradients",
                        "padding exclusion", "batch isolation",
                        "batched versus unpadded", "exact terminal boundary",
                        "penultimate mask identity", "decoder backward",
                        "all auxiliary predictions retained"]}
    (report_dir / f"{name}_tests.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
