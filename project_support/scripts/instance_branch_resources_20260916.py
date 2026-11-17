"""Paired historical-profile cost of the verified instance component only."""
import copy
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import time

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
root = Path("/data3/songcl/Project/Cluster_project/Cluster")
sys.path[:0] = [str(root), str(root/"framework/lib")]
import torch
import numpy as np
import gorilla
from fvcore.nn import FlopCountAnalysis
from framework.dataset import build_dataset, build_dataloader

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
gorilla.set_random_seed(1999)
name = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
config = root/"configs/Quard/ctf_hcg_csort"/(name+".yaml")
cfg = gorilla.Config.fromfile(str(config))
cfg.model.data_root = cfg.data.val.data_root = "/data3/songcl/data/data_cluster/"
cfg.data.val.lang_num_max = 1
model = importlib.import_module("framework.model.Quard_model."+name).Network(**cfg.model).cuda()
checkpoint = Path(cfg.model.data_root)/"sp_unet_backbone.pth"
gorilla.load_checkpoint(model, str(checkpoint), strict=False, map_location="cpu")
model.eval()
dataset = build_dataset(copy.deepcopy(cfg.data.val), logging.getLogger("component-resource"))
loader = build_dataloader(dataset, training=False, batch_size=1, num_workers=0,
                          persistent_workers=False)
batch = next(iter(loader))


class Wrapped(torch.nn.Module):
    def __init__(self, base):
        super().__init__()
        self.base = base
        self.branch = torch.nn.Sequential(torch.nn.Linear(256, 256), torch.nn.ReLU(),
                                          torch.nn.Linear(256, 256)).cuda()
        self.enabled = False
        self.seeds = None
        self.logits = None
        base.dec.register_forward_pre_hook(self.seed_hook)
        base.dec.encoder_layers[0].register_forward_pre_hook(self.feature_hook)

    def seed_hook(self, module, args):
        if self.enabled:
            self.seeds = args[1].long()

    def feature_hook(self, module, args):
        if self.enabled:
            feature = args[2]
            seeds = feature.gather(1, self.seeds[..., None].expand(-1, -1, 256))
            self.logits = self.branch(seeds) @ feature.transpose(1, 2)

    def forward(self, inputs):
        result = self.base(inputs, mode="predict")
        # Return the component so JIT does not eliminate its unused diagnostic path.
        return (result["piou"][0], self.logits) if self.enabled else result["piou"][0]


wrapper = Wrapped(model).eval()
results = []
with torch.no_grad():
    for enabled in (False, True):
        wrapper.enabled = enabled
        profile = FlopCountAnalysis(wrapper, (batch,))
        profile.unsupported_ops_warnings(False)
        profile.uncalled_modules_warnings(False)
        total = profile.total()
        for _ in range(20):
            wrapper(batch)
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        times = []
        for _ in range(100):
            torch.cuda.synchronize()
            start = time.perf_counter()
            output = wrapper(batch)
            torch.cuda.synchronize()
            times.append((time.perf_counter()-start)*1000)
        results.append(dict(component_enabled=enabled, flops=total, flops_g=total/1e9,
            median_ms=float(np.median(times)), p90_ms=float(np.percentile(times, 90)),
            peak_mib=torch.cuda.max_memory_allocated()/2**20,
            unsupported_ops=dict(profile.unsupported_ops()),
            component_shape=list(wrapper.logits.shape) if enabled else None))
        print(json.dumps(results[-1]), flush=True)
result = dict(results=results, batch_size=1, warmup=20, repeat=100,
    device=torch.cuda.get_device_name(), delta_flops=results[1]["flops"]-results[0]["flops"],
    scope="Historical firstVAL/profile/data/pretrained-backbone setup. M95 wrapper "
          "versus samewrapper with native prelanguage FPS component. Both retain "
          "branch parameter allocation;parent peak thus slightly inflated. No full "
          "correspondence/readout,loss or deployable prediction change. Component "
          "cost only,not scientific admission;timings may have external contention.",
    sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), config, checkpoint)})
out = root.parent/"pipeline/instance_branch_resources_20260916"
out.mkdir(exist_ok=True)
(out/"result.json").write_text(json.dumps(result, indent=2))
