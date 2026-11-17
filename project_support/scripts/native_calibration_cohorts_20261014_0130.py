"""Prediction-blind supplemental and disjoint-scene calibration cohorts."""
import ast
import hashlib
import json
import os
from pathlib import Path

PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")
SOURCE = PIPE / "native_role_calibration_20261014_0115.py"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "0ad3570f4aaf40a4122f92287b4bb88a69a8d387ed5ea917af3c409231fab67b")
KIND = os.environ["CLUSTER_CALIBRATION_COHORT"]
assert KIND in ("supplement", "extension")


def choose_cohort(dataset, original):
    root = Path("/data3/songcl/Project/Cluster_project/Cluster")
    data = Path("/data3/songcl/data/data_cluster")
    audit_path = PIPE / "role_weight_audit_20261013_0908.json"
    assert hashlib.sha256(audit_path.read_bytes()).hexdigest() == (
        "48d7a2243257a0287f4669a98dbd80ca4fbb982faa1da79143d6e143d796b5df")
    audit = json.loads(audit_path.read_text())
    for name, path in (
        ("dataset", root / "framework/dataset/scannetv2.py"),
        ("annotations", data / "scanrefer/ScanRefer_train_new.json"),
        ("graphs", data / "scanrefer/scene_graphs_new_train.json"),
    ):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == audit["source_and_data_sha256"][name]
    frozen = {("scene0097_00", 13), ("scene0449_00", 36),
              ("scene0482_00", 39), ("scene0542_00", 41), ("scene0544_00", 17)}
    lookup = {(ann["scene_id"], int(ann["ann_id"])): group
              for group, annotations in enumerate(dataset.scene_inputs) for ann in annotations}
    selection = {}

    def add(scene, aid, family):
        group = lookup[(scene, aid)]
        assert group not in selection
        selection[group] = {
            "group": group, "scene": scene, "trigger_ann_ids": [aid],
            "ann_ids": [int(a["ann_id"]) for a in dataset.scene_inputs[group]],
            "families": [family]}

    if KIND == "supplement":
        for scene, aid in sorted(frozen):
            assert lookup[(scene, aid)] not in original
            add(scene, aid, "supplemental_main")
        metadata = {"requested_supplemental_cases": 5, "selected_cases": 5}
    else:
        import numpy as np
        excluded = {row["scene"] for row in original.values()} | {scene for scene, _ in frozen}
        annotations = json.loads((data / "scanrefer/ScanRefer_train_new.json").read_text())
        graphs = json.loads((data / "scanrefer/scene_graphs_new_train.json").read_text())
        half_mass = {}
        first_ann = {}
        mapper_reads = 0
        for ann in sorted(annotations, key=lambda a: (a["scene_id"], int(a["ann_id"]))):
            scene, aid = ann["scene_id"], int(ann["ann_id"])
            if scene in excluded:
                continue
            first_ann.setdefault(scene, aid)
            maps = dataset._get_token_positive_map_by_parse(graphs[scene][str(aid)], None)
            mapper_reads += 1
            eligible = any(bool(np.any((maps[index][0] > 0) & (maps[index][0] <= .5)))
                           for index in (2, 3, 6))
            if eligible:
                half_mass.setdefault(scene, aid)
        positive = sorted(half_mass)[:64]
        negative = sorted(set(first_ann) - set(half_mass))[:16]
        for scene in positive:
            add(scene, half_mass[scene], "extension_half_mass")
        for scene in negative:
            add(scene, first_ann[scene], "extension_no_half_mass_scene")
        assert not ({row["scene"] for row in selection.values()} & excluded)
        metadata = {
            "excluded_scenes": sorted(excluded), "mapper_reads_for_sampling": mapper_reads,
            "requested_half_mass_scenes": 64, "selected_half_mass_scenes": len(positive),
            "requested_no_half_mass_scenes": 16, "selected_no_half_mass_scenes": len(negative),
            "half_mass_shortfall": 64 - len(positive),
            "no_half_mass_shortfall": 16 - len(negative),
            "scope": "Prediction-blind sampling; unmatched population comparators, not causal controls."}
    selection[4804] = original[4804]
    manifest = {"kind": KIND, "metadata": metadata, "groups": list(selection.values()),
                "bridge_control_group": 4804, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "native_forward_started": False}
    token = os.environ["CLUSTER_TICK_TOKEN"]
    path = PIPE / ("native_calibration_" + KIND + "_" + token + ".manifest.json")
    with path.open("x") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"manifest": str(path), "groups": len(selection),
                      "metadata": metadata}), flush=True)
    return selection


def extend_main(main):
    for index, node in enumerate(main.body):
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "dataset" for target in node.targets):
            main.body[index + 1:index + 1] = ast.parse(
                "cohort = choose_cohort(dataset, cohort)").body
            return
    raise AssertionError("Missing dataset")


module = ast.parse(SOURCE.read_text())
function = next(node for node in module.body if isinstance(node, ast.FunctionDef)
                and node.name == "calibration")
repairs = 0
for node in ast.walk(function):
    if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple):
        for index, statement in enumerate(node.body):
            if (isinstance(statement, ast.Assert)
                    and ast.unparse(statement.test) == "targets[bi]['masks'].shape[0] == 1"):
                node.body[index:index + 1] = ast.parse(
                    "assert len(batch['object_idss'][bi]) == 1\n"
                    "assert targets[bi]['masks'].shape[0] == len(tgt)\n"
                    "assert torch.equal(targets[bi]['masks'], targets[bi]['masks'][:1].expand_as(targets[bi]['masks']))"
                ).body
                repairs += 1
assert repairs == 1
for index, node in enumerate(module.body):
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "main" for target in node.targets):
        module.body[index + 1:index + 1] = ast.parse("extend_main(main)").body
        break
else:
    raise AssertionError("Missing original AST")
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and node.value == "native_role_calibration_":
        node.value = "native_calibration_" + KIND + "_"
    if isinstance(node, ast.Dict) and any(
            isinstance(key, ast.Constant) and key.value == "calibration"
            for key in node.keys if key is not None):
        node.keys.append(ast.Constant(value="choose_cohort"))
        node.values.append(ast.Name(id="choose_cohort", ctx=ast.Load()))
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__,
      "choose_cohort": choose_cohort, "extend_main": extend_main})
