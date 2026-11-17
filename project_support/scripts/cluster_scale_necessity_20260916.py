"""Per-scale cluster-message necessity and cross-scale duplication; diagnosis only."""
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
OUT = ROOT.parent / "pipeline/cluster_scale_necessity_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import gorilla  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CONFIG = ROOT / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
CHECKPOINT = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"
CAPTURED = {"drop": None}


def patched_cluster_to_points(self, point_feats, cluster_feats_list,
                              cluster_ids_list, point_mask):
    """Exact copy of C2F_ClusterAttn_CTF_HCG._cluster_to_points plus a scale drop.

    drop=None reproduces the champion exactly; drop=k zeroes scale k's message
    inside the same learned per-point gate, leaving the gate and every other
    scale untouched.
    """
    B, N, C = point_feats.shape
    num_scales = self.num_scales
    composed_ids = []
    for b in range(B):
        ids_l0 = cluster_ids_list[0][b].long()
        ids_l0 = ids_l0.clamp(min=0, max=cluster_feats_list[0].shape[1] - 1)
        level_ids = [ids_l0]
        for lvl in range(1, num_scales):
            parent_ids = cluster_ids_list[lvl][b].long()
            parent_ids = parent_ids.clamp(
                min=0, max=cluster_feats_list[lvl].shape[1] - 1)
            level_ids.append(parent_ids.gather(0, level_ids[-1]))
        composed_ids.append(level_ids)

    scale_msgs = []
    for lvl in range(num_scales):
        cf = cluster_feats_list[lvl]
        msg = torch.zeros(B, N, C, device=point_feats.device,
                          dtype=point_feats.dtype)
        for b in range(B):
            ids_b = composed_ids[b][lvl]
            n_valid = min(ids_b.shape[0], N)
            msg[b, :n_valid] = cf[b, ids_b[:n_valid]]
        scale_msgs.append(msg)

    stack = torch.stack(scale_msgs, dim=-1)
    global_mean = point_feats.mean(dim=1, keepdim=True).expand_as(point_feats)
    gate_in = torch.cat([point_feats, global_mean], dim=-1)
    lw = torch.softmax(self.level_gate(gate_in), dim=-1)
    if CAPTURED["drop"] is not None:
        stack = stack.clone()
        stack[..., CAPTURED["drop"]] = 0
    fused = (stack * lw.unsqueeze(-2)).sum(dim=-1)
    fused = self.point_out_proj(self.dropout(fused))
    fused = fused.masked_fill(point_mask.unsqueeze(-1), 0)
    CAPTURED["stack"] = stack.detach()
    CAPTURED["lw"] = lw.detach()
    CAPTURED["mask"] = point_mask.detach()
    return fused


