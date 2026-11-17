"""Original graph character coordinates versus native normalization, CPU only."""
from collections import Counter
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(text):
    return " ".join(text.replace(",", " ,").split())


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    from transformers import RobertaTokenizerFast
    from framework.dataset.scannetv2 import ScanNetDataset_sample_graph_edge, get_positive_map
    torch.set_num_threads(1)
    paths = {
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "manifest": PIPE / "point_detail_population_20261009/result.manifest.json",
        "dataset": ROOT / "framework/dataset/scannetv2.py",
    }
    expected = {
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "manifest": "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932",
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
    }
    hashes = {key: sha(path) for key, path in paths.items()}
    assert hashes == expected
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    manifest = json.loads(paths["manifest"].read_text())
    counts, changed, missing = Counter(), [], []
    for row in annotations:
        scene, aid = row["scene_id"], str(row["ann_id"])
        graph = graphs.get(scene, {}).get(aid)
        if graph is None:
            missing.append({"scene": scene, "ann_id": aid})
            counts["missing_graph"] += 1
            continue
        old, new = graph["utterance"], canonical(graph["utterance"])
        counts["annotations"] += 1
        counts["with_comma"] += int("," in old)
        if old == new:
            counts["already_canonical"] += 1
        else:
            counts["changed"] += 1
            changed.append({"scene": scene, "ann_id": aid, "original": old,
                            "canonical": new, "graph_node": graph["graph_node"]})
    tokenizer = RobertaTokenizerFast.from_pretrained(
        str(DATA / "roberta-base"), local_files_only=True)
    dataset = ScanNetDataset_sample_graph_edge.__new__(ScanNetDataset_sample_graph_edge)
    dataset.tokenizer = tokenizer
    raw = "a,b,c,d,e,f,chair"
    normalized = canonical(raw)
    encoded = tokenizer.batch_encode_plus([normalized], padding="longest", return_tensors="pt")
    stale_span = np.array([[raw.index("chair"), raw.index("chair") + len("chair")]])
    correct_span = np.array([[normalized.index("chair"), len(normalized)]])
    wrong_span = np.array([[normalized.index("a"), normalized.index("a") + 1]])
    stale = get_positive_map(encoded, stale_span)
    correct = get_positive_map(encoded, correct_span)
    wrong = get_positive_map(encoded, wrong_span)
    controls = {
        "raw": raw, "canonical": normalized,
        "stale_span": stale_span.tolist(), "correct_span": correct_span.tolist(),
        "stale_tokens": np.where(stale[0] > 0)[0].tolist(),
        "correct_tokens": np.where(correct[0] > 0)[0].tolist(),
        "stale_correct_maxdelta": float(np.abs(stale - correct).max()),
        "wrong_phrase_maxdelta": float(np.abs(wrong - correct).max()),
        "canonical_idempotent": canonical(normalized) == normalized,
    }
    assert controls["stale_correct_maxdelta"] > 0
    assert controls["wrong_phrase_maxdelta"] > 0
    assert controls["canonical_idempotent"]
    frozen_rows, maxdelta = [], 0.0
    for scene in manifest:
        for ann in scene["annotations"]:
            aid = str(ann["ann_id"])
            graph = graphs[scene["scene"]][aid]
            altered = copy.deepcopy(graph)
            altered["utterance"] = canonical(graph["utterance"])
            native = dataset._get_token_positive_map_by_parse(graph, None)
            normalized_maps = dataset._get_token_positive_map_by_parse(altered, None)
            deltas = [float(np.abs(a - b).max()) for a, b in zip(native, normalized_maps)]
            maxdelta = max(maxdelta, *deltas)
            frozen_rows.append({"scene": scene["scene"], "ann_id": int(aid),
                                "string_changed": graph["utterance"] != altered["utterance"],
                                "native_map_maxdelta": max(deltas)})
    assert len(frozen_rows) == 128
    result = {
        "contract": "native_caption_span_coordinates_v1",
        "tick_token": "63db8202cf55406f8f29e19f14229f70",
        "observed_at": datetime.now(timezone.utc).isoformat(), "cpu_only": True,
        "annotation_total": len(annotations), "counts": dict(counts),
        "missing": missing, "changed_rows": changed, "controls": controls,
        "frozen_expressions": len(frozen_rows), "frozen_rows": frozen_rows,
        "frozen_native_role_map_maxdelta": maxdelta, "input_hashes": hashes,
        "script_sha256": sha(Path(__file__)),
        "scope": "Actual canonical-string incidence and original role-map contract, not all parse errors/full-model repeat/backward/resources/efficacy.",
    }
    output = PIPE / "span_coordinate_audit_20261012_1108.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"counts": dict(counts), "controls": controls,
                      "changed_examples": changed[:3], "missing": missing[:3],
                      "frozen_native_role_map_maxdelta": maxdelta,
                      "output_sha256": sha(output)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
