"""Is the correct query even distinguishable in the space the referent head reads?

Forward-only. For each recoverable failure compare the query embedding of the query
that covers the target against the deployed argmax query, and compare that against
the separability available from scene/mask evidence. Diagnosis only.
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
OUT = ROOT.parent / "pipeline/query_separability_20260916"
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
    dataset = build_dataset(cfg.data.train, logging.getLogger("query-sep"))
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
        HELD["coords"], HELD["offsets"] = args[8], args[9]

    def capture_layer(module, args):
        # args: (lang_feats, lang_masks, inst_feats, batch_mask, query,
        #        sp_pos, query_pos, k)
        HELD["inst_feats"] = args[2]
        HELD["query_in"] = args[4]
        HELD["sp_pos"] = args[5]
        HELD["query_pos"] = args[6]

    def capture_ffn(module, args, output):
        HELD["query_out"] = output

    model.criterion.register_forward_pre_hook(capture)
    last = model.dec.decoder_layers[-1]
    last.register_forward_pre_hook(capture_layer)
    last.qqa_ffn.register_forward_hook(capture_ffn)

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
                q = HELD["query_out"][b]
                q_in = HELD["query_in"][b]
                qp = HELD["query_pos"][b].float()
                feats = HELD["inst_feats"][b][:n]
                qn = torch.nn.functional.normalize(q, dim=-1)
                cos_cs = float((qn[best] * qn[chosen]).sum())
                cos_in = float((torch.nn.functional.normalize(q_in[best], dim=-1)
                                * torch.nn.functional.normalize(q_in[chosen], dim=-1)).sum())
                # hint scales: comparing the query against scene features
                mprob = torch.sigmoid(pred["masks"][b, :, :n])
                region = (mprob / mprob.sum(-1, keepdim=True).clamp_min(1e-6)) @ feats
                rn = torch.nn.functional.normalize(region, dim=-1)
                cos_region = float((rn[best] * rn[chosen]).sum())
                # positional separation actually available to the model
                d_pos = float((qp[best] - qp[chosen]).norm())
                # how similar are their masks' spatial extents
                inter = float((masks[best] & masks[chosen]).sum())
                union = float((masks[best] | masks[chosen]).sum())
                # nearest-neighbour separability: is the correct query the unique
                # nearest neighbour of its own mask feature?
                sim = rn @ rn.T
                sim.fill_diagonal_(-2.0)
                nn_of_best = int(sim[best].argmax())
                # language alignment spread across all queries
                rows.append(dict(
                    step=step, scene=scenes[b], expression_slot=slots[b],
                    best_query=best, selected_query=chosen,
                    best_iou=float(iou[best]), selected_iou=float(iou[chosen]),
                    cos_query_correct_selected=cos_cs,
                    cos_queryin_correct_selected=cos_in,
                    cos_region_correct_selected=cos_region,
                    pos_distance_correct_selected=d_pos,
                    mask_iou_correct_selected=inter / max(union, 1.0),
                    nn_of_correct_is_selected=str(nn_of_best == chosen),
                    target_superpoints=int(target.sum())))
            print(json.dumps(dict(step=step, recoverable=len(rows))), flush=True)

    def stats(key):
        vals = sorted(r[key] for r in rows)
        return dict(mean=sum(vals) / len(vals), median=vals[len(vals) // 2],
                    p10=vals[int(.1 * len(vals))],
                    p90=vals[int(.9 * (len(vals) - 1))],
                    min=vals[0], max=vals[-1])

    summary = dict(
        recoverable=len(rows),
        cos_query_correct_selected=stats("cos_query_correct_selected"),
        cos_queryin_correct_selected=stats("cos_queryin_correct_selected"),
        cos_region_correct_selected=stats("cos_region_correct_selected"),
        pos_distance_correct_selected=stats("pos_distance_correct_selected"),
        mask_iou_correct_selected=stats("mask_iou_correct_selected"),
        nearest_region_neighbour_of_correct_is_selected=sum(
            1 for r in rows if r["nn_of_correct_is_selected"] == "True") / len(rows))
    report = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward, 33 recoverable failures. "
              "cos_query_* is the cosine between the final query embedding that the "
              "referent head actually reads for the query covering the target and for "
              "the deployed argmax query. cos_region_* does the same for sigmoid-mask-"
              "weighted pooled scene features. pos_distance is the difference between "
              "the two queries' positions, which the last decoder layer receives but "
              "does not use. If cos_query is close to 1 the referent head cannot in "
              "principle separate the pair. Diagnosis only.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
