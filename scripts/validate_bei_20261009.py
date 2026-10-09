"""Native BEI controls/backward and same-protocol resource measurements."""
import argparse
import copy
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys

NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bei"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
    print(json.dumps({"output": str(path), "sha256": sha(path)}), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("native", "resource", "contracts"))
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--target", choices=("baseline", "champion", "candidate"))
    p.add_argument("--group-batch-size", type=int, choices=(1, 2), default=1)
    a = p.parse_args()
    root = a.root.resolve()
    if (os.name != "posix" or os.environ.get("CUDA_VISIBLE_DEVICES") != "7"
            or a.output.exists()
            or not a.output.resolve().is_relative_to(root.parent / "pipeline")):
        raise ValueError("Fresh project output and native GPU7 required")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib"), str(root / "scripts")]
    config = root / "configs/Quard/bei" / (NAME + ".yaml")
    if a.mode == "resource":
        protocol = root.parent / "pipeline/pdc_validation_scripts/pdc_predict_resource_protocol_20261009.py"
        spec = importlib.util.spec_from_file_location("bei_resource_protocol", protocol)
        resource = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(resource)
        resource.TARGETS["candidate"] = dict(name=NAME, config=config.relative_to(root).as_posix(),
                                            config_sha256=sha(config),
                                            model_source_sha256=resource._model_package_sha256(root, NAME))
        resource._measure_target(a.target, root, Path("/data3/songcl/data/data_cluster"), a.output)
        return
    import torch
    import gorilla
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.20)
    mod = importlib.import_module("framework.model.Quard_model." + NAME)
    operator = importlib.import_module("framework.model.Quard_model." + NAME + ".boundary_incidence")
    gorilla.set_random_seed(1999)
    if a.mode == "contracts":
        e = torch.tensor([[0, 1], [1, 2], [2, 3]], device="cuda")
        y = torch.tensor([[0., 0., 1., 1.]], device="cuda", dtype=torch.double)
        z = torch.zeros_like(y, requires_grad=True)
        loss = operator.incidence_loss(z, y, e)
        gradient = torch.autograd.grad(loss, z)[0]
        gradcheck = torch.autograd.gradcheck(lambda x: operator.incidence_loss(x, y, e), (z,))
        complement_error = float((loss.detach() - operator.incidence_loss(z, 1 - y, e).detach()).abs())
        # At equal logits losses coincide but their oriented gradients must differ.
        other_grad = torch.autograd.grad(operator.incidence_loss(z, 1 - y, e), z)[0]
        oriented = bool(torch.equal(gradient, -other_grad) and gradient.abs().sum() > 0)
        empty = operator.incidence_loss(z, torch.zeros_like(y), e)
        empty_grad = torch.autograd.grad(empty, z)[0]
        no_op = bool(empty == 0 and empty_grad.abs().sum() == 0)
        perm = torch.tensor([2, 0, 3, 1], device="cuda")
        inverse = perm.argsort()
        z2 = torch.randn_like(y, requires_grad=True)
        equivariance = float((operator.incidence_loss(z2, y, e) -
                              operator.incidence_loss(z2[:, perm], y[:, perm], inverse[e])).abs().detach())
        passed = bool(gradcheck and oriented and no_op and equivariance < 1e-10)
        save(a.output, dict(contract="bei_operator_v1", passed=passed,
                            gradcheck=bool(gradcheck), uncertain_gradient=gradient.cpu().tolist(),
                            complement_uncertain_loss_error=complement_error,
                            complement_gradient_anchored=oriented, empty_set_no_op=no_op,
                            permutation_error=equivariance, script_sha256=sha(__file__),
                            training_started=False))
        if not passed:
            raise ValueError("Operator contract failed")
        return
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader
    from m95_multiword_native_31_20260928 import selected_loader, CHECKPOINT_SHA
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    source = build_dataset(cfg.data.train, logging.getLogger("bei-native"))
    population_path = root.parent / "pipeline/point_detail_population_20261009/result.manifest.json"
    population = json.loads(population_path.read_text())
    indices = [r["native_group"] for r in population[:2]]
    loader = selected_loader(source, indices, DataLoader)
    if a.group_batch_size == 2:
        loader = DataLoader(loader.dataset, batch_size=2, num_workers=0,
                            shuffle=False, collate_fn=source.collate_fn)
    model = mod.Network(**cfg.model).cuda().train()
    checkpoint = root.parent / "pipeline/scm_admission_20260914/best.pth"
    if sha(checkpoint) != CHECKPOINT_SHA:
        raise ValueError("Frozen checkpoint differs")
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    records = []
    for bi, batch in enumerate(loader):
        fp = batch_fingerprint(torch, batch)
        held = {}
        hook = model.criterion.register_forward_pre_hook(lambda m, values: held.update(pred=values[0]))
        original_masks, original_loss = None, None
        params = list(model.dec.decoder_layers[-1].qqa_ffn.parameters())
        for arm in ("native", "repeat", "placebo", "bypass"):
            model.criterion.boundary_mode = "native" if arm == "repeat" else arm
            held.clear()
            gorilla.set_random_seed(1999)
            model.zero_grad(set_to_none=True)
            torch.cuda.reset_peak_memory_stats()
            loss, outputs = model(copy.deepcopy(batch), mode="loss")
            masks = held["pred"]["masks"].detach().cpu()
            edge = outputs["boundary_incidence_loss"]
            edge_grads = torch.autograd.grad(edge, params, retain_graph=True, allow_unused=True)
            edge_norms = [None if g is None else float(g.norm()) for g in edge_grads]
            edge_finite = all(g is None or bool(torch.isfinite(g).all()) for g in edge_grads)
            loss.backward()
            if arm == "native":
                original_masks, original_loss = masks, float(loss.detach())
            records.append(dict(batch=bi, arm=arm, input_sha256=fp,
                                scenes=batch["scan_ids"], ann_ids=batch["ann_ids"],
                                native_loss=float(loss.detach()), boundary_loss=float(edge.detach()),
                                loss_delta=float(loss.detach()) - original_loss,
                                mask_max_delta=float((masks - original_masks).abs().max()),
                                edge_existing_decoder_gradient_norms=edge_norms,
                                edge_existing_decoder_gradients_finite=edge_finite,
                                full_backward_finite=all(p.grad is None or bool(torch.isfinite(p.grad).all())
                                                         for p in model.parameters()),
                                peak_allocated_mib=torch.cuda.max_memory_allocated() / 2**20))
            print(json.dumps({k: records[-1][k] for k in ("batch", "arm", "boundary_loss",
                                                        "mask_max_delta", "loss_delta")}), flush=True)
            held.clear()
            del loss, outputs, edge, edge_grads
        hook.remove()
    native = [r for r in records if r["arm"] == "native"]
    repeats = [r for r in records if r["arm"] == "repeat"]
    bypass = [r for r in records if r["arm"] == "bypass"]
    placebo = [r for r in records if r["arm"] == "placebo"]
    repeat_pass = all(r["mask_max_delta"] <= 1e-6 and abs(r["loss_delta"]) <= 1e-6 for r in repeats)
    backward = all(r["boundary_loss"] > 0 and r["edge_existing_decoder_gradients_finite"]
                   and any(v is not None and v > 0 for v in r["edge_existing_decoder_gradient_norms"])
                   and r["full_backward_finite"] for r in native)
    control = (all(r["boundary_loss"] == 0 and r["mask_max_delta"] <= 1e-6 and
                   all(v is None or v == 0 for v in r["edge_existing_decoder_gradient_norms"]) for r in bypass)
               and all(r["mask_max_delta"] <= 1e-6 and abs(r["loss_delta"]) > 1e-6 for r in placebo))
    save(a.output, dict(contract="bei_native_backward_v1", records=records,
                        strict_repeat_pass=repeat_pass, native_backward_pass=backward,
                        matched_control_pass=control, new_trainable_tensor_count=0,
                        physical_group_batch_size=a.group_batch_size,
                        script_sha256=sha(__file__), config_sha256=sha(config),
                        checkpoint_sha256=sha(checkpoint), population_sha256=sha(population_path),
                        optimizer_created=False, training_started=False))
    if not (repeat_pass and backward and control):
        raise ValueError("Native gate failed; evidence preserved")


if __name__ == "__main__":
    main()
