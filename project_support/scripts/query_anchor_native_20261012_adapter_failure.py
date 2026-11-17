"""Native FPS/selected-anchor exposure audit, no optimization or model edits."""
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
    from torch.utils.data import DataLoader
    from framework.dataset import build_dataset
    from m95_multiword_native_31_20260928 import selected_loader
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    manifest = PIPE / "point_detail_population_20261009/result.manifest.json"
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    assert sha(manifest) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    native_loss = ROOT / f"framework/model/Quard_model/{NAME}/loss.py"
    assert sha(native_loss) == "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"
    config = ROOT / f"configs/Quard/ctf_hcg_csort/{NAME}.yaml"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = str(DATA) + "/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("anchor-coverage"))
    manifest_rows = json.loads(manifest.read_text())
    frozen = {(r["scene"], int(a["ann_id"])): sorted(map(int, a["object_ids"]))
              for r in manifest_rows for a in r["annotations"]}
    assert len(manifest_rows) == 32 and len(frozen) == 128
    indices = [int(r["native_group"]) for r in manifest_rows]
    model = importlib.import_module(
        "framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    criterion = model.criterion
    held, last = {}, {}
    hook = criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(pred=inputs[0], args=inputs))
    original = criterion.loss_indi

    def capture(self, logits, targets, matches, count):
        if logits is held["pred"]["indis"]:
            last.update(targets=targets, matches=matches)
        return original(logits, targets, matches, count)

    criterion.loss_indi = types.MethodType(capture, criterion)
    rows, previous = [], {}
    try:
        for trial in (0, 1):
            gorilla.set_random_seed(1999)
            loader = selected_loader(source, indices, DataLoader)
            for bi, batch in enumerate(loader):
                held.clear()
                last.clear()
                gorilla.set_random_seed(1999)
                with torch.no_grad():
                    total, _ = model(batch, mode="loss")
                assert bool(torch.isfinite(total).all())
                pred, args = held["pred"], held["args"]
                labels, fps = args[4], args[7].long()
                scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                          for _ in range(int(n))]
                fingerprint = batch_fingerprint(torch, batch)
                for b, (scene, ann) in enumerate(zip(scenes, batch["ann_ids"])):
                    key = (scene, int(ann))
                    if key not in frozen:
                        continue
                    targets = sorted(map(int, batch["object_idss"][b]))
                    assert targets == frozen[key]
                    physical = labels[b].long()
                    seed_labels = physical[fps[b]]
                    sample = pred["sample_inds"][b].long()
                    sampled_labels = seed_labels[sample]
                    mask = batch["gt_spmasks"][b].flatten().bool()
                    nsp = mask.numel()
                    z = pred["indis"][b].detach().cpu()
                    masks = pred["masks"][b, :, :nsp].detach().cpu()
                    assert sample.numel() == 128 and fps[b].numel() == 512
                    gt = mask.cpu()
                    positive = last["matches"][b][0].tolist()
                    chosen = int(z.softmax(-1)[:, 1].argmax())
                    binary = masks > 0
                    iou = ((binary & gt).sum(-1).float()
                           / (binary | gt).sum(-1).clamp_min(1))
                    target_set = torch.tensor(targets, device=physical.device)
                    fps_membership = torch.isin(seed_labels, target_set)
                    sampled_membership = torch.isin(sampled_labels, target_set)
                    wrong_candidates = sorted(set(physical[:nsp].tolist())
                                              - set(targets) - {-100, -1})
                    wrong_id = wrong_candidates[0] if wrong_candidates else None
                    wrong_membership = (sampled_labels == wrong_id
                                        if wrong_id is not None else None)
                    old = previous.get(key)
                    repeat = None
                    if old is not None:
                        repeat = {
                            "input_equal": old["input"] == fingerprint,
                            "fps_equal": torch.equal(old["fps"], fps[b].cpu()),
                            "samples_equal": torch.equal(old["sample"], sample.cpu()),
                            "labels_equal": torch.equal(old["labels"], physical.cpu()),
                            "positive_ids_equal": old["positive"] == positive,
                            "logit_max_delta": float((old["z"] - z).abs().max()),
                            "mask_max_delta": float((old["masks"] - masks).abs().max()),
                        }
                    previous[key] = {
                        "input": fingerprint, "fps": fps[b].cpu().clone(),
                        "sample": sample.cpu().clone(), "labels": physical.cpu().clone(),
                        "positive": positive, "z": z.clone(), "masks": masks.clone()}
                    rows.append({
                        "trial": trial, "batch": bi, "scene": scene, "ann_id": int(ann),
                        "target_ids": targets, "input_sha256": fingerprint,
                        "target_points": int(batch["gt_pmasks"][b].sum()),
                        "target_superpoints": int(mask.sum()),
                        "physical_target_superpoints": int(
                            torch.isin(physical[:nsp], target_set).sum()),
                        "fps_physical_target_count": int(fps_membership.sum()),
                        "sampled_physical_target_count": int(sampled_membership.sum()),
                        "native_positive_count": len(positive),
                        "native_positive_ids": positive,
                        "sampled_physical_target_ids": sampled_membership.nonzero(
                            as_tuple=True)[0].tolist(),
                        "wrong_instance_control": wrong_id,
                        "identity_control_membership_delta": (
                            int((wrong_membership != sampled_membership).sum())
                            if wrong_membership is not None else None),
                        "selected_query": chosen, "selected_iou": float(iou[chosen]),
                        "oracle_iou": float(iou.max()), "repeat": repeat})
                print(json.dumps({"trial": trial, "batch": bi,
                                  "captured": len(rows)}), flush=True)
    finally:
        criterion.loss_indi = original
        hook.remove()
    cohort = [r for r in rows if r["trial"] == 0]
    repeated = [r["repeat"] for r in rows if r["trial"] == 1]
    assert len(cohort) == len(repeated) == 128
    assert {(r["scene"], r["ann_id"]) for r in cohort} == set(frozen)
    missing = [r for r in cohort if r["sampled_physical_target_count"] == 0]
    result = {
        "contract": "native_physical_query_anchor_coverage_v1", "admission": False,
        "seed": 1999, "checkpoint_sha256": sha(checkpoint),
        "manifest_sha256": sha(manifest), "native_loss_sha256": sha(native_loss),
        "script_sha256": sha(Path(__file__)),
        "summary": {
            "expressions": 128, "scenes": 32,
            "no_surviving_target": sum(r["target_points"] == 0 for r in cohort),
            "no_physical_target_sp": sum(r["physical_target_superpoints"] == 0 for r in cohort),
            "no_fps_target_anchor": sum(r["fps_physical_target_count"] == 0 for r in cohort),
            "no_selected_target_anchor": len(missing),
            "missing_anchor_with_native_fallback_positive": sum(
                r["native_positive_count"] > 0 for r in missing),
            "missing_anchor_oracle_iou_ge_05": sum(r["oracle_iou"] >= .5 for r in missing),
            "all_discrete_repeats_equal": all(
                all(r[k] for k in ("input_equal", "fps_equal", "samples_equal",
                                  "labels_equal", "positive_ids_equal"))
                for r in repeated),
            "native_logit_repeat_max": max(r["logit_max_delta"] for r in repeated),
            "native_mask_repeat_max": max(r["mask_max_delta"] for r in repeated),
        },
        "rows": rows,
        "limits": "Existing native loss-mode eval; no optimization, new-model backward, resources or efficacy. Oracle readout is diagnostic only; physical label majority and actual target point support are distinct."
    }
    output = PIPE / "query_anchor_native_20261012.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"]), flush=True)


if __name__ == "__main__":
    main()
