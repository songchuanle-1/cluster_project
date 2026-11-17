"""Registered original-mapper sign and multi-span tests on remote TRAIN."""
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
TOKEN = "607238b6eece484ca713e5f5c6b04356"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert socket.gethostname() == "das"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from framework.dataset.scannetv2 import get_positive_map
    torch.set_num_threads(1)
    paths = {
        "source": ROOT / "framework/dataset/scannetv2.py",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "config": PIPE / "majority_erasure_original_config_20261012_0910.yaml",
    }
    expected = {
        "source": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "config": "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a",
    }
    for name, path in paths.items():
        assert sha(path) == expected[name], name
    cfg = gorilla.Config.fromfile(str(paths["config"]))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("relation-multispan"))
    mapper = dataset._get_token_positive_map_by_parse

    def node(nid, spans, rel=None):
        return {"node_id": nid, "node_type": "Object", "target_char_span": spans,
                "mod_char_span": [], "pron_char_span": [], "rel_char_span": rel or []}

    graph = {
        "utterance": "a chair beside a table and the chair",
        "graph_node": [node(0, [[2, 7], [30, 35]], [[8, 14]]),
                       node(1, [[17, 22]])],
        "graph_edge": [],
    }
    overlap_graph = copy.deepcopy(graph)
    overlap_graph["graph_node"][1]["target_char_span"] = [[8, 14]]
    control_map = mapper(graph, None)
    overlap_map = mapper(overlap_graph, None)
    encoded = dataset.tokenizer.batch_encode_plus(
        [graph["utterance"]], padding="longest", return_tensors="pt")
    separate = get_positive_map(encoded, np.asarray([[2, 7], [30, 35]]))
    control_later = np.flatnonzero((separate[1] > 0) & (separate[0] == 0)).tolist()
    controls = {
        "relation_disjoint": np.flatnonzero((control_map[6][0] > 0) &
                                           (control_map[4][0] > 0)).tolist(),
        "relation_deliberate_overlap": np.flatnonzero((overlap_map[6][0] > 0) &
                                                     (overlap_map[4][0] > 0)).tolist(),
        "root_two_span_tokens": np.flatnonzero(control_map[1][0] > 0).tolist(),
        "later_only_tokens": control_later,
        "broken_first_only_omissions": control_later,
        "native_later_omissions": [i for i in control_later if control_map[1][0][i] == 0],
    }
    assert not controls["relation_disjoint"]
    assert controls["relation_deliberate_overlap"]
    assert control_later and not controls["native_later_omissions"]
    assert np.array_equal(separate.sum(axis=0), control_map[1][0])
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    assert len(annotations) == 36665
    counts = Counter()
    overlap_cases, omitted_cases = [], []
    multi_examples = []
    dig = hashlib.sha256()
    for number, ann in enumerate(annotations, 1):
        scene, aid = ann["scene_id"], str(ann["ann_id"])
        original = graphs[scene][aid]
        maps = mapper(original, None)
        relation, other = maps[6][0] > 0, maps[4][0] > 0
        intersection = np.flatnonzero(relation & other).tolist()
        counts["expressions"] += 1
        counts["relation_nonempty"] += bool(relation.any())
        counts["other_nonempty"] += bool(other.any())
        counts["relation_other_overlap_expressions"] += bool(intersection)
        counts["relation_other_overlap_tokens"] += len(intersection)
        if intersection:
            overlap_cases.append({"scene": scene, "ann_id": int(aid),
                                  "tokens": intersection, "utterance": original["utterance"]})
        spans = original["graph_node"][0]["target_char_span"]
        if len(spans) > 1:
            counts["multi_root_span_expressions"] += 1
            caption = " ".join(original["utterance"].replace(",", " ,").split())
            encoded = dataset.tokenizer.batch_encode_plus(
                [caption], padding="longest", return_tensors="pt")
            separate = get_positive_map(encoded, np.asarray(spans))
            total = separate.sum(axis=0)
            later = (separate[1:].sum(axis=0) > 0) & (separate[0] == 0)
            omitted = np.flatnonzero((total > 0) & (maps[1][0] == 0)).tolist()
            counts["multi_root_with_later_only_tokens"] += bool(later.any())
            counts["later_only_tokens"] += int(later.sum())
            counts["root_span_union_omission_expressions"] += bool(omitted)
            counts["root_span_union_omission_tokens"] += len(omitted)
            counts["root_span_value_mismatch_expressions"] += not np.array_equal(total, maps[1][0])
            row = {"scene": scene, "ann_id": int(aid), "spans": spans,
                   "later_tokens": np.flatnonzero(later).tolist(), "omitted": omitted}
            if omitted or not np.array_equal(total, maps[1][0]):
                omitted_cases.append(row)
            if len(multi_examples) < 8:
                multi_examples.append(row)
        dig.update(f"{scene}:{aid};".encode())
        for index in (1, 4, 6):
            dig.update(np.ascontiguousarray(maps[index][0]).tobytes())
        if number % 5000 == 0 or number == len(annotations):
            print(json.dumps({"done": number, "counts": dict(counts)}), flush=True)
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
        "script_sha256": sha(Path(__file__)), "inputs": expected,
        "counts": dict(counts), "scene_count": len({a["scene_id"] for a in annotations}),
        "controls": controls, "relation_overlap_cases": overlap_cases,
        "root_span_omitted_cases": omitted_cases, "multi_root_examples": multi_examples,
        "map_digest": dig.hexdigest(),
        "scope": "Original CPU mapper only; no native getter/model/FPS/gradient/resource/efficacy or parser completeness certificate.",
    }
    output = PIPE / "relation_multispan_audit_20261013_0707.json"
    assert not output.exists(), "Refuse overwrite"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "counts": result["counts"], "controls": controls}), flush=True)


if __name__ == "__main__":
    main()
