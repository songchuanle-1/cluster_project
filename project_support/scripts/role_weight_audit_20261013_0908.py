"""Original TRAIN role maps and source-extracted token-weight precedence."""
import ast
from collections import Counter
import copy
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import socket
import sys
from types import SimpleNamespace

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
TOKEN = "3076255a5f0543e9a6de659374e194cc"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert socket.gethostname() == "das"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    paths = {
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "config": PIPE / "majority_erasure_original_config_20261012_0910.yaml",
        "loss": ROOT / "framework/model/Quard_model" / NAME / "loss.py",
    }
    expected = {
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "config": "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a",
        "loss": "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5",
    }
    for key, path in paths.items():
        assert sha(path) == expected[key], key
    cfg = gorilla.Config.fromfile(str(paths["config"]))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("role-weight"))
    mapper = dataset._get_token_positive_map_by_parse
    tree = ast.parse(paths["loss"].read_text())
    function = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "loss_sem_align")

    def is_tmask(node):
        if not isinstance(node, ast.Assign):
            return False
        target = node.targets[0]
        return ((isinstance(target, ast.Name) and target.id == "tmask")
                or (isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "tmask"))

    statements = [copy.deepcopy(n) for n in function.body if is_tmask(n)]
    assert len(statements) == 7, len(statements)
    code = compile(ast.fix_missing_locations(ast.Module(
        body=statements, type_ignores=[])), str(paths["loss"]), "exec")

    def readout(values):
        main, modifier, pronoun, relation = [
            torch.from_numpy(values[i][:1]).unsqueeze(1) for i in (1, 2, 3, 6)]
        namespace = {
            "torch": torch, "self": SimpleNamespace(
                eos_coef=cfg.model.criterion.get("eos_coef", 0.1)),
            "logits": torch.zeros(1, 1, 256),
            "inds": torch.tensor([254]), "positive_map": main > 0,
            "modi_positive_map": modifier, "pron_positive_map": pronoun,
            "rel_positive_map": relation,
        }
        exec(code, namespace)
        original = namespace["tmask"][0]
        preserved = original.clone()
        preserved[main[0, 0] > 0] = 1
        return original.numpy(), preserved.numpy()

    def node(modifier=None, pronoun=None, relation=None):
        return {"node_id": 0, "node_type": "Object",
                "target_char_span": [[6, 11]],
                "mod_char_span": modifier or [], "pron_char_span": pronoun or [],
                "rel_char_span": relation or []}

    controls = {}
    for key, root in {
        "disjoint": node(modifier=[[2, 5]], relation=[[12, 16]]),
        "modifier_overlap": node(modifier=[[6, 11]]),
        "pronoun_overlap": node(pronoun=[[6, 11]]),
        "relation_overlap": node(relation=[[6, 11]]),
    }.items():
        graph = {"utterance": "a red chair near a table",
                 "graph_node": [root], "graph_edge": []}
        values = mapper(graph, None)
        actual, preserved = readout(values)
        coords = np.flatnonzero(values[1][0] > 0)
        controls[key] = {
            "main_tokens": coords.tolist(),
            "original_main_weights": actual[coords].tolist(),
            "preserved_main_weights": preserved[coords].tolist(),
            "changed_tokens": np.flatnonzero(actual != preserved).tolist(),
            "identity_exact": np.array_equal(actual, readout(copy.deepcopy(values))[0]),
        }
    assert not controls["disjoint"]["changed_tokens"]
    for key in ("modifier_overlap", "pronoun_overlap", "relation_overlap"):
        assert controls[key]["changed_tokens"] and controls[key]["identity_exact"]
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    assert len(annotations) == 36665
    trials = []
    selected = {}
    for trial in (0, 1):
        gorilla.set_random_seed(1999)
        counts = Counter()
        digest = hashlib.sha256()
        affected_scenes = set()
        examples = []
        for number, ann in enumerate(annotations, 1):
            scene, aid = ann["scene_id"], str(ann["ann_id"])
            values = mapper(graphs[scene][aid], None)
            main = values[1][0] > 0
            overlap = {}
            for role, index in (("modifier", 2), ("pronoun", 3), ("relation", 6)):
                indices = np.flatnonzero(main & (values[index][0] > 0)).tolist()
                overlap[role] = indices
                counts[role + "_overlap_expressions"] += bool(indices)
                counts[role + "_overlap_tokens"] += len(indices)
            counts["expressions"] += 1
            combined = main & ((values[2][0] > 0) | (values[3][0] > 0)
                               | (values[6][0] > 0))
            counts["overlap_expressions"] += bool(combined.any())
            counts["overlap_tokens"] += int(combined.sum())
            if combined.any():
                actual, preserved = readout(values)
                changed = np.flatnonzero(actual != preserved).tolist()
                counts["weight_override_expressions"] += bool(changed)
                counts["weight_override_tokens"] += len(changed)
                counts["non_overlap_changes"] += int(np.sum((actual != preserved) & ~combined))
                affected_scenes.add(scene)
                row = {"scene": scene, "ann_id": int(aid), "roles": overlap,
                       "changed_tokens": changed,
                       "original_weights": actual[changed].tolist()}
                if len(examples) < 16:
                    examples.append(row)
                if trial == 0:
                    selected.setdefault(scene, row)
            digest.update(f"{scene}:{aid};".encode())
            for index in (1, 2, 3, 6):
                digest.update(np.ascontiguousarray(values[index][0]).tobytes())
            if number % 5000 == 0 or number == len(annotations):
                print(json.dumps({"trial": trial, "done": number,
                                  "counts": dict(counts)}), flush=True)
        trials.append({"counts": dict(counts), "affected_scene_count": len(affected_scenes),
                       "map_sha256": digest.hexdigest(), "examples": examples})
    selection = [selected[key] for key in sorted(selected)[:8]]
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
        "script_sha256": sha(Path(__file__)), "source_and_data_sha256": expected,
        "controls": controls, "trials": trials, "exact_repeat": trials[0] == trials[1],
        "scene_count": len({a["scene_id"] for a in annotations}),
        "frozen_first8positive_scenes": selection,
        "tmask_statement_source_lines": [n.lineno for n in statements],
        "scope": "Original CPU native mapper and exact source-extracted assignments. Controlled256-column arrays, sentinel254; no actual decoder embeddings, Criterion gradient, native whole-model forward/backward, harm, efficacy, resources or novelty certificate.",
    }
    output = PIPE / "role_weight_audit_20261013_0908.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "counts": trials[0]["counts"],
                      "affected_scenes": trials[0]["affected_scene_count"],
                      "exact_repeat": result["exact_repeat"]}), flush=True)


if __name__ == "__main__":
    main()
