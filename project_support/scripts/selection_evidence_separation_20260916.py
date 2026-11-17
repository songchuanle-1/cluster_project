"""Which existing per-query signals separate the correct query from the selected
one in the recoverable failures? Diagnosis only; no model or admission change."""
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
OUT = ROOT.parent / "pipeline/selection_evidence_separation_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import gorilla  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CONFIG = ROOT / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
CHECKPOINT = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"


def main():
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("selection-evidence"))
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

    held = {}

    def capture(module, args):
        held["pred"], held["gt"] = args[0], args[1]
        held["object_ids"], held["labels"] = args[3], args[4]

    model.criterion.register_forward_pre_hook(capture)
    rows = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(n))]
            slots = [j for _, n in enumerate(batch["scenes_len"])
                     for j in range(int(n))]
            pred = held["pred"]
            for b in range(len(scenes)):
                labels = held["labels"][b].long().reshape(-1)
                target = held["gt"][b].flatten()
                n = min(labels.numel(), target.numel(), pred["masks"].shape[-1])
                labels, target = labels[:n], target[:n].bool()
                valid = (labels >= 0) & (labels != 199)
                masks = pred["masks"][b, :, :n] >= 0
                inter = (masks & target).sum(-1).float()
                union = (masks | target).sum(-1).clamp_min(1).float()
                iou = inter / union
                prob = pred["indis"][b].softmax(-1)[:, 1]
                chosen = int(prob.argmax())
                best = int(iou.argmax())
                if float(iou[chosen]) > .5 or float(iou[best]) <= .5:
                    continue
                scores = pred["scores"][b]
                scores = scores.reshape(-1) if scores.dim() > 1 else scores
                sample = pred["sample_inds"][b].long().clamp(0, n - 1)
                ref = pred["ref_scores"][b].reshape(-1)[sample]
                sizes = masks.sum(-1).float()
                overlap = float((masks[best] & masks[chosen]).sum())
                union_bc = float((masks[best] | masks[chosen]).sum())

                def rank(values, idx):
                    order = torch.argsort(values, descending=True)
                    return int((order == idx).nonzero()[0]) + 1

                rows.append(dict(
                    step=step, scene=scenes[b], expression_slot=slots[b],
                    target_superpoints=int(target.sum()),
                    closest_failed_query_iou=float(iou[chosen]),
                    best_query=best, best_iou=float(iou[best]),
                    overlap_correct_selected=overlap,
                    iou_correct_selected=overlap / max(union_bc, 1.0),
                    indis_selected=float(prob[chosen]),
                    indis_best=float(prob[best]),
                    indis_rank_of_best=rank(prob, best),
                    score_selected=float(scores[chosen]),
                    score_best=float(scores[best]),
                    score_rank_of_best=rank(scores, best),
                    ref_selected=float(ref[chosen]),
                    ref_best=float(ref[best]),
                    ref_rank_of_best=rank(ref, best),
                    size_selected=float(sizes[chosen]),
                    size_best=float(sizes[best]),
                    queries_above_half=int((iou > .5).sum()),
                    best_mask_covers_target=float(
                        (masks[best] & target).sum()) / max(int(target.sum()), 1)))
            print(json.dumps(dict(step=step, recoverable=len(rows))), flush=True)

    def summary(key):
        vals = [r[key] for r in rows]
        vals_sorted = sorted(vals)
        return dict(mean=sum(vals) / len(vals) if vals else None,
                    median=vals_sorted[len(vals) // 2] if vals else None,
                    max=vals_sorted[-1] if vals else None,
                    min=vals_sorted[0] if vals else None)

    def top1_rate(key):
        return sum(1 for r in rows if r[key] == 1) / len(rows) if rows else None

    summary_rows = dict(
        recoverable=len(rows),
        indis_rank_of_best=summary("indis_rank_of_best"),
        score_rank_of_best=summary("score_rank_of_best"),
        ref_rank_of_best=summary("ref_rank_of_best"),
        indis_rank_top1=top1_rate("indis_rank_of_best"),
        score_rank_top1=top1_rate("score_rank_of_best"),
        ref_rank_top1=top1_rate("ref_rank_of_best"),
        indis_margin=summary("indis_best"),
        score_margin=summary("score_best"),
        ref_margin=summary("ref_best"),
        score_selected=summary("score_selected"),
        ref_selected=summary("ref_selected"),
        size_selected=summary("size_selected"),
        size_best=summary("size_best"),
        iou_correct_selected=summary("iou_correct_selected"),
        overlap_correct_selected=summary("overlap_correct_selected"),
        closest_failed_query_iou=summary("closest_failed_query_iou"),
        best_iou=summary("best_iou"),
        best_mask_covers_target=summary("best_mask_covers_target"),
        queries_above_half=summary("queries_above_half"))
    report = dict(
        summary=summary_rows, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward, only the recoverable failures "
              "(selected mask wrong AND a query above IoU.5 with the target exists). "
              "Ranks are within the 128 sampled queries; rank1 means that signal "
              "alone would already pick the query that matches the target. "
              "Diagnostic only: no model, novelty, efficacy or resource admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary_rows, indent=2), flush=True)


if __name__ == "__main__":
    main()
