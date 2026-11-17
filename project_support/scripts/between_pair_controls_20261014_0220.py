"""Actual support-gap symmetry, witness identity and duplicate controls."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket

PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")
DATA = Path("/data3/songcl/data/data_cluster")
TOKEN = "66fa1e81aec94d5eb10265ea533669ac"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gap(a, b, point, np):
    delta = b.mean(0) - a.mean(0)
    norm = float(np.linalg.norm(delta))
    if norm == 0:
        return {"status": "zero_center_distance", "value": None}
    direction = delta / norm
    lower, upper = float((a @ direction).max()), float((b @ direction).min())
    if lower >= upper:
        return {"status": "support_intervals_overlap", "value": None}
    value = float(point @ direction)
    return {"status": "positive_gap",
            "value": min(value - lower, upper - value) / (upper - lower),
            "inside": lower < value < upper}


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    import numpy as np
    import torch
    torch.set_num_threads(1)
    a = np.array([[-2., 0, 0], [-1, 0, 0]])
    b = np.array([[1., 0, 0], [2, 0, 0]])
    good = gap(a, b, np.zeros(3), np)
    bad = gap(a, b, np.array([3., 0, 0]), np)
    assert good["inside"] and not bad["inside"]
    assert good == gap(b, a, np.zeros(3), np)
    assert gap(a, a, np.zeros(3), np)["status"] == "zero_center_distance"
    overlap = gap(np.array([[-2., 0, 0], [1., 0, 0]]),
                  np.array([[-1., 0, 0], [2., 0, 0]]), np.zeros(3), np)
    assert overlap["status"] == "support_intervals_overlap"
    rotation = np.array([[0., -1, 0], [1., 0, 0], [0., 0, 1.]])
    translation = np.array([3., -5, 2])
    assert gap(a @ rotation + translation, b @ rotation + translation,
               translation, np) == good
    results = {}
    for kind, prefix in (("initial", "between_pair_inventory_"),
                         ("typed", "between_pair_typed_inventory_")):
        path = PIPE / (prefix + TOKEN + ".json")
        if not path.is_file():
            continue
        result = json.loads(path.read_text())
        if kind == "initial":
            assert sha(path) == "70f066262d8c9a62eaa3288030a31ae0d383dcbb20939a2a396698bee08b38e3"
        rows, counts = [], Counter()
        for case in result["geometry"]:
            if "ann_id" not in case:
                counts["missing_scene_geometry"] += 1
                continue
            scene_file = DATA / ("scannetv2/train/" + case["scene"] + "_refer.pth")
            assert sha(scene_file) == case["geometry_sha256"]
            xyz, _, _, _, instance = torch.load(scene_file, map_location="cpu", weights_only=False)
            xyz, instance = np.asarray(xyz).astype(np.float64), np.asarray(instance)
            supports = {int(oid): xyz[instance == oid] for oid in np.unique(instance) if oid >= 0}
            metadata = next(row for row in result["stored_between_records"]
                            if row["scene"] == case["scene"] and row["ann_id"] == case["ann_id"])
            target = supports[metadata["target_ids"][0]].mean(0)
            references = {node["node_id"]: node for node in case["references"]}
            seen_role_values = {}
            for pair in case["pairs"]:
                if pair["a"] == pair["b"]:
                    assert gap(supports[pair["a"]], supports[pair["b"]], target, np)["status"] == "zero_center_distance"
                    counts["duplicate_witness_invalid"] += 1
                    continue
                readout = gap(supports[pair["a"]], supports[pair["b"]], target, np)
                reverse = gap(supports[pair["b"]], supports[pair["a"]], target, np)
                assert readout["status"] == reverse["status"]
                reverse_error = abs(readout["value"] - reverse["value"]) if readout["value"] is not None else 0
                assert reverse_error <= 1e-6
                rotated = gap(supports[pair["a"]] @ rotation + translation,
                              supports[pair["b"]] @ rotation + translation,
                              target @ rotation + translation, np)
                assert readout["status"] == rotated["status"]
                rotate_error = abs(readout["value"] - rotated["value"]) if readout["value"] is not None else 0
                assert rotate_error <= 1e-6
                assert readout == gap(supports[pair["a"]], supports[pair["b"]], target, np)
                counts[readout["status"]] += 1
                if readout["value"] is not None:
                    key = (pair["left_node"], pair["right_node"])
                    seen_role_values.setdefault(key, []).append(readout["value"])
                    counts["target_in_gap"] += readout["inside"]
                rows.append({
                    "scene": case["scene"], "ann_id": case["ann_id"], "topology": case["topology"],
                    "left_node": pair["left_node"], "right_node": pair["right_node"],
                    "a": pair["a"], "b": pair["b"], "readout": readout,
                    "pair_reversal_error": reverse_error, "rigid_transform_error": rotate_error})
            for values in seen_role_values.values():
                counts["role_pairs_with_alternative_physical_witnesses"] += len(values) > 1
                counts["role_pairs_with_membership_separation"] += min(values) <= 0 < max(values)
                counts["role_pairs_with_continuous_readout_separation"] += max(values) - min(values) > 1e-6
        results[kind] = {"inventory_sha256": sha(path), "counts": dict(counts), "rows": rows}
    output = PIPE / ("between_pair_controls_" + TOKEN + ".json")
    record = {"tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
              "fixtures": {"inside": good, "outside": bad, "overlap": overlap,
                           "duplicate_invalid": True, "rigid_transform_exact": True},
              "cohorts": results, "cpu_only": True, "optimizer_steps": 0,
              "script_sha256": sha(Path(__file__)),
              "scope": "Native geometry operator controls only. Unknown true reference IDs, slab insufficiency, new model/backward/resources/novelty and trained efficacy are not resolved."}
    with output.open("x") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "cohorts": {name: row["counts"] for name, row in results.items()}}), flush=True)


if __name__ == "__main__":
    main()
