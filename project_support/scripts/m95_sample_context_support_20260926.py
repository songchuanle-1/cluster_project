"""Audit exact class-word membership feeding M95 seed-context targets."""
import argparse
import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SOURCE_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
CAPTURE_SHA = "5a1ddd9a906983416adbfb0e9d03b386de92a21803fdf20afe40740b5a69687e"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def class_keys(source):
    tree = ast.parse(source)
    assignments = [node for node in ast.walk(tree)
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Attribute)
                           and target.attr == "type2class" for target in node.targets)]
    if len(assignments) != 1:
        raise ValueError("Dataset class mapping is not unique")
    mapping = ast.literal_eval(assignments[0].value)
    if not isinstance(mapping, dict) or "others" not in mapping:
        raise ValueError("Dataset class mapping unexpected")
    return set(mapping) - {"others"}


def audit(cohort, source, graphs, keys, code_hash):
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]), str(item["object_id"]))].append(item)
    rows = []
    for item in cohort["rows"]:
        identity = item["scene"], int(item["ann_id"]), str(item["target"])
        if len(descriptions[identity]) != 1:
            raise ValueError("Frozen annotation identity not unique")
        name = descriptions[identity][0]["object_name"].replace("_", " ")
        graph = graphs[identity[0]][str(identity[1])]
        lang = " ".join(graph["utterance"].replace(",", " ,").split()) + " . not mentioned"
        matched = sorted(set(lang.split()) & keys)
        target_key = name if name in keys else None
        rows.append({
            "manifest_index": item["manifest_index"], "scene": identity[0],
            "ann_id": identity[1], "target": identity[2],
            "stratum": item["stratum"], "failed": bool(item["failed"]),
            "object_name": name, "target_key": target_key,
            "matched_class_keys": matched, "no_class_key": not matched,
            "missing_target_key": target_key is not None and target_key not in matched,
            "other_class_key": any(key != target_key for key in matched),
        })
    rows.sort(key=lambda r: r["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen capture incomplete")

    def summarize(items):
        return {"rows": len(items), "scenes": len({r["scene"] for r in items}),
                "failures": sum(r["failed"] for r in items),
                "target_in_vocab": sum(r["target_key"] is not None for r in items),
                "no_class_key": sum(r["no_class_key"] for r in items),
                "no_class_key_failures": sum(r["no_class_key"] and r["failed"] for r in items),
                "missing_target_key": sum(r["missing_target_key"] for r in items),
                "missing_target_key_failures": sum(r["missing_target_key"] and r["failed"] for r in items),
                "other_class_key": sum(r["other_class_key"] for r in items),
                "other_class_key_failures": sum(r["other_class_key"] and r["failed"] for r in items)}

    scenes = defaultdict(list)
    for row in rows:
        scenes[(row["scene"], row["stratum"])].append(row)
    pairs = [(a, b) for group in scenes.values() for i, a in enumerate(group)
             for b in group[i + 1:] if a["missing_target_key"] != b["missing_target_key"]]
    return {
        "contract": "m95_sample_context_support_v1", "admission": False,
        "source_sha256": SOURCE_SHA, "graph_sha256": GRAPH_SHA,
        "capture_sha256": CAPTURE_SHA, "dataset_code_sha256": code_hash,
        "class_keys": sorted(keys),
        "summary": {"all": summarize(rows),
                    "ambiguous": summarize([r for r in rows if r["stratum"] == "ambiguous"]),
                    "class_unique": summarize([r for r in rows if r["stratum"] == "class_unique"]),
                    "same_scene_discordant_pairs": len(pairs),
                    "same_scene_missing_failures": sum(
                        a["failed"] if a["missing_target_key"] else b["failed"] for a, b in pairs),
                    "same_scene_control_failures": sum(
                        b["failed"] if a["missing_target_key"] else a["failed"] for a, b in pairs)},
        "rows": rows,
    }


def main():
    p = argparse.ArgumentParser()
    for name in ("source", "graphs", "cohort", "dataset-code", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or sha(args.source) != SOURCE_SHA or sha(args.graphs) != GRAPH_SHA:
        raise ValueError("Native input hash differs or output exists")
    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    if cohort.get("capture_sha256") != CAPTURE_SHA:
        raise ValueError("Frozen capture differs")
    code = args.dataset_code.read_text(encoding="utf-8")
    result = audit(cohort, json.loads(args.source.read_text(encoding="utf-8")),
                   json.loads(args.graphs.read_text(encoding="utf-8")),
                   class_keys(code), sha(args.dataset_code))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
