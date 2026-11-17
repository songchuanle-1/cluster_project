"""Hash-bound original graph key and native caption preprocessing audit."""
import ast
from collections import defaultdict
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
TOKEN = "5d01839a3f8642658868200f877656f3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity_summary(rows):
    groups = defaultdict(list)
    for row in rows:
        ids = row.get("object_ids")
        if ids is None:
            ids = [int(row["object_id"])]
        groups[(str(row["scene_id"]), str(row["ann_id"]))].append(
            (tuple(map(int, ids)), tuple(row["token"])))
    duplicates = sum(len(v) > 1 for v in groups.values())
    target_collisions = sum(len({x[0] for x in v}) > 1 for v in groups.values())
    caption_collisions = sum(len({x[1] for x in v}) > 1 for v in groups.values())
    return groups, {"unique_keys": len(groups), "duplicate_keys": duplicates,
                    "distinct_target_collisions": target_collisions,
                    "distinct_caption_collisions": caption_collisions}


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    paths = {
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "dataset": ROOT / "framework/dataset/scannetv2.py",
    }
    hashes = {k: sha(p) for k, p in paths.items()}
    assert hashes == {
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
    }
    source = paths["dataset"].read_text()
    fn = next(n for n in ast.parse(source).body
              if isinstance(n, ast.FunctionDef) and n.name == "Scene_graph_parse")
    fn = copy.deepcopy(fn)
    prefix = []
    for node in fn.body:
        parser_call = any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                          and isinstance(x.func.value, ast.Name)
                          and x.func.value.id == "sng_parser" for x in ast.walk(node))
        if parser_call:
            break
        prefix.append(node)
    assert prefix and len(prefix) < len(fn.body)
    fn.body = prefix + [ast.Return(value=ast.Name(id="caption", ctx=ast.Load()))]
    namespace = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                 str(paths["dataset"]), "exec"), namespace)
    preprocess = namespace["Scene_graph_parse"]
    row = {"scene_id": "control", "ann_id": 1, "object_id": "17", "token": ["a", "chair"]}
    same = copy.deepcopy(row)
    other = {**row, "object_id": "23", "token": ["a", "table"]}
    _, identical_control = identity_summary([row, same])
    _, collision_control = identity_summary([row, other])
    assert identical_control["duplicate_keys"] == 1
    assert identical_control["distinct_target_collisions"] == 0
    assert collision_control["distinct_target_collisions"] == 1
    assert collision_control["distinct_caption_collisions"] == 1
    wrong_caption_detected = preprocess(" ".join(row["token"])) != preprocess(" ".join(other["token"]))
    assert wrong_caption_detected
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    _, summary = identity_summary(annotations)
    missing, mismatch, normalized_changed = [], [], 0
    for row in annotations:
        scene, aid = str(row["scene_id"]), str(row["ann_id"])
        graph = graphs.get(scene, {}).get(aid)
        if graph is None:
            missing.append({"scene": scene, "ann_id": aid})
            continue
        raw = " ".join(row["token"])
        expected = preprocess(raw)
        normalized_changed += raw != expected
        if expected != graph["utterance"]:
            mismatch.append({"scene": scene, "ann_id": aid,
                             "expected": expected, "actual": graph["utterance"]})
    assert len(annotations) == 36665
    result = {
        "contract": "native_graph_annotation_identity_v1", "tick_token": TOKEN,
        "observed_at": datetime.now(timezone.utc).isoformat(), "cpu_only": True,
        "hostname": socket.gethostname(), "expressions": len(annotations),
        **summary, "missing_graphs": len(missing), "caption_mismatches": len(mismatch),
        "native_preprocessing_changed": normalized_changed,
        "mismatch_rows": mismatch, "missing_rows": missing,
        "controls": {"identical": identical_control, "collision": collision_control,
                     "wrong_caption_detected": wrong_caption_detected},
        "source_hashes": hashes, "script_sha256": sha(Path(__file__)),
        "scope": "Key/lookup integrity only, not correctness of graph root or all parses.",
    }
    output = PIPE / "graph_identity_audit_20261012_1908.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "expressions", "unique_keys", "duplicate_keys", "distinct_target_collisions",
        "distinct_caption_collisions", "missing_graphs", "caption_mismatches",
        "native_preprocessing_changed")}), flush=True)
    print(json.dumps({"output_sha256": sha(output)}), flush=True)


if __name__ == "__main__":
    main()
