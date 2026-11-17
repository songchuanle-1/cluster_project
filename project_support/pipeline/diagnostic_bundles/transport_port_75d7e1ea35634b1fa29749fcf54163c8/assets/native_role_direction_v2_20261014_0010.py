"""Direct semantic-logit directions on the frozen original native cohort."""
import argparse
import ast
import copy
from datetime import datetime, timezone
import gc
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import runpy
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
FIELDS = ("positive_map", "modify_positive_map", "pron_positive_map",
          "other_entity_map", "auxi_entity_positive_map", "rel_positive_map")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def logit_functions(source, criterion, torch):
    original = next(n for n in ast.walk(ast.parse(source.read_text()))
                    if isinstance(n, ast.FunctionDef) and n.name == "loss_sem_align")
    functions = {name: copy.deepcopy(original)
                 for name in ("original", "identity", "precedence", "mass")}
    mass = functions["mass"]
    count = 0
    for i, node in enumerate(mass.body):
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "nb_pos_obj"):
            mass.body[i] = ast.parse(
                "nb_pos_obj = positive_map.sum(1) + (modi_positive_map>0).sum(1)"
                " + (pron_positive_map>0).sum(1) + (rel_positive_map>0).sum(1) + 1e-6"
            ).body[0]
            count += 1
    assert count == 1
    precedence = functions["precedence"]
    last = max(i for i, node in enumerate(precedence.body)
               if isinstance(node, ast.Assign)
               and isinstance(node.targets[0], ast.Subscript)
               and isinstance(node.targets[0].value, ast.Name)
               and node.targets[0].value.id == "tmask")
    precedence.body.insert(last + 1, ast.parse(
        "tmask[(positive_map & ((modi_positive_map>0) |"
        " (pron_positive_map>0) | (rel_positive_map>0))).any(1)] = 1.0"
    ).body[0])
    for name, function in functions.items():
        function.name = "diagnostic_" + name
        function.args.args.append(ast.arg(arg="logits_override"))
        assignments = [node for node in function.body
                       if isinstance(node, ast.Assign)
                       and isinstance(node.targets[0], ast.Name)
                       and node.targets[0].id == "logits"]
        assert len(assignments) == 1
        assignments[0].value = ast.Name(id="logits_override", ctx=ast.Load())
    namespace = {"torch": torch}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=list(functions.values()), type_ignores=[])), str(source), "exec"), namespace)
    return {name: namespace["diagnostic_" + name].__get__(criterion)
            for name in functions}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    assert socket.gethostname() == "das" and os.environ["CUDA_VISIBLE_DEVICES"] == "7"
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
    cohort = {}
    input_hashes = {}
    for family, filename, expected in (
        ("role", "role_gradient_native_20261013_1012.json",
         "ca0697d740a4d239dfe4465542ac75beed09a0d95b963022fc7b796ec6368187"),
        ("relation", "relation_gradient_native_20261013_0707.json",
         "f98351adaf132046fca6ca11158a89a21ca8e0fc5a223d635cf3207b214eb7d4"),
    ):
        path = PIPE / filename
        assert sha(path) == expected
        capture = json.loads(path.read_text())
        input_hashes[filename] = expected
        for row in capture["rows"]:
            if row["trial"] != 0:
                continue
            selection = row["selection"]
            key = selection["group"]
            if key not in cohort:
                cohort[key] = {"group": key, "scene": selection["scene"],
                               "ann_ids": row["ann_ids"], "families": []}
            assert cohort[key]["ann_ids"] == row["ann_ids"]
            cohort[key]["families"].append(family)
    role = json.loads((PIPE / "role_gradient_native_20261013_1012.json").read_text())
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    assert sha(config) == role["config_sha256"]
    package = ROOT / "framework/model/Quard_model" / NAME
    for filename, expected in role["source_shas"].items():
        assert sha(package / filename) == expected
    helper = PIPE / "role_gradient_native_20261013_1012.py"
    assert sha(helper) == "d01eab84334844e45c83b9aa0af437848a255203e4aeaf32e72c146ce220c7a0"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("native-role-direction"))
    model = importlib.import_module("framework.model.Quard_model." + NAME).Network(**cfg.model)
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    assert sha(checkpoint) == role["checkpoint_sha256"]
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()
    functions = logit_functions(package / "loss.py", model.criterion, torch)
    semantic = model.criterion.loss_sem_align
    calls = []

    def capture(*values):
        loss = semantic(*values)
        calls.append((values, loss))
        return loss

    model.criterion.loss_sem_align = capture
    held = {}
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(pred=inputs[0]))
    output = PIPE / ("native_role_direction_v2_" + args.token + ".json")
    progress = PIPE / ("native_role_direction_v2_" + args.token + ".progress.jsonl")
    rows = []
    torch.cuda.reset_peak_memory_stats()
    try:
        with progress.open("x") as stream:
            for selection in cohort.values():
                gorilla.set_random_seed(1999)
                loader = DataLoader(torch.utils.data.Subset(dataset, [selection["group"]]),
                                    batch_size=1, num_workers=0, shuffle=False,
                                    collate_fn=dataset.collate_fn)
                batch = next(iter(loader))
                assert list(map(int, batch["ann_ids"])) == selection["ann_ids"]
                calls.clear()
                held.clear()
                model.zero_grad(set_to_none=True)
                gorilla.set_random_seed(1999)
                total_loss, _ = model(batch, mode="loss")
                final_calls = [(i, values, loss) for i, (values, loss) in enumerate(calls)
                               if values[0] is held["pred"]["proj_tokens"]
                               and values[1] is held["pred"]["proj_queries"]]
                assert len(final_calls) == 1, "Require exact final projected tensor identity"
                call_index, native, native_loss = final_calls[0]
                tokens, queries, lang_masks, targets, indices, num_boxes = native
                raw_logits = (queries.detach() @ tokens.detach().transpose(-1, -2)) / model.criterion.temperature
                conditions = {}
                gradients = {}
                edited_counts = {}
                missing_controls = []
                for name in ("original", "identity", "precedence", "mass",
                             "remove_other_overlap", "remove_relation_overlap",
                             "remove_other_disjoint"):
                    edited = copy.deepcopy(targets)
                    counts = []
                    for bi, target in enumerate(edited):
                        src, tgt = indices[bi]
                        for ti in tgt.tolist():
                            overlap = (target["rel_positive_map"][ti] > 0) & (target["other_entity_map"][ti] > 0)
                            requested = int(overlap.sum())
                            changed = 0
                            if name == "remove_other_overlap":
                                target["other_entity_map"][ti, overlap] = 0
                                changed = requested
                            elif name == "remove_relation_overlap":
                                target["rel_positive_map"][ti, overlap] = 0
                                changed = requested
                            elif name == "remove_other_disjoint":
                                available = ((target["other_entity_map"][ti] > 0) & ~overlap).nonzero().flatten()[:requested]
                                target["other_entity_map"][ti, available] = 0
                                changed = len(available)
                                if changed < requested:
                                    missing_controls.append({"batch": bi, "target": ti,
                                                             "requested": requested, "available": changed})
                            counts.append(changed)
                    values = []
                    derivatives = []
                    for repeat in (0, 1):
                        leaf = raw_logits.detach().clone().requires_grad_()
                        function = functions.get(name, functions["original"])
                        value = function(tokens, queries, lang_masks, edited, indices, num_boxes, leaf)
                        gradient, = torch.autograd.grad(value, leaf)
                        assert bool(torch.isfinite(value)) and bool(torch.isfinite(gradient).all())
                        values.append(float(value.detach()))
                        derivatives.append(gradient.detach())
                    assert values[0] == values[1] and torch.equal(derivatives[0], derivatives[1])
                    gradients[name] = derivatives[0]
                    conditions[name] = {"loss": values[0], "same_capture_repeat_exact": True}
                    edited_counts[name] = counts
                original_delta = abs(conditions["original"]["loss"] - float(native_loss.detach()))
                assert original_delta <= 1e-6
                assert conditions["original"] == conditions["identity"]
                assert torch.equal(gradients["original"], gradients["identity"])
                sites = []
                for bi, (src, tgt) in enumerate(indices):
                    for qi, ti in zip(src.tolist(), tgt.tolist()):
                        target = targets[bi]
                        length = raw_logits.shape[-1]
                        main = target["positive_map"][ti, :length] > 0
                        modifier = target["modify_positive_map"][ti, :length]
                        pronoun = target["pron_positive_map"][ti, :length]
                        relation = target["rel_positive_map"][ti, :length]
                        other = target["other_entity_map"][ti, :length]
                        masks = {
                            "main_secondary": main & ((modifier > 0) | (pronoun > 0) | (relation > 0)),
                            "fractional_secondary": ((modifier > 0) & (modifier < 1)) | ((pronoun > 0) & (pronoun < 1)) | ((relation > 0) & (relation < 1)),
                            "relation_other": (relation > 0) & (other > 0),
                        }
                        for kind, mask in masks.items():
                            for token in mask.nonzero().flatten().tolist():
                                sites.append({
                                    "kind": kind, "batch": bi, "ann_id": int(batch["ann_ids"][bi]),
                                    "query": qi, "target": ti, "token": token,
                                    "logit": float(raw_logits[bi, qi, token]),
                                    "d_loss_d_logit": {name: float(gradient[bi, qi, token])
                                                       for name, gradient in gradients.items()},
                                })
                row = {"selection": selection, "input_sha256": batch_fingerprint(torch, batch),
                       "original_total_loss": float(total_loss.detach()),
                       "native_semantic_call_index": call_index,
                       "native_semantic_call_count": len(calls),
                       "final_tensor_identity_verified": True,
                       "native_final_semantic_loss": float(native_loss.detach()),
                       "injected_original_loss_delta": original_delta,
                       "conditions": conditions, "edited_counts": edited_counts,
                       "missing_disjoint_controls": missing_controls, "sites": sites}
                rows.append(row)
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(json.dumps({"group": selection["group"], "sites": len(sites),
                                  "missing_controls": len(missing_controls), "original_delta": original_delta}), flush=True)
                calls.clear()
                held.clear()
                final_calls.clear()
                del total_loss, native, native_loss, tokens, queries, lang_masks, targets, indices
                del raw_logits, gradients, derivatives, gradient, leaf, value, edited
                gc.collect()
                torch.cuda.empty_cache()
    finally:
        hook.remove()
        model.criterion.loss_sem_align = semantic
    result = {"tick_token": args.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "prior_capture_shas": input_hashes,
              "seed": 1999, "rows": rows, "optimizer_steps": 0, "new_trainable_tensors": 0,
              "allocator_peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
              "allocator_peak_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
              "scope": "Direct native semantic-logit directions; not localization harm, efficacy, exclusive efficiency or new-core admission. Historical full-forward strict repeat FAIL retained."}
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "groups": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
