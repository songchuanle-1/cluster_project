"""Read-only, manifest-bound explicit color-language incidence screen."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
GEOMETRY_SHA = "45d333fc08a6f35b9b7f7741910977e3b8f3fbace2cde44cdd68e7869880c2f5"
COLOR = frozenset("red blue green yellow orange pink purple black white brown gray grey".split())
SPATIAL = frozenset("left right front behind near next".split())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


def bind(manifest, source, geometry):
    source_index = defaultdict(list)
    for item in source:
        key = (item["scene_id"], int(item["ann_id"]), str(item["object_id"]))
        source_index[key].append(item)
    outcomes = {int(row["manifest_index"]): row for row in geometry["rows"]}
    if len(outcomes) != 256 or len(manifest["rows"]) != 256:
        raise ValueError("Expected exactly 256 unique rows")
    result = []
    for row in manifest["rows"]:
        key = (row["scene_id"], int(row["ann_id"]), str(row["target_object_id"]))
        matches = source_index[key]
        if len(matches) != 1:
            raise ValueError(f"Ambiguous or missing description: {key}")
        outcome = outcomes.pop(int(row["manifest_index"]))
        if outcome["scene"] != key[0]:
            raise ValueError("Scene identity differs")
        tokens = words(matches[0]["description"])
        result.append({
            "manifest_index": int(row["manifest_index"]),
            "scene": key[0],
            "stratum": row["stratum"],
            "color_words": sorted(tokens & COLOR),
            "spatial_words": sorted(tokens & SPATIAL),
            "failed": outcome["selected_iou"] <= 0.5,
        })
    if outcomes:
        raise ValueError("Unbound outcomes")
    return sorted(result, key=lambda row: row["manifest_index"])


def group(rows, feature):
    exposed = [r for r in rows if r[feature]]
    other = [r for r in rows if not r[feature]]
    return {
        "exposed": len(exposed),
        "exposed_failures": sum(r["failed"] for r in exposed),
        "unexposed": len(other),
        "unexposed_failures": sum(r["failed"] for r in other),
        "exposed_failure_rate": (
            sum(r["failed"] for r in exposed) / len(exposed) if exposed else None),
        "unexposed_failure_rate": (
            sum(r["failed"] for r in other) / len(other) if other else None),
    }


def analyze(rows):
    scenes = defaultdict(list)
    for row in rows:
        scenes[row["scene"]].append(row)
    pairs = [(a, b) for same in scenes.values() for i, a in enumerate(same)
             for b in same[i + 1:] if bool(a["color_words"]) != bool(b["color_words"])]
    result = {
        "all": {f: group(rows, f) for f in ("color_words", "spatial_words")},
        "by_stratum": {
            s: {f: group([r for r in rows if r["stratum"] == s], f)
                for f in ("color_words", "spatial_words")}
            for s in sorted({r["stratum"] for r in rows})},
        "same_scene_discordant_pairs": len(pairs),
        "same_scene_discordant_scenes": len({a["scene"] for a, _ in pairs}),
        "same_scene_color_failures": sum(
            a["failed"] if a["color_words"] else b["failed"] for a, b in pairs),
        "same_scene_noncolor_failures": sum(
            b["failed"] if a["color_words"] else a["failed"] for a, b in pairs),
    }
    return result


def main():
    p = argparse.ArgumentParser()
    for name in ("manifest", "source", "geometry", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if digest(a.manifest) != MANIFEST_SHA or digest(a.geometry) != GEOMETRY_SHA:
        raise ValueError("Frozen input hash differs")
    manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
    source = json.loads(a.source.read_text(encoding="utf-8"))
    geometry = json.loads(a.geometry.read_text(encoding="utf-8"))
    rows = bind(manifest, source, geometry)
    result = {
        "contract": "m95_explicit_color_language_screen_v1",
        "manifest_sha256": MANIFEST_SHA,
        "geometry_sha256": GEOMETRY_SHA,
        "source_sha256": digest(a.source),
        "summary": analyze(rows),
        "rows": rows,
        "admission": False,
    }
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
