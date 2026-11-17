"""Prediction-blind native annotation cardinality audit, remote CPU only."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def targets(row):
    values = row["object_ids"] if "object_ids" in row else [row["object_id"]]
    if not isinstance(values, list):
        raise ValueError("Native object_ids must be a list")
    return tuple(int(value) for value in values)


def main():
    assert socket.gethostname() == "das"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    paths = {
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "manifest": PIPE / "point_detail_population_20261009/result.manifest.json",
        "dataset": ROOT / "framework/dataset/scannetv2.py",
    }
    expected = {
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "manifest": "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932",
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
    }
    hashes = {key: sha(path) for key, path in paths.items()}
    assert hashes == expected
    annotations = json.loads(paths["annotations"].read_text())
    counts, cardinalities, examples = Counter(), Counter(), []
    by_key = {}
    for row in annotations:
        key = (row["scene_id"], int(row["ann_id"]))
        assert key not in by_key
        try:
            ids = targets(row)
        except (KeyError, TypeError, ValueError) as error:
            counts["malformed_or_missing"] += 1
            examples.append({"scene": key[0], "ann_id": key[1],
                             "error": type(error).__name__})
            continue
        by_key[key] = ids
        counts["explicit_plural_field" if "object_ids" in row else "singular_fallback"] += 1
        cardinalities[str(len(set(ids)))] += 1
        counts["duplicate_ids"] += int(len(ids) != len(set(ids)))
        counts["singleton_projection_equal"] += int(len(ids) == 1 and ids == (ids[0],))
        if len(set(ids)) != 1:
            examples.append({"scene": key[0], "ann_id": key[1], "object_ids": ids})
    manifest = json.loads(paths["manifest"].read_text())
    frozen = Counter()
    for scene in manifest:
        for row in scene["annotations"]:
            ids = by_key[(scene["scene"], int(row["ann_id"]))]
            assert sorted(ids) == sorted(map(int, row["object_ids"]))
            frozen[str(len(set(ids)))] += 1
    controls = {
        "singular_fallback": targets({"object_id": "17"}) == (17,),
        "explicit_singleton": targets({"object_ids": [17]}) == (17,),
        "explicit_plural_detected": len(set(targets({"object_ids": [17, 23]}))) == 2,
        "explicit_field_precedence": targets({"object_id": 17, "object_ids": [23]}) == (23,),
    }
    assert all(controls.values())
    result = {
        "contract": "native_target_cardinality_v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True,
        "tick_token": "544cb1c4187542cd9ebe69d68351bd98",
        "annotation_count": len(annotations), "counts": dict(counts),
        "target_cardinality": dict(cardinalities), "frozen_cardinality": dict(frozen),
        "controls": controls, "non_singleton_or_unknown_examples": examples,
        "input_hashes": hashes, "script_sha256": sha(Path(__file__)),
        "scope": "Dataset target-set schema, not trained efficacy or global route exhaustion.",
    }
    output = PIPE / "target_cardinality_audit_20261012_0910.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"annotations": len(annotations), "counts": dict(counts),
                      "cardinality": dict(cardinalities), "frozen": dict(frozen),
                      "controls": controls, "output_sha256": sha(output)}), flush=True)


if __name__ == "__main__":
    main()
