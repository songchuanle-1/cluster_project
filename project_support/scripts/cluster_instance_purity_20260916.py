"""Cluster-instance purity on fixed TRAIN batches; diagnosis only, no admission."""
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
OUT = ROOT.parent / "pipeline/cluster_instance_purity_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import gorilla  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CONFIG = ROOT / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
CHECKPOINT = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"


def purity(cids, labels, valid):
    """Per-level instance histograms and per-superpoint cluster ids.

    cids[0] is per superpoint; cids[l] maps level-(l-1) cluster -> level-l cluster.
    """
    num_labels = int(labels.max().item()) + 1
    keys = cids[0][valid] * num_labels + labels[valid]
    counts = torch.bincount(
        keys, minlength=(int(cids[0].max().item()) + 1) * num_labels)
    hists = [counts.reshape(-1, num_labels)]
    levels = [cids[0]]
    for lvl in range(1, len(cids)):
        parent = cids[lvl].long()
        out = torch.zeros(int(parent.max().item()) + 1, num_labels,
                          dtype=hists[-1].dtype, device=hists[-1].device)
        out.index_add_(0, parent, hists[-1])
        hists.append(out)
        levels.append(parent[levels[-1]])
    mixed = [(h > 0).sum(1) >= 2 for h in hists]
    return hists, levels, mixed


