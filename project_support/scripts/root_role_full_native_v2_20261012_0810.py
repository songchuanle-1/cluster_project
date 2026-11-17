"""Independent staged TMR full native backward; no optimizer or deployment."""
import gc
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
STAGE = PIPE / "tmr_validation_20261012_0810"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr"


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
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.40)
    static = json.loads((STAGE / "root_role_static_v2_20261012_0810.json").read_text())
    package = STAGE / NAME
    for source in static["files"]:
        assert sha(package / source["filename"]) == source["sha256"]
    config = STAGE / (NAME + ".yaml")
    assert sha(config) == static["config_sha256"]
    spec = importlib.util.spec_from_file_location(
        "tmr_native_validation", package / "__init__.py",
        submodule_search_locations=[str(package)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    source = build_dataset(cfg.data.train, logging.getLogger("tmr-full-native"))
    model = module.Network(**cfg.model)
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    parameters = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    assert not any(n.startswith("target_mention_roles") for n, p in parameters)
    captured = {}
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: captured.update(inputs=inputs))
    manifest = json.loads((PIPE / "point_detail_population_20261009/result.manifest.json").read_text())
    control_group = int(manifest[0]["native_group"])
    rows, old = [], {}
    for batch_size, selected in ((1, [8672]), (2, [8672, control_group])):
        for trial in (0, 1):
            gorilla.set_random_seed(1999)
            loader = DataLoader(torch.utils.data.Subset(source, selected),
                                batch_size=batch_size, num_workers=0, shuffle=False,
                                collate_fn=source.collate_fn, pin_memory=True)
            batch = next(iter(loader))
            original_maps = batch["dense_maps"]
            rebinding, changed = model.target_mention_roles.rebind(
                batch["ann_ids"], batch["scan_ids"], batch["scenes_len"],
                batch["object_idss"], original_maps)
            assert len(changed) == 1
            target_index = changed[0]
            assert int(batch["ann_ids"][target_index]) == 1
            assert torch.equal(original_maps[target_index]["positive_map"][0] > 0,
                               torch.nn.functional.one_hot(
                                   torch.tensor(10), num_classes=256).bool())
            captured.clear()
            model.zero_grad(set_to_none=True)
            gorilla.set_random_seed(1999)
            native_loss, components = model(batch, mode="loss")
            args = list(captured["inputs"])
            assert torch.equal(args[5][target_index]["positive_map"].cpu(),
                               rebinding[target_index]["positive_map"])
            args[5] = original_maps
            original_loss, _ = model.criterion(*args)
            grads = torch.autograd.grad(native_loss.sum(), [p for n, p in parameters],
                                        allow_unused=True, retain_graph=True)
            old_grads = torch.autograd.grad(original_loss.sum(), [p for n, p in parameters],
                                            allow_unused=True)
            gradients = {n: g.detach().cpu() for (n, p), g in zip(parameters, grads)
                         if g is not None}
            finite = all(bool(torch.isfinite(g).all()) for g in gradients.values())
            differences = {n: float((g - h).abs().max())
                           for (n, p), g, h in zip(parameters, grads, old_grads)
                           if g is not None and h is not None}
            nonzero = [n for n, g in gradients.items() if bool((g != 0).any())]
            prediction = captured["inputs"][0]
            logits = prediction["indis"].detach().cpu()
            masks = prediction["masks"].detach().cpu()
            fingerprint = batch_fingerprint(torch, batch)
            prior = old.get(batch_size)
            repeat = None
            if prior:
                repeat = {
                    "input_equal": prior["fingerprint"] == fingerprint,
                    "loss_delta": abs(float(native_loss.detach()) - prior["loss"]),
                    "logit_max_delta": float((logits - prior["logits"]).abs().max()),
                    "mask_max_delta": float((masks - prior["masks"]).abs().max()),
                    "gradient_max_delta": max(
                        float((g - prior["gradients"][n]).abs().max())
                        for n, g in gradients.items()),
                }
            row = {
                "native_batch_size": batch_size, "expressions": len(batch["ann_ids"]),
                "trial": trial, "changed_expression_count": len(changed),
                "loss": float(native_loss.detach()),
                "same_forward_original_loss": float(original_loss.detach()),
                "gradient_tensors": len(gradients), "trainable_tensors": len(parameters),
                "nonzero_gradient_tensors": len(nonzero), "all_gradients_finite": finite,
                "role_changed_gradient_tensors": sum(v > 0 for v in differences.values()),
                "same_forward_gradient_max_delta": max(differences.values()),
                "new_trainable_tensors": 0, "input_sha256": fingerprint, "repeat": repeat,
            }
            assert finite and len(nonzero) > 0 and max(differences.values()) > 0
            rows.append(row)
            print(json.dumps(row), flush=True)
            old[batch_size] = {
                "fingerprint": fingerprint, "loss": float(native_loss.detach()),
                "gradients": gradients, "logits": logits, "masks": masks,
            }
            captured.clear()
            del grads, old_grads, prediction, args, native_loss, original_loss, components
            gc.collect()
            torch.cuda.empty_cache()
    hook.remove()
    result = {
        "contract": "target_mention_full_native_backward_v2",
        "rows": rows, "catalog_entries": len(model.target_mention_roles.catalog),
        "parameters": sum(p.numel() for p in model.parameters()),
        "source_manifest": static, "script_sha256": sha(Path(__file__)),
        "checkpoint_sha256": sha(checkpoint), "seed": 1999,
        "optimizer_steps": 0, "admission": False, "production_deployment": False,
        "scope": "Full native total-loss gradients; strict repeat fields authoritative, no implicit full gate PASS.",
    }
    output = PIPE / "root_role_full_native_v2_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output_sha256": sha(output), "rows": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
