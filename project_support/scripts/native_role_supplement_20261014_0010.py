"""Pre-registered remaining original TRAIN role-overwrite cases, plus control."""
import ast
import hashlib
import json
from pathlib import Path

PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")
SOURCE = PIPE / "native_role_task_fd_20261014_0010.py"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "a3f1c5e6d559187917d0b6c044795952c93d40456be4e75b68b7c501a60ed21d")


def supplemental_cohort(dataset, original):
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
    examples = [row for row in audit["trials"][0]["examples"]
                if (row["scene"], row["ann_id"]) in frozen]
    assert len(examples) == 5
    lookup = {(ann["scene_id"], int(ann["ann_id"])): group
              for group, annotations in enumerate(dataset.scene_inputs) for ann in annotations}
    selection = {}
    for row in examples:
        key = lookup[(row["scene"], row["ann_id"])]
        assert key not in original, "Supplement must not repeat a primary cohort group"
        if key not in selection:
            selection[key] = {"group": key, "scene": row["scene"],
                              "ann_ids": [int(a["ann_id"]) for a in dataset.scene_inputs[key]],
                              "families": ["supplemental_main"],
                              "trigger_ann_ids": []}
        selection[key]["trigger_ann_ids"].append(row["ann_id"])
    selection[4804] = original[4804]
    assert len(selection) == 6
    return selection


def extend_native_main(main):
    for index, statement in enumerate(main.body):
        if (isinstance(statement, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "dataset"
                        for target in statement.targets)):
            main.body[index + 1:index + 1] = ast.parse(
                "cohort = supplemental_cohort(dataset, cohort)").body
            return
    raise AssertionError("Missing original dataset construction")


module = ast.parse(SOURCE.read_text())
for index, statement in enumerate(module.body):
    if (isinstance(statement, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "main"
                    for target in statement.targets)):
        module.body[index + 1:index + 1] = ast.parse("extend_native_main(main)").body
        break
else:
    raise AssertionError("Missing original native AST selection")
for node in ast.walk(module):
    if isinstance(node, ast.Dict) and any(
        isinstance(key, ast.Constant) and key.value == "task_gradients"
        for key in node.keys if key is not None):
        node.keys.append(ast.Constant(value="supplemental_cohort"))
        node.values.append(ast.Name(id="supplemental_cohort", ctx=ast.Load()))
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        node.value = node.value.replace("native_role_task_fd_", "native_role_supplement_")
namespace = {"__name__": "__main__", "__file__": __file__,
             "supplemental_cohort": supplemental_cohort,
             "extend_native_main": extend_native_main}
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"), namespace)
