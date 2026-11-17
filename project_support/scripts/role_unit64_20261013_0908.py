"""Unit-norm64 synthetic Criterion confirmation on frozen original role maps."""
import ast
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
    import torch.nn.functional as F
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    source = ROOT / "framework/model/Quard_model" / NAME / "loss.py"
    decoder = source.parent / "dec.py"
    graphs_path = DATA / "scanrefer/scene_graphs_new_train.json"
    selection_path = PIPE / "role_loss_mass_20261013_0908.json"
    expected = {
        "config": "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a",
        "loss": "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5",
        "decoder": "6f7566bd02121fd218fd1360be7c7b1905c267de8a03f36473779ab4d66b9d3a",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "selection": "db2b06c8e7a4b462a295f5898c28d0ef4300e972f84ccf8135dd8deac165f3da",
    }
    for key, path in {"config": config, "loss": source, "decoder": decoder,
                      "graphs": graphs_path, "selection": selection_path}.items():
        assert sha(path) == expected[key], key
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("role-unit64"))
    mapper = dataset._get_token_positive_map_by_parse
    criterion = importlib.import_module(
        "framework.model.Quard_model." + NAME + ".loss").Criterion(**cfg.model.criterion)
    function = next(n for n in ast.walk(ast.parse(source.read_text()))
                    if isinstance(n, ast.FunctionDef) and n.name == "loss_sem_align")
    functions = {}
    for kind in ("mass", "precedence"):
        controlled = copy.deepcopy(function)
        controlled.name = kind + "_control"
        if kind == "mass":
            indices = [i for i, n in enumerate(controlled.body)
                       if isinstance(n, ast.Assign)
                       and isinstance(n.targets[0], ast.Name)
                       and n.targets[0].id == "nb_pos_obj"]
            assert len(indices) == 1
            controlled.body[indices[0]] = ast.parse(
                "nb_pos_obj = positive_map.sum(1) + (modi_positive_map>0).sum(1)"
                " + (pron_positive_map>0).sum(1) + (rel_positive_map>0).sum(1) + 1e-6"
            ).body[0]
        else:
            index = max(i for i, n in enumerate(controlled.body)
                        if isinstance(n, ast.Assign)
                        and isinstance(n.targets[0], ast.Subscript)
                        and isinstance(n.targets[0].value, ast.Name)
                        and n.targets[0].value.id == "tmask")
            controlled.body.insert(index + 1, ast.parse(
                "tmask[positive_map.any(1)] = 1.0").body[0])
        namespace = {"torch": torch}
        exec(compile(ast.fix_missing_locations(ast.Module(
            body=[controlled], type_ignores=[])), str(source), "exec"), namespace)
        functions[kind] = namespace[controlled.name].__get__(criterion)
    graphs = json.loads(graphs_path.read_text())
    selection = json.loads(selection_path.read_text())["selection"]
    controls = {}
    control_graphs = {}
    for key, end in (("one_token", 7), ("two_tokens", 12)):
        graph = {
            "utterance": "a light blue chair near a table",
            "graph_node": [{
                "node_id": 0, "node_type": "Object",
                "target_char_span": [[13, 18]], "mod_char_span": [[2, end]],
                "pron_char_span": [], "rel_char_span": [],
            }], "graph_edge": [],
        }
        values = mapper(graph, None)
        active = values[2][0] > 0
        controls[key] = {"modifier_token_count": int(active.sum()),
                         "raw_values": values[2][0][active].tolist(),
                         "raw_mass": float(values[2][0].sum()),
                         "boolean_mass": int(active.sum())}
        control_graphs[key] = graph
    assert controls["one_token"]["modifier_token_count"] == 1
    assert controls["two_tokens"]["modifier_token_count"] == 2
    trials = []
    for trial in (0, 1):
        records = []
        cases = [(kind, f'{row["scene"]}:{row["ann_id"]}',
                  graphs[row["scene"]][str(row["ann_id"])])
                 for kind, rows in selection.items() for row in rows]
        cases.extend(("mass", "control:" + key, graph)
                     for key, graph in control_graphs.items())
        for kind, key, graph in cases:
            values = mapper(graph, None)
            target = {field: torch.from_numpy(value[:1]).float()
                      for field, value in zip(FIELDS, values[1:])}
            text = " ".join(graph["utterance"].replace(",", " ,").split())
            length = len(dataset.tokenizer(text)["input_ids"]) + 2
            generator = torch.Generator().manual_seed(1999)
            query_base = torch.randn(1, 128, 64, generator=generator)
            token_base = torch.randn(1, length, 64, generator=generator)
            conditions, gradient_values = {}, {}
            for condition in ("original", "identity", "diagnostic"):
                queries_raw = query_base.clone().requires_grad_()
                tokens_raw = token_base.clone().requires_grad_()
                queries = F.normalize(queries_raw, p=2, dim=-1)
                tokens = F.normalize(tokens_raw, p=2, dim=-1)
                fn = functions[kind] if condition == "diagnostic" else criterion.loss_sem_align
                loss = fn(tokens, queries, torch.ones(1, length, dtype=torch.long),
                          [copy.deepcopy(target)],
                          [(torch.tensor([0]), torch.tensor([0]))], 1)
                gradients = torch.autograd.grad(loss, (queries_raw, tokens_raw))
                gradient_values[condition] = gradients
                digest = hashlib.sha256()
                for gradient in gradients:
                    digest.update(gradient.contiguous().numpy().tobytes())
                conditions[condition] = {
                    "loss": float(loss.detach()), "gradient_sha256": digest.hexdigest(),
                    "gradient_finite": all(bool(torch.isfinite(g).all()) for g in gradients),
                    "gradient_norms": [float(g.norm()) for g in gradients],
                    "query_norm_max_error": float((queries.norm(dim=-1) - 1).abs().max()),
                    "token_norm_max_error": float((tokens.norm(dim=-1) - 1).abs().max()),
                    "max_abs_logit": float(
                        (queries @ tokens.transpose(-1, -2) / criterion.temperature).abs().max()),
                }
            records.append({
                "kind": kind, "key": key, "conditions": conditions,
                "identity_max_gradient_delta": max(
                    float((a - b).abs().max()) for a, b in
                    zip(gradient_values["original"], gradient_values["identity"])),
                "diagnostic_max_gradient_delta": max(
                    float((a - b).abs().max()) for a, b in
                    zip(gradient_values["original"], gradient_values["diagnostic"])),
            })
        trials.append(records)
        print(json.dumps({"trial": trial, "records": len(records)}), flush=True)
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
        "script_sha256": sha(Path(__file__)), "source_and_selection_sha256": expected,
        "controls": controls, "trials": trials, "exact_repeat": trials[0] == trials[1],
        "identity_all_exact": all(
            r["conditions"]["original"] == r["conditions"]["identity"]
            and r["identity_max_gradient_delta"] == 0 for r in trials[0]),
        "all_finite": all(c["gradient_finite"] for r in trials[0]
                          for c in r["conditions"].values()),
        "scope": "Synthetic64D L2-normalized embeddings and derivatives through normalization; fixed original native maps/real original Criterion; NOT actual scene decoder embeddings, model parameter backward, harm, efficacy, resources or independent innovation.",
    }
    output = PIPE / "role_unit64_20261013_0908.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "exact_repeat": result["exact_repeat"],
                      "identity_exact": result["identity_all_exact"],
                      "all_finite": result["all_finite"], "controls": controls}), flush=True)


if __name__ == "__main__":
    main()
