"""Native first-point context assignment prerequisite on annotated TRAIN instances."""
import ast
from collections import defaultdict
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
TOKEN = "612469e22d634f7a971797ff5bd0342e"


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
    torch.set_num_threads(1)
    source = ROOT / "framework/dataset/scannetv2.py"
    annotations = DATA / "scanrefer/ScanRefer_train_new.json"
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    assert sha(source) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    assert sha(annotations) == "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
    assert sha(config) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("semantic-order"))

    cls = next(n for n in ast.parse(source.read_text()).body
               if isinstance(n, ast.ClassDef) and n.name == "ScanNetDataset_sample_graph_edge")
    getter = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                  and n.name == "__getitem__")
    nodes = list(ast.walk(getter))
    initial = next(n for n in nodes if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "point_context_mask"
                           for t in n.targets))
    loop = next(n for n in nodes if isinstance(n, ast.For)
                and isinstance(n.target, ast.Name) and n.target.id == "i_instance")
    function = ast.FunctionDef(
        name="native_context", args=ast.arguments(
            posonlyargs=[], args=[ast.arg(arg=x) for x in (
                "self", "instance_label", "semantic_label", "context_label")],
            kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[initial, loop, ast.Return(value=ast.Name(id="point_context_mask", ctx=ast.Load()))],
        decorator_list=[])
    namespace = {"np": np}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
                 str(source), "exec"), namespace)
    native_context = namespace["native_context"]
    valid = [(s, dataset.nyu40id2class[n])
             for s, n in enumerate(dataset.sem2nyu) if n in dataset.nyu40ids
             and dataset.nyu40id2class[n] != dataset.type2class["others"]]
    s0, c0 = valid[0]
    s1, c1 = next((s, c) for s, c in valid if c != c0)
    ins = np.array([17, 17])
    uniform = native_context(dataset, ins, np.array([s0, s0]), {c0})
    mixed = native_context(dataset, ins, np.array([s0, s1]), {c0})
    mixed_reversed = native_context(dataset, ins, np.array([s1, s0]), {c0})
    assert np.array_equal(uniform, np.ones(2))
    assert np.array_equal(mixed, np.ones(2))
    assert np.array_equal(mixed_reversed, -np.ones(2))
    assert np.array_equal(uniform, native_context(
        dataset, ins[::-1], np.array([s0, s0])[::-1], {c0})[::-1])
    controls = {"uniform_identity": True, "uniform_reversal": True,
                "mixed_reversal_changed_points": int((mixed != mixed_reversed).sum()),
                "semantic_indices": [s0, s1], "native_classes": [c0, c1]}

    anns = json.loads(annotations.read_text())
    by_scene = defaultdict(lambda: defaultdict(list))
    for ann in anns:
        ids = ann.get("object_ids", [int(ann["object_id"])] if "object_id" in ann else None)
        assert ids is not None
        for oid in ids:
            by_scene[ann["scene_id"]][int(oid)].append(int(ann["ann_id"]))
    rows, inputs = [], []
    mixed_semantic = mixed_classes = changed = missing = physical = 0
    for number, (scene, targets) in enumerate(sorted(by_scene.items()), 1):
        path = DATA / f"scannetv2/train/{scene}_refer.pth"
        _, _, _, semantic, instance = torch.load(path, map_location="cpu", weights_only=False)
        semantic, instance = np.asarray(semantic), np.asarray(instance)
        inputs.append({"scene": scene, "sha256": sha(path)})
        order = np.argsort(instance, kind="stable")
        labels, starts, lengths = np.unique(instance[order], return_index=True, return_counts=True)
        groups = {int(label): order[start:start + length]
                  for label, start, length in zip(labels, starts, lengths)}
        for oid, ann_ids in targets.items():
            physical += 1
            idx = groups.get(oid)
            if idx is None:
                missing += 1
                rows.append({"scene": scene, "object_id": oid, "status": "missing_geometry"})
                continue
            sem = semantic[idx].astype(np.int64)
            values, counts = np.unique(sem, return_counts=True)
            mapped = []
            for value in values:
                if value < 0:
                    mapped.append(None)
                else:
                    assert value < len(dataset.sem2nyu)
                    nyu = dataset.sem2nyu[value]
                    mapped.append(dataset.nyu40id2class.get(nyu))
            if len(values) > 1:
                mixed_semantic += 1
            if len(set(mapped)) > 1:
                mixed_classes += 1
            if len(values) > 1:
                local_ins = np.full(len(sem), oid)
                context = set(dataset.type2class.values()) - {dataset.type2class["others"]}
                # Probe each actual mentioned category plus all native categories.
                sets = [{c} for c in set(mapped) if c is not None] + [context]
                max_delta = 0
                for selected in sets:
                    first = native_context(dataset, local_ins, sem, selected)
                    reverse = native_context(dataset, local_ins[::-1], sem[::-1], selected)[::-1]
                    max_delta = max(max_delta, int((first != reverse).sum()))
                changed += max_delta > 0
                rows.append({"scene": scene, "object_id": oid, "ann_ids": ann_ids,
                             "semantic_values": values.tolist(), "counts": counts.tolist(),
                             "native_classes": mapped, "reversal_changed_points": max_delta})
        if number % 50 == 0 or number == len(by_scene):
            print(json.dumps({"scenes_done": number, "physical_targets": physical,
                              "mixed_semantic": mixed_semantic, "changed": changed}), flush=True)
    assert len(anns) == 36665 and len(by_scene) == 562 and physical == 7875
    result = {
        "contract": "native_instance_semantic_firstpoint_order_v1", "tick_token": TOKEN,
        "observed_at": datetime.now(timezone.utc).isoformat(), "cpu_only": True,
        "hostname": socket.gethostname(), "expressions": len(anns),
        "scenes": len(by_scene), "physical_targets": physical,
        "missing_geometry": missing, "mixed_semantic_targets": mixed_semantic,
        "mixed_class_targets": mixed_classes, "reversal_changed_targets": changed,
        "controls": controls, "nonuniform_rows": rows, "inputs": inputs,
        "dataset_sha256": sha(source), "config_sha256": sha(config),
        "annotations_sha256": sha(annotations), "script_sha256": sha(Path(__file__)),
        "taxonomy_sha256": sha(DATA / "scannetv2-labels.combined.tsv"),
        "scope": "Raw annotated native TRAIN instances; not all context caption coverage or full-model backward.",
    }
    output = PIPE / "semantic_order_audit_20261012_1611.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "physical_targets", "missing_geometry", "mixed_semantic_targets",
        "mixed_class_targets", "reversal_changed_targets")}), flush=True)
    print(json.dumps({"output_sha256": sha(output)}), flush=True)


if __name__ == "__main__":
    main()
