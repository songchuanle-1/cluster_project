"""Referent-head ranking versus target IoU on fixed TRAIN; diagnosis only."""
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
OUT = ROOT.parent / "pipeline/indis_selection_margin_20260916"
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
    dataset = build_dataset(cfg.data.train, logging.getLogger("indis-margin"))
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
                prob = pred["indis"][b].softmax(-1)[:, 1]
                masks = pred["masks"][b, :, :n] >= 0
                inter_t = (masks & target).sum(-1).float()
                union_t = (masks | target).sum(-1).clamp_min(1).float()
                iou_t = inter_t / union_t
                obj_ids = [int(v) for v in held["object_ids"][b]]
                num_labels = int(labels.max().item()) + 1
                onehot = torch.nn.functional.one_hot(
                    labels.clamp_min(0), num_labels).float().to(masks.device)
                inst_inter = masks.float() @ onehot
                counts = torch.bincount(labels[valid], minlength=num_labels).float()
                pred_n = masks.float().sum(-1, keepdim=True)
                inst_union = counts.unsqueeze(0) + pred_n - inst_inter
                inst_iou = inst_inter / inst_union.clamp_min(1)
                ref_mask = torch.zeros(num_labels, dtype=torch.bool)
                for i in obj_ids:
                    if 0 <= i < num_labels:
                        ref_mask[i] = True
                wrong_iou = inst_iou[:, ~ref_mask]
                best_wrong, best_wrong_idx = (
                    wrong_iou.max(-1) if wrong_iou.shape[1] else
                    (torch.zeros_like(prob), torch.zeros_like(prob, dtype=torch.long)))
                chosen = int(prob.argmax())
                best_q = int(iou_t.argmax())
                order = torch.argsort(prob, descending=True)
                rank_of_best = int((order == best_q).nonzero()[0]) + 1
                rows.append(dict(
                    step=step, scene=scenes[b], expression_slot=slots[b],
                    target_superpoints=int(target.sum()),
                    success=float(iou_t[chosen]) > .5,
                    selected_query=chosen,
                    selected_iou=float(iou_t[chosen]),
                    selected_indis=float(prob[chosen]),
                    best_query=best_q, best_iou=float(iou_t[best_q]),
                    best_indis=float(prob[best_q]),
                    best_query_rank_by_indis=rank_of_best,
                    indis_margin_best_minus_selected=float(prob[best_q] - prob[chosen]),
                    selected_wrong_instance_iou=float(best_wrong[chosen]),
                    top_indis_is_best_iou=chosen == best_q,
                    queries_above_half=int((iou_t > .5).sum())))
            print(json.dumps(dict(step=step, expressions=len(rows))), flush=True)

    fail = [r for r in rows if not r["success"]]
    ok = [r for r in rows if r["success"]]

    def mean(group, key):
        values = [r[key] for r in group if r[key] is not None]
        return sum(values) / len(values) if values else None

    recoverable = [r for r in fail if r["best_iou"] > .5]
    near_tie = [r for r in recoverable
                if abs(r["indis_margin_best_minus_selected"]) < .1]
    rows_sorted = sorted(rows, key=lambda r: r["best_query_rank_by_indis"])
    summary = dict(
        expressions=len(rows), success=len(ok), failure=len(fail),
        recoverable=len(recoverable),
        recoverable_selected_indis_gt_best=sum(
            1 for r in recoverable if r["selected_indis"] > r["best_indis"]),
        recoverable_near_tie_abs_margin_lt_0_1=len(near_tie),
        recoverable_mean_margin=mean(recoverable, "indis_margin_best_minus_selected"),
        recoverable_median_margin=(
            sorted(r["indis_margin_best_minus_selected"]
                   for r in recoverable)[len(recoverable) // 2]
            if recoverable else None),
        recoverable_best_rank_median=(
            sorted(r["best_query_rank_by_indis"] for r in recoverable)[
                len(recoverable) // 2] if recoverable else None),
        recoverable_best_rank_max=max(
            (r["best_query_rank_by_indis"] for r in recoverable), default=None),
        recoverable_selected_wrong_instance_iou_gt_half=sum(
            1 for r in recoverable
            if r["selected_wrong_instance_iou"] > .5),
        recoverable_mean_selected_wrong_instance_iou=mean(
            recoverable, "selected_wrong_instance_iou"),
        recoverable_mean_selected_indis=mean(recoverable, "selected_indis"),
        recoverable_mean_best_indis=mean(recoverable, "best_indis"))
    report = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward. indis class-1 probability is "
              "the deployed referent score. best_query is the query with the largest "
              "mask-overlap with the target; selected_query is the indis argmax. "
              "Margin is best minus selected, so a negative value means the deployed "
              "head ranks the correct query ABOVE its chosen one. This is a "
              "ranking-head diagnostic only; ranking mechanisms are a closed "
              "direction and nothing here is admitted. No model, novelty, efficacy or "
              "resource claim.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
