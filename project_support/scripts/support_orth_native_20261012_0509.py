"""Native support correspondence and CSORT derivative diagnosis; no optimizer."""
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys

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
    hierarchy_path = ROOT / f"framework/model/Quard_model/{NAME}/hier_postprocess.py"
    assert sha(manifest) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    assert sha(hierarchy_path) == "7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f"
    config = ROOT / f"configs/Quard/ctf_hcg_csort/{NAME}.yaml"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("support-orth"))
    manifest_rows = json.loads(manifest.read_text())
    frozen = {(r["scene"], int(a["ann_id"])): sorted(map(int, a["object_ids"]))
              for r in manifest_rows for a in r["annotations"]}
    model = importlib.import_module(
        "framework.model.Quard_model." + NAME).Network(**cfg.model)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    held = {}
    hook = model.dec.cluster_att.register_forward_pre_hook(
        lambda module, args: held.update(
            features=[t.detach().cpu() for t in args[3]],
            maps=args[4],
            ids=[[t.detach().cpu().long() for t in level] for level in args[5]]))
    objective = model.dec.cluster_att._cross_scale_orth_loss

    def reconstructed(fine, parent, count):
        return torch.stack([fine[parent == c].mean(0) for c in range(count)])

    def coupled(fine_native, parent, coarse_count, mapping):
        fine = fine_native.double().clone().requires_grad_(True)
        coarse = reconstructed(fine, parent, coarse_count)
        value = objective(coarse.unsqueeze(0), fine.unsqueeze(0), [mapping])
        grad = torch.autograd.grad(value, fine)[0]
        assert bool(torch.isfinite(value)) and bool(torch.isfinite(grad).all())
        return float(value), grad, float(coarse.norm(dim=-1).min())

    rows = []
    try:
        gorilla.set_random_seed(1999)
        loader = selected_loader(source, [int(r["native_group"]) for r in manifest_rows],
                                 DataLoader)
        for bi, batch in enumerate(loader):
            held.clear()
            gorilla.set_random_seed(1999)
            with torch.no_grad():
                loss, _ = model(batch, mode="loss")
            assert bool(torch.isfinite(loss).all())
            fingerprint = batch_fingerprint(torch, batch)
            scenes = [scene for scene, count in zip(
                batch["scan_ids"], batch["scenes_len"]) for _ in range(int(count))]
            for b, (scene, ann) in enumerate(zip(scenes, batch["ann_ids"])):
                key = scene, int(ann)
                if key not in frozen:
                    continue
                assert sorted(map(int, batch["object_idss"][b])) == frozen[key]
                for level in (0, 1):
                    fine_native = held["features"][level][b]
                    coarse_native = held["features"][level + 1][b]
                    parent = held["ids"][level + 1][b]
                    coarse_count = coarse_native.shape[0]
                    assert fine_native.shape[0] == parent.numel()
                    assert all(bool((parent == c).any()) for c in range(coarse_count))
                    exact = {f: [int(c)] for f, c in enumerate(parent.tolist())}
                    rotated = {f: [(int(c) + 1) % coarse_count]
                               for f, c in enumerate(parent.tolist())}
                    original = held["maps"][level][b]
                    edges = [(int(f), int(c)) for f, cs in original.items() for c in cs]
                    tests = {}
                    for name, mapping in (("support", exact), ("rotated", rotated),
                                          ("original", original)):
                        value, grad, min_norm = coupled(
                            fine_native, parent, coarse_count, mapping)
                        again, grad_again, _ = coupled(
                            fine_native, parent, coarse_count, mapping)
                        tests[name] = {
                            "loss": value, "gradient_max": float(grad.abs().max()),
                            "gradient_l2": float(grad.norm()),
                            "gradient_finite": True, "parent_min_norm": min_norm,
                            "repeat_loss_delta": abs(value - again),
                            "repeat_gradient_max_delta": float((grad - grad_again).abs().max())}
                    actual_fine = fine_native.double().clone().requires_grad_(True)
                    actual_coarse = coarse_native.double().clone().requires_grad_(True)
                    value = objective(actual_coarse.unsqueeze(0),
                                      actual_fine.unsqueeze(0), [exact])
                    gradients = torch.autograd.grad(value, (actual_fine, actual_coarse))
                    mean = reconstructed(fine_native.double(), parent, coarse_count)
                    row = {
                        "scene": scene, "ann_id": int(ann), "level": level,
                        "input_sha256": fingerprint, "fine_count": parent.numel(),
                        "coarse_count": coarse_count, "sparse_edges": len(edges),
                        "fine_covered_by_original": len(set(f for f, c in edges)),
                        "original_edges_with_actual_parent": sum(
                            int(parent[f]) == c for f, c in edges),
                        "original_wrong_parent_edges": sum(
                            int(parent[f]) != c for f, c in edges),
                        "actual_coarse_vs_support_mean_max": float(
                            (coarse_native.double() - mean).abs().max()),
                        "native_detached_support_loss": float(value),
                        "native_detached_fine_gradient_max": float(gradients[0].abs().max()),
                        "native_detached_coarse_gradient_max": float(gradients[1].abs().max()),
                        "tests": tests}
                    rows.append(row)
            print(json.dumps({"batch": bi, "pairs": len(rows)}), flush=True)
    finally:
        hook.remove()
    assert len(rows) == 256
    assert {(r["scene"], r["ann_id"]) for r in rows} == set(frozen)
    summary = {
        "expressions": 128, "scenes": 32, "native_scale_pairs": len(rows),
        "fine_total": sum(r["fine_count"] for r in rows),
        "sparse_edge_total": sum(r["sparse_edges"] for r in rows),
        "fine_covered_total": sum(r["fine_covered_by_original"] for r in rows),
        "wrong_parent_edges": sum(r["original_wrong_parent_edges"] for r in rows),
        "coarse_mean_max_delta": max(r["actual_coarse_vs_support_mean_max"] for r in rows),
        "native_detached_support_loss_min": min(r["native_detached_support_loss"] for r in rows),
        "native_detached_support_loss_max": max(r["native_detached_support_loss"] for r in rows),
        "coupled_support_loss_max_abs_from_one": max(
            abs(r["tests"]["support"]["loss"] - 1) for r in rows),
        "coupled_support_gradient_max": max(
            r["tests"]["support"]["gradient_max"] for r in rows),
        "coupled_original_gradient_max": max(
            r["tests"]["original"]["gradient_max"] for r in rows),
        "coupled_rotated_gradient_max": max(
            r["tests"]["rotated"]["gradient_max"] for r in rows),
        "rotated_control_separated_pairs": sum(
            abs(r["tests"]["rotated"]["loss"] - r["tests"]["support"]["loss"]) > 1e-6
            for r in rows),
        "original_control_separated_pairs": sum(
            abs(r["tests"]["original"]["loss"] - r["tests"]["support"]["loss"]) > 1e-6
            for r in rows),
        "all_parent_norms_above_original_epsilon": all(
            r["tests"]["support"]["parent_min_norm"] > 1e-6 for r in rows),
        "operator_repeat_loss_max": max(
            t["repeat_loss_delta"] for r in rows for t in r["tests"].values()),
        "operator_repeat_gradient_max": max(
            t["repeat_gradient_max_delta"] for r in rows for t in r["tests"].values())}
    result = {
        "contract": "native_support_faithful_csort_operator_v1", "seed": 1999,
        "admission": False, "summary": summary, "rows": rows,
        "script_sha256": sha(Path(__file__)), "checkpoint_sha256": sha(checkpoint),
        "manifest_sha256": sha(manifest), "hierarchy_sha256": sha(hierarchy_path),
        "config_sha256": sha(config),
        "limits": "Operator derivatives on detached native float64 features. No complete new-model backward/resource/independence/efficacy gate. Whole native forward repeats not measured here; separate captured failures remain failures. Original correspondence objective is not claimed ineffective."}
    output = PIPE / "support_orth_native_20261012_0509.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
