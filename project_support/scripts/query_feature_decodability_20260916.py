"""Is referent identity decodable from the query features the head reads?

Earlier probes were LINEAR and concluded readouts are exhausted. That is too strong a
conclusion for a feasibility question: what matters is whether the information needed
for the referent decision exists at all in the query's own features. This runs a
nonlinear head with scene-grouped cross-validation on ONE same-forward capture.

Labels per query:
  positive  - the query's sampled seed superpoint carries the referred instance id
              (the native training-positive criterion)
  accept    - the query's own predicted mask reaches IoU>0.5 with the referred object
              (what deployment actually needs)

If a scene-held-out nonlinear head can rank `accept`/`positive` queries near the top,
the bottleneck is supervision and the information exists; if it stays near the
deployed head's own performance, the query features themselves lack it and any fix
must add a new input path.
"""
import hashlib
import importlib
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false")
ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
OUT = ROOT.parent / "pipeline/query_feature_decodability_20260916"
sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
import gorilla  # noqa: E402
from framework.dataset import build_dataset, build_dataloader  # noqa: E402

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.15)
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CONFIG = ROOT / "configs/Quard/ctf_hcg_csort" / (NAME + ".yaml")
CHECKPOINT = ROOT.parent / "pipeline/scm_admission_20260914/best.pth"
HELD = {}


def mlp(dims, device):
    layers, prev = [], dims[0]
    for d in dims[1:-1]:
        layers += [torch.nn.Linear(prev, d), torch.nn.ReLU()]
        prev = d
    layers += [torch.nn.Linear(prev, dims[-1])]
    return torch.nn.Sequential(*layers).to(device)


