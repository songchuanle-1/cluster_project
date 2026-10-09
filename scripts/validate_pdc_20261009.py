"""Native controls/backward and calibrated resources for the independent PDC."""
import argparse
import copy
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys

NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pdc"
PARENT = NAME.removesuffix("_pdc")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
    print(json.dumps({"output": str(path), "sha256": sha(path)}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["native", "resource", "contracts"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", choices=["baseline", "champion", "candidate"])
    args = parser.parse_args()
    root = args.root.resolve()
    if (os.name != "posix" or os.environ.get("CUDA_VISIBLE_DEVICES") != "7"
            or args.output.exists()
            or not args.output.resolve().is_relative_to(root.parent / "pipeline")):
        raise ValueError("GPU7 native host and fresh project output required")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib"), str(root / "scripts")]
    config = root / "configs/Quard/pdc" / (NAME + ".yaml")
    if args.mode == "resource":
        import champion_baseline_resource_gate_20260922 as resource
        resource.TARGETS["candidate"] = {
            "name": NAME, "config": config.relative_to(root).as_posix(),
            "config_sha256": sha(config),
            "model_source_sha256": resource._model_package_sha256(root, NAME),
        }
        resource._measure_target(args.target, root,
                                 Path("/data3/songcl/data/data_cluster"), args.output)
        return
    import torch
    import gorilla
    from torch_scatter import scatter_mean
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.35)
    mod = importlib.import_module("framework.model.Quard_model." + NAME)
    from importlib import import_module
    Field = import_module("framework.model.Quard_model." + NAME + ".point_field").PointDetailField
    gorilla.set_random_seed(1999)
    if args.mode == "contracts":
        field = Field(6, 4).double().cuda()
        points = torch.randn(7, 4, dtype=torch.double, device="cuda", requires_grad=True)
        sp = torch.tensor([0, 0, 0, 1, 1, 2, 2], device="cuda")
        query = torch.randn(2, 6, dtype=torch.double, device="cuda", requires_grad=True)
        coarse = torch.randn(2, 3, dtype=torch.double, device="cuda", requires_grad=True)
        detail = field.center(points, sp)
        fine = field(query, coarse, detail, sp)
        mean_error = float((scatter_mean(fine, sp, dim=1) - coarse).abs().max())
        broadcast = field(query, coarse, torch.zeros_like(detail), sp)
        bypass_error = float((broadcast - coarse[:, sp]).abs().max())
        permutation = torch.tensor([2, 0, 1, 4, 3, 6, 5], device="cuda")
        equivariance_error = float((field(query, coarse, detail[permutation], sp) -
                                    fine[:, permutation]).abs().max())
        gradcheck = torch.autograd.gradcheck(
            lambda p, q, c: field(q, c, field.center(p, sp), sp),
            (points, query, coarse))
        fine.square().mean().backward()
        active = all(p.grad is not None and torch.isfinite(p.grad).all()
                     and p.grad.abs().sum() > 0 for p in field.parameters())
        passed = mean_error < 1e-10 and bypass_error == 0 and equivariance_error < 1e-10 and gradcheck and active
        save(args.output, dict(contract="pdc_operator_v1", passed=bool(passed),
                               mean_conservation_error=mean_error,
                               broadcast_bypass_error=bypass_error,
                               within_sp_equivariance_error=equivariance_error,
                               gradcheck=bool(gradcheck), all_new_tensors_active=bool(active),
                               script_sha256=sha(__file__), training_started=False))
        if not passed:
            raise ValueError("Operator contracts failed")
        return
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader
    from m95_multiword_native_31_20260928 import selected_loader, CHECKPOINT_SHA
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    source = build_dataset(cfg.data.train, logging.getLogger("pdc-native"))
    population_path = root.parent / "pipeline/point_detail_population_20261009/result.manifest.json"
    population = json.loads(population_path.read_text())
    selected = [row["native_group"] for row in population[:2]]
    loader = selected_loader(source, selected, DataLoader)
    model = mod.Network(**cfg.model).cuda().train()
    checkpoint = root.parent / "pipeline/scm_admission_20260914/best.pth"
    if sha(checkpoint) != CHECKPOINT_SHA:
        raise ValueError("Frozen diagnostic checkpoint differs")
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    incompatible = model.load_state_dict(state, strict=False)
    if incompatible.unexpected_keys or set(incompatible.missing_keys) != {
            "point_field.coefficients.0.weight", "point_field.coefficients.0.bias",
            "point_field.coefficients.2.weight", "point_field.coefficients.2.bias"}:
        raise ValueError("Only the genuinely new point field may be uninitialized")
    records = []
    for bi, batch in enumerate(loader):
        fp = batch_fingerprint(torch, batch)
        pred_held, fields = {}, []
        pre = model.criterion.register_forward_pre_hook(
            lambda module, inputs: pred_held.update(pred=inputs[0]))
        original_masks = None
        original_loss = None
        for arm in ("original", "repeat", "broadcast"):
            fields.clear()
            pred_held.clear()
            def replace_detail(module, inputs):
                q, coarse, detail, sp = inputs
                if arm == "broadcast":
                    detail = torch.zeros_like(detail)
                fields.append((coarse, detail, sp))
                return q, coarse, detail, sp
            control = model.point_field.register_forward_pre_hook(replace_detail)
            gorilla.set_random_seed(1999)
            model.zero_grad(set_to_none=True)
            torch.cuda.reset_peak_memory_stats()
            try:
                loss, losses = model(copy.deepcopy(batch), mode="loss")
                if not bool(torch.isfinite(loss).all()):
                    raise ValueError("Nonfinite full native loss")
                masks = pred_held["pred"]["masks"].detach().cpu()
                loss.backward()
            finally:
                control.remove()
            grads = {name: {"finite": p.grad is not None and bool(torch.isfinite(p.grad).all()),
                            "nonzero": p.grad is not None and bool(p.grad.abs().sum() > 0),
                            "norm": 0.0 if p.grad is None else float(p.grad.norm())}
                     for name, p in model.point_field.named_parameters()}
            conservation = max(float(scatter_mean(d, sp, dim=0).abs().max())
                               for _, d, sp in fields)
            if arm == "original":
                original_masks = masks
                original_loss = float(loss)
            records.append({
                "batch": bi, "arm": arm, "input_sha256": fp,
                "scenes": batch["scan_ids"], "ann_ids": batch["ann_ids"],
                "native_loss": float(loss), "point_bce": float(losses["point_bce_loss"]),
                "point_dice": float(losses["point_dice_loss"]),
                "new_tensor_gradients": grads, "detail_center_error": conservation,
                "detail_energy": sum(float(d.square().sum()) for _, d, _ in fields),
                "coarse_mask_max_difference": float((masks - original_masks).abs().max()),
                "native_loss_repeat_difference": float(loss) - original_loss,
                "peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
            })
            pred_held.clear()
            fields.clear()
            del loss, losses
        pre.remove()
    originals = [r for r in records if r["arm"] == "original"]
    controls = [r for r in records if r["arm"] == "broadcast"]
    repeats = [r for r in records if r["arm"] == "repeat"]
    backward = all(all(g["finite"] and g["nonzero"] for g in r["new_tensor_gradients"].values())
                   for r in originals)
    control_pass = (all(r["detail_energy"] > 0 for r in originals)
                    and all(r["detail_energy"] == 0 and r["coarse_mask_max_difference"] == 0
                            and all(g["finite"] and not g["nonzero"]
                                    for g in r["new_tensor_gradients"].values())
                            for r in controls))
    repeat_pass = all(r["coarse_mask_max_difference"] <= 1e-6
                      and abs(r["native_loss_repeat_difference"]) <= 1e-6 for r in repeats)
    save(args.output, dict(contract="pdc_native_backward_v1", records=records,
                           native_backward_pass=backward, matched_control_pass=control_pass,
                           strict_repeat_pass=repeat_pass, script_sha256=sha(__file__),
                           config_sha256=sha(config), checkpoint_sha256=sha(checkpoint),
                           population_manifest_sha256=sha(population_path),
                           optimizer_created=False, training_started=False))
    if not (backward and control_pass and repeat_pass):
        raise ValueError("Native backward/control/repeat gate failed; evidence preserved")


if __name__ == "__main__":
    main()
