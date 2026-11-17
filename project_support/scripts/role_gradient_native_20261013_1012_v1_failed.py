"""Frozen M95 role diagnostics; original model, no optimizer or new tensor."""
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


def controls(source, criterion, torch):
    function = next(n for n in ast.walk(ast.parse(source.read_text()))
                    if isinstance(n, ast.FunctionDef) and n.name == "loss_sem_align")
    mass = copy.deepcopy(function)
    mass.name = "mass_control"
    replaced = 0
    for index, statement in enumerate(mass.body):
        if (isinstance(statement, ast.Assign)
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == "nb_pos_obj"):
            mass.body[index] = ast.parse(
                "nb_pos_obj = positive_map.sum(1) + (modi_positive_map>0).sum(1)"
                " + (pron_positive_map>0).sum(1) + (rel_positive_map>0).sum(1) + 1e-6"
            ).body[0]
            replaced += 1
    assert replaced == 1
    precedence = copy.deepcopy(function)
    precedence.name = "precedence_control"
    last = max(i for i, s in enumerate(precedence.body)
               if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Subscript)
               and isinstance(s.targets[0].value, ast.Name)
               and s.targets[0].value.id == "tmask")
    precedence.body.insert(last + 1, ast.parse(
        "tmask[positive_map.any(1)] = 1.0").body[0])
    namespace = {"torch": torch}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[mass, precedence], type_ignores=[])), str(source), "exec"), namespace)
    return {k: namespace[k + "_control"].__get__(criterion)
            for k in ("mass", "precedence")}


