"""Read-only same-scene distinct-target identical-description audit."""
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


def normalized(text):
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def audit(cohort, source):
    by_identity, normalized_groups, raw_groups = defaultdict(list), defaultdict(set), defaultdict(set)
    for item in source:
        identity = item["scene_id"], int(item["ann_id"]), str(item["object_id"])
        by_identity[identity].append(item)
        normalized_groups[(identity[0], normalized(item["description"]))].add(identity[2])
        raw_groups[(identity[0], item["description"])].add(identity[2])
    rows = []
    for item in cohort["rows"]:
        key = item["scene"], int(item["ann_id"]), str(item["target"])
        if len(by_identity[key]) != 1:
            raise ValueError("Non-unique frozen annotation identity")
        desc = by_identity[key][0]["description"]
        peers = sorted(normalized_groups[(key[0], normalized(desc))] - {key[2]})
        rows.append({
            "manifest_index": item["manifest_index"], "scene": key[0],
            "ann_id": key[1], "target": key[2], "stratum": item["stratum"],
            "failed": bool(item["failed"]), "description": desc,
            "collision": bool(peers), "peer_targets": peers,
            "raw_collision": len(raw_groups[(key[0], desc)]) > 1,
        })
    rows.sort(key=lambda r: r["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen capture incomplete")

    def summary(items):
        return {"rows": len(items), "scenes": len({r["scene"] for r in items}),
                "failures": sum(r["failed"] for r in items),
                "collisions": sum(r["collision"] for r in items),
                "collision_failures": sum(r["collision"] and r["failed"] for r in items),
                "raw_collisions": sum(r["raw_collision"] for r in items)}

    scenes = defaultdict(list)
    for row in rows:
        scenes[(row["scene"], row["stratum"])].append(row)
    pairs = [(a, b) for group in scenes.values() for i, a in enumerate(group)
             for b in group[i + 1:] if a["collision"] != b["collision"]]
    return {
        "contract": "m95_description_collision_v1", "admission": False,
        "source_sha256": SOURCE_SHA, "capture_sha256": CAPTURE_SHA,
        "summary": {
            "all": summary(rows),
            "ambiguous": summary([r for r in rows if r["stratum"] == "ambiguous"]),
            "class_unique": summary([r for r in rows if r["stratum"] == "class_unique"]),
            "source_collision_groups": sum(len(ids) > 1 for ids in normalized_groups.values()),
            "source_raw_collision_groups": sum(len(ids) > 1 for ids in raw_groups.values()),
            "same_scene_discordant_pairs": len(pairs),
            "same_scene_collision_failures": sum(
                a["failed"] if a["collision"] else b["failed"] for a, b in pairs),
            "same_scene_control_failures": sum(
                b["failed"] if a["collision"] else a["failed"] for a, b in pairs),
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
