"""Native target-distractor context alias capture; no model or optimizer edits."""
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import types

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "7"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT), str(ROOT / "framework/lib")]
    import torch
    import gorilla
    from torch.utils.data import DataLoader
    from framework.dataset import build_dataset
    from m95_multiword_native_31_20260928 import selected_loader
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    manifest = PIPE / "point_detail_population_20261009/result.manifest.json"
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    dataset_path = ROOT / "framework/dataset/scannetv2.py"
    assert sha(manifest) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    assert sha(dataset_path) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    config = ROOT / f"configs/Quard/ctf_hcg_csort/{NAME}.yaml"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("scale-alias"))
    manifest_rows = json.loads(manifest.read_text())
    frozen = {(r["scene"], int(a["ann_id"])): sorted(map(int, a["object_ids"]))
              for r in manifest_rows for a in r["annotations"]}
    indices = [int(r["native_group"]) for r in manifest_rows]
    model = importlib.import_module(
        "framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    original_label = source.get_sp_label
    semantics, captured, criterion_args = {}, {}, {}

    def capture_labels(self, superpoints, instances, classes):
        result = original_label(superpoints, instances, classes)
        semantics.clear()
        for instance in instances.unique().tolist():
            valid = classes[instances == instance]
            valid = valid[valid >= 0]
            if valid.numel():
                values, counts = valid.unique(return_counts=True)
                semantics[int(instance)] = int(values[counts.argmax()])
        return result

    source.get_sp_label = types.MethodType(capture_labels, source)
    attention = model.dec.cluster_att
    original_readback = attention._cluster_to_points

    def capture_context(self, point_feats, features, ids, point_mask):
        output = original_readback(point_feats, features, ids, point_mask)
        captured.update(ids=[[t.detach().cpu() for t in level] for level in ids],
                        features=[t.detach().cpu() for t in features],
                        output=output.detach().cpu())
        return output

    attention._cluster_to_points = types.MethodType(capture_context, attention)
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: criterion_args.update(inputs=inputs))
    rows, previous = [], {}

    def distributions(levels, mask):
        return [torch.bincount(level[mask], minlength=int(level.max()) + 1)
                for level in levels]

    def compare(left, right):
        equal, overlaps = [], []
        for a, b in zip(left, right):
            equal.append(bool(torch.equal(a * b.sum(), b * a.sum())))
            aa, bb = a > 0, b > 0
            overlaps.append(float((aa & bb).sum() / (aa | bb).sum().clamp_min(1)))
        return {"distribution_equal": equal, "support_jaccard": overlaps,
                "all_scales_distribution_equal": all(equal)}

    try:
        for trial in (0, 1):
            gorilla.set_random_seed(1999)
            loader = selected_loader(source, indices, DataLoader)
            for bi, batch in enumerate(loader):
                captured.clear()
                criterion_args.clear()
                gorilla.set_random_seed(1999)
                with torch.no_grad():
                    loss, _ = model(batch, mode="loss")
                assert bool(torch.isfinite(loss).all())
                args = criterion_args["inputs"]
                pred, labels, coords, offsets = args[0], args[4], args[8], args[9]
                fingerprint = batch_fingerprint(torch, batch)
                scenes = [scene for scene, count in zip(
                    batch["scan_ids"], batch["scenes_len"]) for _ in range(int(count))]
                for b, (scene, ann) in enumerate(zip(scenes, batch["ann_ids"])):
                    key = scene, int(ann)
                    if key not in frozen:
                        continue
                    targets = sorted(map(int, batch["object_idss"][b]))
                    assert targets == frozen[key]
                    physical = labels[b].detach().cpu().long()
                    nsp = int(offsets[b + 1] - offsets[b])
                    physical = physical[:nsp]
                    pos = coords[int(offsets[b]):int(offsets[b + 1])].detach().cpu()
                    level = captured["ids"][0][b].long()
                    levels = [level]
                    for l in (1, 2):
                        levels.append(captured["ids"][l][b].long()[levels[-1]])
                    assert all(t.numel() == nsp for t in levels)
                    context = captured["output"][b, :nsp]
                    z = pred["indis"][b].detach().cpu()
                    masks = pred["masks"][b, :, :nsp].detach().cpu()
                    row = {"trial": trial, "scene": scene, "ann_id": int(ann),
                           "target_ids": targets, "input_sha256": fingerprint,
                           "status": "multi_target" if len(targets) != 1 else "pending"}
                    if len(targets) == 1:
                        target = targets[0]
                        tm = physical == target
                        category = semantics.get(target)
                        choices = [i for i in physical.unique().tolist()
                                   if i not in (target, -100, -1, 199)
                                   and category is not None
                                   and semantics.get(i) == category]
                        if not bool(tm.any()):
                            row["status"] = "missing_physical_target_support"
                        elif category is None:
                            row["status"] = "missing_native_semantic_class"
                        elif not choices:
                            row["status"] = "no_same_category_distractor"
                        else:
                            center = pos[tm].mean(0)
                            ordered = sorted(choices, key=lambda i: (
                                float((pos[physical == i].mean(0) - center).norm()), i))
                            near, far = ordered[0], ordered[-1]
                            nm, fm = physical == near, physical == far
                            td = distributions(levels, tm)
                            row.update(
                                status="eligible", native_semantic_class=category,
                                distractor=near, far_control=far,
                                distractor_count=len(choices),
                                target_superpoints=int(tm.sum()),
                                distractor_superpoints=int(nm.sum()),
                                closest_control=compare(td, distributions(levels, nm)),
                                self_control=compare(td, td),
                                far_control_readout=compare(td, distributions(levels, fm)),
                                context_mean_l2=float(
                                    (context[tm].mean(0) - context[nm].mean(0)).norm()),
                                target_level_counts=[t.tolist() for t in td],
                                distractor_level_counts=[
                                    t.tolist() for t in distributions(levels, nm)])
                    old = previous.get(key)
                    repeat = None
                    if old:
                        repeat = {
                            "input_equal": old["input"] == fingerprint,
                            "composed_ids_equal": all(torch.equal(a, bb) for a, bb
                                                     in zip(old["levels"], levels)),
                            "pair_readout_equal": old["control"] == row.get("closest_control"),
                            "status_equal": old["status"] == row["status"],
                            "logit_max_delta": float((old["z"] - z).abs().max()),
                            "mask_max_delta": float((old["masks"] - masks).abs().max())}
                    previous[key] = {"input": fingerprint, "levels": levels,
                                     "control": row.get("closest_control"),
                                     "status": row["status"], "z": z, "masks": masks}
                    row["repeat"] = repeat
                    rows.append(row)
                print(json.dumps({"trial": trial, "batch": bi,
                                  "captured": len(rows)}), flush=True)
    finally:
        hook.remove()
        attention._cluster_to_points = original_readback
        source.get_sp_label = original_label
    cohort = [r for r in rows if r["trial"] == 0]
    repeat = [r["repeat"] for r in rows if r["trial"] == 1]
    assert len(cohort) == len(repeat) == 128
    assert {(r["scene"], r["ann_id"]) for r in cohort} == set(frozen)
    eligible = [r for r in cohort if r["status"] == "eligible"]
    aliases = [r for r in eligible
               if r["closest_control"]["all_scales_distribution_equal"]]
    summary = {
        "expressions": 128, "scenes": 32, "eligible": len(eligible),
        "eligible_scenes": len({r["scene"] for r in eligible}),
        "status_counts": {s: sum(r["status"] == s for r in cohort)
                          for s in sorted({r["status"] for r in cohort})},
        "all_scale_aliases": len(aliases),
        "per_scale_equal_count": [sum(r["closest_control"]["distribution_equal"][l]
                                      for r in eligible) for l in (0, 1, 2)],
        "self_control_all_equal": all(r["self_control"]["all_scales_distribution_equal"]
                                      for r in eligible),
        "distinct_far_control_count": sum(r["distractor"] != r["far_control"]
                                          for r in eligible),
        "input_repeat_equal": all(r["input_equal"] for r in repeat),
        "composed_ids_repeat_equal": all(r["composed_ids_equal"] for r in repeat),
        "pair_readout_repeat_equal": all(r["pair_readout_equal"] for r in repeat),
        "native_logit_repeat_max": max(r["logit_max_delta"] for r in repeat),
        "native_mask_repeat_max": max(r["mask_max_delta"] for r in repeat)}
    result = {"contract": "native_target_distractor_scale_alias_v1",
              "seed": 1999, "admission": False, "summary": summary, "rows": rows,
              "script_sha256": sha(Path(__file__)),
              "checkpoint_sha256": sha(checkpoint), "manifest_sha256": sha(manifest),
              "dataset_sha256": sha(dataset_path), "config_sha256": sha(config),
              "hierarchy_sha256": sha(ROOT / f"framework/model/Quard_model/{NAME}/hier_postprocess.py"),
              "limits": "Native loss-mode eval; exact context support diagnosis only. Distinct fine supports do not prove task discrimination or efficacy. Physical majority support is not raw target geometry."}
    output = PIPE / "scale_alias_native_20261012_0509.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
