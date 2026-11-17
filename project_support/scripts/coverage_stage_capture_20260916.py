"""Same-forward native TRAIN coverage decomposition, diagnostic only."""
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false")
ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
OUT = ROOT.parent / "pipeline/coverage_stage_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import torch
import gorilla
from framework.dataset import build_dataset, build_dataloader

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
name = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
config = ROOT / "configs/Quard/ctf_hcg_csort" / (name + ".yaml")
checkpoint = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"
cfg = gorilla.Config.fromfile(str(config))
cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
gorilla.set_random_seed(1999)
dataset = build_dataset(cfg.data.train, logging.getLogger("coverage-stage"))
loader = build_dataloader(dataset, batch_size=2, num_workers=0,
                          persistent_workers=False)
batches = []
for batch in loader:
    batches.append(batch)
    if len(batches) == 16:
        break
model = importlib.import_module("framework.model.Quard_model." + name).Network(**cfg.model)
state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
    state.pop(key, None)
model.load_state_dict(state, strict=True)
del state
model.cuda().eval()
rows = []
current = {}


def capture(module, args):
    pred, gt_masks, _, object_ids, instance_labels = args[:5]
    fps = args[7].long()
    assert fps.ndim == 2
    batch = current["batch"]
    scene_ids = [scene for scene, count in zip(batch["scan_ids"], batch["scenes_len"])
                 for _ in range(int(count))]
    for b, gt in enumerate(gt_masks):
        target = gt.flatten().bool()
        n = len(target)
        seeds = fps[b]
        selected_seeds = seeds[pred["sample_inds"][b].long()]
        assert int(seeds.max()) < n and int(selected_seeds.max()) < n
        layers = []
        for layer in [*pred.get("aux_outputs", []), pred]:
            masks = layer["masks"][b, :, :n] >= 0
            intersection = (masks & target).sum(-1)
            union = (masks | target).sum(-1).clamp_min(1)
            iou = intersection / union
            chosen = int(layer["indis"][b].softmax(-1)[:, 1].argmax())
            layers.append(dict(best=float(iou.max()), selected=float(iou[chosen]),
                               best_query=int(iou.argmax()), selected_query=chosen,
                               success_queries=int((iou > .5).sum())))
        instance_target = torch.zeros_like(instance_labels[b], dtype=torch.bool)
        for obj in object_ids[b]:
            instance_target |= instance_labels[b] == obj
        rows.append(dict(batch=current["step"], scene=scene_ids[b],
                         ann_id=int(batch["ann_ids"][b]),
                         object_ids=[int(v) for v in object_ids[b]],
                         target_sp=int(target.sum()), fps_unique=int(seeds.unique().numel()),
                         fps_target=int(target[seeds].sum()),
                         sampled_target=int(target[selected_seeds].sum()),
                         fps_instance_target=int(instance_target[seeds].sum()),
                         sampled_instance_target=int(instance_target[selected_seeds].sum()),
                         layers=layers))


model.criterion.register_forward_pre_hook(capture)
OUT.mkdir(parents=True, exist_ok=True)
with torch.no_grad():
    for step, batch in enumerate(batches):
        current.update(step=step, batch=batch)
        gorilla.set_random_seed(1999)
        loss, _ = model(batch, mode="loss")
        assert torch.isfinite(loss).all()
        print(json.dumps(dict(batch=step, expressions=len(rows))), flush=True)
summary = dict(expressions=len(rows), scenes=len({r["scene"] for r in rows}),
               no_fps_target=sum(r["fps_target"] == 0 for r in rows),
               dropped_target=sum(r["fps_target"] > 0 and r["sampled_target"] == 0 for r in rows),
               mask_limited=sum(r["layers"][-1]["best"] <= .5 for r in rows),
               recoverable=sum(r["layers"][-1]["best"] > .5 and
                               r["layers"][-1]["selected"] <= .5 for r in rows),
               success=sum(r["layers"][-1]["selected"] > .5 for r in rows))
report = dict(summary=summary, rows=rows,
              sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__), config, checkpoint)},
              scope="16 predefined augmented TRAIN batches, M95 eval mode, native loss path. "
                    "Same-forward FPS/sample/mask provenance. SP IoU only; "
                    "best-query oracle is diagnostic, not deployable or causal evidence.")
(OUT / "result.json").write_text(json.dumps(report, indent=2))
print(json.dumps(summary), flush=True)
