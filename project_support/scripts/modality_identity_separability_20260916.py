"""Does the paired 2D modality carry instance-level identity that 3D features lack?

Same protocol as the 3D instance-feature measurement, but on the raw clip_feat rows
the loader actually feeds the fusion, so the comparison is apples-to-apples on the
same 28 recoverable failures. Forward-only diagnostic; nothing admitted.
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
OUT = ROOT.parent / "pipeline/modality_identity_separability_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import gorilla  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CONFIG = ROOT / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
CHECKPOINT = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"
HELD = {}


def rank_stats(rows, key):
    vals = sorted(r[key] for r in rows)
    n = len(vals)
    return dict(mean=sum(vals) / n, median=vals[n // 2],
                top1=sum(1 for v in vals if v == 1) / n,
                top3=sum(1 for v in vals if v <= 3) / n,
                top5=sum(1 for v in vals if v <= 5) / n,
                p90=vals[int(.9 * (n - 1))])


def main():
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("modality-sep"))
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
        HELD["coords"], HELD["offsets"] = args[8], args[9]

    def capture_layer(module, args):
        HELD["inst_feats"] = args[2]

    model.criterion.register_forward_pre_hook(capture)
    model.dec.decoder_layers[-1].register_forward_pre_hook(capture_layer)
    # feats_2d is fused into inst_feats inside DEC.forward_iter_pred, before the
    # decoder layers run, so it must be captured there rather than from a layer hook.
    native_iter_pred = model.dec.forward_iter_pred

    def wrapped_iter_pred(x, fps_seed_sp, batch_offsets, lang_feats=None,
                          lang_masks=None, sp_pos=None, feats_2d=None):
        HELD["feats_2d"] = feats_2d
        return native_iter_pred(x, fps_seed_sp, batch_offsets, lang_feats,
                                lang_masks, sp_pos, feats_2d)

    model.dec.forward_iter_pred = wrapped_iter_pred

    rows = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(n))]
            slots = [j for _, n in enumerate(batch["scenes_len"])
                     for j in range(int(n))]
            pred = HELD["pred"]
            for b in range(len(scenes)):
                labels = HELD["labels"][b].long().reshape(-1)
                target = HELD["gt"][b].flatten()
                n = min(labels.numel(), target.numel(), pred["masks"].shape[-1])
                labels, target = labels[:n], target[:n].bool()
                valid = (labels >= 0) & (labels != 199)
                masks = pred["masks"][b, :, :n] >= 0
                iou = ((masks & target).sum(-1).float()
                       / (masks | target).sum(-1).clamp_min(1).float())
                prob = pred["indis"][b].softmax(-1)[:, 1]
                chosen = int(prob.argmax())
                if float(iou[chosen]) > .5:
                    continue
                obj_ids = [int(v) for v in HELD["object_ids"][b]]
                num = int(labels.max().item()) + 1
                counts = torch.bincount(labels[valid], minlength=num).float()
                # the wrong instance the deployed mask actually segments
                sel = masks[chosen].float()
                inter = torch.bincount(labels[valid], weights=sel[valid],
                                       minlength=num)
                pred_n = float(sel[valid].sum())
                inst_iou = inter / (counts + pred_n - inter).clamp_min(1)
                winner = int(inst_iou.argmax())
                if winner in obj_ids:
                    continue
                rec = dict(step=step, scene=scenes[b], expression_slot=slots[b],
                           wrong_instance=winner)
                raw2d = HELD["feats_2d"]
                # feats_2d is [total_points, C] before the per-scene expand/pad
                seg2d = None
                if raw2d is not None:
                    lo = int(HELD["offsets"][b])
                    hi = int(HELD["offsets"][b + 1])
                    seg2d = raw2d[lo:hi].float()
                    if seg2d.shape[0] != n:
                        seg2d = None
                for tag, feats in (("feat3d", HELD["inst_feats"][b][:n].float()),
                                   ("feat2d", seg2d)):
                    if feats is None:
                        continue
                    acc = torch.zeros(num, feats.shape[-1], device=feats.device)
                    acc.index_add_(0, labels[valid], feats[valid])
                    means = acc / counts.clamp_min(1).unsqueeze(-1)
                    ids = torch.nonzero(counts > 0).squeeze(-1)
                    centred = means[ids] - means[ids].mean(0, keepdim=True)
                    m = torch.nn.functional.normalize(centred, dim=-1)
                    sim = m @ m.T
                    eye = torch.eye(len(ids), dtype=torch.bool,
                                    device=sim.device)
                    sim = sim.masked_fill(eye, float("-inf"))
                    wpos = int(torch.nonzero(ids == winner).squeeze())
                    order = torch.argsort(sim[wpos], descending=True)
                    ranked = ids[order]
                    off = (m @ m.T)[~eye]
                    best = min(int(torch.nonzero(ranked == o).squeeze()) + 1
                               for o in obj_ids)
                    rec[f"{tag}_best_target_rank"] = best
                    rec[f"{tag}_null_mean"] = float(off.mean())
                    rec[f"{tag}_sim_wrong"] = float(sim[wpos][order[0]])
                    best_id = int(ranked[0])
                    if best_id in obj_ids:
                        tpos = int(torch.nonzero(ids == best_id).squeeze())
                        rec[f"{tag}_sim_target_wrong"] = float(sim[wpos][tpos])
                rows.append(rec)
            print(json.dumps(dict(step=step, failures=len(rows))), flush=True)

    # chance levels, per expression
    summary = dict(failures=len(rows),
                   feat3d=rank_stats(rows, "feat3d_best_target_rank"),
                   feat2d=rank_stats(rows, "feat2d_best_target_rank"))
    for tag in ("feat3d", "feat2d"):
        vals = [r[f"{tag}_null_mean"] for r in rows]
        summary[f"{tag}_null_mean"] = sum(vals) / len(vals)
        sw = [r[f"{tag}_sim_wrong"] for r in rows]
        summary[f"{tag}_sim_nearest_other"] = sum(sw) / len(sw)
    report = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward, recoverable failures with an "
              "identified wrong instance. feat3d = final encoder inst_feats; feat2d = "
              "the clip_feat rows the loader feeds to the 2D projection (raw, before "
              "input_proj_2d). Both are averaged per instance and centred on the scene "
              "mean, self-similarity excluded, then ranked by similarity to the wrongly "
              "selected instance. Diagnosis only; no model, novelty or efficacy "
              "admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
