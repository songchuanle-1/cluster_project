"""Native point-category versus parser target role; remote CPU diagnosis."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
CLASSES = {"cabinet": 2, "bed": 3, "chair": 4, "sofa": 5, "table": 6,
           "door": 7, "window": 8, "bookshelf": 9, "picture": 10,
           "counter": 12, "desk": 13, "curtain": 14, "toilet": 16,
           "sink": 17, "bathtub": 18}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    import numpy as np
    import torch
    torch.set_num_threads(1)
    paths = {
        "manifest": PIPE / "point_detail_population_20261009/result.manifest.json",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
    }
    expected = {
        "manifest": "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932",
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
    }
    hashes = {k: sha(p) for k, p in paths.items()}
    assert hashes == expected
    manifest = json.loads(paths["manifest"].read_text())
    annotations = {(a["scene_id"], int(a["ann_id"])): a
                   for a in json.loads(paths["annotations"].read_text())}
    graphs = json.loads(paths["graphs"].read_text())
    rows, inputs, counts = [], [], Counter()
    for scene_row in manifest:
        scene = scene_row["scene"]
        path = DATA / f"scannetv2/train/{scene}_refer.pth"
        _, _, _, sem, ins = torch.load(path, map_location="cpu", weights_only=False)
        sem, ins = map(np.asarray, (sem, ins))
        classes = {}
        for oid in np.unique(ins):
            labels = sem[ins == oid]
            labels = labels[labels >= 0].astype(int)
            if oid >= 0 and len(labels):
                classes[int(oid)] = int(np.bincount(labels).argmax())
        inputs.append({"scene": scene, "path": str(path), "sha256": sha(path)})
        for frozen in scene_row["annotations"]:
            aid = int(frozen["ann_id"])
            a = annotations[scene, aid]
            targets = sorted(map(int, a.get("object_ids", [a.get("object_id")])))
            assert targets == sorted(map(int, frozen["object_ids"]))
            graph = graphs[scene][str(aid)]
            nodes = graph["graph_node"]
            root = next(n for n in nodes if n["node_id"] == 0)
            category = classes.get(targets[0]) if len(targets) == 1 else None
            root_category = CLASSES.get(root["lemma_head"].lower().strip())
            compatible = [n for n in nodes if n["node_type"] == "Object"
                          and category is not None
                          and CLASSES.get(n["lemma_head"].lower().strip()) == category]
            name = " ".join(re.findall(r"[a-z]+", str(a.get("object_name", "")).lower()))
            row = {
                "scene": scene, "ann_id": aid,
                "native_group": int(scene_row["native_group"]),
                "targets": targets, "native_category": category,
                "annotation_object_name": name, "annotation_category": CLASSES.get(name),
                "root_lemma": root["lemma_head"], "root_category": root_category,
                "compatible_node_ids": [n["node_id"] for n in compatible],
                "caption": a["description"],
                "root_target_spans": root["target_char_span"],
                "compatible_target_spans": [n["target_char_span"] for n in compatible],
            }
            if category is None:
                row["status"] = "native_target_category_unknown"
            elif root_category is None:
                row["status"] = "root_category_unmapped"
            elif root_category == category:
                row["status"] = "category_consistent_root"
            elif not compatible:
                row["status"] = "root_mismatch_no_compatible_graph_mention"
            elif len(compatible) == 1:
                row["status"] = "root_mismatch_unique_compatible_mention"
            else:
                row["status"] = "root_mismatch_multiple_compatible_mentions"
            counts[row["status"]] += 1
            counts["expressions"] += 1
            rows.append(row)
    assert len(rows) == 128
    examples = [r for r in rows if r["status"].startswith("root_mismatch")][:8]
    result = {
        "contract": "native_target_mention_role_audit_v1", "counts": dict(counts),
        "rows": rows, "input_hashes": hashes, "native_geometry": inputs,
        "script_sha256": sha(Path(__file__)), "cpu_only": True, "admission": False,
        "scope": "Category agreement is not full mention co-reference or model efficacy.",
    }
    output = PIPE / "root_role_audit_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"counts": dict(counts), "examples": examples,
                      "output_sha256": sha(output)}, indent=2))


if __name__ == "__main__":
    main()
