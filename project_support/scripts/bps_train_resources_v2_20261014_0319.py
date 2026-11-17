"""Uniform clean-process native forward/backward resource comparison."""
import argparse
import copy
from datetime import datetime, timezone
import gc
import hashlib
import importlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import socket
import statistics
import sys
import time

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
TOKEN = "1d59938f077948578e91e2cf34fc9d53"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--target", required=True, choices=("baseline", "champion", "candidate"))
    args = parser.parse_args()
    assert args.token == TOKEN and socket.gethostname() == "das"
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "7"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    stage = PIPE / ("bps_staging_" + TOKEN + "_v2")
    sys.path[:0] = [str(stage), str(ROOT), str(ROOT / "framework/lib"), str(PIPE)]
    import pdc_predict_resource_protocol_20261009 as protocol
    assert sha(stage / "pdc_predict_resource_protocol_20261009.py") == "10b2a09ff117352717d04110432c5d181632b3aebbd8e792eed9f9e69b5bfb76"
    import numpy as np
    import torch
    import gorilla
    from torch.utils.data import DataLoader
    from framework.dataset import build_dataset
    from bps_native_20261014_0319 import fingerprint
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.25)
    static = json.loads((stage / "source_manifest.json").read_text())
    if args.target == "candidate":
        config = stage / (NAME + ".yaml")
        assert sha(config) == static["config_sha256"]
        package = stage / NAME
        assert {p.name: sha(p) for p in package.glob("*.py")} == static["package"]
        spec = importlib.util.spec_from_file_location(
            "bps_train_resource_validation", package / "__init__.py",
            submodule_search_locations=[str(package)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        Network = module.Network
        source_identity = static["package"]
    else:
        target = protocol.TARGETS[args.target]
        config = ROOT / target["config"]
        assert sha(config) == target["config_sha256"]
        assert protocol._model_package_sha256(ROOT, target["name"]) == target["model_source_sha256"]
        Network = importlib.import_module("framework.model.Quard_model." + target["name"]).Network
        source_identity = target["model_source_sha256"]
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = str(DATA)
    reference = gorilla.Config.fromfile(str(PIPE / "majority_erasure_original_config_20261012_0910.yaml"))
    reference.data.train.data_root = str(DATA) + "/"
    assert reference.train.seed == 1999 and reference.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(copy.deepcopy(reference.data.train), logging.getLogger("bps-train-resource"))
    loader = DataLoader(torch.utils.data.Subset(dataset, [5743, 7787]), batch_size=2,
                        num_workers=0, shuffle=False, collate_fn=dataset.collate_fn)
    batch = next(iter(loader))
    input_sha = fingerprint(batch)
    gorilla.set_random_seed(1999)
    model = Network(**dict(cfg.model))
    checkpoint = DATA / "sp_unet_backbone.pth"
    gorilla.load_checkpoint(model, str(checkpoint), strict=False, map_location="cpu")
    model.cuda().train()
    losses = []
    torch.cuda.reset_peak_memory_stats()
    def run():
        model.zero_grad(set_to_none=True)
        gorilla.set_random_seed(1999)
        loss, parts = model(batch, mode="loss")
        if not bool(torch.isfinite(loss).all()):
            raise RuntimeError("Nonfinite native loss")
        loss.backward()
        if any(p.grad is not None and not bool(torch.isfinite(p.grad).all())
               for p in model.parameters()):
            raise RuntimeError("Nonfinite native backward")
        value = float(loss.detach())
        del loss, parts
        return value
    for _ in range(20):
        run()
    torch.cuda.synchronize()
    times = []
    for _ in range(100):
        torch.cuda.synchronize()
        started = time.perf_counter()
        value = run()
        torch.cuda.synchronize()
        times.append((time.perf_counter() - started) * 1000)
        losses.append(value)
    readout = (model.between_support.last_readout if args.target == "candidate" else None)
    metrics = {"latency_ms_median": statistics.median(times),
               "latency_ms_p90": float(np.percentile(times, 90)),
               "peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
               "peak_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
               "params": sum(p.numel() for p in model.parameters()),
               "loss_min": min(losses), "loss_max": max(losses)}
    result = {"tick_token": TOKEN, "target": args.target,
              "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "config_sha256": sha(config),
              "source_identity": source_identity, "checkpoint_sha256": sha(checkpoint),
              "protocol": {"mode": "loss_forward_backward", "model_training": True,
                           "groups": [5743, 7787], "batch_size": 2, "seed": 1999,
                           "warmup": 20, "repeat": 100, "input_sha256": input_sha,
                           "checkpoint": "native_common_backbone", "optimizer": False},
              "metrics": metrics, "readout": readout, "all_losses_gradients_finite": True,
              "native_forward_count": 120, "native_backward_count": 120,
              "optimizer_steps": 0,
              "scope": "Supplemental shared training-path resources including CPU geometry; no optimizer/efficacy/exclusive speed."}
    output = PIPE / ("bps_train_resources_v2_" + args.target + "_" + TOKEN + ".json")
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "target": args.target,
                      "metrics": metrics, "input_sha256": input_sha}), flush=True)


if __name__ == "__main__":
    main()
