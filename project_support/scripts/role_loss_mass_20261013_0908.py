"""Actual normalized role maps; original Criterion on controlled CPU inputs."""
import ast
from collections import Counter
import copy
from datetime import datetime, timezone
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
TOKEN = "3076255a5f0543e9a6de659374e194cc"
FIELDS = ("positive_map", "modify_positive_map", "pron_positive_map",
          "other_entity_map", "auxi_entity_positive_map", "rel_positive_map")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    source = ROOT / "framework/model/Quard_model" / NAME / "loss.py"
    audit = PIPE / "role_weight_audit_20261013_0908.json"
    paths = {
        "config": config, "loss": source,
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "precedence_audit": audit,
    }
    expected = {
        "config": "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a",
        "loss": "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5",
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "precedence_audit": "48d7a2243257a0287f4669a98dbd80ca4fbb982faa1da79143d6e143d796b5df",
    }
    for key, path in paths.items():
        assert sha(path) == expected[key], key
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("role-loss-mass"))
    mapper = dataset._get_token_positive_map_by_parse
    criterion = importlib.import_module(
        "framework.model.Quard_model." + NAME + ".loss").Criterion(**cfg.model.criterion)
    function = next(n for n in ast.walk(ast.parse(source.read_text()))
                    if isinstance(n, ast.FunctionDef) and n.name == "loss_sem_align")
    original = criterion.loss_sem_align
    mass_function = copy.deepcopy(function)
    mass_function.name = "mass_control"
    denominator_replaced = 0
    for index, statement in enumerate(mass_function.body):
        if (isinstance(statement, ast.Assign)
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == "nb_pos_obj"):
            mass_function.body[index] = ast.parse(
                "nb_pos_obj = positive_map.sum(1) + (modi_positive_map>0).sum(1)"
                " + (pron_positive_map>0).sum(1) + (rel_positive_map>0).sum(1) + 1e-6"
            ).body[0]
            denominator_replaced += 1
    assert denominator_replaced == 1
    precedence_function = copy.deepcopy(function)
    precedence_function.name = "precedence_control"
    last_tmask = max(
        index for index, statement in enumerate(precedence_function.body)
        if isinstance(statement, ast.Assign)
        and isinstance(statement.targets[0], ast.Subscript)
        and isinstance(statement.targets[0].value, ast.Name)
        and statement.targets[0].value.id == "tmask")
    precedence_function.body.insert(
        last_tmask + 1, ast.parse("tmask[positive_map.any(1)] = 1.0").body[0])
    namespace = {"torch": torch}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[mass_function, precedence_function], type_ignores=[])),
        str(source), "exec"), namespace)
    modified = {
        "precedence": namespace["precedence_control"].__get__(criterion),
        "mass": namespace["mass_control"].__get__(criterion),
    }
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    assert len(annotations) == 36665
    counts = Counter()
    affected_scenes = set()
    large_scenes = set()
    selected = {}
    digest = hashlib.sha256()
    maximum_ratio = 1.0
    for number, ann in enumerate(annotations, 1):
        scene, aid = ann["scene_id"], str(ann["ann_id"])
        values = mapper(graphs[scene][aid], None)
        boolean_main = (values[1][0] > 0).astype(np.float32)
        raw = boolean_main + values[2][0] + values[3][0] + values[6][0]
        boolean = boolean_main.copy()
        for index in (2, 3, 6):
            boolean += values[index][0] > 0
        difference = raw != boolean
        counts["expressions"] += 1
        counts["exact_mass_discrepancy_expressions"] += bool(difference.any())
        counts["exact_mass_discrepancy_tokens"] += int(difference.sum())
        if difference.any():
            affected_scenes.add(scene)
        half_mass = np.zeros(256, dtype=bool)
        for role, index in (("modifier", 2), ("pronoun", 3), ("relation", 6)):
            active = values[index][0] > 0
            small = active & (values[index][0] <= 0.5)
            half_mass |= small
            counts[role + "_active_tokens"] += int(active.sum())
            counts[role + "_half_mass_tokens"] += int(small.sum())
            counts[role + "_half_mass_expressions"] += bool(small.any())
        counts["half_mass_expressions"] += bool(half_mass.any())
        counts["half_mass_tokens"] += int(half_mass.sum())
        if half_mass.any():
            large_scenes.add(scene)
            coords = np.flatnonzero(half_mass).tolist()
            ratio = boolean[half_mass] / (raw[half_mass] + 1e-6)
            maximum_ratio = max(maximum_ratio, float(ratio.max()))
            row = {"scene": scene, "ann_id": int(aid),
                   "tokens": coords, "raw_mass": raw[coords].tolist(),
                   "boolean_mass": boolean[coords].tolist()}
            if scene not in selected or int(aid) < selected[scene]["ann_id"]:
                selected[scene] = row
        digest.update(f"{scene}:{aid};".encode())
        for index in (1, 2, 3, 6):
            digest.update(np.ascontiguousarray(values[index][0]).tobytes())
        if number % 5000 == 0 or number == len(annotations):
            print(json.dumps({"done": number, "counts": dict(counts)}), flush=True)
    mass_selection = [selected[scene] for scene in sorted(selected)[:8]]
    precedence_selection = json.loads(audit.read_text())["frozen_first8positive_scenes"]
    selection = {"mass": mass_selection, "precedence": precedence_selection}
    lookup = {(a["scene_id"], int(a["ann_id"])): i
              for i, group in enumerate(dataset.scene_inputs) for a in group}
    groups = sorted({lookup[(row["scene"], row["ann_id"])]
                     for rows in selection.values() for row in rows})
    getter_trials = []
    for trial in (0, 1):
        gorilla.set_random_seed(1999)
        records = []
        for index in groups:
            item = dataset[index]
            dig, failures = hashlib.sha256(), []
            for expression, aid in enumerate(item[0]):
                values = mapper(graphs[item[1]][str(aid)], None)
                for field, value in zip(FIELDS, values[1:]):
                    actual = item[13][expression][field]
                    if not torch.equal(actual, torch.from_numpy(value).float()):
                        failures.append({"ann_id": int(aid), "field": field})
                    dig.update(actual.contiguous().numpy().tobytes())
            records.append({"group": index, "scene": item[1],
                            "ann_ids": list(map(int, item[0])),
                            "map_sha256": dig.hexdigest(), "failures": failures})
        getter_trials.append(records)
    loss_trials = []
    for trial in (0, 1):
        gorilla.set_random_seed(1999)
        records = []
        for kind, cases in selection.items():
            for case in cases:
                graph = graphs[case["scene"]][str(case["ann_id"])]
                values = mapper(graph, None)
                target = {field: torch.from_numpy(value[:1]).float()
                          for field, value in zip(FIELDS, values[1:])}
                coords = (case["tokens"] if kind == "mass" else case["changed_tokens"])
                text = " ".join(graph["utterance"].replace(",", " ,").split())
                length = len(dataset.tokenizer(text)["input_ids"]) + 2
                assert 0 <= coords[0] < length - 2
                tokens = torch.eye(length).unsqueeze(0)
                masks = torch.ones(1, length, dtype=torch.long)
                indices = [(torch.tensor([0]), torch.tensor([0]))]
                for logit in (0.0, 4.0, 8.0):
                    conditions, gradients = {}, {}
                    for condition in ("original", "identity", "diagnostic"):
                        queries = torch.zeros(1, 128, length, requires_grad=True)
                        with torch.no_grad():
                            queries[0, 0, coords[0]] = logit * criterion.temperature
                        function_to_use = modified[kind] if condition == "diagnostic" else original
                        loss = function_to_use(tokens, queries, masks,
                                               [copy.deepcopy(target)], indices, 1)
                        gradient = torch.autograd.grad(loss, queries)[0]
                        gradients[condition] = gradient
                        conditions[condition] = {
                            "loss": float(loss.detach()),
                            "coordinate_gradient": float(gradient[0, 0, coords[0]]),
                            "gradient_sha256": hashlib.sha256(
                                gradient.contiguous().numpy().tobytes()).hexdigest(),
                            "finite": bool(torch.isfinite(gradient).all()
                                           and torch.isfinite(loss)),
                        }
                    records.append({
                        "kind": kind, "scene": case["scene"], "ann_id": case["ann_id"],
                        "controlled_logit": logit, "token_columns": length,
                        "probe_token": coords[0], "conditions": conditions,
                        "identity_gradient_max_delta": float(
                            (gradients["identity"] - gradients["original"]).abs().max()),
                        "diagnostic_gradient_max_delta": float(
                            (gradients["diagnostic"] - gradients["original"]).abs().max()),
                    })
        loss_trials.append(records)
        print(json.dumps({"loss_trial": trial, "records": len(records)}), flush=True)
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
        "script_sha256": sha(Path(__file__)), "inputs_sha256": expected,
        "counts": dict(counts), "scene_count": len({a["scene_id"] for a in annotations}),
        "exact_discrepancy_scenes": len(affected_scenes), "half_mass_scenes": len(large_scenes),
        "maximum_boolean_over_raw_denominator_ratio": maximum_ratio,
        "map_sha256": digest.hexdigest(), "selection": selection,
        "getter_trials": getter_trials, "getter_exact_repeat": getter_trials[0] == getter_trials[1],
        "getter_failures": sum(len(r["failures"]) for t in getter_trials for r in t),
        "getter_expressions": sum(len(r["ann_ids"]) for r in getter_trials[0]),
        "loss_trials": loss_trials, "loss_exact_repeat": loss_trials[0] == loss_trials[1],
        "identity_all_exact": all(r["identity_gradient_max_delta"] == 0
                                  and r["conditions"]["original"] == r["conditions"]["identity"]
                                  for r in loss_trials[0]),
        "all_finite": all(c["finite"] for r in loss_trials[0]
                          for c in r["conditions"].values()),
        "scope": "Actual native TRAIN maps/getter maps; original Criterion and isolated AST controls on explicit SYNTHETIC identity-token/zero-query inputs with one controlled logit, not64D decoder outputs. No whole-native model, harm, efficacy, new-core, backward admission or resource certificate.",
    }
    output = PIPE / "role_loss_mass_20261013_0908.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "counts": result["counts"], "half_mass_scenes": result["half_mass_scenes"],
                      "getter_expressions": result["getter_expressions"],
                      "getter_repeat": result["getter_exact_repeat"],
                      "getter_failures": result["getter_failures"],
                      "loss_repeat": result["loss_exact_repeat"],
                      "identity_exact": result["identity_all_exact"],
                      "all_finite": result["all_finite"]}), flush=True)


if __name__ == "__main__":
    main()
