"""Can the object-level referent question be learned from the query the head reads?

Forward-only feature dump plus a grouped cross-validated linear probe. This tests
whether the missing discrimination is supervised (fixable by retargeting the loss)
or representational (not fixable without new inputs). Diagnosis only.
"""
import hashlib
import importlib
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import torch

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false")
ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
OUT = ROOT.parent / "pipeline/referent_learnability_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import gorilla  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CONFIG = ROOT / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
CHECKPOINT = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"
HELD = {}


def logistic_fit(x, y, steps=600, lr=0.35, l2=1e-3):
    w = np.zeros(x.shape[1], dtype=np.float64)
    b = 0.0
    for _ in range(steps):
        z = x @ w + b
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        g = p - y
        w -= lr * (x.T @ g / len(y) + l2 * w)
        b -= lr * g.mean()
    return w, b


def main():
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("learnability"))
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
        HELD["labels"] = args[4]
        HELD["dense"] = args[5]
        HELD["coords"], HELD["offsets"] = args[8], args[9]

    def capture_ffn(module, args, output):
        HELD["query"] = output

    def capture_qla(module, args, output):
        # CrossAttentionLayer returns (output, output_weight, src_weight)
        HELD["qla_attn"] = output[1]

    model.criterion.register_forward_pre_hook(capture)
    last = model.dec.decoder_layers[-1]
    last.qqa_ffn.register_forward_hook(capture_ffn)
    last.qla.register_forward_hook(capture_qla)

    feats, labels, groups, mask_iou, indis = [], [], [], [], []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(n))]
            pred = HELD["pred"]
            coords, offsets = HELD["coords"], HELD["offsets"]
            for b in range(len(scenes)):
                lab = HELD["labels"][b].long().reshape(-1)
                target = HELD["gt"][b].flatten()
                n = min(lab.numel(), target.numel(), pred["masks"].shape[-1])
                lab, target = lab[:n], target[:n].bool()
                masks = pred["masks"][b, :, :n]
                iou = (((masks >= 0) & target).sum(-1).float()
                       / ((masks >= 0) | target).sum(-1).clamp_min(1).float())
                if float(iou.max()) <= .5:
                    continue
                q = HELD["query"][b].float()
                attn = HELD["qla_attn"][b].float()     # [Q, L]
                dense = HELD["dense"][b]

                def group_attn(name):
                    raw = dense.get(name)
                    L = attn.shape[-1]
                    if raw is None:
                        return torch.zeros(attn.shape[0], 2, device=attn.device)
                    raw = raw.to(attn.device).reshape(-1)[:L]
                    m = raw > 0
                    if not bool(m.any()):
                        return torch.zeros(attn.shape[0], 2, device=attn.device)
                    sub = attn[:, m]
                    return torch.stack([sub.mean(-1), sub.max(-1).values], dim=-1)

                prob = torch.sigmoid(masks)
                size = prob.sum(-1) / max(n, 1)
                xyz = coords[int(offsets[b]):int(offsets[b + 1])].float()
                centre = xyz.mean(0, keepdim=True)
                w = prob / prob.sum(-1, keepdim=True).clamp_min(1e-6)
                geom = w @ xyz
                rel = geom - centre
                scale = xyz.norm(dim=-1).mean().clamp_min(1e-6)
                extra = torch.cat([size[:, None], rel / scale], dim=-1)
                lang = torch.cat([group_attn(n) for n in
                                  ("positive_map", "modify_positive_map",
                                   "other_entity_map", "rel_positive_map")], dim=-1)
                feats.append(torch.cat([q, extra, lang], dim=-1).cpu().numpy())
                labels.append((iou > .5).float().cpu().numpy())
                mask_iou.append(iou.cpu().numpy())
                indis.append(pred["indis"][b].softmax(-1)[:, 1].cpu().numpy())
                groups.append(scenes[b])
            print(json.dumps(dict(step=step, expressions=len(feats))), flush=True)

    x = np.concatenate(feats).astype(np.float64)
    y = np.concatenate(labels).astype(np.float64)
    miou = np.concatenate(mask_iou)
    ind = np.concatenate(indis)
    gid = np.array(groups)
    sizes = np.array([len(f) for f in feats])
    mu, sd = x.mean(0), x.std(0) + 1e-6
    x = (x - mu) / sd
    offsets = np.concatenate([[0], np.cumsum(sizes)])

    uniq = np.unique(gid)
    rng = np.random.RandomState(1999)
    rng.shuffle(uniq)
    fold_of = {g: i % 5 for i, g in enumerate(uniq)}
    scores = np.zeros(len(y))
    for fold in range(5):
        test_groups = {g for g, f in fold_of.items() if f == fold}
        te = np.concatenate([np.arange(offsets[i], offsets[i + 1])
                             for i, g in enumerate(gid) if g in test_groups])
        tr_mask = np.ones(len(y), dtype=bool)
        tr_mask[te] = False
        w, b = logistic_fit(x[tr_mask], y[tr_mask])
        scores[te] = 1.0 / (1.0 + np.exp(-np.clip(x[te] @ w + b, -30, 30)))

    def rank_in_expression(values, idx):
        order = np.argsort(-values)
        return int(np.where(order == idx)[0][0]) + 1

    probe_top1 = probe_rank = indis_top1 = indis_rank = 0
    n_expr = 0
    probe_hits = indis_hits = 0
    for i in range(len(sizes)):
        s, e = offsets[i], offsets[i + 1]
        best = int(np.argmax(miou[s:e]))
        others = np.argsort(-miou[s:e])
        usable = miou[s:e][others] > .5
        if not usable.any():
            continue
        n_expr += 1
        pr = rank_in_expression(scores[s:e], best)
        ir = rank_in_expression(ind[s:e], best)
        probe_rank += pr
        indis_rank += ir
        probe_top1 += int(pr == 1)
        indis_top1 += int(ir == 1)
        probe_hits += int(miou[s:e][int(np.argmax(scores[s:e]))] > .5)
        indis_hits += int(miou[s:e][int(np.argmax(ind[s:e]))] > .5)

    summary = dict(
        queries=int(len(y)), expressions=int(n_expr),
        scenes=int(len(set(gid))),
        positive_query_rate=float(y.mean()),
        probe_top1=probe_top1 / n_expr,
        probe_mean_rank=probe_rank / n_expr,
        probe_selected_mask_hit_rate=probe_hits / n_expr,
        indis_top1=indis_top1 / n_expr,
        indis_mean_rank=indis_rank / n_expr,
        indis_selected_mask_hit_rate=indis_hits / n_expr,
        probe_positive_rate=float((scores > .5).mean()))
    report = dict(
        summary=summary,
        scope="Fixed16 TRAIN batches, M95 eval forward, features frozen. The probe is "
              "an L2 logistic regression on the final query embedding (which the "
              "referent head reads) plus the query's own mask geometry (size and "
              "mask-centroid offset), label = the query's mask overlaps the referred "
              "instance above IoU.5. Five-fold cross-validation grouped by scene, so "
              "no scene appears in both train and test. This measures learnability of "
              "the object-level question from the head's own input; it is not the "
              "model, not a trained head, and not an admission. The geometry columns "
              "are available to a mask-conditioned readout but are NOT currently "
              "given to indis.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
