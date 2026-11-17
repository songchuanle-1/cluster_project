"""Read-only TRAIN category-name disagreement for the same instance ID."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

SOURCE_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
CAPTURE_SHA = "5a1ddd9a906983416adbfb0e9d03b386de92a21803fdf20afe40740b5a69687e"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(text):
    parts = re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
    return " ".join(p[:-1] if len(p) > 3 and p.endswith("s") else p for p in parts)


def audit(cohort, source):
    objects, identities = defaultdict(list), defaultdict(list)
    for item in source:
        scene, instance = item["scene_id"], str(item["object_id"])
        objects[(scene, instance)].append(item)
        identities[(scene, int(item["ann_id"]), instance)].append(item)
    rows = []
    for item in cohort["rows"]:
        key = item["scene"], int(item["ann_id"]), str(item["target"])
        if len(identities[key]) != 1:
            raise ValueError("Frozen annotation identity not unique")
        group = objects[(key[0], key[2])]
        names = sorted({normalize(row["object_name"]) for row in group})
        rows.append({
            "manifest_index": item["manifest_index"], "scene": key[0],
            "ann_id": key[1], "target": key[2], "stratum": item["stratum"],
            "failed": bool(item["failed"]), "annotation_count": len(group),
            "names": names,
            "variants": [{"ann_id": int(row["ann_id"]),
                          "name": row["object_name"],
                          "description": row["description"]} for row in group],
            "exposed": len(names) > 1,
        })
    rows.sort(key=lambda r: r["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen cohort incomplete")

    def summary(items):
        return {"rows": len(items), "scenes": len({r["scene"] for r in items}),
                "failures": sum(r["failed"] for r in items),
                "single_annotation": sum(r["annotation_count"] == 1 for r in items),
                "multi_same_name": sum(r["annotation_count"] > 1 and not r["exposed"] for r in items),
                "multi_same_name_failures": sum(r["annotation_count"] > 1 and not r["exposed"] and r["failed"] for r in items),
                "exposed": sum(r["exposed"] for r in items),
                "exposed_failures": sum(r["exposed"] and r["failed"] for r in items)}

    scene_rows = defaultdict(list)
    for row in rows:
        scene_rows[(row["scene"], row["stratum"])].append(row)
    pairs = [(a, b) for group in scene_rows.values() for i, a in enumerate(group)
             for b in group[i + 1:] if a["exposed"] != b["exposed"]]
    return {
        "contract": "m95_object_category_conflict_v1", "admission": False,
        "source_sha256": SOURCE_SHA, "capture_sha256": CAPTURE_SHA,
        "summary": {
            "all": summary(rows),
            "ambiguous": summary([r for r in rows if r["stratum"] == "ambiguous"]),
            "class_unique": summary([r for r in rows if r["stratum"] == "class_unique"]),
            "same_scene_discordant_pairs": len(pairs),
            "same_scene_exposed_failures": sum(
                a["failed"] if a["exposed"] else b["failed"] for a, b in pairs),
            "same_scene_control_failures": sum(
                b["failed"] if a["exposed"] else a["failed"] for a, b in pairs),
        }, "rows": rows,
    }


def main():
    p = argparse.ArgumentParser()
    for name in ("source", "cohort", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or sha(args.source) != SOURCE_SHA:
        raise ValueError("Output exists or source hash differs")
    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    if cohort.get("capture_sha256") != CAPTURE_SHA:
        raise ValueError("Frozen capture differs")
    result = audit(cohort, json.loads(args.source.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
