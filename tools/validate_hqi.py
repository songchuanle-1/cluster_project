"""Focused HQI topology tests and matched full-model resource measurements."""
import argparse
import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch
from fvcore.nn import FlopCountAnalysis
import gorilla

from framework import resolve_network
from framework.dataset import build_dataset, build_dataloader
from framework.utils import get_root_logger
from tools import train as train_module


PARENT = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CHILD = PARENT + "_hqi"


def topology_test():
    module = importlib.import_module(f"framework.model.Quard_model.{CHILD}.dec")
    bank = module.SharedClusterBank([4, 2, 1], d_model=3).cuda()
    bank.cluster_ids_list = [
        [torch.tensor([0, 0, 1, 2, 3], device="cuda"),
         torch.tensor([0, 1, 1], device="cuda")],
        [torch.tensor([0, 0, 1, 1], device="cuda"),
         torch.tensor([0, 0], device="cuda")],
        [torch.tensor([0, 0], device="cuda"),
         torch.tensor([0], device="cuda")],
    ]
    obj = module.DEC.__new__(module.DEC)
    torch.nn.Module.__init__(obj)
    obj.cluster_bank = bank
    feats = torch.arange(30, device="cuda", dtype=torch.float32).view(2, 5, 3)
    feats.requires_grad_()
    mask = torch.tensor([[False]*5, [False]*3+[True]*2], device="cuda")
    offsets = torch.tensor([0, 5, 8], device="cuda")
    seeds = torch.randn(2, 2, 3, device="cuda", requires_grad=True)
    indices = torch.tensor([[4, 0], [2, 2]], device="cuda")
    out = obj._query_seed_context(seeds, indices, feats, mask, offsets)
    levels = bank.build_cluster_feats(module.batch2flatten(feats, mask), offsets)
    expected = []
    for b in range(2):
        rows = []
        for q in range(2):
            idx = indices[b, q].item()
            parts = [seeds[b, q]]
            for level in range(3):
                idx = bank.cluster_ids_list[level][b][idx].item()
                parts.append(levels[level][b, idx])
            rows.append(torch.cat(parts))
        expected.append(torch.stack(rows))
    torch.testing.assert_close(out, torch.stack(expected))
    out.sum().backward()
    assert torch.isfinite(feats.grad).all() and feats.grad.abs().sum() > 0
    assert seeds.grad.abs().sum() > 0
    assert feats.grad[1, 3:].abs().sum() == 0
    changed = feats.detach().clone()
    changed[1] += 1000
    other = obj._query_seed_context(seeds.detach(), indices, changed, mask, offsets)
    torch.testing.assert_close(other[0], out.detach()[0])
    print("HQI topology: ancestry, uneven padding, repeated seeds, gradients, batch isolation PASS")


def profile(name, data_root, report_dir):
    gorilla.set_random_seed(1999)
    suffix = "ctf_hcg_csort_hqi" if name == CHILD else "ctf_hcg_csort"
    config = f"configs/Quard/{suffix}/{name}.yaml"
    cfg = gorilla.Config.fromfile(config)
    cfg.model.data_root = data_root
    cfg.data.val.data_root = data_root
    cfg.data.val.lang_num_max = 1
    cfg.data.train.data_root = data_root
    cfg.train.pretrain = str(Path(data_root) / "sp_unet_backbone.pth")
    logger = get_root_logger(log_file=str(report_dir / f"{name}.log"))
    model = resolve_network(config)(**cfg.model).cuda()
    gorilla.load_checkpoint(model, cfg.train.pretrain, strict=False, map_location="cpu")
    model.eval()
    dataset = build_dataset(copy.deepcopy(cfg.data.val), logger)
    loader_cfg = copy.deepcopy(cfg.dataloader.val)
    loader_cfg.batch_size = 1
    loader_cfg.num_workers = 0
    loader_cfg.persistent_workers = False
    loader = build_dataloader(dataset, training=False, **loader_cfg)
    batch = next(iter(loader))
    with torch.no_grad():
        flop = FlopCountAnalysis(model, (batch, "predict"))
        flop.unsupported_ops_warnings(False)
        flop.uncalled_modules_warnings(False)
        total = flop.total()
        for _ in range(20):
            model(batch, mode="predict")
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        times = []
        for _ in range(100):
            torch.cuda.synchronize()
            start = time.perf_counter()
            result = model(batch, mode="predict")
            torch.cuda.synchronize()
            times.append((time.perf_counter() - start) * 1000)
        assert all(torch.isfinite(v).all() for v in result["piou"])
        result = {
            "config": config, "flops": total, "flops_g": total / 1e9,
            "unsupported_ops": dict(flop.unsupported_ops()),
            "params": sum(p.numel() for p in model.parameters()),
            "median_ms": float(np.median(times)),
            "p90_ms": float(np.percentile(times, 90)),
            "peak_allocated_mb": torch.cuda.max_memory_allocated() / 1024**2,
            "warmup": 20, "repeat": 100, "batch_size": 1,
            "device": torch.cuda.get_device_name(),
        }
    del model, loader, batch
    torch.cuda.empty_cache()
    print(json.dumps(result))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--stage", choices=("all", "topology", "parent", "child"),
                        default="all")
    args = parser.parse_args()
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    if args.stage == "topology":
        topology_test()
        return
    if args.stage in ("parent", "child"):
        result = profile(PARENT if args.stage == "parent" else CHILD,
                         args.data_root, report_dir)
        (report_dir / f"{args.stage}.json").write_text(json.dumps(result, indent=2))
        return
    # Independent model packages register the same legacy Criterion class name.
    for stage in ("topology", "parent", "child"):
        subprocess.run([sys.executable, __file__, "--data-root", args.data_root,
                        "--report-dir", str(report_dir), "--stage", stage],
                       check=True)
    results = [json.loads((report_dir / f"{stage}.json").read_text())
               for stage in ("parent", "child")]
    (report_dir / "hqi_profile.json").write_text(json.dumps(results, indent=2))
    assert results[1]["flops"] <= 10e9, "HQI exceeds FLOPs limit; do not enqueue"
    assert results[1]["peak_allocated_mb"] <= 1.15 * results[0]["peak_allocated_mb"]
    print("Full-model finite output and resource eligibility PASS")


if __name__ == "__main__":
    main()
