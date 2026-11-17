"""Original native partition and collate contracts for short language groups."""
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
TOKEN = "df2a9c7a64ac4f32aaeeb64746369555"


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
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    for path, expected in (
        (source, "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"),
        (annotations, "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"),
        (config, "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"),
    ):
        assert sha(path) == expected
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("short-group"))
    anns = json.loads(annotations.read_text())
    original_keys = [(a["scene_id"], int(a["ann_id"])) for a in dataset.scanrefer]
    flattened = [(a["scene_id"], int(a["ann_id"])) for group in dataset.scene_inputs for a in group]
    assert len(anns) == 36665
    partition = {
        "annotations": len(anns), "groups": len(dataset.scene_inputs),
        "group_length_counts": dict(Counter(len(g) for g in dataset.scene_inputs)),
        "missing_keys": len(set(original_keys) - set(flattened)),
        "extra_keys": len(set(flattened) - set(original_keys)),
        "duplicate_keys": sum(n - 1 for n in Counter(flattened).values() if n > 1),
        "cross_scene_groups": sum(len({a["scene_id"] for a in g}) != 1 for g in dataset.scene_inputs),
        "original_order_equal": original_keys == flattened,
    }
    selected = []
    for length in sorted(set(map(len, dataset.scene_inputs))):
        indices = [i for i, group in enumerate(dataset.scene_inputs) if len(group) == length][:2]
        for i in indices:
            selected.append({"native_group": i, "length": length,
                             "scene": dataset.scene_inputs[i][0]["scene_id"],
                             "ann_ids": [int(a["ann_id"]) for a in dataset.scene_inputs[i]]})
    assert len(selected) <= 8 and len(selected) % 2 == 0

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

    trials = []
    for trial in range(2):
        gorilla.set_random_seed(1999)
        fetched = [dataset[g["native_group"]] for g in selected]
        rows = []
        for start in range(0, len(fetched), 2):
            for reverse in (False, True):
                pair = fetched[start:start + 2]
                if reverse:
                    pair = pair[::-1]
                batch = dataset.collate_fn(pair)
                expected_ids = [aid for item in pair for aid in item[0]]
                expected_lengths = [len(item[0]) for item in pair]
                failures = []
                def check(name, condition):
                    if not condition:
                        failures.append(name)
                check("ann_ids", batch["ann_ids"] == expected_ids)
                check("scan_ids", batch["scan_ids"] == [item[1] for item in pair])
                check("scenes_len", batch["scenes_len"].tolist() == expected_lengths)
                fields = {"object_idss": 6, "gt_pmasks": 7, "gt_spmasks": 8,
                          "sp_ref_masks": 9, "meta_datas": 12, "dense_maps": 13,
                          "view_dependents": 14}
                for name, idx in fields.items():
                    expected = [v for item in pair for v in item[idx]]
                    check(name + "_count", len(batch[name]) == len(expected_ids))
                    check(name + "_identity", digest(batch[name]) == digest(expected))
                texts = [text for item in pair for text in item[10]]
                tokens = dataset.tokenizer.batch_encode_plus(texts, padding="longest", return_tensors="pt")
                check("lang_tokenss", torch.equal(batch["lang_tokenss"], tokens["input_ids"]))
                check("lang_masks", torch.equal(batch["lang_masks"], tokens["attention_mask"]))
                check("lang_count", batch["lang_tokenss"].shape[0] == len(expected_ids))
                check("geometry_count", len(batch["batch_offsets"]) == len(pair) + 1)
                check("instance_label_count", len(batch["sp_ins_labels"]) == len(pair))
                expanded_scene_ids = [item[1] for item in pair for _ in item[0]]
                fixed4_scene_ids = [item[1] for item in pair for _ in range(4)]
                wrong_fixed4_detected = expanded_scene_ids != fixed4_scene_ids
                rows.append({"groups": [selected[start + (1 - j if reverse else j)]["native_group"] for j in range(2)],
                             "reverse_pair": reverse, "lengths": expected_lengths,
                             "expressions": len(expected_ids), "failure_count": len(failures),
                             "failures": failures, "fixed4_negative_control_detected": wrong_fixed4_detected,
                             "native_batch_digest": digest(batch)})
        trials.append({"getter_digests": [digest(item) for item in fetched], "collations": rows})
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
        "script_sha256": sha(Path(__file__)), "source_sha256": sha(source),
        "annotations_sha256": sha(annotations), "config_sha256": sha(config),
        "partition": partition, "selected": selected, "trials": trials,
        "exact_repeat": trials[0] == trials[1],
        "collation_failures": sum(r["failure_count"] for r in trials[0]["collations"]),
        "short_collations": sum(any(n < 4 for n in r["lengths"]) for r in trials[0]["collations"]),
        "short_negative_control_detected": sum(r["fixed4_negative_control_detected"] for r in trials[0]["collations"]),
        "scope": "Original loss-input partition/collate only; no GPU FPS, expansion, decoder or whole-model backward certification.",
    }
    output = PIPE / "short_group_audit_20261013_0109.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "partition": partition, "selected_expressions": sum(g["length"] for g in selected),
                      "collation_failures": result["collation_failures"],
                      "short_negative_control_detected": result["short_negative_control_detected"],
                      "exact_repeat": result["exact_repeat"]}), flush=True)


if __name__ == "__main__":
    main()