def main():
    cfg = gorilla.Config.fromfile(str(CONFIG))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("decodability"))
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

    last = model.dec.decoder_layers[-1]

    def q_ffn_hook(module, args, output):
        HELD["query"] = output

    def layer_hook(module, args):
        HELD["query_pos"] = args[6]
        HELD["sp_pos"] = args[5]

    def crit_hook(module, args):
        HELD["pred"], HELD["gt"] = args[0], args[1]
        HELD["object_ids"] = args[3]
        HELD["labels"] = args[4]
        HELD["fps"] = args[7]
        HELD["coords"] = args[8]
        HELD["offsets"] = args[9]

    last.qqa_ffn.register_forward_hook(q_ffn_hook)
    last.register_forward_pre_hook(layer_hook)
    model.criterion.register_forward_pre_hook(crit_hook)

    feats, meta = [], []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            pred = HELD["pred"]
            q = HELD["query"]                     # [B, Q, C] final query
            qpos = HELD["query_pos"].float()      # [B, Q, 3]
            scenes = [s for s, cnt in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(cnt))]
            for b in range(pred["masks"].shape[0]):
                labels = HELD["labels"][b].long().reshape(-1)
                target = HELD["gt"][b].flatten()
                n = min(labels.numel(), target.numel(), pred["masks"].shape[-1])
                labels, target = labels[:n], target[:n].bool()
                valid = (labels >= 0) & (labels != 199)
                if not bool(valid.any()) or not bool(target.any()):
                    continue
                obj_ids = {int(v) for v in HELD["object_ids"][b]}
                if not obj_ids:
                    continue
                masks = pred["masks"][b, :, :n]            # logits
                mbin = masks >= 0
                inter = (mbin & target).sum(-1).float()
                union = (mbin | target).sum(-1).clamp_min(1).float()
                iou = inter / union
                prob = pred["indis"][b].softmax(-1)[:, 1]
                fps = HELD["fps"][b].long()
                sample = pred["sample_inds"][b].long().clamp(0, len(fps) - 1)
                seeds = fps[sample].clamp(0, n - 1)
                seed_inst = labels[seeds]
                is_positive = torch.tensor(
                    [bool(valid[seeds[i]]) and int(seed_inst[i]) in obj_ids
                     for i in range(len(seeds))], device=labels.device)
                accept = iou > .5
                # mask geometry features, no GT involved
                mprob = torch.sigmoid(masks)
                msize = mprob.sum(-1) / max(n, 1)
                coords = HELD["coords"]
                lo, hi = int(HELD["offsets"][b]), int(HELD["offsets"][b + 1])
                xyz = coords[lo:hi].float()[:n]
                centre = xyz.mean(0, keepdim=True)
                scale = xyz.norm(dim=-1).mean().clamp_min(1e-6)
                w = mprob / mprob.sum(-1, keepdim=True).clamp_min(1e-6)
                cen = w @ xyz
                geom = torch.cat([(cen - centre) / scale, msize[:, None],
                                  masks.max(-1).values[:, None]], dim=-1)
                posrel = (qpos[b] - centre) / scale
                f = torch.cat([q[b], posrel, geom], dim=-1)
                feats.append(f.cpu().numpy())
                meta.append(dict(
                    scene=str(scenes[b]) if b < len(scenes) else "?",
                    step=step, n_queries=int(f.shape[0]),
                    positive=is_positive.cpu().numpy().astype(np.float32),
                    accept=accept.cpu().numpy().astype(np.float32),
                    iou=iou.cpu().numpy(), indis=prob.cpu().numpy()))
            print(json.dumps(dict(step=step, expressions=len(meta))), flush=True)

    dim = feats[0].shape[-1]
    scenes = sorted({m["scene"] for m in meta})
    rng = np.random.RandomState(1999)
    perm = rng.permutation(len(scenes))
    fold_of = {scenes[perm[i]]: i % 5 for i in range(len(scenes))}

    results = {}
    for label_name in ("accept", "positive"):
        scores = [None] * len(meta)
        for fold in range(5):
            te = [i for i, m in enumerate(meta)
                  if fold_of[m["scene"]] == fold]
            tr = [i for i, m in enumerate(meta)
                  if fold_of[m["scene"]] != fold]
            if not te or not tr:
                continue
            x_tr = np.concatenate([feats[i] for i in tr])
            y_tr = np.concatenate([meta[i][label_name] for i in tr])
            mu, sd = x_tr.mean(0), x_tr.std(0) + 1e-6
            x_tr = (x_tr - mu) / sd
            net_dims = [dim, 256, 64, 1]
            # fit once per fold on all training expressions
            net = mlp(net_dims, "cuda")
            opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
            xt = torch.tensor(x_tr, dtype=torch.float32, device="cuda")
            yt = torch.tensor(y_tr, dtype=torch.float32,
                              device="cuda").unsqueeze(-1)
            lossf = torch.nn.BCEWithLogitsLoss()
            for _ in range(300):
                opt.zero_grad()
                lossf(net(xt), yt).backward()
                opt.step()
            for i in te:
                xs = (feats[i] - mu) / sd
                with torch.no_grad():
                    scores[i] = net(torch.tensor(
                        xs, dtype=torch.float32, device="cuda")
                    ).squeeze(-1).cpu().numpy()

        top1_probe = top1_indis = 0
        hit_probe = hit_indis = 0
        n_expr = 0
        for i, m in enumerate(meta):
            if scores[i] is None:
                continue
            n_expr += 1
            tgt = m["accept"] if label_name == "accept" else m["positive"]
            if not bool(tgt.any()):
                continue
            q_probe = int(np.argmax(scores[i]))
            q_indis = int(np.argmax(m["indis"]))
            hit_probe += int(m["accept"][q_probe] > .5)
            hit_indis += int(m["accept"][q_indis] > .5)
            if tgt[q_probe] > .5:
                top1_probe += 1
            if tgt[q_indis] > .5:
                top1_indis += 1
        results[label_name] = dict(
            expressions=n_expr,
            probe_selects_acceptable=hit_probe / max(n_expr, 1),
            indis_selects_acceptable=hit_indis / max(n_expr, 1),
            probe_top1_matches_label=top1_probe / max(n_expr, 1),
            indis_top1_matches_label=top1_indis / max(n_expr, 1))

    summary = dict(
        expressions=len(meta), scenes=len(scenes),
        feature_dim=int(dim), folds=5, protocol="scene-grouped CV, no scene in both "
        "train and test", labels=results)
    report = dict(
        summary=summary,
        scope="Fixed16 TRAIN batches, M95 eval forward, ONE same-forward capture. "
              "Features per query: final decoder query embedding (256), query position "
              "relative to the scene centroid, predicted-mask centroid offset, "
              "normalised mask size, max mask logit. No GT is used as a feature; GT is "
              "used only to form labels. A scene-grouped 3-layer MLP is trained per "
              "fold and evaluated on held-out scenes, so this measures whether the "
              "information is present in the head's own input, not memorisation. "
              "Feasibility probe only; not a deployable head, and no model, novelty or "
              "efficacy admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
