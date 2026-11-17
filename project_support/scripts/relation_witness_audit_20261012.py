"""Native annotation and point-geometry audit; remote CPU only."""
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
    manifest_path = PIPE / "point_detail_population_20261009/result.manifest.json"
    anno_path = DATA / "scanrefer/ScanRefer_train_new.json"
    graph_path = DATA / "scanrefer/scene_graphs_new_train.json"
    assert sha(manifest_path) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    assert sha(anno_path) == "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
    assert sha(graph_path) == "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
    manifest = json.loads(manifest_path.read_text())
    annos = {(a["scene_id"], int(a["ann_id"])): a
             for a in json.loads(anno_path.read_text())}
    graphs = json.loads(graph_path.read_text())
    rows, input_files, counts = [], [], Counter()
    for scene_row in manifest:
        scene = scene_row["scene"]
        file = DATA / f"scannetv2/train/{scene}_refer.pth"
        xyz, rgb, superpoint, semantic, instance = torch.load(
            file, map_location="cpu", weights_only=False)
        xyz, semantic, instance = map(np.asarray, (xyz, semantic, instance))
        centers, classes = {}, {}
        for oid in np.unique(instance):
            if oid < 0:
                continue
            selected = instance == oid
            centers[int(oid)] = xyz[selected].mean(0).astype(np.float64)
            valid_labels = semantic[selected]
            valid_labels = valid_labels[valid_labels >= 0].astype(int)
            if len(valid_labels):
                classes[int(oid)] = int(np.bincount(valid_labels).argmax())
        input_files.append({"scene": scene, "path": str(file), "sha256": sha(file)})
        for frozen in scene_row["annotations"]:
            aid = int(frozen["ann_id"])
            a = annos[(scene, aid)]
            target_ids = sorted(map(int, a.get("object_ids", [a.get("object_id")])))
            assert target_ids == sorted(map(int, frozen["object_ids"]))
            graph = graphs[scene][str(aid)]
            nodes = {n["node_id"]: n for n in graph["graph_node"]}
            record = {"scene": scene, "ann_id": aid, "target_ids": target_ids,
                      "caption": a["description"],
                      "relation_edges": [], "eligible": []}
            counts["expressions"] += 1
            if any(n != 0 and v["node_type"] == "Object" for n, v in nodes.items()):
                counts["expressions_with_other_object_node"] += 1
            for edge in graph["graph_edge"]:
                record["relation_edges"].append({
                    k: edge[k] for k in ("obj_idx", "sub_idx", "relation",
                                        "object", "subject")})
                if 0 not in (edge["obj_idx"], edge["sub_idx"]):
                    continue
                other_id = (edge["sub_idx"] if edge["obj_idx"] == 0
                            else edge["obj_idx"])
                other = nodes[other_id]
                if other["node_type"] != "Object":
                    counts["target_edges_to_scene_node"] += 1
                    continue
                counts["target_edges_to_object_node"] += 1
                relation = edge["relation"].lower()
                if re.search(r"\b(left|right|front|behind)\b", relation):
                    counts["excluded_view_dependent_edges"] += 1
                    continue
                word = relation.strip()
                if word not in ("above", "below", "under", "over", "underneath"):
                    counts["excluded_non_vertical_or_composite_edges"] += 1
                    continue
                name = other["lemma_head"].lower().strip()
                if name not in CLASSES:
                    counts["excluded_unmapped_reference_category"] += 1
                    continue
                rel_indices = edge.get("relation_idx", [])
                tokens = graph["utterance"].split()
                if not rel_indices:
                    counts["excluded_missing_relation_span"] += 1
                    continue
                begin = min(rel_indices)
                end = max(rel_indices)
                target_positions = [i for k in ("target_mask", "pron_mask")
                                    for i, flag in enumerate(nodes[0].get(k, [])) if flag]
                other_positions = [i for i, flag in enumerate(other["target_mask"]) if flag]
                target_before = any(i < begin for i in target_positions)
                anchor_after = any(i > end for i in other_positions)
                anchor_before = any(i < begin for i in other_positions)
                target_after = any(i > end for i in target_positions)
                if target_before and anchor_after and not (anchor_before and target_after):
                    orientation = 1
                elif anchor_before and target_after and not (target_before and anchor_after):
                    orientation = -1
                else:
                    counts["excluded_ambiguous_direction"] += 1
                    continue
                ref_ids = [i for i, c in classes.items()
                           if c == CLASSES[name] and i not in target_ids]
                entry = {"predicate": word, "anchor_category": name,
                         "reference_ids": ref_ids, "orientation": orientation,
                         "source_relation_tokens": [tokens[i] for i in rel_indices]}
                if len(target_ids) != 1 or target_ids[0] not in centers:
                    entry["status"] = "missing_or_multiple_native_target"
                elif not ref_ids:
                    entry["status"] = "no_native_reference_instance"
                else:
                    sign = 1 if word in ("above", "over") else -1
                    offsets = {i: orientation * sign * float(
                        centers[target_ids[0]][2] - centers[i][2]) for i in ref_ids}
                    compatible = [i for i, delta in offsets.items() if delta > 0]
                    entry.update(signed_vertical_offsets=offsets,
                                 compatible_reference_ids=compatible)
                    if len(compatible) == 1:
                        entry["status"] = "unique_vertical_sign_witness"
                    elif not compatible:
                        entry["status"] = "native_sign_contradiction"
                    else:
                        entry["status"] = "multiple_sign_compatible_witnesses"
                    entry["same_category_permutation_changes_readout"] = (
                        len(ref_ids) > 1 and 0 < len(compatible) < len(ref_ids))
                counts[entry["status"]] += 1
                record["eligible"].append(entry)
            rows.append(record)
    assert len(rows) == 128 and len({r["scene"] for r in rows}) == 32
    result = {"contract": "relation_witness_vertical_sign_audit_v1",
              "seed": 1999, "cpu_only": True, "admission": False,
              "counts": dict(counts), "rows": rows, "native_geometry": input_files,
              "input_hashes": {"manifest": sha(manifest_path),
                               "annotations": sha(anno_path), "graphs": sha(graph_path)},
              "script_sha256": sha(Path(__file__)),
              "limits": "Vertical centroid sign is necessary but not sufficient for natural-language relation truth. Unique sign does not establish true anchor identity; viewpoint predicates excluded. No checkpoint forward, causal efficacy or novel core certified."}
    output = PIPE / "relation_witness_audit_20261012.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps({"output": str(output), "sha256": sha(output),
                      "counts": result["counts"],
                      "eligible_rows": [r for r in rows if r["eligible"]]}, indent=2))


if __name__ == "__main__":
    main()
