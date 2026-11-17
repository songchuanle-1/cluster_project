"""Does the 2D identity advantage cash out under the language?

3D identity separability did not translate into referent selection, and the 2D lead
was measured only as instance-similarity structure. This tests the decisive question:
after the model's own projections into the shared d_model space, does language
alignment prefer the referred instance over the wrongly selected one, and does the 2D
path do so better than the 3D path? Forward-only diagnostic; nothing admitted.
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
OUT = ROOT.parent / "pipeline/modality_language_alignment_20260916"
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
    dataset = build_dataset(cfg.data.train, logging.getLogger("modality-lang"))
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

    dec = model.dec
    native = dec.forward_iter_pred

    def wrapped(x, fps_seed_sp, batch_offsets, lang_feats=None,
                lang_masks=None, sp_pos=None, feats_2d=None):
        with torch.no_grad():
            p3 = dec.input_proj(x)                 # 3D branch before fusion
            p2 = (dec.input_proj_2d(feats_2d)
                  if feats_2d is not None else None)   # 2D branch before fusion
            lang_proj = dec.lang_proj(lang_feats)
            lang_proj = dec.lang_norm(lang_proj)
            # input_proj output is flat [total_N, C]; batch it exactly as the model does
            p3b, bmask = dec.get_batches(p3, batch_offsets)
            p2b = dec.get_batches(p2, batch_offsets)[0] if p2 is not None else None
        HELD.update(p3=p3b, p2=p2b, batch_mask=bmask, lang=lang_proj,
                    lang_masks=lang_masks, offsets=batch_offsets, feats_2d=feats_2d)
        return native(x, fps_seed_sp, batch_offsets, lang_feats,
                      lang_masks, sp_pos, feats_2d)

    dec.forward_iter_pred = wrapped

    def capture(module, args):
        HELD["pred"], HELD["gt"] = args[0], args[1]
        HELD["object_ids"] = args[3]
        HELD["labels"] = args[4]
        HELD["dense"] = args[5]

    model.criterion.register_forward_pre_hook(capture)

    rows = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            pred = HELD["pred"]
            # p3/p2 are the fused-batch tensors [B, Nmax, C] after get_batches
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
                chosen = int(prob.argmax())
                if float(iou[chosen]) > .5:
                    continue
                obj_ids = [int(v) for v in HELD["object_ids"][b]]
                if not obj_ids:
                    continue
                num = int(labels.max().item()) + 1
                counts = torch.bincount(labels[valid], minlength=num).float()
                sel = masks[chosen].float()
                inter = torch.bincount(labels[valid], weights=sel[valid],
                                       minlength=num)
                pred_n = float(sel[valid].sum())
                inst_iou = inter / (counts + pred_n - inter).clamp_min(1)
                winner = int(inst_iou.argmax())
                if winner in obj_ids:
                    continue
                # referent phrase tokens from the dataset's own maps
                lm = (~HELD["lang_masks"][b]).bool()
                dense = HELD["dense"][b]
                ref_tok = dense.get("positive_map")
                if ref_tok is None:
                    continue
                ref_tok = ref_tok.to(lm.device).reshape(-1)[:lm.shape[0]]
                ref_mask = (ref_tok > 0) & lm
                if not bool(ref_mask.any()):
                    continue

                def align(feat_space, text_space, pool="mean"):
                    acc = torch.zeros(num, feat_space.shape[-1],
                                      device=feat_space.device)
                    acc.index_add_(0, labels[valid], feat_space[valid])
                    cen = acc / counts.clamp_min(1).unsqueeze(-1)
                    f = torch.nn.functional.normalize(cen, dim=-1)
                    tok = torch.nn.functional.normalize(text_space[ref_mask], dim=-1)
                    if pool == "mean":
                        t = torch.nn.functional.normalize(
                            text_space[ref_mask].mean(0, keepdim=True), dim=-1)
                        return (f @ t.T)[:, 0]
                    # max over referent tokens: keeps the most compatible token per
                    # instance instead of averaging token meanings
                    sim = f @ tok.T
                    return sim.max(-1).values

                rec = dict(step=step,
                           scene=(str(scenes[b]) if b < len(scenes) else None),
                           wrong_instance=winner,
                           target_instances=obj_ids,
                           selected_iou=float(iou[chosen]))
                variants = []
                for tag, fs in (("3d", HELD["p3"][b][:n]),
                                ("2d", (HELD["p2"][b][:n]
                                        if HELD["p2"] is not None else None))):
                    if fs is not None:
                        for pool in ("mean", "max"):
                            variants.append((f"{tag}_{pool}", fs, pool))
                for tag, fs, pool in variants:
                    ts = HELD["lang"][b]
                    s = align(fs.float(), ts.float(), pool)
                    order = torch.argsort(s, descending=True)
                    ids = torch.arange(num, device=s.device)
                    ranked = ids[order]
                    target_ranks = {o: int(torch.nonzero(ranked == o).squeeze()) + 1
                                    for o in obj_ids}
                    best = min(target_ranks.values())
                    best_obj = min(target_ranks, key=target_ranks.get)
                    wpos = int(torch.nonzero(ids == winner).squeeze())
                    tpos = int(torch.nonzero(ids == best_obj).squeeze())
                    rec[f"{tag}_best_target_rank"] = best
                    rec[f"{tag}_target_minus_wrong"] = float(s[tpos] - s[wpos])
                    rec[f"{tag}_prefers_target"] = bool(s[tpos] > s[wpos])
                rows.append(rec)
            print(json.dumps(dict(step=step, failures=len(rows))), flush=True)

    def stats(tag):
        vals = sorted(r[f"{tag}_best_target_rank"] for r in rows
                      if f"{tag}_best_target_rank" in r)
        n = len(vals)
        marg = [r[f"{tag}_target_minus_wrong"] for r in rows
                if f"{tag}_target_minus_wrong" in r]
        return dict(n=n, median=vals[n // 2], mean=sum(vals) / n,
                    top1=sum(1 for v in vals if v == 1) / n,
                    top3=sum(1 for v in vals if v <= 3) / n,
                    top5=sum(1 for v in vals if v <= 5) / n,
                    prefers_target=sum(1 for m in marg if m > 0) / len(marg),
                    mean_margin=sum(marg) / len(marg))

    summary = dict(failures=len(rows),
                   **{tag: stats(tag) for tag in
                      ("3d_mean", "3d_max", "2d_mean", "2d_max")})
    report = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward, recoverable failures with an "
              "identified wrong instance. Both branches are the model's own "
              "projections into the shared d_model space (input_proj for 3D, "
              "input_proj_2d for the clip_feat rows, lang_norm(lang_proj(...)) for "
              "text), so the two modalities and the language are compared in one "
              "space. Language evidence is the dataset's own referent-phrase token "
              "map. Ranks are over all instances of the scene, ranked by "
              "language-instance cosine. Diagnosis only; no model, novelty or "
              "efficacy admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
