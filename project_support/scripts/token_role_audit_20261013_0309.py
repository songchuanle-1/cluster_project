"""Two registered native TRAIN token-supervision diagnostics, CPU only."""
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
TOKEN = "3d7b538083db43b2932216472dedaa8c"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    source = ROOT / "framework/dataset/scannetv2.py"
    annotations = DATA / "scanrefer/ScanRefer_train_new.json"
    graph_path = DATA / "scanrefer/scene_graphs_new_train.json"
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    frozen_manifest = PIPE / "point_detail_population_20261009/result.manifest.json"
    for path, expected in (
        (source, "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"),
        (annotations, "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"),
        (graph_path, "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"),
        (config, "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"),
        (frozen_manifest, "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"),
    ):
        assert sha(path) == expected, str(path)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("token-role-audit"))
    anns = json.loads(annotations.read_text())
    graphs = json.loads(graph_path.read_text())
    assert len(anns) == 36665
    mapper = dataset._get_token_positive_map_by_parse

    def node(nid, spans):
        return {"node_id": nid, "node_type": "Object", "target_char_span": spans,
                "mod_char_span": [], "pron_char_span": [], "rel_char_span": []}

    distinct = {"utterance": "a chair beside a table",
                "graph_node": [node(0, [[2, 7]]), node(1, [[17, 22]])],
                "graph_edge": []}
    overlapping = copy.deepcopy(distinct)
    overlapping["graph_node"][1]["target_char_span"] = [[2, 7]]
    empty = copy.deepcopy(distinct)
    empty["graph_node"][0]["target_char_span"] = []
    out_of_range = copy.deepcopy(distinct)
    out_of_range["graph_node"][0]["target_char_span"] = [[100, 105]]

    def signature(graph):
        values = mapper(graph, None)
        main_indices = np.flatnonzero(values[1][0] > 0).tolist()
        other_indices = np.flatnonzero(values[4][0] > 0).tolist()
        return {"main": main_indices, "other": other_indices,
                "intersection": sorted(set(main_indices) & set(other_indices)),
                "empty_main": not main_indices}

    controls = {name: signature(g) for name, g in
                (("distinct", distinct), ("overlap", overlapping), ("empty", empty),
                 ("out_of_range", out_of_range))}
    assert not controls["distinct"]["empty_main"] and not controls["distinct"]["intersection"]
    assert controls["overlap"]["intersection"] == controls["distinct"]["main"]
    assert controls["empty"]["empty_main"] and controls["out_of_range"]["empty_main"]
    assert controls["distinct"]["other"] == controls["empty"]["other"]
    counts = Counter()
    collisions, omissions = [], []
    root_node_types = Counter()
    token_digest = hashlib.sha256()
    for n, ann in enumerate(anns, 1):
        scene, aid = ann["scene_id"], str(ann["ann_id"])
        graph = graphs[scene][aid]
        values = mapper(graph, None)
        main, other = values[1][0] > 0, values[4][0] > 0
        overlap = np.flatnonzero(main & other).tolist()
        is_empty = not bool(main.any())
        counts["expressions"] += 1
        counts["with_other_map"] += bool(other.any())
        counts["with_multiple_graph_nodes"] += len(graph["graph_node"]) > 1
        counts["overlap_expressions"] += bool(overlap)
        counts["overlap_tokens"] += len(overlap)
        counts["empty_main_expressions"] += is_empty
        root_node_types[str(graph["graph_node"][0].get("node_type"))] += 1
        token_digest.update(f"{scene}:{aid};".encode())
        for value in values[1:]:
            token_digest.update(np.ascontiguousarray(value[0]).tobytes())
        if overlap or is_empty:
            text = " ".join(graph["utterance"].replace(",", " ,").split())
            encoded = dataset.tokenizer(text, return_offsets_mapping=True)
            special = set(i for i, off in enumerate(encoded["offset_mapping"]) if off == (0, 0))
            record = {
                "scene": scene, "ann_id": int(aid),
                "object_ids": list(map(int, ann["object_ids"])) if "object_ids" in ann else [int(ann["object_id"])],
                "utterance": text, "intersection": overlap,
                "special_intersection": sorted(set(overlap) & special),
                "active_intersection": sorted(set(overlap) - special),
                "main_tokens": np.flatnonzero(main).tolist(),
                "other_tokens": np.flatnonzero(other).tolist(),
                "root": graph["graph_node"][0],
                "other_nodes": [g for g in graph["graph_node"] if g["node_id"] != 0 and g["node_type"] == "Object"],
                "modifier_tokens": np.flatnonzero(values[2][0] > 0).tolist(),
                "pronoun_tokens": np.flatnonzero(values[3][0] > 0).tolist(),
                "relation_tokens": np.flatnonzero(values[6][0] > 0).tolist(),
            }
            if overlap:
                collisions.append(record)
            if is_empty:
                omissions.append(record)
        if n % 5000 == 0 or n == len(anns):
            print(json.dumps({"done": n, "overlap": len(collisions),
                              "empty_main": len(omissions)}), flush=True)

    lookup = {(a["scene_id"], int(a["ann_id"])): i
              for i, group in enumerate(dataset.scene_inputs) for a in group}
    selections = {}
    for name, cases in (("overlap", collisions), ("empty_main", omissions)):
        chosen, seen = [], set()
        for r in sorted(cases, key=lambda r: (r["scene"], r["ann_id"])):
            if r["scene"] in seen:
                continue
            chosen.append({"scene": r["scene"], "trigger_ann_id": r["ann_id"],
                           "native_group": lookup[(r["scene"], r["ann_id"])]})
            seen.add(r["scene"])
            if len(chosen) == 8:
                break
        selections[name] = chosen
    groups = {r["native_group"]: r for rows in selections.values() for r in rows}
    capture_basis = "prediction-blind first positive per scene for each registered hypothesis"
    if not groups:
        groups = {r["native_group"]: r for r in json.loads(frozen_manifest.read_text())[:8]}
        capture_basis = "no real positives; first8unchanged frozen manifest groups as mapper/getter contract control"

    def digest(value):
        h = hashlib.sha256()
        def consume(item):
            if torch.is_tensor(item):
                consume(("tensor", str(item.dtype), tuple(item.shape)))
                h.update(item.detach().cpu().contiguous().numpy().tobytes())
            elif isinstance(item, np.ndarray):
                consume(("array", str(item.dtype), item.shape))
                h.update(item.tobytes())
            elif isinstance(item, dict):
                for key in sorted(item):
                    consume(key)
                    consume(item[key])
            elif isinstance(item, (tuple, list)):
                h.update(b"[")
                for child in item:
                    consume(child)
                h.update(b"]")
            else:
                h.update(repr(item).encode())
                h.update(b";")
        consume(value)
        return h.hexdigest()

    fields = ["tokens_positive", "positive_map", "modify_positive_map", "pron_positive_map",
              "other_entity_map", "auxi_entity_positive_map", "rel_positive_map"]
    trials = []
    for trial in range(2):
        gorilla.set_random_seed(1999)
        rows = []
        for index, group in sorted(groups.items()):
            item = dataset[index]
            failure_fields = []
            for e, aid in enumerate(item[0]):
                reference = mapper(graphs[item[1]][str(aid)], None)
                for name, value in zip(fields, reference):
                    if not torch.equal(item[13][e][name], torch.from_numpy(value).float()):
                        failure_fields.append({"ann_id": int(aid), "field": name})
            rows.append({"scene": item[1], "native_group": index,
                         "ann_ids": list(map(int, item[0])), "expressions": len(item[0]),
                         "native_all_output_digest": digest(item), "map_failures": failure_fields})
        trials.append(rows)
    assert trials[0] == trials[1]
    assert all(not r["map_failures"] for r in trials[0])
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
        "script_sha256": sha(Path(__file__)), "source_sha256": sha(source),
        "annotations_sha256": sha(annotations), "graphs_sha256": sha(graph_path),
        "config_sha256": sha(config), "frozen_manifest_sha256": sha(frozen_manifest),
        "counts": dict(counts), "scene_count": len({a["scene_id"] for a in anns}),
        "root_node_types": dict(root_node_types), "six_main_role_rows_digest": token_digest.hexdigest(),
        "controls": controls, "collisions": collisions, "omissions": omissions,
        "selected_by_hypothesis": selections, "capture_basis": capture_basis,
        "trials": trials, "native_capture_expressions": sum(r["expressions"] for r in trials[0]),
        "native_exact_repeat": trials[0] == trials[1],
        "scope": "Original map/getter transport only. Real overlap/omission does not establish parser error, loss conflict, whole-model backward or trained benefit.",
    }
    output = PIPE / "token_role_audit_20261013_0309.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "counts": result["counts"],
                      "native_capture_expressions": result["native_capture_expressions"],
                      "native_exact_repeat": result["native_exact_repeat"]}), flush=True)


if __name__ == "__main__":
    main()
