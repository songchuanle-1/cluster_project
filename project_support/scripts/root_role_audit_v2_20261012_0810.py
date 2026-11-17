"""Corrected taxonomy plus literal annotation-name anchor, no identity claims."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
# Native sem2nyu ordering in the frozen dataset: counter11, desk12, curtain13.
CLASSES = {"cabinet": 2, "bed": 3, "chair": 4, "sofa": 5, "table": 6,
           "door": 7, "window": 8, "bookshelf": 9, "picture": 10,
           "counter": 11, "desk": 12, "curtain": 13, "refrigerator": 14,
           "toilet": 16, "sink": 17, "bathtub": 18}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower()))


def main():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    import numpy as np
    import torch
    torch.set_num_threads(1)
    paths = {
        "manifest": PIPE / "point_detail_population_20261009/result.manifest.json",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "dataset": ROOT / "framework/dataset/scannetv2.py",
    }
    expected = {
        "manifest": "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932",
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
    }
    hashes = {k: sha(p) for k, p in paths.items()}
    assert hashes == expected
    dataset_text = paths["dataset"].read_text()
    assert "self.sem2nyu = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 24, 28, 33, 34, 36, 39]" in dataset_text
    manifest = json.loads(paths["manifest"].read_text())
    annotations = json.loads(paths["annotations"].read_text())
    by_id = {(a["scene_id"], int(a["ann_id"])): a for a in annotations}
    graphs = json.loads(paths["graphs"].read_text())

    def text_alignment(a):
        graph = graphs[a["scene_id"]][str(a["ann_id"])]
        root = next(n for n in graph["graph_node"] if n["node_id"] == 0)
        caption = " ".join(graph["utterance"].replace(",", " ,").split())
        name = normalized(a.get("object_name", ""))
        words = name.split()
        pattern = r"\b" + r"\s+".join(map(re.escape, words)) + r"\b" if words else r"(?!x)x"
        mentions = [[m.start(), m.end()] for m in re.finditer(pattern, caption, re.I)]
        root_spans = root["target_char_span"]
        overlap = any(max(l, x) < min(r, y) for l, r in mentions for x, y in root_spans)
        return graph, root, caption, name, mentions, overlap

    counts, full_counts, rows, inputs = Counter(), Counter(), [], []
    for a in annotations:
        graph, root, caption, name, mentions, overlap = text_alignment(a)
        status = ("literal_target_in_root" if overlap else
                  "literal_target_outside_root" if mentions else
                  "literal_target_not_found")
        full_counts[status] += 1
        full_counts["expressions"] += 1
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
            a = by_id[scene, aid]
            targets = sorted(map(int, a.get("object_ids", [a.get("object_id")])))
            assert targets == sorted(map(int, frozen["object_ids"]))
            graph, root, caption, name, mentions, overlap = text_alignment(a)
            category = classes.get(targets[0]) if len(targets) == 1 else None
            root_category = CLASSES.get(root["lemma_head"].lower().strip())
            row = {
                "scene": scene, "ann_id": aid, "native_group": int(scene_row["native_group"]),
                "targets": targets, "native_category": category,
                "annotation_object_name": name, "annotation_category": CLASSES.get(name),
                "root_lemma": root["lemma_head"], "root_category": root_category,
                "caption": caption, "literal_target_spans": mentions,
                "root_target_spans": root["target_char_span"],
                "object_nodes": [{"node_id": n["node_id"], "target": n["target"],
                                  "lemma_head": n["lemma_head"],
                                  "spans": n["target_char_span"]}
                                 for n in graph["graph_node"] if n["node_type"] == "Object"],
                "literal_root_overlap": overlap,
                "literal_status": ("literal_target_in_root" if overlap else
                                   "literal_target_outside_root" if mentions else
                                   "literal_target_not_found"),
            }
            if category is None:
                row["status"] = "native_target_category_unknown"
            elif root_category is None:
                row["status"] = "root_category_unmapped"
            elif root_category == category:
                row["status"] = "category_consistent_root"
            else:
                row["status"] = "root_native_category_mismatch"
            counts[row["status"]] += 1
            counts[row["literal_status"]] += 1
            counts["expressions"] += 1
            rows.append(row)
    assert len(rows) == 128
    examples = [r for r in rows if r["literal_status"] == "literal_target_outside_root"]
    result = {
        "contract": "native_target_mention_role_audit_v2",
        "counts": dict(counts), "full_train_literal_counts": dict(full_counts),
        "rows": rows, "input_hashes": hashes, "native_geometry": inputs,
        "script_sha256": sha(Path(__file__)), "cpu_only": True, "admission": False,
        "adapter_correction": "V1 inherited incorrect counter/desk/curtain semantic indices. V1 result/source retained; V2 uses verified native sem2nyu taxonomy and independently literal annotation-name spans.",
        "scope": "Literal label mentions/category agreement do not resolve multiple same-category referents, annotation inconsistency or trained efficacy.",
    }
    output = PIPE / "root_role_audit_v2_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"counts": dict(counts),
                      "full_train_literal_counts": dict(full_counts),
                      "examples": examples, "output_sha256": sha(output)}, indent=2))


if __name__ == "__main__":
    main()
