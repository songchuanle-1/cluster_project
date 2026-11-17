"""Prediction-blind stored BETWEEN topology and native support geometry."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    assert args.token == "66fa1e81aec94d5eb10265ea533669ac"
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    paths = {
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "config": PIPE / "majority_erasure_original_config_20261012_0910.yaml"}
    hashes = {
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
        "config": "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"}
    for key, path in paths.items():
        assert sha(path) == hashes[key], key
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    assert len(annotations) == 36665
    counts = Counter()
    records = []
    first = {}
    for ann in sorted(annotations, key=lambda a: (a["scene_id"], int(a["ann_id"]))):
        scene, aid = ann["scene_id"], int(ann["ann_id"])
        graph = graphs[scene][str(aid)]
        counts["all_train_expressions"] += 1
        literal = bool(re.search(r"\bbetween\b", graph["utterance"].lower()))
        nodes = {node["node_id"]: node for node in graph["graph_node"]}
        root_edges = [edge for edge in graph["graph_edge"]
                      if 0 in (edge["obj_idx"], edge["sub_idx"])
                      and re.search(r"\bbetween\b", edge["relation"].lower())]
        if not literal and not root_edges:
            continue
        counts["literal_between"] += literal
        counts["stored_root_between"] += bool(root_edges)
        objects = [node for key, node in nodes.items() if key != 0 and node["node_type"] == "Object"]
        endpoint_ids = sorted({
            edge["sub_idx"] if edge["obj_idx"] == 0 else edge["obj_idx"]
            for edge in root_edges
            if nodes[edge["sub_idx"] if edge["obj_idx"] == 0 else edge["obj_idx"]]["node_type"] == "Object"})
        counts["at_least_two_direct_reference_nodes"] += len(endpoint_ids) >= 2
        row = {"scene": scene, "ann_id": aid, "caption": graph["utterance"],
               "target_ids": list(map(int, ann.get("object_ids", [ann.get("object_id")]))),
               "direct_between_reference_node_ids": endpoint_ids,
               "nonroot_objects": [{
                   "node_id": node["node_id"], "lemma_head": node.get("lemma_head"),
                   "target_char_span": node.get("target_char_span", [])} for node in objects],
               "edges": [{key: edge.get(key) for key in (
                   "obj_idx", "sub_idx", "relation", "object", "subject")}
                   for edge in graph["graph_edge"]],
               "topology": "two_direct_roles" if len(endpoint_ids) >= 2 else
                           "one_direct_role_with_other_nodes" if endpoint_ids and len(objects) >= 2 else
                           "single_or_missing_stored_reference_role"}
        counts[row["topology"]] += 1
        records.append(row)
        if root_edges and len(objects) >= 2:
            first.setdefault(scene, row)
    frozen = [first[scene] for scene in sorted(first)[:8]]
    cfg = gorilla.Config.fromfile(str(paths["config"]))
    cfg.data.train.data_root = str(DATA) + "/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("between-pair"))
    lookup = {(ann["scene_id"], int(ann["ann_id"])): group
              for group, annos in enumerate(dataset.scene_inputs) for ann in annos}
    for row in frozen:
        group = lookup[(row["scene"], row["ann_id"])]
        row["native_group"] = group
        row["group_ann_ids"] = [int(a["ann_id"]) for a in dataset.scene_inputs[group]]
    manifest_path = PIPE / ("between_pair_" + args.token + ".manifest.json")
    with manifest_path.open("x") as stream:
        json.dump({"tick_token": args.token, "counts": dict(counts), "frozen": frozen,
                   "source_hashes": hashes, "prediction_used": False,
                   "physical_geometry_read_started": False}, stream, indent=2)
        stream.write("\n")
    class_to_raw = defaultdict(list)
    for raw, nyu in enumerate(dataset.sem2nyu):
        if nyu in dataset.nyu40id2class:
            class_to_raw[dataset.nyu40id2class[nyu]].append(raw)
    geometry = []
    for row in frozen:
        scene = row["scene"]
        path = DATA / ("scannetv2/train/" + scene + "_refer.pth")
        if not path.is_file():
            geometry.append({"scene": scene, "status": "missing_native_geometry"})
            continue
        xyz, _, _, semantic, instance = torch.load(path, map_location="cpu", weights_only=False)
        xyz, semantic, instance = map(np.asarray, (xyz, semantic, instance))
        supports = {}
        classes = {}
        for oid in np.unique(instance):
            if oid < 0:
                continue
            mask = instance == oid
            points = xyz[mask].astype(np.float64)
            supports[int(oid)] = points
            labels = semantic[mask]
            labels = labels[labels >= 0].astype(int)
            if len(labels):
                raw = int(np.bincount(labels).argmax())
                if raw < len(dataset.sem2nyu):
                    nyu = dataset.sem2nyu[raw]
                    classes[int(oid)] = dataset.nyu40id2class.get(nyu)
        references = []
        for node in row["nonroot_objects"]:
            name = str(node["lemma_head"]).lower().strip()
            category = dataset.type2class.get(name)
            ids = sorted(oid for oid, cls in classes.items()
                         if cls == category and category is not None and oid not in row["target_ids"])
            references.append({**node, "native_category": category,
                               "candidate_ids": ids, "identity_known": False})
        pair_readouts = []
        for left_index, left in enumerate(references):
            for right in references[left_index + 1:]:
                for a in left["candidate_ids"]:
                    for b in right["candidate_ids"]:
                        if a == b:
                            pair_readouts.append({"a": a, "b": b, "status": "duplicate_witness_invalid"})
                            continue
                        pa, pb = supports[a], supports[b]
                        delta = pb.mean(0) - pa.mean(0)
                        norm = float(np.linalg.norm(delta))
                        if norm == 0:
                            pair_readouts.append({"a": a, "b": b, "status": "zero_center_distance"})
                            continue
                        direction = delta / norm
                        lower, upper = float((pa @ direction).max()), float((pb @ direction).min())
                        centers = {oid: float(points.mean(0) @ direction)
                                   for oid, points in supports.items()}
                        target_id = row["target_ids"][0]
                        target_value = centers.get(target_id)
                        pair_readouts.append({
                            "left_node": left["node_id"], "right_node": right["node_id"],
                            "a": a, "b": b, "gap": [lower, upper],
                            "status": "positive_gap" if lower < upper else "support_intervals_overlap",
                            "target_projected_center": target_value,
                            "target_in_gap": lower < target_value < upper if target_value is not None and lower < upper else None,
                            "same_class_distractor_in_gap": {
                                str(oid): lower < center < upper for oid, center in centers.items()
                                if oid != target_id and classes.get(oid) == classes.get(target_id)} if lower < upper else {},
                            "scope": "Unknown physical reference identity; necessary slab only, not truth labels."})
        geometry.append({"scene": scene, "ann_id": row["ann_id"], "native_group": row["native_group"],
                         "topology": row["topology"], "references": references,
                         "geometry_sha256": sha(path), "pairs": pair_readouts})
        print(json.dumps({"scene": scene, "topology": row["topology"],
                          "reference_nodes": len(references), "physical_pair_readouts": len(pair_readouts)}), flush=True)
    result = {"tick_token": args.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "counts": dict(counts), "stored_between_records": records,
              "frozen_scene_count": len(frozen), "requested_scenes": 8,
              "selection_shortfall": 8 - len(frozen), "frozen_manifest_sha256": sha(manifest_path),
              "native_sem2nyu": dataset.sem2nyu, "native_type2class": dataset.type2class,
              "geometry": geometry, "source_hashes": hashes,
              "script_sha256": sha(Path(__file__)), "cpu_only": True,
              "optimizer_steps": 0, "new_models": 0,
              "scope": "Metadata/geometry diagnostic only; reference identity, novel mechanism, native backward, resource efficiency and trained benefit are not established."}
    output = PIPE / ("between_pair_inventory_" + args.token + ".json")
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "counts": result["counts"],
                      "frozen_scenes": len(frozen)}), flush=True)


if __name__ == "__main__":
    main()
