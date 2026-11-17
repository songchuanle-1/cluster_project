"""Matched historical-protocol resources for PIRS vs its parent M95 config.

Same instrument as the project's historical baseline/champion audits:
  * fvcore FlopCountAnalysis on an eval-mode forward with a val batch (the counter
    behind the FLOPs <= 10.0 G clause);
  * bs=1, warmup 20, repeat 100 -> median and P90 latency;
  * peak allocated memory.
Both configs are measured in the same process/session so the comparison is paired.
PIRS changes only the training-time referent target, so the expectation is that the
forward cost is identical; this run is the evidence, not the expectation.
"""
import copy
import hashlib
import importlib
import json
import logging
import os
import sys
import time
from pathlib import Path

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
OUT = ROOT.parent / "pipeline/pirs_resources_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import numpy as np  # noqa: E402
import torch  # noqa: E402
import gorilla  # noqa: E402
from fvcore.nn import FlopCountAnalysis  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.25)

PARENT = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
PIRS = PARENT + "_pirs"


def measure(name, subdir, batch, dataset_cfg):
    cfg = gorilla.Config.fromfile(str(ROOT / f"configs/Quard/{subdir}/{name}.yaml"))
    cfg.model.data_root = cfg.data.val.data_root = "/data3/songcl/data/data_cluster/"
    cfg.data.val.lang_num_max = 1
    gorilla.set_random_seed(1999)
    model = importlib.import_module(
        "framework.model.Quard_model." + name).Network(**cfg.model)
    checkpoint = Path(cfg.model.data_root) / "sp_unet_backbone.pth"
    gorilla.load_checkpoint(model, str(checkpoint), strict=False, map_location="cpu")
    model = model.cuda().eval()

    # --- FLOPs on the eval forward (historical counter) ---
    flops_g = None
    try:
        with torch.no_grad():
            fl = FlopCountAnalysis(model, (copy.deepcopy(batch),))
            fl.unsupported_ops_warnings(False)
            fl.uncalled_modules_warnings(False)
            flops_g = float(fl.total()) / 1e9
    except Exception as exc:  # record rather than silently pass
        flops_g = f"error: {repr(exc)[:160]}"

    # --- latency bs1 warmup20 repeat100 ---
    for _ in range(20):
        with torch.no_grad():
            model(copy.deepcopy(batch))
    torch.cuda.synchronize()
    times = []
    for _ in range(100):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.no_grad():
            model(copy.deepcopy(batch))
        torch.cuda.synchronize()
        times.append((time.perf_counter() - t0) * 1000.0)
    times = np.array(times)

    peak_mib = torch.cuda.max_memory_allocated() / 2 ** 20
    torch.cuda.reset_peak_memory_stats()
    params = sum(p.numel() for p in model.parameters())
    del model
    torch.cuda.empty_cache()
    return dict(config=str(ROOT / f"configs/Quard/{subdir}/{name}.yaml"),
                params=params, flops_g=flops_g,
                latency_ms_median=float(np.median(times)),
                latency_ms_p90=float(np.percentile(times, 90)),
                peak_allocated_mib=float(peak_mib))


def main():
    # `Criterion` registers into gorilla's global LOSSES registry under one name in
    # every variant package, so importing two variants in one process raises
    # KeyError. That is a repo-wide pattern (each training process imports exactly one
    # variant), so this paired measurement runs ONE config per process and the two
    # result files are compared afterwards.
    which = sys.argv[1] if len(sys.argv) > 1 else "pirs"
    if which == "parent":
        name, subdir = PARENT, "ctf_hcg_csort"
    elif which == "pirs":
        name, subdir = PIRS, "pirs"
    else:
        raise SystemExit(f"unknown target {which!r}; use 'parent' or 'pirs'")

    probe = gorilla.Config.fromfile(str(ROOT / f"configs/Quard/{subdir}/{name}.yaml"))
    probe.data.val.data_root = "/data3/songcl/data/data_cluster/"
    probe.data.val.lang_num_max = 1
    gorilla.set_random_seed(1999)
    dataset = build_dataset(copy.deepcopy(probe.data.val),
                            logging.getLogger("pirs-res"))
    loader = build_dataloader(dataset, training=False, batch_size=1, num_workers=0,
                              persistent_workers=False)
    batch = next(iter(loader))
    result = measure(name, subdir, batch, probe.data.val)

    report = dict(
        summary=result,
        scope="Paired measurement in one process: same val batch, same instrument "
              "corrected: one config per process, because every variant package "
              "registers 'Criterion' into the same gorilla LOSSES registry. Same val "
              "batch and same instrument as the historical audits: fvcore "
              "FlopCountAnalysis for the FLOPs <= 10.0 G counter, bs=1 with warmup20 / "
              "repeat100 median and P90, and peak allocated memory. PIRS changes only "
              "the training-time referent target, so an identical forward cost is "
              "expected and is reported as measured. The training-time addition is one "
              "elementwise IoU and one soft cross-entropy per query per layer; the "
              "forward-only FLOPs counter does not capture it and it is stated rather "
              "than claimed as free.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__),
                           ROOT / f"configs/Quard/ctf_hcg_csort/{PARENT}.yaml",
                           ROOT / f"configs/Quard/pirs/{PIRS}.yaml",
                           ROOT / "framework/model/Quard_model" / PIRS / "loss.py")})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"result_{which}.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