def main():
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("purity"))
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
        held["coords"], held["offsets"] = args[8], args[9]

    model.criterion.register_forward_pre_hook(capture)
    rows = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            cids_list = model.dec.cluster_bank.cluster_ids_list
            scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(n))]
            slots = [j for _, n in enumerate(batch["scenes_len"])
                     for j in range(int(n))]
            for b in range(len(scenes)):
                labels = held["labels"][b].long()
                valid = (labels >= 0) & (labels != 199)
                cids = [c[b].long() for c in cids_list]
                hists, levels, mixed = purity(cids, labels, valid)
                obj_ids = [int(v) for v in held["object_ids"][b]]
                ref_tensor = torch.tensor(obj_ids, device=labels.device)
                is_ref = valid & torch.isin(labels, ref_tensor)
                n_ref = int(is_ref.sum())
                contamination = []
                for lvl in range(len(mixed)):
                    if n_ref == 0:
                        contamination.append(None)
                        continue
                    flag = mixed[lvl][levels[lvl]]
                    contamination.append(float((flag & is_ref).sum()) / n_ref)
                pred, n = held["pred"], labels.numel()
                masks = pred["masks"][b, :, :n] >= 0
                chosen = int(pred["indis"][b].softmax(-1)[:, 1].argmax())
                target = held["gt"][b].flatten().bool()
                sel = masks[chosen]
                iou = float((sel & target).sum()) / max(int((sel | target).sum()), 1)
                num_labels = int(labels.max().item()) + 1
                inter = torch.bincount(labels[valid], weights=sel[valid].float(),
                                       minlength=num_labels)
                total = torch.bincount(labels[valid], minlength=num_labels).float()
                pred_n = float(sel[valid].sum())
                inst_iou = inter / (total + pred_n - inter).clamp_min(1)
                winner = int(inst_iou.argmax())
                winner_is_wrong = winner not in obj_ids
                coords = held["coords"]
                lo, hi = int(held["offsets"][b]), int(held["offsets"][b + 1])
                xyz = coords[lo:hi].float()
                inst_ids = labels[valid].unique().tolist()
                centroids = {}
                for inst in inst_ids:
                    m = valid & (labels == inst)
                    centroids[int(inst)] = xyz[m].mean(0)
                target_centroid = torch.stack(
                    [centroids[i] for i in obj_ids if i in centroids]).mean(0)
                others = [i for i in centroids if i not in obj_ids]

                def co_cluster(inst):
                    w = torch.unique(levels[0][valid & (labels == inst)])
                    return bool(torch.isin(torch.unique(levels[0][is_ref]), w).any())

                other_share = [co_cluster(i) for i in others]
                other_dist = [float((centroids[i] - target_centroid).norm())
                              for i in others]
                share = []
                if winner_is_wrong and n_ref:
                    is_win = valid & (labels == winner)
                    for lvl in range(len(mixed)):
                        t = torch.unique(levels[lvl][is_ref])
                        w = torch.unique(levels[lvl][is_win])
                        share.append(bool(torch.isin(t, w).any()))
                rows.append(dict(
                    step=step, scene=scenes[b], expression_slot=slots[b],
                    superpoints=n, valid_superpoints=int(valid.sum()),
                    instances=int(labels[valid].unique().numel()),
                    referred=obj_ids, referred_superpoints=n_ref,
                    selected_iou=iou, selected_query=chosen, success=iou > .5,
                    winner_instance=winner, winner_iou=float(inst_iou[winner]),
                    winner_is_wrong=winner_is_wrong,
                    target_winner_centroid_distance=(
                        float((centroids[winner] - target_centroid).norm())
                        if winner in centroids else None),
                    mean_other_centroid_distance=(
                        sum(other_dist) / len(other_dist) if other_dist else None),
                    target_winner_co_cluster_l0=(
                        co_cluster(winner) if winner in centroids else None),
                    mean_other_co_cluster_l0=(
                        sum(other_share) / len(other_share) if other_share else None),
                    target_winner_share_cluster=share,
                    clusters=[h.shape[0] for h in hists],
                    mixed_clusters=[int(m.sum()) for m in mixed],
                    mixed_cluster_fraction=[float(m.float().mean()) for m in mixed],
                    target_contamination=contamination))
            print(json.dumps(dict(step=step, expressions=len(rows))), flush=True)
    ok = [r for r in rows if r["success"]]
    bad = [r for r in rows if not r["success"]]
    wrong = [r for r in rows if r["winner_is_wrong"]]

    def mean(group, index):
        values = [r["target_contamination"][index] for r in group
                  if r["target_contamination"][index] is not None]
        return sum(values) / len(values) if values else None

    def share_rate(group):
        rates = []
        for i in range(3):
            hits = [r for r in group if len(r["target_winner_share_cluster"]) == 3]
            rates.append(None if not hits else
                         sum(int(r["target_winner_share_cluster"][i])
                             for r in hits) / len(hits))
        return rates

    def field_mean(group, key):
        values = [r[key] for r in group if r.get(key) is not None]
        return sum(values) / len(values) if values else None

    summary = dict(
        expressions=len(rows), scenes=len({r["scene"] for r in rows}),
        success=len(ok), failure=len(bad), wrong_instance=len(wrong),
        global_mixed_cluster_fraction=[
            sum(r["mixed_clusters"][i] for r in rows)
            / max(sum(r["clusters"][i] for r in rows), 1) for i in range(3)],
        replicated_scene_expressions=len(rows) - len({r["scene"] for r in rows}),
        mean_target_contamination_all=[mean(rows, i) for i in range(3)],
        mean_target_contamination_success=[mean(ok, i) for i in range(3)],
        mean_target_contamination_failure=[mean(bad, i) for i in range(3)],
        wrong_target_winner_share_cluster=share_rate(wrong),
        wrong_winner_co_cluster_l0=field_mean(wrong, "target_winner_co_cluster_l0"),
        wrong_mean_other_co_cluster_l0=field_mean(wrong, "mean_other_co_cluster_l0"),
        wrong_winner_centroid_distance=field_mean(
            wrong, "target_winner_centroid_distance"),
        wrong_mean_other_centroid_distance=field_mean(
            wrong, "mean_other_centroid_distance"))
    report = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward, geometry from the model's own "
              "FPS partitioner. Cluster purity uses native sp_ins_labels; winner is the "
              "scene instance with the largest overlap with the selected query mask. "
              "Expressions of multi-expression scenes repeat one geometry, so scene "
              "counts are not independent samples. No model, novelty, efficacy or "
              "resource admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
