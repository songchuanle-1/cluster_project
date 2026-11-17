"""Composition of the native matched-positive set that supervises every head.

`Criterion.match_sampled_ins` returns `indices`; loss_indi, the score regression and
the mask losses are all applied to exactly that set. This hooks that function, so the
measured set is the native one by construction, and asks (a) how many positives
actually have a mask that covers the referred instance, and (b) how many
mask-covering queries are excluded from supervision. Forward-only; nothing admitted.
"""
import hashlib
import json
import os
from pathlib import Path

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false")
ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
OUT = ROOT.parent / "pipeline/matched_positive_composition_20260916"


def main():
    import torch

    base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
    src = base.read_text().split(
        "model.criterion.register_forward_pre_hook(capture)")[0]
    ns = {"__file__": str(base)}
    exec(compile(src, str(base), "exec"), ns)
    torch, model, batches = ns["torch"], ns["model"], ns["batches"]
    held, calls = {}, []

    native = model.criterion.match_sampled_ins

    def wrapped(*args, **kwargs):
        topk, in_obj, matched, counts = native(*args, **kwargs)
        calls.append((matched[0].detach().cpu(), counts))
        return topk, in_obj, matched, counts

    model.criterion.match_sampled_ins = wrapped

    def capture(module, args):
        held["pred"], held["gt"] = args[0], args[1]
        held["object_ids"], held["labels"] = args[3], args[4]

    model.criterion.register_forward_pre_hook(capture)
    rows = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            ns["current"].update(step=step, batch=batch)
            calls.clear()
            ns["gorilla"].set_random_seed(1999)
            loss, _ = model(batch, mode="loss")
            assert torch.isfinite(loss).all()
            pred = held["pred"]
            scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(n))]
            nonempty = [b for b in range(len(scenes))
                        if len(held["object_ids"][b]) > 0]
            # match_sampled_ins is called twice per non-empty item: seed set, then
            # query set. The query set is what supervises loss_indi and the heads.
            for i, b in enumerate(nonempty):
                if 2 * i + 1 >= len(calls):
                    continue
                q_ids = calls[2 * i + 1][0]
                labels = held["labels"][b].long().reshape(-1)
                target = held["gt"][b].flatten()
                n = min(labels.numel(), target.numel(),
                        pred["masks"].shape[-1])
                labels, target = labels[:n], target[:n].bool()
                q_ids = q_ids[q_ids < pred["masks"].shape[1]]
                pos = torch.zeros(pred["masks"].shape[1], dtype=torch.bool,
                                  device=pred["masks"].device)
                pos[q_ids.long().to(pos.device)] = True
                masks = pred["masks"][b, :, :n] >= 0
                iou = ((masks & target).sum(-1).float()
                       / (masks | target).sum(-1).clamp_min(1).float())
                mask_ok = iou > .5
                selected = int(pred["indis"][b].softmax(-1)[:, 1].argmax())
                rec = dict(
                    step=step, scene=scenes[b],
                    positives=int(pos.sum()),
                    positives_mask_ok=int((pos & mask_ok).sum()),
                    positives_mask_bad=int((pos & ~mask_ok).sum()),
                    mask_ok_excluded=int((~pos & mask_ok).sum()),
                    mean_iou_positives=(float(iou[pos].mean())
                                        if int(pos.sum()) else None),
                    mean_iou_positives_bad=(float(iou[pos & ~mask_ok].mean())
                                            if int((pos & ~mask_ok).sum()) else None),
                    mean_iou_excluded=(float(iou[~pos & mask_ok].mean())
                                       if int((~pos & mask_ok).sum()) else None),
                    selected_is_positive=bool(pos[selected]),
                    selected_mask_ok=bool(mask_ok[selected]),
                    selected_iou=float(iou[selected]),
                    target_superpoints=int(target.sum()))
                rows.append(rec)
            print(json.dumps(dict(step=step, expressions=len(rows))), flush=True)

    def tot(key):
        return sum(r[key] for r in rows)

    def mean_of(key):
        vals = [r[key] for r in rows if r[key] is not None]
        return sum(vals) / len(vals) if vals else None

    pos_total = tot("positives")
    ok = tot("positives_mask_ok")
    bad = tot("positives_mask_bad")
    excl = tot("mask_ok_excluded")
    summary = dict(
        expressions=len(rows),
        positive_query_slots=pos_total,
        positives_with_mask_ok=ok,
        positives_with_mask_bad=bad,
        positive_mask_ok_rate=ok / pos_total if pos_total else None,
        mask_ok_queries_excluded=excl,
        exclusions_per_positive=excl / pos_total if pos_total else None,
        mean_iou_of_positive_queries=mean_of("mean_iou_positives"),
        mean_iou_of_mask_bad_positives=mean_of("mean_iou_positives_bad"),
        mean_iou_of_excluded_mask_ok=mean_of("mean_iou_excluded"),
        expressions_with_no_good_positive=sum(
            1 for r in rows if r["positives_mask_ok"] == 0),
        expressions_with_exclusions=sum(
            1 for r in rows if r["mask_ok_excluded"] > 0),
        selected_query_is_a_training_positive=sum(
            1 for r in rows if r["selected_is_positive"]) / max(len(rows), 1),
        selected_query_mask_ok=sum(
            1 for r in rows if r["selected_mask_ok"]) / max(len(rows), 1),
        scenes=len({r["scene"] for r in rows}))
    report = dict(
        summary=summary, per_expression=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward. The positive set is intercepted "
              "from the model's own Criterion.match_sampled_ins (query-level call), so "
              "it is exactly the set that supervises loss_indi, the score regression "
              "and the mask losses. mask_ok means the query's own predicted mask "
              "overlaps the referred instance above IoU .5. Expressions repeat scenes, "
              "so counts are not independent samples. Diagnosis only; no model, "
              "novelty or efficacy admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), base, ns["config"], ns["checkpoint"])})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
