"""Would mask-region language evidence rank the correct query? Forward-only upper-bound
probe using already-trained operators. Diagnosis only; nothing is admitted."""
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
OUT = ROOT.parent / "pipeline/region_language_separation_20260916"
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
    dataset = build_dataset(cfg.data.train, logging.getLogger("region-language"))
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

    def capture_layer(module, args):
        HELD["lang_feats"], HELD["lang_masks"] = args[0], args[1]
        HELD["inst_feats"] = args[2]

    def capture_ffn(module, args, output):
        # qqa_ffn output is exactly the query that prediction_head consumes.
        HELD["query"] = output

    model.criterion.register_forward_pre_hook(capture)
    last = model.dec.decoder_layers[-1]
    last.register_forward_pre_hook(capture_layer)
    last.qqa_ffn.register_forward_hook(capture_ffn)
    camap = model.dec.sampling_module.camap
    pv = last.contrastive_align_projection_vision
    pt = last.contrastive_align_projection_text

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
            lang_feats, lang_masks = HELD["lang_feats"], HELD["lang_masks"]
            inst_feats, query, mask_feats = (HELD["inst_feats"], HELD["query"],
                                             HELD["inst_feats"])
            for b in range(len(scenes)):
                labels = HELD["labels"][b].long().reshape(-1)
                target = HELD["gt"][b].flatten()
                n = min(labels.numel(), target.numel(), pred["masks"].shape[-1],
                        inst_feats.shape[1], mask_feats.shape[1])
                labels, target = labels[:n], target[:n].bool()
                masks = pred["masks"][b, :, :n] >= 0
                inter = (masks & target).sum(-1).float()
                union = (masks | target).sum(-1).clamp_min(1).float()
                iou = inter / union
                prob = pred["indis"][b].softmax(-1)[:, 1]
                chosen, best = int(prob.argmax()), int(iou.argmax())
                if float(iou[chosen]) > .5 or float(iou[best]) <= .5:
                    continue
                q = query[b]
                feats = inst_feats[b][:n]
                mprob = torch.sigmoid(pred["masks"][b, :, :n])
                weight = mprob / mprob.sum(-1, keepdim=True).clamp_min(1e-6)
                region = weight @ feats
                valid = (~lang_masks[b]).bool()
                lf = lang_feats[b]

                def sim(a, c):
                    """[Q,d] x [M,d] -> [Q,M] cosine similarity."""
                    a = torch.nn.functional.normalize(a, dim=-1)
                    c = torch.nn.functional.normalize(c, dim=-1)
                    return a @ c.T

                v_indis = prob
                v_sem_query = sim(pv(q), pt(lf))[:, valid].max(-1).values
                v_sem_region = sim(pv(region), pt(lf))[:, valid].max(-1).values
                qp, kp = camap.query_proj, camap.key_proj
                v_camap_region = sim(qp(region), kp(lf))[:, valid].mean(-1)
                point_lang = sim(qp(feats), kp(lf))[:, valid].mean(-1)
                v_point_max = (point_lang.unsqueeze(0) * mprob).max(-1).values
                v_point_mean = (point_lang.unsqueeze(0) * weight).sum(-1)
                text_mean = lf[valid].mean(0, keepdim=True)
                v_region_norm_cos = sim(region, text_mean)[:, 0]
                q_norm_cos = sim(q, text_mean)[:, 0]

                def rank(values, idx):
                    order = torch.argsort(values, descending=True)
                    return int((order == idx).nonzero()[0]) + 1

                variants = {
                    "indis_deployed": v_indis,
                    "sem_query_trained": v_sem_query,
                    "sem_region": v_sem_region,
                    "camap_region": v_camap_region,
                    "camap_point_max_in_mask": v_point_max,
                    "camap_point_mean_in_mask": v_point_mean,
                    "raw_region_lang_cos": v_region_norm_cos,
                    "raw_query_lang_cos": q_norm_cos}
                rec = dict(step=step, scene=scenes[b], expression_slot=slots[b],
                           best_query=best, best_iou=float(iou[best]),
                           target_superpoints=int(target.sum()),
                           selected_region_size=float(mprob[chosen].sum()),
                           correct_region_size=float(mprob[best].sum()))
                for key, values in variants.items():
                    values = values.reshape(-1)
                    rec[f"{key}__rank"] = rank(values, best)
                    rec[f"{key}__best"] = float(values[best])
                    rec[f"{key}__selected"] = float(values[chosen])
                rows.append(rec)
            print(json.dumps(dict(step=step, recoverable=len(rows))), flush=True)

    variant_names = [k for k in rows[0] if k.endswith("__rank")]
    summary = dict(recoverable=len(rows))
    for key in variant_names:
        base = key[:-6]
        ranks = sorted(r[key] for r in rows)
        margins = [r[f"{base}__best"] - r[f"{base}__selected"] for r in rows]
        summary[base] = dict(
            median_rank=ranks[len(ranks) // 2],
            mean_rank=sum(ranks) / len(ranks),
            top1_rate=sum(1 for x in ranks if x == 1) / len(ranks),
            top5_rate=sum(1 for x in ranks if x <= 5) / len(ranks),
            wins=sum(1 for m in margins if m > 0),
            mean_margin=sum(margins) / len(margins))
    report = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward, 33 recoverable failures. All "
              "operators are the model's own trained modules: sem_* use the trained "
              "contrastive align projections (applied to the query, or to the "
              "mask-pooled region feature); camap_* use the trained sampling "
              "language-point projections. Region features are sigmoid-mask-weighted "
              "poolings of the final encoder inst_feats. Applying the vision "
              "projection to a region feature is out-of-distribution, so a positive "
              "result is a necessary-condition probe, not an admissible design; a "
              "negative result across ALL variants would instead show that region "
              "language evidence is insufficient. Ranking designs remain a closed "
              "direction. No model, novelty, efficacy or resource admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
