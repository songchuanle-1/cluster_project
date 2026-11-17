"""Prediction-blind physical target semantic class contract for frozen M95."""
import argparse
import ast
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

CAPTURE_SHA = "9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd"
PRODUCER_SHA = "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a"
ANNOTATIONS_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
DATASET_SHA = "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
LABELS_SHA = "9c17c0da2061beea889edc9f49ff14e8218f4cd040ab241fc70186e03b32a744"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def native_mapping(source, tsv):
    tree = ast.parse(source)
    values = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in (
                    "type2class", "sem2nyu", "nyu40ids"
                ):
                    if target.attr in values:
                        raise ValueError("Duplicate native mapping " + target.attr)
                    value = node.value
                    if target.attr == "nyu40ids" and isinstance(value, ast.Call):
                        func = value.func
                        if (not isinstance(func, ast.Attribute)
                                or not isinstance(func.value, ast.Name)
                                or (func.value.id, func.attr) != ("np", "array")
                                or len(value.args) != 1 or value.keywords):
                            raise ValueError("Unexpected native NYU array constructor")
                        value = value.args[0]
                    values[target.attr] = ast.literal_eval(value)
    if set(values) != {"type2class", "sem2nyu", "nyu40ids"}:
        raise ValueError("Native class mapping incomplete")
    labels = {}
    for line in tsv.splitlines()[1:]:
        cells = line.split("\t")
        if len(cells) < 8:
            raise ValueError("Malformed native label TSV")
        nyu = int(cells[4])
        if nyu in values["nyu40ids"]:
            labels.setdefault(nyu, set()).add(cells[7])
    nyu_to_class = {}
    for nyu, names in labels.items():
        mapped = {values["type2class"].get(name, values["type2class"]["others"])
                  for name in names}
        if len(mapped) != 1:
            raise ValueError("Nonunique NYU class mapping")
        nyu_to_class[nyu] = mapped.pop()
    sem_to_class = {}
    for index, nyu in enumerate(values["sem2nyu"]):
        if nyu in nyu_to_class:
            sem_to_class[index] = nyu_to_class[nyu]
    return values["type2class"], sem_to_class


def audit(capture, annotations, type2class, sem_to_class):
    if (capture.get("producer_sha256") != PRODUCER_SHA
            or capture.get("capture_mode") != "full_train_scan"
            or not capture.get("native_capture_completed")):
        raise ValueError("Frozen producer contract differs")
    source = {}
    for item in annotations:
        key = (item["scene_id"], int(item["ann_id"]), str(item["object_id"]))
        if key in source:
            raise ValueError("Duplicate annotation identity")
        source[key] = item
    rows = []
    for item in capture["rows"]:
        identity = (item["scene"], int(item["ann_id"]), str(item["target_object_id"]))
        if identity not in source:
            raise ValueError("Missing annotation identity")
        name = source[identity]["object_name"].replace("_", " ")
        expected = type2class.get(name)
        if expected == type2class["others"]:
            expected = None
        target_ids = set(map(int, item["target_instances"]))
        if not target_ids or str(item["target_object_id"]) not in {
                str(value) for value in target_ids}:
            raise ValueError("Frozen target instance binding differs")
        labels = item["physical_instance_labels"]
        semantics = item["semantic_labels"]
        if len(labels) != len(semantics):
            raise ValueError("Native physical/semantic axes differ")
        observed = {sem_to_class.get(int(sem))
                    for instance, sem in zip(labels, semantics)
                    if int(instance) in target_ids}
        resolved = expected is not None and len(observed) == 1 and None not in observed
        actual = next(iter(observed)) if resolved else None
        rows.append({
            "manifest_index": int(item["manifest_index"]),
            "scene": identity[0], "ann_id": identity[1],
            "target": identity[2], "stratum": item["stratum"],
            "failed": float(item["ious"][int(item["selected_query"])]) <= 0.5,
            "object_name": name, "expected_class": expected,
            "observed_classes": sorted(v for v in observed if v is not None),
            "unresolved": not resolved,
            "exposed": bool(resolved and actual != expected),
        })
    rows.sort(key=lambda x: x["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen manifest coverage differs")

    def tally(group):
        eligible = [r for r in group if not r["unresolved"]]
        exposed = [r for r in eligible if r["exposed"]]
        return {
            "rows": len(group), "scenes": len({r["scene"] for r in group}),
            "failures": sum(r["failed"] for r in group),
            "eligible": len(eligible), "eligible_failures": sum(r["failed"] for r in eligible),
            "exposed": len(exposed), "exposed_failures": sum(r["failed"] for r in exposed),
        }

    pairs = [(a, b) for i, a in enumerate(rows) for b in rows[i + 1:]
             if a["scene"] == b["scene"] and a["stratum"] == b["stratum"]
             and not a["unresolved"] and not b["unresolved"]
             and a["expected_class"] == b["expected_class"]
             and a["exposed"] != b["exposed"]]
    return {
        "contract": "m95_physical_semantic_contract_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "source_sha256": ANNOTATIONS_SHA,
        "summary": {
            "all": tally(rows),
            "ambiguous": tally([r for r in rows if r["stratum"] == "ambiguous"]),
            "class_unique": tally([r for r in rows if r["stratum"] == "class_unique"]),
            "same_scene_class_matched_discordant_pairs": len(pairs),
            "same_scene_exposed_failures": sum(
                a["failed"] if a["exposed"] else b["failed"] for a, b in pairs),
            "same_scene_control_failures": sum(
                b["failed"] if a["exposed"] else a["failed"] for a, b in pairs),
        },
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "annotations", "dataset-code", "labels", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or digest(args.capture) != CAPTURE_SHA:
        raise ValueError("Output exists or frozen capture hash differs")
    if (digest(args.dataset_code) != DATASET_SHA
            or digest(args.annotations) != ANNOTATIONS_SHA
            or digest(args.labels) != LABELS_SHA):
        raise ValueError("Native source/annotation/labels hash differs")
    type2class, sem_to_class = native_mapping(
        args.dataset_code.read_text(encoding="utf-8"),
        args.labels.read_text(encoding="utf-8"))
    result = audit(
        json.loads(args.capture.read_text(encoding="utf-8")),
        json.loads(args.annotations.read_text(encoding="utf-8")),
        type2class, sem_to_class)
    result["annotations_sha256"] = digest(args.annotations)
    result["labels_sha256"] = digest(args.labels)
    args.output.write_text(
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
