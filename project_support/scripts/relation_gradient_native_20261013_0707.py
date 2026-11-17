"""Native M95 same-forward role intersections; no optimizer or new model."""
import copy
from datetime import datetime, timezone
import gc
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
TOKEN = "607238b6eece484ca713e5f5c6b04356"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == "7"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT), str(ROOT / "framework/lib")]
    import torch
    import gorilla
    from torch.utils.data import DataLoader
    from framework.dataset import build_dataset
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.25)
    audit_path = PIPE / "relation_multispan_audit_20261013_0707.json"
    assert sha(audit_path) == "ac0ac8e5702eca0ba03246ac28bae4f9d6e9f675fa0198b06f8e05b1c07aed7e"
    audit = json.loads(audit_path.read_text())
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    assert sha(config) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    package = ROOT / "framework/model/Quard_model" / NAME
    expected = {
        "network.py": "5a77eb852b3c6e5de2804d80a2c7a16504f1fd8a57aa94dc6045d9f35587625d",
        "dec.py": "6f7566bd02121fd218fd1360be7c7b1905c267de8a03f36473779ab4d66b9d3a",
        "loss.py": "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5",
    }
    for name, expected_sha in expected.items():
        assert sha(package / name) == expected_sha, name
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("relation-native"))
    lookup = {(a["scene_id"], int(a["ann_id"])): i
              for i, group in enumerate(dataset.scene_inputs) for a in group}
    selected, seen = [], set()
    for row in sorted(audit["relation_overlap_cases"], key=lambda r: (r["scene"], r["ann_id"])):
        if row["scene"] in seen:
            continue
        selected.append({"scene": row["scene"], "trigger_ann_id": row["ann_id"],
                         "group": lookup[(row["scene"], row["ann_id"])]})
        seen.add(row["scene"])
        if len(selected) == 8:
            break
    manifest = json.loads((PIPE / "point_detail_population_20261009/result.manifest.json").read_text())
    selected.append({"scene": manifest[0]["scene"], "trigger_ann_id": None,
                     "group": int(manifest[0]["native_group"]), "control": True})
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    held = {}
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(args=inputs))
    semantic = model.criterion.loss_sem_align
    semantic_calls = []

    def capture_semantic(*args):
        value = semantic(*args)
        semantic_calls.append((args, value))
        return value

    model.criterion.loss_sem_align = capture_semantic
    rows, previous = [], {}
    try:
        for trial in (0, 1):
            for selection in selected:
                gorilla.set_random_seed(1999)
                loader = DataLoader(torch.utils.data.Subset(dataset, [selection["group"]]),
                                    batch_size=1, num_workers=0, shuffle=False,
                                    collate_fn=dataset.collate_fn)
                batch = next(iter(loader))
                held.clear()
                semantic_calls.clear()
                model.zero_grad(set_to_none=True)
                fingerprint = batch_fingerprint(torch, batch)
                gorilla.set_random_seed(1999)
                original_loss, _ = model(batch, mode="loss")
                assert semantic_calls, "Native semantic path must be reached"
                args = list(held["args"])
                native_sem_args = list(semantic_calls[0][0])
                pred = args[0]
                variables = [pred["proj_queries"], pred["proj_tokens"]]
                original_grads = torch.autograd.grad(original_loss.sum(), variables,
                                                     retain_graph=True, allow_unused=True)
                orig_maps = args[5]
                overlaps = []
                edit_counts = {}
                conditions = {}
                for condition in ("identity", "remove_other_overlap", "remove_relation_overlap",
                                  "remove_other_disjoint"):
                    edited = copy.deepcopy(orig_maps)
                    changed = 0
                    for expression, item in enumerate(edited):
                        overlap = (item["rel_positive_map"] > 0) & (item["other_entity_map"] > 0)
                        if condition == "identity":
                            if bool(overlap.any()):
                                overlaps.append({"ann_id": int(batch["ann_ids"][expression]),
                                                 "tokens": overlap[0].nonzero().flatten().tolist()})
                        elif condition == "remove_other_overlap":
                            changed += int(overlap.sum())
                            item["other_entity_map"][overlap] = 0
                        elif condition == "remove_relation_overlap":
                            changed += int(overlap.sum())
                            item["rel_positive_map"][overlap] = 0
                        else:
                            requested = int(overlap[0].sum())
                            available = ((item["other_entity_map"][0] > 0) &
                                         ~overlap[0]).nonzero().flatten()[:requested]
                            item["other_entity_map"][0, available] = 0
                            changed += len(available)
                    args[5] = edited
                    semantic_calls.clear()
                    loss, _ = model.criterion(*args)
                    grads = torch.autograd.grad(loss.sum(), variables,
                                                retain_graph=True, allow_unused=True)
                    delta = [None if g is None or h is None else float((g - h).abs().max())
                             for g, h in zip(grads, original_grads)]
                    conditions[condition] = {
                        "total_loss": float(loss.detach()),
                        "loss_delta": float((loss - original_loss).detach()),
                        "semantic_loss": float(semantic_calls[0][1].detach()),
                        "final_query_token_gradient_max_delta": delta,
                        "all_present_gradients_finite": all(
                            bool(torch.isfinite(g).all()) for g in grads if g is not None),
                        "missing_gradient_variables": [i for i, g in enumerate(grads) if g is None],
                    }
                    edit_counts[condition] = changed
                logits = pred["indis"].detach().cpu()
                masks = pred["masks"].detach().cpu()
                old = previous.get(selection["group"])
                repeat = None
                if old:
                    repeat = {
                        "input_equal": fingerprint == old["fingerprint"],
                        "loss_delta": abs(float(original_loss.detach()) - old["loss"]),
                        "logit_max_delta": float((logits - old["logits"]).abs().max()),
                        "mask_max_delta": float((masks - old["masks"]).abs().max()),
                        "gradient_max_delta": max(
                            float((g.detach().cpu() - h).abs().max())
                            for g, h in zip(original_grads, old["gradients"])
                            if g is not None and h is not None),
                    }
                    repeat["strict_1e6_pass"] = repeat["input_equal"] and all(
                        repeat[k] <= 1e-6 for k in
                        ("loss_delta", "logit_max_delta", "mask_max_delta", "gradient_max_delta"))
                row = {
                    "trial": trial, "selection": selection,
                    "ann_ids": list(map(int, batch["ann_ids"])), "input_sha256": fingerprint,
                    "overlaps": overlaps, "edited_position_counts": edit_counts,
                    "original_total_loss": float(original_loss.detach()),
                    "conditions": conditions, "repeat": repeat,
                }
                rows.append(row)
                previous[selection["group"]] = {
                    "fingerprint": fingerprint, "loss": float(original_loss.detach()),
                    "logits": logits, "masks": masks,
                    "gradients": [None if g is None else g.detach().cpu() for g in original_grads],
                }
                print(json.dumps(row), flush=True)
                held.clear()
                semantic_calls.clear()
                del pred, args, variables, original_loss, original_grads, loss, grads, native_sem_args
                gc.collect()
                torch.cuda.empty_cache()
    finally:
        hook.remove()
        model.criterion.loss_sem_align = semantic
    output = PIPE / "relation_gradient_native_20261013_0707.json"
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "script_sha256": sha(Path(__file__)), "checkpoint_sha256": sha(checkpoint),
        "source_shas": expected, "config_sha256": sha(config),
        "audit_sha256": sha(audit_path), "seed": 1999,
        "selection_rule": "First8distinct TRAIN scenes sorted by scene and annotation among map-positive cases, plus first frozen population group; no prediction selection.",
        "rows": rows, "optimizer_steps": 0, "new_trainable_tensors": 0,
        "scope": "Same-forward diagnostic map ablations and final query/token gradients; not new-core backward/resource/novelty/efficacy PASS.",
    }
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "rows": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
