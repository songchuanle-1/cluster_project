"""Best deployed rank over ALL acceptable masks, not just the highest-IoU query.

Corrects a load-bearing metric: earlier ticks judged 'recoverable' by the rank of the
single maximum-IoU query. If several queries are above IoU 0.5, the deployed ordering
only has to place one of them at the top for the expression to succeed. This measures
the best rank among all acceptable queries, in one same-forward capture.
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
OUT = ROOT.parent / "pipeline/acceptable_mask_rank_20260916"
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
    dataset = build_dataset(cfg.data.train, logging.getLogger("acceptable"))
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
        HELD["object_ids"] = args[3]
        HELD["labels"] = args[4]

    model.criterion.register_forward_pre_hook(capture)
    rows = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            pred = HELD["pred"]
            scenes = [s for s, cnt in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(cnt))]
            for b in range(pred["masks"].shape[0]):
                labels = HELD["labels"][b].long().reshape(-1)
                target = HELD["gt"][b].flatten()
                n = min(labels.numel(), target.numel(), pred["masks"].shape[-1])
                labels, target = labels[:n], target[:n].bool()
                valid = (labels >= 0) & (labels != 199)
                if not bool(valid.any()):
                    continue
                masks = pred["masks"][b, :, :n] >= 0
                iou = ((masks & target).sum(-1).float()
                       / (masks | target).sum(-1).clamp_min(1).float())
                prob = pred["indis"][b].softmax(-1)[:, 1]
                order = torch.argsort(prob, descending=True)
                rank_of = torch.empty_like(order)
                rank_of[order] = torch.arange(1, len(order) + 1,
                                              device=order.device)
                accepted = iou > .5
                n_acc = int(accepted.sum())
                chosen = int(prob.argmax())
                best_iou_q = int(iou.argmax())
                rows.append(dict(
                    step=step, scene=str(scenes[b]) if b < len(scenes) else None,
                    success=bool(iou[chosen] > .5),
                    n_acceptable=n_acc,
                    best_acceptable_rank=(int(rank_of[accepted].min())
                                          if n_acc else None),
                    max_iou_query_rank=(int(rank_of[best_iou_q])
                                        if float(iou[best_iou_q]) > .5 else None),
                    selected_rank_of_acceptable=(int(rank_of[chosen])
                                                 if n_acc else None),
                    selected_iou=float(iou[chosen]),
                    best_iou=float(iou[best_iou_q]),
                    target_superpoints=int(target.sum())))
            print(json.dumps(dict(step=step, expressions=len(rows))), flush=True)

    acc = [r for r in rows if r["n_acceptable"] > 0]

    def frac(group, pred):
        return sum(1 for r in group if pred(r)) / len(group) if group else None

    summary = dict(
        expressions=len(rows), scenes=len({r["scene"] for r in rows}),
        success=sum(1 for r in rows if r["success"]),
        expressions_with_acceptable_mask=len(acc),
        mean_acceptable_per_expression=(
            sum(r["n_acceptable"] for r in rows) / len(rows)),
        # the corrected ceiling: an expression is oracle-recoverable if ANY
        # acceptable query exists, regardless of the highest-IoU query's rank
        oracle_any_acceptable_rate=len(acc) / len(rows),
        selected_is_acceptable_when_any_exists=frac(acc, lambda r: r["success"]),
        best_acceptable_rank_median=(
            sorted(r["best_acceptable_rank"] for r in acc)[len(acc) // 2]
            if acc else None),
        best_acceptable_rank_1=frac(acc, lambda r: r["best_acceptable_rank"] == 1),
        best_acceptable_rank_top5=frac(acc, lambda r: r["best_acceptable_rank"] <= 5),
        best_acceptable_rank_top20=frac(acc, lambda r: r["best_acceptable_rank"] <= 20),
        max_iou_query_rank_median=(
            sorted(r["max_iou_query_rank"] for r in acc
                   if r["max_iou_query_rank"])[
                len([r for r in acc if r["max_iou_query_rank"]]) // 2]
            if any(r["max_iou_query_rank"] for r in acc) else None),
        failures_with_acceptable=sum(
            1 for r in rows if not r["success"] and r["n_acceptable"] > 0),
        failures_no_acceptable=sum(
            1 for r in rows if not r["success"] and r["n_acceptable"] == 0))
    report = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward, ONE same-forward capture (no "
              "cross-capture joins). 'Acceptable' means the query's own mask reaches "
              "IoU>0.5 with the referred instance. best_acceptable_rank is the best "
              "(lowest) rank in the deployed indis ordering among ALL acceptable "
              "queries, which is the correct oracle-recoverability test and replaces "
              "judging by the single maximum-IoU query. Ranks are over the produced "
              "query set. Diagnosis only; no model, novelty or efficacy admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
