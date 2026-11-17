"""Causal intervention: force selection inside the training-positive set.

The 2026-09-13 decisions (20260913-061110, 20260913-071026) refused label repair
because "descriptive association is not causal evidence" and "scientific admission
remains incomplete". This runs the missing intervention instead: hold the trained
checkpoint fixed and only change WHICH query is selected, in one same-forward capture.

  deployed : argmax of indis over all sampled queries (the model's actual behaviour)
  positive : argmax of indis restricted to queries whose seed superpoint carries the
             referred instance id, i.e. the native training-positive set
  anyseed  : argmax restricted to queries whose seed lies inside ANY instance
             (weaker than `positive`: needs no referent identity, only objectness)

`positive` is oracle (it needs GT at test time). It is therefore a causal test of the
mechanism, and an upper bound, never a deployable result. `anyseed` is reported to
show how much of the effect survives when referent identity is not available.
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
OUT = ROOT.parent / "pipeline/positive_membership_intervention_20260916"
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
    dataset = build_dataset(cfg.data.train, logging.getLogger("intervention"))
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
        HELD["fps"] = args[7]

    model.criterion.register_forward_pre_hook(capture)
    rows = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            gorilla.set_random_seed(1999)
            model(batch, mode="loss")
            pred = HELD["pred"]
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
                masks = pred["masks"][b, :, :n] >= 0
                iou = ((masks & target).sum(-1).float()
                       / (masks | target).sum(-1).clamp_min(1).float())
                prob = pred["indis"][b].softmax(-1)[:, 1]
                obj_ids = {int(v) for v in HELD["object_ids"][b]}
                if not obj_ids:
                    continue
                fps = HELD["fps"][b].long()
                sample = pred["sample_inds"][b].long().clamp(0, len(fps) - 1)
                seed_inst = labels[fps[sample].clamp(0, n - 1)]
                seed_valid = valid[fps[sample].clamp(0, n - 1)]
                is_positive = seed_valid & torch.tensor(
                    [int(v) in obj_ids for v in seed_inst], device=labels.device)
                is_anyseed = seed_valid & (seed_inst != 199)

                def pick(mask):
                    if not bool(mask.any()):
                        return int(prob.argmax()), False
                    p = prob.clone()
                    p[~mask] = -1.0
                    return int(p.argmax()), True

                d_q, _ = pick(torch.ones_like(is_positive, dtype=torch.bool))
                p_q, p_ok = pick(is_positive)
                a_q, a_ok = pick(is_anyseed)
                rows.append(dict(
                    step=step, scene=(str(scenes[b]) if b < len(scenes) else None),
                    deployed_success=bool(iou[d_q] > .5),
                    positive_success=bool(iou[p_q] > .5),
                    positive_available=bool(p_ok),
                    anyseed_success=bool(iou[a_q] > .5),
                    anyseed_available=bool(a_ok),
                    n_positive=int(is_positive.sum()),
                    n_anyseed=int(is_anyseed.sum()),
                    deployed_iou=float(iou[d_q]),
                    positive_iou=float(iou[p_q]),
                    anyseed_iou=float(iou[a_q]),
                    any_acceptable=int((iou > .5).sum())))
            print(json.dumps(dict(step=step, expressions=len(rows))), flush=True)

    by_scene = defaultdict(list)
    for r in rows:
        by_scene[r["scene"]].append(r)

    def bootstrap(values, draws=10000, seed=1999):
        rng = np.random.RandomState(seed)
        v = np.asarray(values, dtype=float)
        n = len(v)
        s = v[rng.randint(0, n, size=(draws, n))].mean(axis=1)
        return dict(mean=float(s.mean()), lo=float(np.percentile(s, 2.5)),
                    hi=float(np.percentile(s, 97.5)))

    def report(key):
        pooled = sum(1 for r in rows if r[key]) / len(rows)
        scene_rates = [sum(1 for r in g if r[key]) / len(g)
                       for g in by_scene.values()]
        return dict(pooled=pooled, scene_balanced=float(np.mean(scene_rates)),
                    scene_bootstrap_95ci=bootstrap(scene_rates))

    succ = {k: report(k) for k in
            ("deployed_success", "positive_success", "anyseed_success")}
    deltas = []
    for r in rows:
        deltas.append(int(r["positive_success"]) - int(r["deployed_success"]))
    by_scene_delta = []
    for g in by_scene.values():
        by_scene_delta.append(
            sum(int(r["positive_success"]) - int(r["deployed_success"])
                for r in g) / len(g))
    summary = dict(
        expressions=len(rows), scenes=len(by_scene),
        positive_available=sum(1 for r in rows if r["positive_available"]) / len(rows),
        anyseed_available=sum(1 for r in rows if r["anyseed_available"]) / len(rows),
        mean_positives_per_expression=(
            sum(r["n_positive"] for r in rows) / len(rows)),
        mean_anyseed_per_expression=(
            sum(r["n_anyseed"] for r in rows) / len(rows)),
        success=succ,
        paired_delta_positive_minus_deployed=dict(
            pooled=float(np.mean(deltas)),
            scene_balanced=float(np.mean(by_scene_delta)),
            scene_bootstrap_95ci=bootstrap(by_scene_delta)),
        fixed=sum(1 for r in rows
                  if r["positive_success"] and not r["deployed_success"]),
        broken=sum(1 for r in rows
                   if r["deployed_success"] and not r["positive_success"]))
    report_doc = dict(
        summary=summary, rows=rows,
        scope="Fixed16 TRAIN batches, M95 eval forward, ONE same-forward capture. Only "
              "the selection rule changes; the checkpoint, the query set and all "
              "scores are untouched. `positive` selection is oracle because the "
              "training-positive set is defined with GT instance labels, so it is a "
              "causal test and an upper bound, never a deployable result. `anyseed` "
              "drops referent identity and keeps only objectness, so it shows how much "
              "of the effect survives without GT identity. Diagnosis only; no model, "
              "novelty or efficacy admission.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(__file__), CONFIG, CHECKPOINT)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(report_doc, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
