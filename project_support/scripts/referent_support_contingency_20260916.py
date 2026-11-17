"""Native contingency between the seed-based referent positives used for training
and the mask-based positives a deployment-correct head would need.

Answers: does the deployed score follow seed containment, mask quality, both or
neither? Forward-only on the fixed TRAIN forward; diagnosis, nothing admitted.
"""
import hashlib
import importlib
import json
import logging
import os
import sys
from pathlib import Path

import torch

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false")
ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
OUT = ROOT.parent / "pipeline/referent_support_contingency_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import gorilla  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CONFIG = ROOT / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
CHECKPOINT = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"
HELD = {}


def main():
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("support"))
    loader = build_dataloader(dataset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    batches = []
    for batch in loader:
        batches.append(batch)
        if len(batches) == 16:
            break
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    del state
    model.cuda().eval()

    def capture(module, args):
        HELD["pred"], HELD["gt"] = args[0], args[1]
        HELD["object_ids"], HELD["labels"] = args[3], args[4]
        HELD["fps"] = args[7]

    model.criterion.register_forward_pre_hook(capture)

    cells = {(s, m): [] for s in (0, 1) for m in (0, 1)}
    per_expression = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(n))]
            pred = HELD["pred"]
            for b in range(len(scenes)):
                labels = HELD["labels"][b].long().reshape(-1)
                target = HELD["gt"][b].flatten()
                n = min(labels.numel(), target.numel(), pred["masks"].shape[-1])
                labels, target = labels[:n], target[:n].bool()
                obj_ids = [int(v) for v in HELD["object_ids"][b]]
                is_ref = torch.zeros(n, dtype=torch.bool, device=labels.device)
                for o in obj_ids:
                    is_ref |= labels == o
                fps = HELD["fps"][b].long()
                sample = pred["sample_inds"][b].long().clamp(0, len(fps) - 1)
                seeds = fps[sample].clamp(0, n - 1)
                seed_pos = is_ref[seeds]
                masks = pred["masks"][b, :, :n] >= 0
                iou = ((masks & target).sum(-1).float()
                       / (masks | target).sum(-1).clamp_min(1).float())
                mask_pos = iou > .5
                prob = pred["indis"][b].softmax(-1)[:, 1]
                for si in (0, 1):
                    for mi in (0, 1):
                        sel = (seed_pos == bool(si)) & (mask_pos == bool(mi))
                        if int(sel.sum()):
                            cells[(si, mi)].append(float(prob[sel].mean()))
                same = int((seed_pos == mask_pos).sum())
                per_expression.append(dict(
                    step=step, scene=scenes[b],
                    queries=int(seed_pos.numel()),
                    seed_pos=int(seed_pos.sum()),
                    mask_pos=int(mask_pos.sum()),
                    agreement=same / int(seed_pos.numel()),
                    seed_only=int((seed_pos & ~mask_pos).sum()),
                    mask_only=int((~seed_pos & mask_pos).sum()),
                    selected_seed_pos=bool(seed_pos[int(prob.argmax())]),
                    selected_mask_pos=bool(mask_pos[int(prob.argmax())]),
                    selected_iou=float(iou[int(prob.argmax())])))
            print(json.dumps(dict(step=step, expressions=len(per_expression))),
                  flush=True)

    def cell_stats(key):
        vals = cells[key]
        return dict(n=len(vals),
                    mean_indis=sum(vals) / len(vals) if vals else None)

    rec = [r for r in per_expression if r["selected_iou"] <= .5 and r["mask_pos"]]
    summary = dict(
        expressions=len(per_expression),
        contingency={f"seed{k[0]}_mask{k[1]}": cell_stats(k) for k in cells},
        mean_agreement=sum(r["agreement"] for r in per_expression)
        / len(per_expression),
        seed_only_total=sum(r["seed_only"] for r in per_expression),
        mask_only_total=sum(r["mask_only"] for r in per_expression),
        recoverable=len(rec),
        recoverable_selected_seed_positive=sum(
            1 for r in rec if r["selected_seed_pos"]) / max(len(rec), 1),
        recoverable_selected_mask_positive=sum(
            1 for r in rec if r["selected_mask_pos"]) / max(len(rec), 1))
    report = dict(
        summary=summary, per_expression=per_expression,
        scope="Fixed16 TRAIN batches, M95 eval forward. seed_pos = the query's sampled "
              "FPS seed superpoint carries the referred instance id, which is the "
              "positive criterion of Criterion.match_sampled_ins. mask_pos = the "
              "query's predicted mask overlaps the referred instance above IoU.5, "
              "which is what deployment measures. Cells report the mean indis class-1 "
              "probability. Diagnosis only; no model, novelty or efficacy admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