def main():
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("scale-necessity"))
    loader = build_dataloader(dataset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    batches = []
    for batch in loader:
        batches.append(batch)
        if len(batches) == 16:
            break
    module = importlib.import_module("framework.model.Quard_model." + NAME)
    cls = module.hier_postprocess.C2F_ClusterAttn_CTF_HCG
    cls._cluster_to_points = patched_cluster_to_points
    model = module.Network(**cfg.model)
    state = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    del state
    model.cuda().eval()

    held = {}

    def capture(module_, args):
        held["pred"], held["gt"] = args[0], args[1]
        held["object_ids"], held["labels"] = args[3], args[4]

    model.criterion.register_forward_pre_hook(capture)
    branches = {"base": None, "drop_l0": 0, "drop_l1": 1, "drop_l2": 2}
    records = {name: [] for name in branches}
    duplication = []

    with torch.no_grad():
        for step, batch in enumerate(batches):
            scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(n))]
            slots = [j for _, n in enumerate(batch["scenes_len"])
                     for j in range(int(n))]
            for name, drop in branches.items():
                CAPTURED["drop"] = drop
                gorilla.set_random_seed(1999)
                model(batch, mode="loss")
                stack = CAPTURED["stack"]
                lw = CAPTURED["lw"]
                mask = CAPTURED["mask"]
                pred = held["pred"]
                for b in range(len(scenes)):
                    labels = held["labels"][b].long().reshape(-1)
                    n = min(labels.numel(), mask.shape[1], stack.shape[1],
                            held["gt"][b].numel(), pred["masks"].shape[-1])
                    labels = labels[:n]
                    valid = ((~mask[b]).reshape(-1)[:n]
                             & (labels >= 0) & (labels != 199))
                    if step == 0 and b == 0 and name == "base":
                        print(json.dumps(dict(
                            debug="shapes", labels=list(labels.shape),
                            valid=list(valid.shape), n=n,
                            mask=list(mask.shape), stack=list(stack.shape),
                            gt=list(held["gt"][b].shape),
                            pred_masks=list(pred["masks"].shape))), flush=True)
                    masks = pred["masks"][b, :, :n] >= 0
                    chosen = int(pred["indis"][b].softmax(-1)[:, 1].argmax())
                    target = held["gt"][b].flatten()[:n].bool()
                    sel = masks[chosen]
                    iou = float((sel & target).sum()) / max(
                        int((sel | target).sum()), 1)
                    obj_ids = [int(v) for v in held["object_ids"][b]]
                    num_labels = int(labels.max().item()) + 1
                    inter = torch.bincount(labels[valid].to(torch.long),
                                           weights=sel[valid].float(),
                                           minlength=num_labels)
                    total = torch.bincount(labels[valid].to(torch.long),
                                           minlength=num_labels).float()
                    pred_n = float(sel[valid].sum())
                    inst_iou = inter / (total + pred_n - inter).clamp_min(1)
                    winner = int(inst_iou.argmax())
                    records[name].append(dict(
                        step=step, scene=scenes[b], expression_slot=slots[b],
                        selected_iou=iou, success=iou > .5,
                        winner_instance=winner,
                        winner_is_wrong=winner not in obj_ids,
                        mean_level_weight=[float(lw[b][:n][valid][:, i].mean())
                                           for i in range(lw.shape[-1])],
                        dominant_scale=(
                            int(lw[b][:n][valid].mean(0).argmax())
                            if int(valid.sum()) else None)))
                    if name == "base":
                        ref = valid & torch.isin(
                            labels, torch.tensor(obj_ids, device=labels.device))
                        point = stack[b][:n]
                        cos = []
                        for i in range(point.shape[-1]):
                            for j in range(i + 1, point.shape[-1]):
                                a = point[:, :, i][ref]
                                c = point[:, :, j][ref]
                                if a.shape[0] < 2:
                                    cos.append(None)
                                    continue
                                denom = (a.norm(dim=-1) * c.norm(dim=-1))
                                ok = denom > 1e-8
                                if int(ok.sum()) < 2:
                                    cos.append(None)
                                    continue
                                cos.append(float((a[ok] * c[ok]).sum(-1).div(
                                    denom[ok]).mean()))
                        dup = dict(
                            cos_l0_l1=cos[0], cos_l0_l2=cos[1], cos_l1_l2=cos[2],
                            norm_l0=float(point[:, :, 0][ref].norm(dim=-1).mean())
                            if int(ref.sum()) else None,
                            norm_l1=float(point[:, :, 1][ref].norm(dim=-1).mean())
                            if int(ref.sum()) else None,
                            norm_l2=float(point[:, :, 2][ref].norm(dim=-1).mean())
                            if int(ref.sum()) else None)
                        duplication.append(dict(
                            step=step, scene=scenes[b], expression_slot=slots[b],
                            **dup))
            print(json.dumps(dict(step=step, expressions=len(records["base"]))),
                  flush=True)

    def summarize(name):
        rows = records[name]
        dominant = {}
        for r in rows:
            key = r["dominant_scale"]
            dominant[str(key)] = dominant.get(str(key), 0) + 1
        return dict(
            expressions=len(rows),
            success=sum(r["success"] for r in rows),
            wrong_instance=sum(r["winner_is_wrong"] for r in rows),
            mean_selected_iou=sum(r["selected_iou"] for r in rows) / len(rows),
            mean_level_weight=[
                sum(r["mean_level_weight"][i] for r in rows) / len(rows)
                for i in range(3)],
            dominant_scale_counts=dominant)

    base = records["base"]
    flips = {}
    for name in ("drop_l0", "drop_l1", "drop_l2"):
        rows = records[name]
        improved = [r for r, b in zip(rows, base)
                    if r["selected_iou"] > b["selected_iou"] + 1e-6]
        regressed = [r for r, b in zip(rows, base)
                     if r["selected_iou"] < b["selected_iou"] - 1e-6]
        fixed = [r for r, b in zip(rows, base)
                 if r["success"] and not b["success"]]
        broke = [r for r, b in zip(rows, base)
                 if b["success"] and not r["success"]]
        d_win = [r for r, b in zip(rows, base)
                 if r["winner_instance"] != b["winner_instance"]]
        flips[name] = dict(improved=len(improved), regressed=len(regressed),
                           fixed=fixed, broke=broke, winner_changed=len(d_win))

    def dup_mean(key):
        values = [r[key] for r in duplication if r.get(key) is not None]
        return sum(values) / len(values) if values else None

    summary = dict(
        scenes=len({r["scene"] for r in duplication}),
        branches={name: summarize(name) for name in branches},
        branch_effects=flips,
        duplication=dict(
            mean_cos_l0_l1=dup_mean("cos_l0_l1"),
            mean_cos_l0_l2=dup_mean("cos_l0_l2"),
            mean_cos_l1_l2=dup_mean("cos_l1_l2"),
            mean_norm_l0=dup_mean("norm_l0"),
            mean_norm_l1=dup_mean("norm_l1"),
            mean_norm_l2=dup_mean("norm_l2")))
    report = dict(
        summary=summary, records=records, duplication=duplication,
        scope="Fixed16 TRAIN batches, M95 eval forward. Only the last encoder layer "
              "uses cluster attention (cluster_att_num_layers=1). Dropping a scale "
              "zeroes that scale's message inside the unchanged learned per-point "
              "gate; the gate is softmax over three scales, so remaining weights are "
              "not renormalised. Cosine duplication is over target superpoints only. "
              "Forward-only intervention: it does not undo training effects and is "
              "not a novel variant. No model, novelty, efficacy or resource admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
