"""Two preregistered native TRAIN diagnostics; no production changes."""
import ast
from collections import defaultdict
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
TOKEN = "42f0e79c9e444f47808a5e16c9ea80d4"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ids(ann):
    return list(map(int, ann["object_ids"])) if "object_ids" in ann else [int(ann["object_id"])]


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import torch_scatter
    import gorilla
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    source = ROOT / "framework/dataset/scannetv2.py"
    annotations = DATA / "scanrefer/ScanRefer_train_new.json"
    taxonomy = DATA / "scannetv2-labels.combined.tsv"
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    manifest_path = PIPE / "point_detail_population_20261009/result.manifest.json"
    for path, expected in (
        (source, "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"),
        (annotations, "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"),
        (config, "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"),
        (manifest_path, "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"),
    ):
        assert sha(path) == expected
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("category-support"))
    anns = json.loads(annotations.read_text())
    manifest = json.loads(manifest_path.read_text())
    assert len(anns) == 36665 and len(manifest) == 32
    mapping = dataset.type2class
    other = mapping["others"]
    raw_classes = {}
    with taxonomy.open(newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            raw_classes[row["raw_category"]] = mapping.get(row["nyu40class"], other)
    by_scene = defaultdict(lambda: defaultdict(list))
    for ann in anns:
        for oid in ids(ann):
            by_scene[ann["scene_id"]][oid].append(ann)
    joined = []
    geometry_hashes = []
    for number, (scene, targets) in enumerate(sorted(by_scene.items()), 1):
        path = DATA / f"scannetv2/train/{scene}_refer.pth"
        _, _, _, semantic, instance = torch.load(path, map_location="cpu", weights_only=False)
        semantic, instance = np.asarray(semantic), np.asarray(instance)
        geometry_hashes.append({"scene": scene, "sha256": sha(path)})
        order = np.argsort(instance, kind="stable")
        labels, starts, lengths = np.unique(instance[order], return_index=True, return_counts=True)
        groups = {int(label): order[start:start + length]
                  for label, start, length in zip(labels, starts, lengths)}
        for oid, rows in targets.items():
            index = groups.get(oid)
            physical = None
            sem_values = []
            if index is not None:
                sem_values = np.unique(semantic[index]).astype(int).tolist()
                if len(sem_values) == 1 and 0 <= sem_values[0] < len(dataset.sem2nyu):
                    physical = dataset.nyu40id2class.get(dataset.sem2nyu[sem_values[0]])
            for ann in rows:
                name = ann["object_name"].replace("_", " ")
                named = mapping.get(name, raw_classes.get(name))
                status = ("missing_geometry" if index is None else
                          "unmapped" if named is None or physical is None else
                          "others_inconclusive" if named == other or physical == other else
                          "agree" if named == physical else "mismatch")
                joined.append({"scene": scene, "object_id": oid, "ann_id": int(ann["ann_id"]),
                               "name": name, "name_class": named, "physical_class": physical,
                               "semantic_values": sem_values, "status": status})
        if number % 100 == 0 or number == len(by_scene):
            print(json.dumps({"raw_scenes_done": number, "joined": len(joined)}), flush=True)
    assert len(by_scene) == 562 and sum(map(len, by_scene.values())) == 7875
    counts = {status: sum(row["status"] == status for row in joined)
              for status in ("missing_geometry", "unmapped", "others_inconclusive", "agree", "mismatch")}
    group_lookup = {(a["scene_id"], int(a["ann_id"])): i
                    for i, group in enumerate(dataset.scene_inputs) for a in group}
    selected, scenes = [], set()
    for row in sorted((r for r in joined if r["status"] == "mismatch"),
                      key=lambda r: (r["scene"], r["ann_id"])):
        if row["scene"] not in scenes:
            selected.append({"scene": row["scene"], "native_group": group_lookup[(row["scene"], row["ann_id"])]})
            scenes.add(row["scene"])
        if len(selected) == 8:
            break
    selection = "first comparable mismatch per scene" if selected else "first8unchanged frozen manifest groups"
    if not selected:
        selected = manifest[:8]
    selection_path = PIPE / "target_category_manifest_20261012_2308.json"
    assert not selection_path.exists()
    selection_path.write_text(json.dumps({"selection": selection, "groups": selected,
                                          "tick_token": TOKEN}, indent=2) + "\n")

    def digest(item):
        h = hashlib.sha256()
        def consume(value):
            if torch.is_tensor(value):
                consume(("tensor", str(value.dtype), tuple(value.shape)))
                h.update(value.detach().cpu().contiguous().numpy().tobytes())
            elif isinstance(value, np.ndarray):
                consume(("array", str(value.dtype), value.shape))
                h.update(value.tobytes())
            elif isinstance(value, dict):
                for key in sorted(value):
                    consume(key)
                    consume(value[key])
            elif isinstance(value, (tuple, list)):
                h.update(b"[")
                for child in value:
                    consume(child)
                h.update(b"]")
            else:
                h.update(repr(value).encode())
                h.update(b";")
        consume(item)
        return h.hexdigest()

    def rng():
        return random.getstate(), np.random.get_state(), torch.get_rng_state()
    def restore(state):
        random.setstate(state[0])
        np.random.set_state(state[1])
        torch.set_rng_state(state[2])
    metadata_trials = []
    for trial in range(2):
        gorilla.set_random_seed(1999)
        rows = []
        for group in selected:
            index = group["native_group"]
            before = rng()
            original = dataset[index]
            after = rng()
            saved = copy.deepcopy(dataset.scene_inputs[index])
            for ann in dataset.scene_inputs[index]:
                current = ann["object_name"].replace("_", " ")
                ann["object_name"] = "table" if current != "table" else "chair"
            assert dataset.scene_inputs[index] != saved
            restore(before)
            counterfactual = dataset[index]
            dataset.scene_inputs[index] = saved
            restore(after)
            rows.append({"scene": group["scene"], "native_group": index,
                         "expressions": len(original[0]), "all_outputs_equal": digest(original) == digest(counterfactual),
                         "original_digest": digest(original), "counterfactual_digest": digest(counterfactual)})
        metadata_trials.append(rows)
    assert metadata_trials[0] == metadata_trials[1]
    used_name = [n.lineno for n in ast.walk(ast.parse(source.read_text()))
                 if isinstance(n, ast.Constant) and n.value == "object_name"]
    common = {"tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
              "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
              "source_sha256": sha(source), "annotations_sha256": sha(annotations),
              "config_sha256": sha(config), "taxonomy_sha256": sha(taxonomy),
              "manifest_sha256": sha(manifest_path), "script_sha256": sha(Path(__file__))}
    category = {**common, "contract": "native_target_category_and_metadata_transport_v1",
                "expressions": len(anns), "joined_expression_targets": len(joined),
                "scenes": len(by_scene), "physical_targets": 7875, "join_counts": counts,
                "mismatch_rows": [r for r in joined if r["status"] == "mismatch"],
                "geometry_inputs": geometry_hashes, "annotation_name_source_lines": used_name,
                "native_rows": metadata_trials[0], "native_repeat_exact": True,
                "native_changed_groups": sum(not r["all_outputs_equal"] for r in metadata_trials[0]),
                "controls": {"identity_class": mapping["chair"] == mapping["chair"],
                             "distinct_class": mapping["chair"] != mapping["table"],
                             "others_excluded": True, "metadata_deliberately_changed": True},
                "selection_sha256": sha(selection_path),
                "scope": "TRAIN naming consistency and sampled direct metadata transport; not caption category/root correctness or model efficacy."}
    category_path = PIPE / "target_category_audit_20261012_2308.json"
    assert not category_path.exists()
    category_path.write_text(json.dumps(category, indent=2) + "\n")
    print(json.dumps({"category_counts": counts, "native_changed_groups": category["native_changed_groups"],
                      "result_sha256": sha(category_path)}), flush=True)

    gapped = torch.tensor([0, 2])
    values = torch.tensor([1., 3.])
    gap_mean = torch_scatter.scatter_mean(values, gapped, dim=0)
    compact = np.unique(gapped.numpy(), return_inverse=True)[1]
    compact_mean = torch_scatter.scatter_mean(values, torch.from_numpy(compact), dim=0)
    assert gap_mean.tolist() == [1., 0., 3.] and compact_mean.tolist() == [1., 3.]
    support_trials = []
    for trial in range(2):
        gorilla.set_random_seed(1999)
        rows, batches = [], []
        pair = []
        for number, group in enumerate(manifest, 1):
            item = dataset[group["native_group"]]
            assert item[1] == group["scene"]
            assignment = item[5].long()
            occupancy = torch.bincount(assignment, minlength=int(assignment.max()) + 1)
            support_count = len(occupancy)
            lengths = [len(item[11])] + [len(mask) for field in (8, 9) for mask in item[field]]
            assert all(length == support_count for length in lengths)
            rows.append({"scene": item[1], "native_group": group["native_group"],
                         "expressions": len(item[0]), "points": len(assignment),
                         "supports": support_count, "empty_ids": int((occupancy == 0).sum()),
                         "min_occupancy": int(occupancy.min()), "assignment_sha256": digest(assignment)})
            pair.append(item)
            if len(pair) == 2:
                batch = dataset.collate_fn(pair)
                keys = list(batch)
                key = next(k for k in keys if k in ("superpoints", "superpoint"))
                assigned = batch[key].long()
                occupied = torch.bincount(assigned, minlength=int(assigned.max()) + 1)
                batches.append({"scenes": [x[1] for x in pair], "empty_ids": int((occupied == 0).sum()),
                                "supports": len(occupied), "assignment_sha256": digest(assigned)})
                pair = []
            if number % 8 == 0:
                print(json.dumps({"support_trial": trial, "native_groups_done": number}), flush=True)
        assert not pair
        support_trials.append({"rows": rows, "batches": batches})
    assert support_trials[0] == support_trials[1]
    support = {**common, "observed_at": datetime.now(timezone.utc).isoformat(),
               "contract": "native_cropped_support_occupancy_v1", "native_groups": 32,
               "native_expressions": sum(r["expressions"] for r in support_trials[0]["rows"]),
               "native_repeat_exact": True, **support_trials[0],
               "total_empty_getter_ids": sum(r["empty_ids"] for r in support_trials[0]["rows"]),
               "total_empty_collated_ids": sum(r["empty_ids"] for r in support_trials[0]["batches"]),
               "controls": {"gapped_empty_rows": 1, "compacted_empty_rows": 0,
                            "gapped_mean": gap_mean.tolist(), "compacted_mean": compact_mean.tolist()},
               "scope": "Fixed32/128 native cropped supports and16consecutive-pair collations, not full model/backward or arbitrary crops."}
    support_path = PIPE / "support_compaction_audit_20261012_2308.json"
    assert not support_path.exists()
    support_path.write_text(json.dumps(support, indent=2) + "\n")
    print(json.dumps({"support_empty_getter": support["total_empty_getter_ids"],
                      "support_empty_collated": support["total_empty_collated_ids"],
                      "support_result_sha256": sha(support_path)}), flush=True)


if __name__ == "__main__":
    main()
