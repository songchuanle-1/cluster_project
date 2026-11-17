"""Build the prediction-blind production catalog on authorized native data."""
import argparse
import ast
from collections import Counter
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    assert args.token == "1d59938f077948578e91e2cf34fc9d53"
    assert socket.gethostname() == "das" and os.environ["CUDA_VISIBLE_DEVICES"] == ""
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
    expected = {
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
        "config": "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"}
    assert {k: sha(p) for k, p in paths.items()} == expected
    cfg = gorilla.Config.fromfile(str(paths["config"]))
    cfg.data.train.data_root = str(DATA) + "/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("bps-catalog"))
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    counts = Counter()
    records = {}
    for ann in annotations:
        scene, aid = ann["scene_id"], str(int(ann["ann_id"]))
        graph = graphs[scene][aid]
        nodes = {n["node_id"]: n for n in graph["graph_node"]}
        tokens = graph["utterance"].split()
        events = {}
        for edge in graph["graph_edge"]:
            if 0 not in (edge["obj_idx"], edge["sub_idx"]):
                continue
            if "between" not in edge["relation"].lower():
                continue
            positions = tuple(i for i in edge.get("relation_idx", [])
                              if 0 <= i < len(tokens) and tokens[i].lower() == "between")
            other = edge["sub_idx"] if edge["obj_idx"] == 0 else edge["obj_idx"]
            if not positions:
                counts["edge_missing_actual_between_position"] += 1
                continue
            if other == 0 or nodes[other]["node_type"] != "Object":
                counts["edge_nonobject_reference"] += 1
                continue
            events.setdefault(positions, set()).add(other)
        counts["all_train_expressions"] += 1
        if not events:
            counts["no_stored_event_expressions"] += 1
            continue
        rows = []
        for positions, ref_ids in sorted(events.items()):
            refs = [{"node_id": nid, "lemma": nodes[nid]["lemma_head"].lower().strip(),
                     "category": dataset.type2class.get(nodes[nid]["lemma_head"].lower().strip())}
                    for nid in sorted(ref_ids)]
            rows.append({"positions": list(positions), "references": refs})
            counts["events"] += 1
            counts["single_node_events"] += len(refs) < 2
            counts["two_known_category_events"] += sum(r["category"] is not None for r in refs) >= 2
            counts["unknown_category_roles"] += sum(r["category"] is None for r in refs)
        objects = sorted(map(int, ann.get("object_ids", [ann.get("object_id")])))
        key = scene + "/" + aid
        assert key not in records
        records[key] = {"target_ids": objects, "events": rows}
        counts["stored_event_expressions"] += 1
    scenes = sorted({key.split("/")[0] for key in records})
    instances, raw_hashes, missing = {}, {}, []
    for index, scene in enumerate(scenes):
        path = DATA / ("scannetv2/train/" + scene + "_refer.pth")
        if not path.is_file():
            missing.append(scene)
            continue
        raw_hashes[scene] = sha(path)
        _, _, _, semantic, instance = torch.load(path, map_location="cpu", weights_only=False)
        semantic, instance = map(np.asarray, (semantic, instance))
        table = {}
        for oid in np.unique(instance):
            if oid < 0:
                continue
            labels = semantic[instance == oid]
            labels = labels[labels >= 0].astype(int)
            category = None
            if len(labels):
                raw = int(np.bincount(labels).argmax())
                if raw < len(dataset.sem2nyu):
                    category = dataset.nyu40id2class.get(dataset.sem2nyu[raw])
            table[str(int(oid))] = category
            counts["native_instances"] += 1
            counts["unknown_instance_categories"] += category is None
        instances[scene] = table
        if index % 50 == 0:
            print(json.dumps({"completed_scenes": index + 1, "total": len(scenes)}), flush=True)
    assert counts["all_train_expressions"] == 36665
    catalog = {"schema_version": 1, "tick_token": args.token,
               "observed_at": datetime.now(timezone.utc).isoformat(),
               "records": records, "instances": instances, "raw_scene_sha256": raw_hashes,
               "missing_native_scenes": missing, "counts": dict(counts),
               "source_sha256": expected, "type2class": dataset.type2class,
               "sem2nyu": dataset.sem2nyu, "script_sha256": sha(Path(__file__)),
               "scope": "TRAIN-only candidate-category catalog, not true reference labels."}
    output = PIPE / ("bps_catalog_" + args.token + ".json")
    with output.open("x") as stream:
        json.dump(catalog, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "counts": dict(counts), "native_scenes": len(instances),
                      "missing_scenes": len(missing)}), flush=True)


if __name__ == "__main__":
    main()
