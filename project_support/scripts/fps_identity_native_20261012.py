"""Controlled native coordinate/FPS/referent-binding diagnosis."""
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
DATA = Path("/data3/songcl/data/data_cluster")
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
    from framework.dataset import build_dataset
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    manifest = PIPE / "point_detail_population_20261009/result.manifest.json"
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    assert sha(manifest) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    cfg = gorilla.Config.fromfile(str(
        ROOT / f"configs/Quard/ctf_hcg_csort/{NAME}.yaml"))
    cfg.model.data_root = cfg.data.train.data_root = str(DATA) + "/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("fps-identity"))
    selected = next(r for r in json.loads(manifest.read_text())
                    if r["scene"] == "scene0124_00")
    index = int(selected["native_group"])
    native_module = importlib.import_module(
        "framework.model.Quard_model." + NAME + ".network")
    model = native_module.Network(**cfg.model)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    gorilla.set_random_seed(1999)
    batch = source.collate_fn([source[index]])
    assert sorted(batch["ann_ids"]) == sorted(int(a["ann_id"])
                                              for a in selected["annotations"])
    fingerprint = batch_fingerprint(torch, batch)
    held, captured, last = {}, {}, {}
    reference = {}
    phase = ["original"]
    original_expand = model.expand_and_fps
    original_loss = model.criterion.loss_indi
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(pred=inputs[0], args=inputs))

    def expand(self, features, coords, offsets, labels, lengths, images, mode=None):
        raw = coords.detach().clone()
        if not reference:
            reference["coords"] = raw.clone()
        used = reference["coords"] if phase[0] == "fixed_geometry" else coords
        result = original_expand(features, used, offsets, labels, lengths, images, mode)
        captured.update(raw=raw, used=used.detach().clone(), fps=result[2].detach().clone())
        return result

    def loss(self, logits, targets, matches, count):
        if logits is held["pred"]["indis"]:
            last.update(matches=matches)
        return original_loss(logits, targets, matches, count)

    model.expand_and_fps = types.MethodType(expand, model)
    model.criterion.loss_indi = types.MethodType(loss, model.criterion)
    rows, baseline, saved = [], None, None
    try:
        for mode in ("original", "fixed_geometry"):
            phase[0] = mode
            phase_reference = None
            for trial in range(4):
                gorilla.set_random_seed(1999)
                held.clear()
                captured.clear()
                last.clear()
                with torch.no_grad():
                    total, _ = model(batch, mode="loss")
                assert bool(torch.isfinite(total).all())
                args, pred = held["args"], held["pred"]
                samples = pred["sample_inds"].long()
                fps = captured["fps"].long()
                labels = torch.stack([x[f] for x, f in zip(args[4], fps)])
                physical = labels.gather(1, samples)
                positives = [sorted(x[0].tolist()) for x in last["matches"]]
                state = {
                    "coords": captured["used"].cpu(), "fps": fps.cpu(),
                    "samples": samples.cpu(), "physical": physical.cpu(),
                    "positives": positives, "z": pred["indis"].detach().cpu(),
                    "m": pred["masks"].detach().cpu()}
                if baseline is None:
                    baseline = {k: v.clone() if torch.is_tensor(v) else v
                                for k, v in state.items()}
                if phase_reference is None:
                    phase_reference = {k: v.clone() if torch.is_tensor(v) else v
                                       for k, v in state.items()}
                previous = phase_reference
                current = {
                    "mode": mode, "trial": trial, "native_total_loss": float(total),
                    "raw_coordinate_delta_from_initial": float(
                        (captured["raw"].cpu() - reference["coords"].cpu()).abs().max()),
                    "used_coordinate_delta_from_phase_first": float(
                        (state["coords"] - previous["coords"]).abs().max()),
                    "fps_changed_indices": int((state["fps"] != previous["fps"]).sum()),
                    "sample_changed_indices": int((state["samples"] != previous["samples"]).sum()),
                    "physical_query_instance_changes": int(
                        (state["physical"] != previous["physical"]).sum()),
                    "native_positive_changes": sum(
                        len(set(a) ^ set(b)) for a, b in zip(positives, previous["positives"])),
                    "logit_repeat_delta": float((state["z"] - previous["z"]).abs().max()),
                    "mask_repeat_delta": float((state["m"] - previous["m"]).abs().max()),
                    "physical_instances": state["physical"].tolist(),
                    "positive_query_ids": positives}
                rows.append(current)
                saved = state
                print(json.dumps({k: v for k, v in current.items()
                                  if k not in ("physical_instances", "positive_query_ids")}),
                      flush=True)
        coords = reference["coords"].unsqueeze(0).contiguous()
        fps_trials = []
        for _ in range(2):
            gorilla.set_random_seed(1999)
            fps_trials.append(native_module.FurthestPointSampling.apply(
                coords, int(cfg.model.fps_num)).detach().cpu())
        match_controls = []
        for b, target_ids in enumerate(batch["object_idss"]):
            original_labels = args[4][b]
            selected_labels = original_labels[fps[b]][samples[b]]
            values, counts = selected_labels.unique(return_counts=True)
            candidates = [(int(n), int(v)) for v, n in zip(values, counts)
                          if int(v) >= 0 and int(v) not in target_ids]
            if not candidates:
                match_controls.append({"ann_id": batch["ann_ids"][b],
                                       "control": "unavailable"})
                continue
            wrong = max(candidates)[1]
            local_coords = captured["used"]
            object_center = local_coords[original_labels == wrong].mean(0, keepdim=True)
            sampled_coords = local_coords[fps[b]][samples[b]]
            _, _, wrong_matches, _ = model.criterion.match_sampled_ins(
                selected_labels, [wrong], sampled_coords, object_center)
            wrong_positive = set(wrong_matches[0].tolist())
            match_controls.append({
                "ann_id": int(batch["ann_ids"][b]), "wrong_target_id": wrong,
                "positive_assignment_delta": len(
                    wrong_positive ^ set(saved["positives"][b]))})
    finally:
        model.expand_and_fps = original_expand
        model.criterion.loss_indi = original_loss
        hook.remove()
    original_rows = [r for r in rows if r["mode"] == "original"]
    fixed_rows = [r for r in rows if r["mode"] == "fixed_geometry"]
    result = {
        "contract": "native_fixed_geometry_fps_identity_v1", "admission": False,
        "manifest_sha256": sha(manifest), "checkpoint_sha256": sha(checkpoint),
        "script_sha256": sha(Path(__file__)), "input_sha256": fingerprint,
        "scene": "scene0124_00", "seed": 1999, "expressions": len(batch["ann_ids"]),
        "ann_ids": list(map(int, batch["ann_ids"])),
        "summary": {
            "original_positive_assignment_changes": sum(
                r["native_positive_changes"] for r in original_rows),
            "original_physical_instance_changes": sum(
                r["physical_query_instance_changes"] for r in original_rows),
            "original_fps_changes": sum(r["fps_changed_indices"] for r in original_rows),
            "fixed_geometry_positive_assignment_changes": sum(
                r["native_positive_changes"] for r in fixed_rows),
            "fixed_geometry_fps_changes": sum(r["fps_changed_indices"] for r in fixed_rows),
            "fixed_input_fps_primitive_equal": torch.equal(*fps_trials),
            "original_logit_repeat_max": max(r["logit_repeat_delta"] for r in original_rows),
            "original_mask_repeat_max": max(r["mask_repeat_delta"] for r in original_rows),
            "fixed_geometry_logit_repeat_max": max(r["logit_repeat_delta"] for r in fixed_rows),
            "fixed_geometry_mask_repeat_max": max(r["mask_repeat_delta"] for r in fixed_rows),
            "negative_identity_control_separated": all(
                r.get("positive_assignment_delta", 0) > 0 for r in match_controls),
            "all_native_strict_repeat_pass": all(
                r["logit_repeat_delta"] <= 1e-6 and r["mask_repeat_delta"] <= 1e-6
                for r in rows)},
        "rows": rows, "negative_identity_controls": match_controls,
        "limits": "Single original frozen group, new declared fixed batch fingerprint, no assumption it equals the earlier full-population augmentation. Diagnostic coordinate restoration and existing native forward only; not model repair/new-model backward/resources/efficacy. Earlier native failures retained."
    }
    output = PIPE / "fps_identity_native_20261012.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"]), flush=True)


if __name__ == "__main__":
    main()
