"""Bounded full model CPS check on the existing fixed TRAIN batch."""
import copy
import importlib
import json
import os
from pathlib import Path
import sys
import time
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
root = Path("/data3/songcl/Project/Cluster_project/Cluster")
work = Path("/tmp/cps_admission_20260914")
fixed = Path("/data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914")
sys.path[:0] = [str(root), str(root / "framework/lib")]
import torch
import gorilla
import framework.model.Quard_model as packages
packages.__path__ = [str(work), *packages.__path__]
torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
base = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
name = base + "_cps"
cfg = gorilla.Config.fromfile(str(work / (name + ".yaml")))
cfg.model.data_root = "/data3/songcl/data/data_cluster/"
gorilla.set_random_seed(1999)
module = importlib.import_module("framework.model.Quard_model." + name)
model = module.Network(**cfg.model)
state = torch.load(fixed / "best.pth", map_location="cpu", weights_only=False)["model"]
for k in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
    if k in state:
        del state[k]
model.load_state_dict(state, strict=True)
del state
model.cuda()
batch = torch.load(fixed / "fixed_batch.pth", map_location="cpu", weights_only=False)["batch"]
report = dict(scenes=batch["scan_ids"], expressions=len(batch["object_idss"]),
              labels=batch["object_idss"], scene_lengths=batch["scenes_len"].tolist(),
              parameters=sum(p.numel() for p in model.parameters()), modes={})
model.train()
for amp in (False, True):
    gorilla.set_random_seed(1999)
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
        loss, details = model(copy.deepcopy(batch), mode="loss")
    loss.backward()
    torch.cuda.synchronize()
    assert torch.isfinite(loss).all()
    assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    assert float(details["cps_eligible_pairs"]) > 0
    report["modes"][str(amp)] = dict(loss=float(loss), finite_backward=True,
        peak_mib=torch.cuda.max_memory_allocated()/2**20, seconds=time.monotonic()-started,
        cps={k: float(v.detach()) for k,v in details.items() if k.startswith("cps_")})
    model.zero_grad(set_to_none=True)
    del loss, details
path = work / "full_check.json"
assert not path.exists()
path.write_text(json.dumps(report, indent=2, default=str))
print(json.dumps(report, indent=2, default=str))
