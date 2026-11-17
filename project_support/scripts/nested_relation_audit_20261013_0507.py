"""Registered native nested-relation map audit, remote CPU only."""
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

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
TOKEN = "f3d67c69338443d28eee4349fd8576ab"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert socket.gethostname() == "das"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import gorilla
    import numpy as np
    import torch
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    paths = {
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "config": PIPE / "majority_erasure_original_config_20261012_0910.yaml",
    }
    expected = {
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "config": "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a",
    }
    for key, path in paths.items():
        assert sha(path) == expected[key], str(path)
    cfg = gorilla.Config.fromfile(str(paths["config"]))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("nested-relations"))
    mapper = dataset._get_token_positive_map_by_parse
    anns = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())

    def union_graph(graph):
        changed = copy.deepcopy(graph)
        spans = changed["graph_node"][0]["rel_char_span"]
        for node in changed["graph_node"][1:]:
            if node.get("node_type") == "Object":
                for span in node.get("rel_char_span", []):
                    if span not in spans:
                        spans.append(span)
        return changed

    def active(graph):
        return np.flatnonzero(mapper(graph, None)[6][0] > 0).tolist()

    def node(nid, target, relation):
        return {"node_id": nid, "node_type": "Object",
                "target_char_span": target, "mod_char_span": [],
                "pron_char_span": [], "rel_char_span": relation}

    text = "a chair beside a table near a window"
    nested = {"utterance": text, "graph_edge": [],
              "graph_node": [node(0, [[2, 7]], [[8, 14]]),
                             node(1, [[17, 22]], [[23, 27]]),
                             node(2, [[30, 36]], [])]}
    root_only = copy.deepcopy(nested)
    root_only["graph_node"][1]["rel_char_span"] = []
    covered = copy.deepcopy(nested)
    covered["graph_node"][0]["rel_char_span"].append([23, 27])
    controls = {
        name: {"original": active(graph), "union": active(union_graph(graph))}
        for name, graph in (("nested", nested), ("root_only", root_only),
                            ("already_covered", covered))
    }
    assert len(controls["nested"]["union"]) > len(controls["nested"]["original"])
    assert controls["root_only"]["original"] == controls["root_only"]["union"]
    assert controls["already_covered"]["original"] == controls["already_covered"]["union"]
    counts, node_types, keys = Counter(), Counter(), Counter()
    examples, changed_scenes = [], set()
    map_digest = hashlib.sha256()
    for i, ann in enumerate(anns, 1):
        graph = graphs[ann["scene_id"]][str(ann["ann_id"])]
        native = mapper(graph, None)
        nonroot = [n for n in graph["graph_node"][1:] if n.get("node_type") == "Object"]
        nested_spans = [span for node in nonroot for span in node.get("rel_char_span", [])]
        counts["expressions"] += 1
        counts["nonroot_object_nodes"] += len(nonroot)
        counts["nonroot_relation_spans"] += len(nested_spans)
        counts["expressions_with_nonroot_relation_spans"] += bool(nested_spans)
        for node in graph["graph_node"]:
            node_types[str(node.get("node_type"))] += 1
            keys.update(node.keys())
        original = np.flatnonzero(native[6][0] > 0).tolist()
        alternative = union_graph(graph)
        if nested_spans:
            modified = mapper(alternative, None)
            new = sorted(set(np.flatnonzero(modified[6][0] > 0).tolist()) - set(original))
            assert all(np.array_equal(a, b) for a, b in zip(native[:6], modified[:6]))
        else:
            new = []
        counts["expressions_with_nonroot_only_relation_tokens"] += bool(new)
        counts["nonroot_only_relation_tokens"] += len(new)
        counts["root_relation_nonempty"] += bool(original)
        map_digest.update(f'{ann["scene_id"]}:{ann["ann_id"]}:{original}:{new};'.encode())
        if new:
            changed_scenes.add(ann["scene_id"])
            if len(examples) < 16:
                examples.append({"scene": ann["scene_id"], "ann_id": int(ann["ann_id"]),
                                 "utterance": graph["utterance"], "original": original,
                                 "new": new, "graph": graph})
        if i % 5000 == 0 or i == len(anns):
            print(json.dumps({"done": i, "counts": dict(counts)}), flush=True)
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
        "script_sha256": sha(Path(__file__)), "source_hashes": expected,
        "counts": dict(counts), "scene_count": len({a["scene_id"] for a in anns}),
        "changed_scene_count": len(changed_scenes), "node_types": dict(node_types),
        "node_field_counts": dict(keys), "controls": controls,
        "examples_first16_original_order": examples, "map_digest": map_digest.hexdigest(),
        "scope": "Original mapper evidence only; union diagnostic is not a deployable mechanism or admission/backward/resource proof."
    }
    output = PIPE / "nested_relation_audit_20261013_0507.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "counts": result["counts"], "changed_scene_count": len(changed_scenes)}))


if __name__ == "__main__":
    main()
