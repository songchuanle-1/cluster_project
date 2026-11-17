"""Prediction-blind native TRAIN phrase/physical-reference identifiability."""
from collections import Counter, defaultdict
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


def normalize(value):
    if isinstance(value, list):
        value = " ".join(map(str, value))
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower()))


def phrase(node):
    return (normalize(node.get("lemma_head", "")),
            normalize(node.get("mod_text", "")))


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
    hashes = {key: sha(path) for key, path in paths.items()}
    assert hashes == expected
    manifest = json.loads(paths["manifest"].read_text())
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    by_scene, by_id = defaultdict(list), {}
    for annotation in annotations:
        by_scene[annotation["scene_id"]].append(annotation)
        by_id[annotation["scene_id"], int(annotation["ann_id"])] = annotation
    rows, collisions, inputs, counts = [], [], [], Counter()
    for scene_row in manifest:
        scene = scene_row["scene"]
        inventory, witnesses = defaultdict(set), defaultdict(list)
        for annotation in by_scene[scene]:
            graph = graphs[scene][str(annotation["ann_id"])]
            main_node = next(n for n in graph["graph_node"] if n["node_id"] == 0)
            key = phrase(main_node)
            targets = list(map(int, annotation.get(
                "object_ids", [annotation.get("object_id")])))
            inventory[key].update(targets)
            witnesses[key].append({"ann_id": int(annotation["ann_id"]),
                                   "targets": targets,
                                   "description": annotation["description"]})
        geometry = DATA / f"scannetv2/train/{scene}_refer.pth"
        _, _, _, semantic, instance = torch.load(
            geometry, map_location="cpu", weights_only=False)
        semantic, instance = map(np.asarray, (semantic, instance))
        physical_classes = {}
        for oid in np.unique(instance):
            valid = semantic[instance == oid]
            valid = valid[valid >= 0].astype(int)
            if oid >= 0 and len(valid):
                physical_classes[int(oid)] = int(np.bincount(valid).argmax())
        inputs.append({"scene": scene, "path": str(geometry), "sha256": sha(geometry)})
        for frozen in scene_row["annotations"]:
            aid = int(frozen["ann_id"])
            annotation = by_id[scene, aid]
            targets = sorted(map(int, annotation.get(
                "object_ids", [annotation.get("object_id")])))
            assert targets == sorted(map(int, frozen["object_ids"]))
            graph = graphs[scene][str(aid)]
            references = []
            for node in graph["graph_node"]:
                if node["node_id"] == 0 or node["node_type"] != "Object":
                    continue
                key = phrase(node)
                linked = sorted(inventory.get(key, set()) - set(targets))
                class_id = CLASSES.get(key[0])
                native = sorted(i for i, c in physical_classes.items()
                                if c == class_id and i not in targets)
                wrong_keys = sorted(k for k in inventory if k[0] != key[0])
                wrong = wrong_keys[0] if wrong_keys else None
                entry = {
                    "node_id": node["node_id"], "phrase_key": list(key),
                    "linked_annotated_targets": linked,
                    "native_same_category": native,
                    "native_category_known": class_id is not None,
                    "independent_annotation_ids": sorted({
                        w["ann_id"] for w in witnesses.get(key, [])
                        if w["ann_id"] != aid}),
                    "self_control_equal": phrase(dict(node)) == key,
                    "wrong_category_control_equal": wrong == key if wrong else None,
                    "physical_reference_identity": "unknown",
                }
                if not linked:
                    entry["status"] = "no_independent_target_phrase_match"
                elif len(linked) == 1:
                    entry["status"] = "one_annotated_phrase_match_not_identity"
                else:
                    entry["status"] = "multiple_distinct_target_phrase_matches"
                    if len(collisions) < 6:
                        collisions.append({
                            "scene": scene, "ann_id": aid, "node": node,
                            "description": annotation["description"],
                            "phrase_key": list(key), "physical_ids": linked,
                            "independent_annotations": witnesses[key][:8]})
                if len(linked) == 1 and len(native) > 1:
                    counts["unique_annotation_but_multiple_physical_instances"] += 1
                counts[entry["status"]] += 1
                counts["reference_mentions"] += 1
                references.append(entry)
            counts["expressions"] += 1
            counts["expressions_with_references"] += bool(references)
            rows.append({"scene": scene, "ann_id": aid, "targets": targets,
                         "references": references})
    assert len(rows) == 128 and len({r["scene"] for r in rows}) == 32
    result = {
        "contract": "scene_shared_reference_identifiability_v1",
        "counts": dict(counts), "rows": rows, "collision_examples": collisions,
        "input_hashes": hashes, "native_geometry": inputs,
        "script_sha256": sha(Path(__file__)), "cpu_only": True, "admission": False,
        "scope": "Phrase/category joins do not establish true physical co-reference.",
    }
    output = PIPE / "shared_reference_audit_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"counts": dict(counts), "collision_examples": collisions,
                      "output_sha256": sha(output)}, indent=2))


if __name__ == "__main__":
    main()
