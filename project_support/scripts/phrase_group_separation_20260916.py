"""Which phrase group carries the discriminative signal for the correct query?

Uses the model's own trained contrastive align projections and the dataset's
existing modifier / pronoun / other-entity / relation token maps. Forward-only
diagnostic; nothing is admitted.
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
OUT = ROOT.parent / "pipeline/phrase_group_separation_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import gorilla  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CONFIG = ROOT / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
CHECKPOINT = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"
HELD = {}
GROUPS = ("positive_map", "modify_positive_map", "pron_positive_map",
          "other_entity_map", "rel_positive_map")


def main():
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("phrase-groups"))
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
        HELD["dense"] = args[5]

    def capture_layer(module, args):
        HELD["lang_feats"], HELD["lang_masks"] = args[0], args[1]
        HELD["inst_feats"] = args[2]

    def capture_ffn(module, args, output):
        HELD["query"] = output

    model.criterion.register_forward_pre_hook(capture)
    last = model.dec.decoder_layers[-1]
    last.register_forward_pre_hook(capture_layer)
    last.qqa_ffn.register_forward_hook(capture_ffn)
    pv = last.contrastive_align_projection_vision
    pt = last.contrastive_align_projection_text
    camap = model.dec.sampling_module.camap

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
                n = min(labels.numel(), target.numel(), pred["masks"].shape[-1],
                        HELD["inst_feats"].shape[1])
                labels, target = labels[:n], target[:n].bool()
                masks = pred["masks"][b, :, :n] >= 0
                iou = ((masks & target).sum(-1).float()
                       / (masks | target).sum(-1).clamp_min(1).float())
                prob = pred["indis"][b].softmax(-1)[:, 1]
                chosen, best = int(prob.argmax()), int(iou.argmax())
                if float(iou[chosen]) > .5 or float(iou[best]) <= .5:
                    continue
                lf = HELD["lang_feats"][b]
                valid_tok = (~HELD["lang_masks"][b]).bool()
                tv = torch.nn.functional.normalize(pt(lf), dim=-1)
                qv = torch.nn.functional.normalize(pv(HELD["query"][b]), dim=-1)
                qraw = torch.nn.functional.normalize(HELD["query"][b], dim=-1)
                lraw = torch.nn.functional.normalize(lf, dim=-1)
                cam_q = torch.nn.functional.normalize(
                    camap.query_proj(HELD["inst_feats"][b][:n]), dim=-1)
                cam_k = torch.nn.functional.normalize(camap.key_proj(lf), dim=-1)
                feat_sims = cam_q @ cam_k.T          # [points, L]
                mprob = torch.sigmoid(pred["masks"][b, :, :n])

                dense = HELD["dense"][b]

                def group_mask(name):
                    raw = dense.get(name)
                    if raw is None:
                        return None
                    raw = raw.to(lf.device).reshape(-1)[:lf.shape[0]]
                    m = (raw > 0) & valid_tok
                    return m if bool(m.any()) else None

                rec = dict(step=step, scene=scenes[b], expression_slot=slots[b],
                           best_query=best, best_iou=float(iou[best]),
                           selected_query=chosen)
                for name in GROUPS:
                    gm = group_mask(name)
                    rec[f"n_{name}"] = int(gm.sum()) if gm is not None else 0
                    if gm is None:
                        continue
                    # query-projection alignment with this phrase group
                    s_q = (qv @ tv[gm].T).max(-1).values
                    # region/mask-driven alignment using the point-language matcher
                    point_g = feat_sims[:, gm].max(-1).values
                    s_region = (point_g.unsqueeze(0) * mprob).sum(-1) / \
                        mprob.sum(-1).clamp_min(1e-6)
                    # raw feature cosine against the group centroid
                    centroid = torch.nn.functional.normalize(
                        lraw[gm].mean(0, keepdim=True), dim=-1)
                    s_raw = (qraw @ centroid.T)[:, 0]
                    for tag, values in (("qproj", s_q), ("pointregion", s_region),
                                        ("raw", s_raw)):
                        values = values.reshape(-1)
                        order = torch.argsort(values, descending=True)
                        rec[f"{name}|{tag}|rank"] = int((order == best).nonzero()[0]) + 1
                        rec[f"{name}|{tag}|best"] = float(values[best])
                        rec[f"{name}|{tag}|selected"] = float(values[chosen])
                rows.append(rec)
            print(json.dumps(dict(step=step, recoverable=len(rows))), flush=True)

    summary = dict(recoverable=len(rows))
    summary["group_token_counts"] = {
        name: dict(present=sum(1 for r in rows if r[f"n_{name}"] > 0),
                   mean_tokens=(sum(r[f"n_{name}"] for r in rows)
                                / max(sum(1 for r in rows if r[f"n_{name}"] > 0), 1)))
        for name in GROUPS}
    for key in sorted(k for k in rows[0] if k.endswith("|rank")):
        base = key[:-5]
        ranks = sorted(r[key] for r in rows if key in r)
        margins = [r[f"{base}|best"] - r[f"{base}|selected"]
                   for r in rows if f"{base}|best" in r]
        summary[base] = dict(
            n=len(ranks), median_rank=ranks[len(ranks) // 2],
            mean_rank=sum(ranks) / len(ranks),
            top1=sum(1 for x in ranks if x == 1) / len(ranks),
            top5=sum(1 for x in ranks if x <= 5) / len(ranks),
            wins=sum(1 for m in margins if m > 0),
            mean_margin=sum(margins) / len(margins))
    report = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward, 33 recoverable failures. "
              "Phrase groups are the dataset's own token maps: positive_map "
              "(referent mention), modify (attributes), pron (pronouns), "
              "other_entity (other mentioned objects), rel (relations). Three "
              "scoring variants per group: qproj = trained vision/text projection "
              "cosine (the sem_align operator, exactly in distribution on the query "
              "side); pointregion = trained sampling language-point matcher pooled "
              "over the query's predicted mask; raw = unprojected feature cosine to "
              "the group centroid. Diagnostic only; no model, novelty or efficacy "
              "admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
