"""Native physical/lexical join and diagnostic-only paired context transport."""
import ast
from collections import Counter, defaultdict
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
TOKEN = "df2a9c7a64ac4f32aaeeb64746369555"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_ids(ann):
    return list(map(int, ann["object_ids"])) if "object_ids" in ann else [int(ann["object_id"])]


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    import framework.dataset.scannetv2 as native
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    source = ROOT / "framework/dataset/scannetv2.py"
    annotations = DATA / "scanrefer/ScanRefer_train_new.json"
    graphs_path = DATA / "scanrefer/scene_graphs_new_train.json"
    taxonomy = DATA / "scannetv2-labels.combined.tsv"
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    for path, expected in (
        (source, "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"),
        (annotations, "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"),
        (graphs_path, "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"),
        (config, "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"),
    ):
        assert sha(path) == expected, str(path)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("context-coverage"))
    mapping = dataset.type2class
    other = mapping["others"]
    inverse = {value: name for name, value in mapping.items()}
    raw_classes = {}
    with taxonomy.open(newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            raw_classes[row["raw_category"]] = mapping.get(row["nyu40class"], other)
    tree = ast.parse(source.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "ScanNetDataset_sample_graph_edge")
    getter = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__getitem__")
    word_loop = next(n for n in ast.walk(getter) if isinstance(n, ast.For)
                     and isinstance(n.target, ast.Name) and n.target.id == "word")
    lexical = ast.FunctionDef(
        name="original_classes",
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="self"), ast.arg(arg="lang_utterance")],
                           kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=ast.parse("context_label = set()").body + [copy.deepcopy(word_loop)]
        + ast.parse("return context_label").body, decorator_list=[])
    scope = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[lexical], type_ignores=[])),
                 str(source), "exec"), scope)
    original_classes = scope["original_classes"]
    controls = {"present": sorted(original_classes(dataset, "a chair . not mentioned")),
                "absent": sorted(original_classes(dataset, "an unnamed object . not mentioned"))}
    assert controls == {"present": [mapping["chair"]], "absent": []}
    anns = json.loads(annotations.read_text())
    graphs = json.loads(graphs_path.read_text())
    by_scene = defaultdict(lambda: defaultdict(list))
    for ann in anns:
        for oid in object_ids(ann):
            by_scene[ann["scene_id"]][oid].append(ann)
    joined, geometry_hashes = [], []
    for number, (scene, targets) in enumerate(sorted(by_scene.items()), 1):
        path = DATA / f"scannetv2/train/{scene}_refer.pth"
        _, _, _, semantic, instance = torch.load(path, map_location="cpu", weights_only=False)
        semantic, instance = np.asarray(semantic), np.asarray(instance)
        geometry_hashes.append({"scene": scene, "sha256": sha(path)})
        labels, first = np.unique(instance, return_index=True)
        instance_classes = {}
        for oid, pos in zip(labels, first):
            value = int(semantic[pos])
            instance_classes[int(oid)] = (dataset.nyu40id2class.get(dataset.sem2nyu[value])
                                         if 0 <= value < len(dataset.sem2nyu) else None)
        for oid, rows in targets.items():
            physical = instance_classes.get(oid)
            for ann in rows:
                name = ann["object_name"].replace("_", " ")
                named = mapping.get(name, raw_classes.get(name))
                status = ("unmapped" if named is None or physical is None else
                          "others_inconclusive" if named == other or physical == other else
                          "agree" if named == physical else "mismatch")
                aid = int(ann["ann_id"])
                text = " ".join(graphs[scene][str(aid)]["utterance"].replace(",", " ,").split()) + " . not mentioned"
                licensed = original_classes(dataset, text)
                distractors = [i for i, c in instance_classes.items()
                               if c == physical and i not in object_ids(ann)]
                joined.append({"scene": scene, "ann_id": aid, "object_id": oid,
                               "name": name, "join_status": status, "physical_class": physical,
                               "class_name": inverse.get(physical),
                               "class_licensed": physical in licensed,
                               "same_class_distractor_ids": distractors,
                               "utterance": text})
        if number % 100 == 0 or number == len(by_scene):
            print(json.dumps({"scenes_done": number, "rows": len(joined)}), flush=True)
    assert len(anns) == len(joined) == 36665 and len(by_scene) == 562
    assert sum(map(len, by_scene.values())) == 7875
    eligible = [r for r in joined if r["join_status"] == "unmapped"
                and r["physical_class"] not in (None, other) and not r["class_licensed"]]
    group_lookup = {(a["scene_id"], int(a["ann_id"])): i
                    for i, group in enumerate(dataset.scene_inputs) for a in group}
    selected, seen = [], set()
    for row in sorted(eligible, key=lambda r: (r["scene"], r["ann_id"])):
        if row["scene"] in seen:
            continue
        selected.append({**row, "native_group": group_lookup[(row["scene"], row["ann_id"])]})
        seen.add(row["scene"])
        if len(selected) == 8:
            break
    oracle = {(r["scene"], r["ann_id"]): r["physical_class"] for r in eligible}
    namespace = dict(native.__dict__)
    namespace["coverage_oracle"] = oracle
    patched = copy.deepcopy(getter)

    class InsertOracle(ast.NodeTransformer):
        def visit_For(self, node):
            if isinstance(node.target, ast.Name) and node.target.id == "word":
                return [node] + ast.parse(
                    "coverage_class = coverage_oracle.get((scan_id, ann_id))\n"
                    "if coverage_class is not None:\n"
                    "    context_label.add(coverage_class)").body
            return self.generic_visit(node)

    patched = InsertOracle().visit(patched)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[patched], type_ignores=[])),
                 str(source), "exec"), namespace)
    counterfactual_getter = namespace["__getitem__"]

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

    def rng():
        return random.getstate(), np.random.get_state(), torch.get_rng_state()

    def restore(state):
        random.setstate(state[0])
        np.random.set_state(state[1])
        torch.set_rng_state(state[2])

    trials = []
    for trial in range(2):
        gorilla.set_random_seed(1999)
        rows = []
        for group in selected:
            before = rng()
            original = dataset[group["native_group"]]
            after = rng()
            restore(before)
            changed = counterfactual_getter(dataset, group["native_group"])
            restore(after)
            equal_noncontext = all(digest(original[i]) == digest(changed[i])
                                   for i in range(16) if i != 9)
            assert equal_noncontext
            exprs = []
            for e, aid in enumerate(original[0]):
                old, new = original[9][e], changed[9][e]
                diff = old != new
                target = torch.as_tensor(original[8][e])
                pure_target = old == 1
                assert torch.equal(old[pure_target], new[pure_target])
                exprs.append({"ann_id": int(aid), "eligible": (original[1], int(aid)) in oracle,
                              "changed_supports": int(diff.sum()), "target_gt_supports": int(target.sum()),
                              "changed_outside_target_gt": int((diff & ~target).sum()),
                              "old_new": sorted(Counter((float(a), float(b))
                                                       for a, b in zip(old[diff], new[diff])).items()),
                              "max_delta": float((new - old).abs().max()),
                              "pure_target_supports_preserved": int(pure_target.sum())})
            rows.append({"scene": group["scene"], "native_group": group["native_group"],
                         "noncontext_equal": equal_noncontext,
                         "original_digest": digest(original), "counterfactual_digest": digest(changed),
                         "expressions": exprs})
        trials.append(rows)
    assert trials[0] == trials[1]
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
        "source_sha256": sha(source), "annotations_sha256": sha(annotations),
        "graphs_sha256": sha(graphs_path), "taxonomy_sha256": sha(taxonomy),
        "script_sha256": sha(Path(__file__)), "config_sha256": sha(config),
        "geometry_hashes": geometry_hashes,
        "denominator": {"expressions": len(joined), "scenes": len(by_scene), "physical_targets": 7875},
        "join_status": dict(Counter(r["join_status"] for r in joined)),
        "unmapped_physical_classes": dict(Counter(str(r["physical_class"])
                                                for r in joined if r["join_status"] == "unmapped")),
        "eligible": {"expressions": len(eligible), "scenes": len({r["scene"] for r in eligible}),
                     "physical_targets": len({(r["scene"], r["object_id"]) for r in eligible}),
                     "with_same_class_distractors": sum(bool(r["same_class_distractor_ids"]) for r in eligible),
                     "class_counts": dict(Counter(r["class_name"] for r in eligible))},
        "controls": controls, "selected": selected, "trials": trials,
        "exact_repeat": trials[0] == trials[1],
        "scope": "TRAIN physical class is diagnostic oracle, not deployed; transport is not trained harm or efficacy.",
    }
    output = PIPE / "context_coverage_audit_20261013_0109.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "eligible": result["eligible"],
                      "changed_expressions": sum(e["changed_supports"] > 0 for r in trials[0] for e in r["expressions"]),
                      "exact_repeat": result["exact_repeat"]}), flush=True)


if __name__ == "__main__":
    main()
