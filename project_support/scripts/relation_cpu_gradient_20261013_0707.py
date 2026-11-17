"""Actual native maps/getters and original loss on explicit synthetic inputs."""
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
TOKEN = "607238b6eece484ca713e5f5c6b04356"


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
    audit_path = PIPE / "relation_multispan_audit_20261013_0707.json"
    assert sha(audit_path) == "ac0ac8e5702eca0ba03246ac28bae4f9d6e9f675fa0198b06f8e05b1c07aed7e"
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    assert sha(config) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    loss_source = ROOT / "framework/model/Quard_model" / NAME / "loss.py"
    assert sha(loss_source) == "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"
    source = ROOT / "framework/dataset/scannetv2.py"
    assert sha(source) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    graph_path = DATA / "scanrefer/scene_graphs_new_train.json"
    assert sha(graph_path) == "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
    audit = json.loads(audit_path.read_text())
    graphs = json.loads(graph_path.read_text())
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("relation-cpu"))
    criterion = importlib.import_module(
        "framework.model.Quard_model." + NAME + ".loss").Criterion(**cfg.model.criterion)
    mapper = dataset._get_token_positive_map_by_parse
    lookup = {(a["scene_id"], int(a["ann_id"])): i
              for i, group in enumerate(dataset.scene_inputs) for a in group}
    selected, seen = [], set()
    cases = sorted(audit["relation_overlap_cases"], key=lambda r: (r["scene"], r["ann_id"]))
    for case in cases:
        if case["scene"] in seen:
            continue
        selected.append({"scene": case["scene"], "trigger_ann_id": case["ann_id"],
                         "group": lookup[(case["scene"], case["ann_id"])]})
        seen.add(case["scene"])
        if len(selected) == 8:
            break
    fields = ("tokens_positive", "positive_map", "modify_positive_map", "pron_positive_map",
              "other_entity_map", "auxi_entity_positive_map", "rel_positive_map")
    getter_trials = []
    for trial in (0, 1):
        gorilla.set_random_seed(1999)
        records = []
        for selection in selected:
            item = dataset[selection["group"]]
            dig, failures = hashlib.sha256(), []
            for expression, aid in enumerate(item[0]):
                reference = mapper(graphs[item[1]][str(aid)], None)
                for field, value in zip(fields, reference):
                    actual = item[13][expression][field]
                    if not torch.equal(actual, torch.from_numpy(value).float()):
                        failures.append({"ann_id": int(aid), "field": field})
                    dig.update(actual.contiguous().numpy().tobytes())
            records.append({"selection": selection, "ann_ids": list(map(int, item[0])),
                            "map_sha256": dig.hexdigest(), "map_failures": failures})
        getter_trials.append(records)
    loss_trials = []
    for trial in (0, 1):
        gorilla.set_random_seed(1999)
        records = []
        for case in cases:
            graph = graphs[case["scene"]][str(case["ann_id"])]
            values = mapper(graph, None)
            target = {field: torch.from_numpy(value[:1]).float()
                      for field, value in zip(fields[1:], values[1:])}
            text = " ".join(graph["utterance"].replace(",", " ,").split())
            length = len(dataset.tokenizer(text)["input_ids"]) + 2
            tokens = torch.eye(length).unsqueeze(0)
            masks = torch.ones(1, length, dtype=torch.long)
            indices = [(torch.tensor([0]), torch.tensor([0]))]
            overlap = (target["rel_positive_map"] > 0) & (target["other_entity_map"] > 0)
            coords = overlap[0].nonzero().flatten()
            conditions, counts = {}, {}
            for condition in ("original", "identity", "remove_other_overlap",
                              "remove_relation_overlap", "remove_other_disjoint"):
                edited = copy.deepcopy(target)
                count = 0
                if condition == "remove_other_overlap":
                    edited["other_entity_map"][overlap] = 0
                    count = int(overlap.sum())
                elif condition == "remove_relation_overlap":
                    edited["rel_positive_map"][overlap] = 0
                    count = int(overlap.sum())
                elif condition == "remove_other_disjoint":
                    positions = ((edited["other_entity_map"][0] > 0) &
                                 ~overlap[0]).nonzero().flatten()[:len(coords)]
                    edited["other_entity_map"][0, positions] = 0
                    count = len(positions)
                queries = torch.zeros(1, 128, length, requires_grad=True)
                loss = criterion.loss_sem_align(tokens, queries, masks, [edited], indices, 1)
                grad = torch.autograd.grad(loss, queries)[0]
                conditions[condition] = {
                    "loss": float(loss.detach()),
                    "overlap_coordinate_gradients": grad[0, 0, coords].tolist(),
                    "all_gradients_finite": bool(torch.isfinite(grad).all()),
                    "gradient_sha256": hashlib.sha256(grad.contiguous().numpy().tobytes()).hexdigest(),
                }
                counts[condition] = count
            records.append({"scene": case["scene"], "ann_id": case["ann_id"],
                            "overlap_tokens": coords.tolist(), "controlled_token_columns": length,
                            "edit_counts": counts, "conditions": conditions})
        loss_trials.append(records)
        print(json.dumps({"trial": trial, "cases": len(records)}), flush=True)
    original_gradients = [
        gradient for r in loss_trials[0]
        for gradient in r["conditions"]["original"]["overlap_coordinate_gradients"]]
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "script_sha256": sha(Path(__file__)), "audit_sha256": sha(audit_path),
        "loss_source_sha256": sha(loss_source), "dataset_sha256": sha(source),
        "config_sha256": sha(config), "seed": 1999, "cpu_only": True,
        "getter_trials": getter_trials, "getter_map_exact_repeat": getter_trials[0] == getter_trials[1],
        "getter_map_failures": sum(len(r["map_failures"]) for rows in getter_trials for r in rows),
        "getter_expressions": sum(len(r["ann_ids"]) for r in getter_trials[0]),
        "loss_trials": loss_trials, "synthetic_loss_exact_repeat": loss_trials[0] == loss_trials[1],
        "cases": len(cases), "scenes": len({c["scene"] for c in cases}),
        "overlap_coordinate_original_positive": sum(g > 0 for g in original_gradients),
        "overlap_coordinate_original_negative": sum(g < 0 for g in original_gradients),
        "overlap_coordinate_original_zero": sum(g == 0 for g in original_gradients),
        "disjoint_control_count_shortfalls": sum(
            r["edit_counts"]["remove_other_disjoint"] < len(r["overlap_tokens"])
            for r in loss_trials[0]),
        "scope": "Actual native getter maps; original loss function on ZERO SYNTHETIC query and identity-token inputs, not64D decoder embeddings. No whole-model native backward or trained harm/efficacy/novelty/resource certificate.",
    }
    output = PIPE / "relation_cpu_gradient_20261013_0707.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "cases": result["cases"],
                      "scenes": result["scenes"], "getter_expressions": result["getter_expressions"],
                      "getter_repeat": result["getter_map_exact_repeat"],
                      "getter_failures": result["getter_map_failures"],
                      "synthetic_repeat": result["synthetic_loss_exact_repeat"],
                      "positive_gradients": result["overlap_coordinate_original_positive"],
                      "negative_gradients": result["overlap_coordinate_original_negative"],
                      "shortfall_controls": result["disjoint_control_count_shortfalls"]}), flush=True)


if __name__ == "__main__":
    main()
