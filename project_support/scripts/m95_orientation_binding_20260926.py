"""Audit exact native TRAIN descriptions for the frozen orientation screen."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SCREEN_SHA = "494b446c95dd3bf3e0aa583dfbe4a84d7a8e6eccc8023599b838398e452a0599"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(screen, manifest, source):
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]),
                      str(item["object_id"]))].append(item["description"])
    bound = {int(row["manifest_index"]): row for row in manifest["rows"]}
    rows = []
    for row in screen["rows"]:
        if not row["orientation_words"]:
            continue
        entry = bound[int(row["manifest_index"])]
        key = (entry["scene_id"], int(entry["ann_id"]),
               str(entry["target_object_id"]))
        if len(descriptions[key]) != 1 or row["scene"] != key[0]:
            raise ValueError("Frozen identity mismatch")
        rows.append({"manifest_index": row["manifest_index"], "scene": key[0],
                     "target_class": entry["target_class"],
                     "target_object_id": key[2], "failed": row["failed"],
                     "description": descriptions[key][0]})
    return rows


def main():
    p = argparse.ArgumentParser()
    for name in ("screen", "manifest", "source", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if sha(a.screen) != SCREEN_SHA:
        raise ValueError("Frozen screen differs")
    rows = audit(json.loads(a.screen.read_text(encoding="utf-8")),
                 json.loads(a.manifest.read_text(encoding="utf-8")),
                 json.loads(a.source.read_text(encoding="utf-8")))
    a.output.write_text(json.dumps({"screen_sha256": SCREEN_SHA,
                                    "source_sha256": sha(a.source),
                                    "rows": rows, "admission": False},
                                   indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(rows, ensure_ascii=True))


if __name__ == "__main__":
    main()
