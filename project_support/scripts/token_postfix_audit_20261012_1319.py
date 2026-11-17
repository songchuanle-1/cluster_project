"""Full native TRAIN supervision-prefix token identity under original postfix."""
from collections import Counter
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
SUFFIX = " . not mentioned"


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
    from framework.dataset.scannetv2 import ScanNetDataset_sample_graph_edge
    torch.set_num_threads(1)
    paths = {
        "dataset": ROOT / "framework/dataset/scannetv2.py",
        "manifest": PIPE / "point_detail_population_20261009/result.manifest.json",
        "graphs": DATA / "scanrefer/scene_graphs_new_train.json",
        "annotations": DATA / "scanrefer/ScanRefer_train_new.json",
    }
    expected = {
        "dataset": "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d",
        "manifest": "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932",
        "graphs": "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08",
        "annotations": "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d",
    }
    hashes = {key: sha(path) for key, path in paths.items()}
    assert hashes == expected
    annotations = json.loads(paths["annotations"].read_text())
    graphs = json.loads(paths["graphs"].read_text())
    manifest = json.loads(paths["manifest"].read_text())
    tokenizer = RobertaTokenizerFast.from_pretrained(str(DATA / "roberta-base"),
                                                    local_files_only=True)
    counts, changed = Counter(), []
    for start in range(0, len(annotations), 256):
        rows = annotations[start:start + 256]
        texts = [canonical(graphs[a["scene_id"]][str(a["ann_id"])]["utterance"])
                 for a in rows]
        base = tokenizer(texts, return_offsets_mapping=True)
        model = tokenizer([t + SUFFIX for t in texts], return_offsets_mapping=True)
        for i, ann in enumerate(rows):
            ids, offsets = base["input_ids"][i][:-1], base["offset_mapping"][i][:-1]
            model_ids = model["input_ids"][i][:len(ids)]
            model_offsets = model["offset_mapping"][i][:len(ids)]
            id_drift, offset_drift = ids != model_ids, offsets != model_offsets
            counts["annotations"] += 1
            counts["token_id_drift"] += int(id_drift)
            counts["offset_drift"] += int(offset_drift)
            if id_drift or offset_drift:
                changed.append({"scene": ann["scene_id"], "ann_id": ann["ann_id"],
                                "caption": texts[i], "id_drift": id_drift,
                                "offset_drift": offset_drift})
    text = "the chair beside the table"
    base = tokenizer(text, return_offsets_mapping=True)
    native = tokenizer(text + SUFFIX, return_offsets_mapping=True)
    wrong = tokenizer("wrong " + text + SUFFIX, return_offsets_mapping=True)
    count = len(base["input_ids"]) - 1
    controls = {
        "native_identity": base["input_ids"][:-1] == native["input_ids"][:count],
        "wrong_prefix_detected": base["input_ids"][:-1] != wrong["input_ids"][:count],
        "wrong_offsets_detected": base["offset_mapping"][:-1] != wrong["offset_mapping"][:count],
        "eos_is_not_caption_supervision": base["input_ids"][-1] == tokenizer.eos_token_id,
    }
    assert all(controls.values())
    dataset = ScanNetDataset_sample_graph_edge.__new__(ScanNetDataset_sample_graph_edge)
    dataset.tokenizer = tokenizer
    frozen, role_counts = [], Counter()
    for scene in manifest:
        for ann in scene["annotations"]:
            aid = str(ann["ann_id"])
            graph = graphs[scene["scene"]][aid]
            caption = canonical(graph["utterance"])
            before = tokenizer(caption, return_offsets_mapping=True)
            after = tokenizer(caption + SUFFIX, return_offsets_mapping=True)
            maps = dataset._get_token_positive_map_by_parse(graph, None)
            record = {"scene": scene["scene"], "ann_id": int(aid), "roles": []}
            for name, role_map in zip(
                    ("target", "modifier", "pronoun", "other_entity", "auxiliary", "relation"),
                    maps[1:]):
                active = np.unique(np.where(role_map > 0)[1]).tolist()
                role_counts["roles"] += 1
                role_counts["empty_roles"] += int(not active)
                drift, eos, out_of_range = [], [], []
                for index in active:
                    if index >= len(before["input_ids"]) or index >= len(after["input_ids"]):
                        out_of_range.append(index)
                        continue
                    if before["input_ids"][index] == tokenizer.eos_token_id:
                        eos.append(index)
                    if (before["input_ids"][index] != after["input_ids"][index]
                            or before["offset_mapping"][index] != after["offset_mapping"][index]):
                        drift.append(index)
                role_counts["active_indices"] += len(active)
                role_counts["drift_indices"] += len(drift)
                role_counts["eos_indices"] += len(eos)
                role_counts["out_of_range_indices"] += len(out_of_range)
                record["roles"].append({"role": name, "active": active, "drift": drift,
                                        "eos": eos, "out_of_range": out_of_range})
            frozen.append(record)
    assert len(frozen) == 128
    result = {
        "contract": "native_caption_postfix_token_identity_v1",
        "tick_token": "8e65b0e186784f1ca037a3d81231f738",
        "observed_at": datetime.now(timezone.utc).isoformat(), "cpu_only": True,
        "counts": dict(counts), "changed_rows": changed,
        "controls": controls, "frozen_expressions": len(frozen),
        "native_role_counts": dict(role_counts), "frozen_rows": frozen,
        "suffix": SUFFIX, "input_hashes": hashes, "script_sha256": sha(Path(__file__)),
        "scope": "Caption postfix token identity, not all parser correctness, full-model backward/resources/efficacy.",
    }
    output = PIPE / "token_postfix_audit_20261012_1319.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"counts": dict(counts), "native_role_counts": dict(role_counts),
                      "controls": controls, "changed_examples": changed[:3],
                      "output_sha256": sha(output)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
