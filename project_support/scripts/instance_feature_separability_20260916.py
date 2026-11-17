"""Are same-name instances separable in the encoder features the mask head reads?

If the target instance's feature centroid is near the top of the ranking by
similarity to the wrongly selected instance, no mask-reading head or loss on top of
these features can separate the pair, and the mechanism must change the
representation. Forward-only diagnostic; nothing admitted.
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
OUT = ROOT.parent / "pipeline/instance_feature_separability_20260916"
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
    dataset = build_dataset(cfg.data.train, logging.getLogger("instance-sep"))
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
        HELD["inst_feats"] = args[2]

    model.criterion.register_forward_pre_hook(capture)
    model.dec.decoder_layers[-1].register_forward_pre_hook(capture_layer)

    rows = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(n))]
            slots = [j for _, n in enumerate(batch["scenes_len"])
                     for j in range(int(n))]
            pred, feats_all = HELD["pred"], HELD["inst_feats"]
            coords = HELD["coords"]
            for b in range(len(scenes)):
                labels = HELD["labels"][b].long().reshape(-1)
                target = HELD["gt"][b].flatten()
                n = min(labels.numel(), target.numel(), pred["masks"].shape[-1],
                        feats_all.shape[1])
                labels, target = labels[:n], target[:n].bool()
                valid = (labels >= 0) & (labels != 199)
                masks = pred["masks"][b, :, :n] >= 0
                iou = ((masks & target).sum(-1).float()
                       / (masks | target).sum(-1).clamp_min(1).float())
                prob = pred["indis"][b].softmax(-1)[:, 1]
                chosen, best = int(prob.argmax()), int(iou.argmax())
                if float(iou[chosen]) > .5 or float(iou[best]) <= .5:
                    continue
                obj_ids = [int(v) for v in HELD["object_ids"][b]]
                num = int(labels.max().item()) + 1
                feats = feats_all[b][:n].float()
                counts = torch.bincount(labels[valid], minlength=num).float()
                # accumulate per-instance feature means
                acc = torch.zeros(num, feats.shape[-1], device=feats.device)
                acc.index_add_(0, labels[valid], feats[valid])
                means = acc / counts.clamp_min(1).unsqueeze(-1)
                present = counts > 0
                ids = torch.nonzero(present).squeeze(-1)
                # Deep features share a dominant mean direction; raw cosine is
                # inflated by it (scene mean pairwise .93 here). Centre on the scene
                # mean so the similarity measures *instance-specific* content.
                centred = means[ids] - means[ids].mean(0, keepdim=True)
                m = torch.nn.functional.normalize(centred, dim=-1)
                sim = m @ m.T
                eye = torch.eye(len(ids), dtype=torch.bool, device=sim.device)
                sim_noself = sim.masked_fill(eye, float("-inf"))
                # which instance does the deployed mask most overlap (the wrong one)
                sel = masks[chosen].float()
                inter = torch.bincount(labels[valid],
                                       weights=sel[valid], minlength=num)
                pred_n = float(sel[valid].sum())
                union = counts + pred_n - inter
                inst_iou = inter / union.clamp_min(1)
                winner = int(inst_iou.argmax())
                if winner in obj_ids:
                    continue
                # rank all instances by feature similarity to the wrong instance
                wpos = int(torch.nonzero(ids == winner).squeeze())
                order = torch.argsort(sim_noself[wpos], descending=True)
                ranked_ids = ids[order]
                ranks = {}
                for o in obj_ids:
                    pos = int(torch.nonzero(ranked_ids == o).squeeze())
                    ranks[o] = pos + 1
                # category-agnostic null: mean pairwise similarity among instances
                off = sim[~eye]
                # spatial distance between target and wrong instance centroids
                xyz = coords[int(HELD["offsets"][b]):int(HELD["offsets"][b + 1])].float()
                cen = torch.zeros(num, 3, device=feats.device)
                cen.index_add_(0, labels[valid], xyz[valid])
                cen = cen / counts.clamp_min(1).unsqueeze(-1)
                rows.append(dict(
                    step=step, scene=scenes[b], expression_slot=slots[b],
                    n_instances=int(len(ids)),
                    wrong_instance=winner,
                    target_ranks=ranks,
                    best_target_rank=min(ranks.values()),
                    sim_target_wrong=float(sim[wpos][int(
                        torch.nonzero(ids == min(ranks, key=ranks.get)).squeeze())]),
                    sim_top=float(sim[wpos][order[0]]),
                    sim_mean=float(off.mean()),
                    spatial_distance=float(
                        (cen[winner] - cen[min(ranks, key=ranks.get)]).norm()),
                    selected_iou=float(iou[chosen]),
                    winner_mask_iou=float(inst_iou[winner])))
            print(json.dumps(dict(step=step, recoverable=len(rows))), flush=True)

    def stats(key):
        vals = sorted(r[key] for r in rows)
        return dict(mean=sum(vals) / len(vals), median=vals[len(vals) // 2],
                    p10=vals[int(.1 * len(vals))],
                    p90=vals[int(.9 * (len(vals) - 1))],
                    min=vals[0], max=vals[-1])

    summary = dict(
        recoverable=len(rows),
        best_target_rank=stats("best_target_rank"),
        target_rank_top1=sum(1 for r in rows if r["best_target_rank"] == 1)
        / len(rows),
        target_rank_top3=sum(1 for r in rows if r["best_target_rank"] <= 3)
        / len(rows),
        target_rank_top5=sum(1 for r in rows if r["best_target_rank"] <= 5)
        / len(rows),
        sim_target_wrong=stats("sim_target_wrong"),
        sim_top=stats("sim_top"),
        sim_mean=stats("sim_mean"),
        spatial_distance=stats("spatial_distance"))
    report = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward. Instance feature centroids are "
              "means of the final encoder inst_feats over each instance's superpoints "
              "(native sp_ins_labels), centred on the scene mean because deep features "
              "share a dominant mean direction that inflates raw cosine. For each "
              "recoverable failure we rank every "
              "instance by cosine similarity to the instance the deployed query "
              "actually segmented; best_target_rank is the rank of the referred "
              "instance in that ranking, so rank 1 means the encoder features make the "
              "referred instance the nearest neighbour of the wrongly selected one. "
              "Self-similarity is excluded. Also reported: pairwise similarity null "
              "over all instance pairs in the scene, and the spatial distance between "
              "the two centroids. Under the null (no instance-specific content) the "
              "target rank would be uniform over the instances, i.e. about half the "
              "scene. Diagnosis "
              "only; no model, novelty or efficacy admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
