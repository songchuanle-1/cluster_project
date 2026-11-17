"""Paired native full-loss diagnostic, not a production model or admission."""
import copy
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false")
root = Path("/data3/songcl/Project/Cluster_project/Cluster")
sys.path[:0] = [str(root), str(root / "framework/lib")]
import torch
import gorilla
from framework.dataset import build_dataset, build_dataloader
from capture_boundary_components_20260915 import components

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
name = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca"
package = "framework.model.Quard_model." + name
helper = importlib.import_module(package + ".boundary_assignment")
loss_module = importlib.import_module(package + ".loss")
cfg_path = root / "configs/Quard/ctf_hcg_csort_bca" / (name + ".yaml")
cfg = gorilla.Config.fromfile(str(cfg_path))
cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
checkpoint = Path("/data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914/best.pth")
gorilla.set_random_seed(1999)
dataset = build_dataset(cfg.data.train, logging.getLogger("component-full"))
loader = build_dataloader(dataset, batch_size=2, num_workers=0, persistent_workers=False)
# Capture before model initialization to preserve the earlier incidence RNG order.
batches = []
for batch in loader:
    batches.append(batch)
    if len(batches) == 2:
        break
model = importlib.import_module(package).Network(**cfg.model)
state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
    state.pop(key, None)
model.load_state_dict(state, strict=True)
del state
model.cuda().train()
original = loss_module.boundary_loss
capture = {}


def paired(pred, targets, indices, contacts, lengths, denominator):
    global_loss, stats = original(pred, targets, indices, contacts, lengths, denominator)
    total = pred[0].sum() * 0
    records = []
    offset = 0
    for edges, length in zip(contacts, lengths):
        for b in range(offset, offset + int(length)):
            qs, ts = indices[b]
            if targets[b]["masks"] is None or not len(qs):
                continue
            expression = pred[b].sum() * 0
            for q, t in zip(qs.tolist(), ts.tolist()):
                gt = targets[b]["masks"][t].bool()
                groups = components(edges.tolist(), gt.cpu().tolist())
                n = sum(g["size"] for g in groups)
                local = pred[b][q].sum() * 0
                boundary = sorted(v for g in groups for v in g["members"])
                for g in groups:
                    members = g["members"]
                    local = local + helper.conditional_assignment(
                        pred[b][q, members], gt[members]) * len(members) / n
                expression = expression + local
                if n:
                    z = pred[b][q, boundary]
                    glob = helper.conditional_assignment(z, gt[boundary])
                    if len(groups) == 1:
                        torch.testing.assert_close(local, glob, atol=2e-5, rtol=2e-5)
                    shifted = pred[b][q].detach().clone()
                    for j, g in enumerate(groups):
                        shifted[g["members"]] += (j + 1) * 2
                    control = sum(helper.conditional_assignment(
                        shifted[g["members"]], gt[g["members"]]) * g["size"] / n
                        for g in groups)
                    torch.testing.assert_close(local.detach(), control, atol=2e-5, rtol=2e-5)
                records.append(dict(expression=b, query=q, target=t, groups=groups,
                                    global_boundary=float(glob.detach()) if n else 0,
                                    component_boundary=float(local.detach())))
            total = total + expression / len(qs)
        offset += int(length)
    capture.update(pred=pred, records=records, global_loss=global_loss,
                   component_loss=total / denominator.clamp_min(1))
    return global_loss, stats


loss_module.boundary_loss = paired
out = Path("/tmp/component_full_loss_20260915-1625")
out.mkdir(exist_ok=False)
reports = []
for step, batch in enumerate(batches):
    gorilla.set_random_seed(1999)
    full, details = model(copy.deepcopy(batch), mode="loss")
    alternative = full + capture["component_loss"] - capture["global_loss"]
    preds = capture["pred"]
    gg = torch.autograd.grad(full, preds, retain_graph=True)
    cg = torch.autograd.grad(alternative, preds, retain_graph=True)
    assert all(torch.isfinite(v).all() for v in (*gg, *cg))
    # This isolates optimizer action on logits; it is not parameter-space training.
    effects = []
    for gradients in (gg, cg):
        params = [torch.nn.Parameter(p.detach().clone()) for p in preds]
        optimizer = torch.optim.AdamW(params, lr=cfg.optimizer.lr,
                                     weight_decay=cfg.optimizer.weight_decay)
        for p, grad in zip(params, gradients):
            p.grad = grad.detach().clone()
        optimizer.step()
        effects.append([p.detach().cpu() for p in params])
    alternative.backward()
    finite = all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    assert finite
    artifact = out / f"batch_{step}.pth"
    torch.save(dict(logits=[p.detach().cpu() for p in preds],
                    global_gradients=[g.cpu() for g in gg],
                    component_gradients=[g.cpu() for g in cg],
                    logit_adamw_after=effects, records=capture["records"],
                    scenes=batch["scan_ids"], ann_ids=batch["ann_ids"],
                    object_ids=batch["object_idss"]), artifact)
    reports.append(dict(step=step, global_full=float(full.detach()),
                        component_full=float(alternative.detach()),
                        parameter_backward_finite=finite,
                        connected=sum(len(r["groups"]) == 1 for r in capture["records"]),
                        disconnected=sum(len(r["groups"]) > 1 for r in capture["records"]),
                        artifact=str(artifact),
                        sha256=hashlib.sha256(artifact.read_bytes()).hexdigest()))
    print(json.dumps(reports[-1]), flush=True)
    model.zero_grad(set_to_none=True)
    capture.clear()
    del full, alternative, details, gg, cg, preds
report = dict(batches=reports, controls="connected equality and component shifts PASS",
              scope="FP32 native TRAIN two batches; same forward/matches; all BCE/aux retained. "
                    "Logit-space fresh AdamW only, NOT matched parameter optimizer efficacy. "
                    "No novelty, admission, generalization or resource gate claim.",
              sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__), cfg_path, checkpoint, Path(helper.__file__))})
(out / "result.json").write_text(json.dumps(report, indent=2))
