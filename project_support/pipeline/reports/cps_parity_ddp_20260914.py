"""CPS same-process inference isolation and inherited DDP reduction check."""
import copy
import importlib
import json
import logging
import os
from pathlib import Path
import sys
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
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
module = importlib.import_module("framework.model.Quard_model." + name)
model = module.Network(**cfg.model).cuda().eval()
state = torch.load(fixed / "best.pth", map_location="cpu", weights_only=False)["model"]
for k in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
    state.pop(k, None)
model.load_state_dict(state)
del state
from framework.dataset import build_dataset, build_dataloader
cfg.data.val.data_root = cfg.model.data_root
cfg.data.val.lang_num_max = 1
cfg.dataloader.val.batch_size = 1
cfg.dataloader.val.num_workers = 0
cfg.dataloader.val.persistent_workers = False
gorilla.set_random_seed(1999)
dataset = build_dataset(copy.deepcopy(cfg.data.val), logging.getLogger("cps_parity"))
batch = next(iter(build_dataloader(dataset, training=False, **copy.deepcopy(cfg.dataloader.val))))
with torch.no_grad():
    gorilla.set_random_seed(1999)
    before = model(copy.deepcopy(batch), mode="predict")
    # Same forward object with a criterion that cannot execute: prediction must
    # not read any training label coupling or call the paired loss.
    def forbidden(*args, **kwargs):
        raise AssertionError("Criterion called in prediction")
    model.criterion.forward = forbidden
    gorilla.set_random_seed(1999)
    after = model(copy.deepcopy(batch), mode="predict")
checked = []
for key in ("piou", "pious", "p_r_iou", "seed_ind", "sample_ind", "pred_pmasks"):
    if key in before:
        checked.append(key)
        for a, b in zip(before[key], after[key]):
            torch.testing.assert_close(torch.as_tensor(a), torch.as_tensor(b))
assert checked, list(before)
# CPU algebra of inherited world-size-averaged gradients; no new all-reduce
# was introduced. Explicitly not a multiprocess production DDP execution.
ddp = []
for counts in ((1, 3), (0, 4), (0, 0)):
    x = torch.tensor(0.7, dtype=torch.double, requires_grad=True)
    denom = max(sum(counts), 1)
    local = [n * torch.nn.functional.softplus(-x) / denom for n in counts]
    actual = torch.autograd.grad(sum(local) / 2, x, retain_graph=True)[0]
    expected = torch.autograd.grad(sum(counts) * torch.nn.functional.softplus(-x) / (denom * 2), x)[0]
    torch.testing.assert_close(actual, expected)
    ddp.append(dict(counts=counts, gradient=float(actual)))
report = dict(inference_criterion_independent=True, expressions=1, checked_keys=checked,
              repeated_seed1999_outputs_close=True, inherited_ddp_algebra=ddp,
              production_multiprocess_ddp_tested=False)
(work / "parity_ddp.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