def smoke(criterion, modified, torch, token):
    rows = []
    for trial in (0, 1):
        for case in ("disjoint", "precedence", "mass"):
            target = {field: torch.zeros(1, 256) for field in FIELDS}
            target["positive_map"][0, 2] = 1
            if case == "precedence":
                target["rel_positive_map"][0, 2] = 1
            elif case == "mass":
                target["modify_positive_map"][0, 3:5] = 0.5
            else:
                target["rel_positive_map"][0, 3] = 1
            gradients, values = {}, {}
            for kind, function in {"original": criterion.loss_sem_align,
                                   "identity": criterion.loss_sem_align, **modified}.items():
                torch.manual_seed(1999)
                queries = torch.nn.functional.normalize(
                    torch.randn(1, 128, 64), dim=-1).detach().requires_grad_()
                tokens = torch.nn.functional.normalize(
                    torch.randn(1, 8, 64), dim=-1).detach().requires_grad_()
                loss = function(tokens, queries, torch.ones(1, 8, dtype=torch.long),
                                [copy.deepcopy(target)],
                                [(torch.tensor([0]), torch.tensor([0]))], 1)
                gradient = torch.autograd.grad(loss, (queries, tokens))
                gradients[kind] = gradient
                values[kind] = {
                    "loss": float(loss.detach()),
                    "finite": bool(torch.isfinite(loss)) and all(
                        bool(torch.isfinite(g).all()) for g in gradient),
                    "gradient_sha256": [
                        hashlib.sha256(g.detach().contiguous().numpy().tobytes()).hexdigest()
                        for g in gradient],
                }
            delta = {kind: max(float((g - h).abs().max()) for g, h in
                               zip(gradient, gradients["original"]))
                     for kind, gradient in gradients.items()}
            assert values["identity"] == values["original"]
            assert all(v["finite"] for v in values.values())
            assert delta["precedence"] == 0 if case != "precedence" else delta["precedence"] > 0
            assert delta["mass"] == 0 if case != "mass" else delta["mass"] > 0
            rows.append({"trial": trial, "case": case, "values": values, "delta": delta})
    assert [{k: v for k, v in r.items() if k != "trial"} for r in rows[:3]] == [
        {k: v for k, v in r.items() if k != "trial"} for r in rows[3:]]
    output = PIPE / "role_gradient_smoke_20261013_1012.json"
    result = {"tick_token": token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "cpu_only": True, "rows": rows,
              "scope": "Adapter unit test on synthetic inputs, not a new scientific/native-model result."}
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "rows": len(rows), "all_checks_pass": True}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--cpu-smoke", action="store_true")
    options = parser.parse_args()
    assert socket.gethostname() == "das"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ("" if options.cpu_smoke else "7")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT), str(ROOT / "framework/lib")]
    import torch
    import gorilla
    from torch.utils.data import DataLoader
    from framework.dataset import build_dataset
    from m95_final_seed_target_probe_20260927 import batch_fingerprint
    torch.set_num_threads(1)
    audit_path = PIPE / "role_loss_mass_20261013_0908.json"
    assert sha(audit_path) == "db2b06c8e7a4b462a295f5898c28d0ef4300e972f84ccf8135dd8deac165f3da"
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
    criterion = importlib.import_module(
        "framework.model.Quard_model." + NAME + ".loss").Criterion(**cfg.model.criterion)
    modified = controls(package / "loss.py", criterion, torch)
    if options.cpu_smoke:
        smoke(criterion, modified, torch, options.token)
        return
    torch.cuda.set_per_process_memory_fraction(0.25)
    cfg.model.data_root = cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("relation-native"))
    lookup = {(a["scene_id"], int(a["ann_id"])): i
              for i, group in enumerate(dataset.scene_inputs) for a in group}
    selected = copy.deepcopy(audit["getter_trials"][0])
    assert len(selected) == 16 and sum(len(s["ann_ids"]) for s in selected) == 64
    assert {s["group"] for s in selected} == {
        lookup[(row["scene"], row["ann_id"])]
        for cases in audit["selection"].values() for row in cases}
    manifest_path = PIPE / "point_detail_population_20261009/result.manifest.json"
    assert sha(manifest_path) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    manifest = json.loads(manifest_path.read_text())
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
    modified = controls(package / "loss.py", model.criterion, torch)
    held = {}
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs: held.update(args=inputs))
    semantic = model.criterion.loss_sem_align
    semantic_calls = []
    active = [semantic]

    def capture_semantic(*args):
        value = active[0](*args)
        semantic_calls.append((args, value))
        return value

    model.criterion.loss_sem_align = capture_semantic
    rows, previous = [], {}
    output = PIPE / "role_gradient_native_20261013_1012.json"
    progress = PIPE / "role_gradient_native_20261013_1012.progress.jsonl"
    progress_stream = progress.open("x")
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
                active[0] = semantic
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
                assert all(g is not None for g in original_grads), "Missing original embedding gradient"
                assert all(bool(torch.isfinite(g).all()) for g in original_grads)
                assert selection.get("control") or list(map(int, batch["ann_ids"])) == selection["ann_ids"]
                maps_digest = hashlib.sha256()
                for item in args[5]:
                    for field in FIELDS:
                        maps_digest.update(item[field].detach().cpu().contiguous().numpy().tobytes())
                map_equal = selection.get("control") or maps_digest.hexdigest() == selection["map_sha256"]
                conditions = {}
                condition_gradients = {}
                for condition in ("identity", "precedence", "mass"):
                    active[0] = semantic if condition == "identity" else modified[condition]
                    semantic_calls.clear()
                    loss, _ = model.criterion(*args)
                    grads = torch.autograd.grad(loss.sum(), variables,
                                                retain_graph=True, allow_unused=True)
                    delta = [None if g is None or h is None else float((g - h).abs().max())
                             for g, h in zip(grads, original_grads)]
                    conditions[condition] = {
                        "total_loss": float(loss.detach()),
                        "loss_delta": float((loss - original_loss).detach()),
                        "semantic_calls": len(semantic_calls),
                        "semantic_loss": [float(call[1].detach()) for call in semantic_calls],
                        "final_query_token_gradient_max_delta": delta,
                        "all_present_gradients_finite": all(
                            bool(torch.isfinite(g).all()) for g in grads if g is not None),
                        "missing_gradient_variables": [i for i, g in enumerate(grads) if g is None],
                    }
                    condition_gradients[condition] = [None if g is None else g.detach().cpu()
                                                      for g in grads]
                active[0] = semantic
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
                        "conditions": {
                            kind: {
                                "loss_delta": abs(value["total_loss"] - old["conditions"][kind]["total_loss"]),
                                "gradient_max_delta": max(
                                    float((g - h).abs().max()) for g, h in
                                    zip(condition_gradients[kind], old["condition_gradients"][kind])
                                    if g is not None and h is not None),
                            } for kind, value in conditions.items()},
                    }
                    repeat["strict_1e6_pass"] = repeat["input_equal"] and map_equal and all(
                        repeat[k] <= 1e-6 for k in
                        ("loss_delta", "logit_max_delta", "mask_max_delta", "gradient_max_delta")) and all(
                            all(v <= 1e-6 for v in check.values())
                            for check in repeat["conditions"].values())
                row = {
                    "trial": trial, "selection": selection,
                    "ann_ids": list(map(int, batch["ann_ids"])), "input_sha256": fingerprint,
                    "maps_equal_frozen_getter": bool(map_equal),
                    "original_total_loss": float(original_loss.detach()),
                    "conditions": conditions, "repeat": repeat,
                }
                rows.append(row)
                progress_stream.write(json.dumps(row, allow_nan=False) + "\n")
                progress_stream.flush()
                previous[selection["group"]] = {
                    "fingerprint": fingerprint, "loss": float(original_loss.detach()),
                    "logits": logits, "masks": masks,
                    "gradients": [None if g is None else g.detach().cpu() for g in original_grads],
                    "conditions": conditions, "condition_gradients": condition_gradients,
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
        progress_stream.close()
    result = {
        "tick_token": options.token, "observed_at": datetime.now(timezone.utc).isoformat(),
        "script_sha256": sha(Path(__file__)), "checkpoint_sha256": sha(checkpoint),
        "source_shas": expected, "config_sha256": sha(config),
        "audit_sha256": sha(audit_path), "seed": 1999,
        "selection_rule": "Frozen16groups64expressions from prior mass/precedence selections, plus first original population group; no prediction selection.",
        "rows": rows, "optimizer_steps": 0, "new_trainable_tensors": 0,
        "scope": "Same-forward single semantic AST edits and actual projected embedding gradients; not new-core backward/resource/novelty/efficacy PASS.",
    }
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "rows": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
