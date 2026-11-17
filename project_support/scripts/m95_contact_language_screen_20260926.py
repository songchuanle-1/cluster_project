"""Frozen-cohort explicit contact phrase screen; read-only CPU analysis."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from m95_color_language_screen_20260926 import bind, group, words


MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
GEOMETRY_SHA = "45d333fc08a6f35b9b7f7741910977e3b8f3fbace2cde44cdd68e7869880c2f5"
PHRASES = (
    "on top of", "on the top of", "sitting on", "standing on", "resting on",
    "under", "underneath", "below", "against", "attached to", "hanging from",
    "leaning against",
)
CONTROL = frozenset("left right front behind near next".split())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contact_phrases(text):
    normalized = " ".join(re.findall(r"[a-z]+", text.lower()))
    return sorted(p for p in PHRASES if re.search(r"\b" + re.escape(p) + r"\b", normalized))


def analyze(rows):
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene"]].append(row)
    pairs = [(a, b) for same in by_scene.values() for i, a in enumerate(same)
             for b in same[i + 1:]
             if bool(a["contact_phrases"]) != bool(b["contact_phrases"])]
    return {
        "all": {f: group(rows, f) for f in ("contact_phrases", "direction_words")},
        "by_stratum": {
            s: {f: group([r for r in rows if r["stratum"] == s], f)
                for f in ("contact_phrases", "direction_words")}
            for s in sorted({r["stratum"] for r in rows})},
        "same_scene_discordant_pairs": len(pairs),
        "same_scene_discordant_scenes": len({a["scene"] for a, _ in pairs}),
        "same_scene_contact_failures": sum(
            a["failed"] if a["contact_phrases"] else b["failed"] for a, b in pairs),
        "same_scene_noncontact_failures": sum(
            b["failed"] if a["contact_phrases"] else a["failed"] for a, b in pairs),
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("manifest", "source", "geometry", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    if digest(args.manifest) != MANIFEST_SHA or digest(args.geometry) != GEOMETRY_SHA:
        raise ValueError("Frozen input hash differs")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    geometry = json.loads(args.geometry.read_text(encoding="utf-8"))
    rows = bind(manifest, source, geometry)
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]), str(item["object_id"]))].append(
            item["description"])
    manifest_by_index = {int(r["manifest_index"]): r for r in manifest["rows"]}
    for row in rows:
        entry = manifest_by_index[row["manifest_index"]]
        key = (row["scene"], int(entry["ann_id"]), str(entry["target_object_id"]))
        if len(descriptions[key]) != 1:
            raise ValueError("Description join differs")
        description = descriptions[key][0]
        row["contact_phrases"] = contact_phrases(description)
        row["direction_words"] = sorted(words(description) & CONTROL)
        del row["color_words"]
        del row["spatial_words"]
    result = {
        "contract": "m95_contact_language_screen_v1",
        "manifest_sha256": MANIFEST_SHA,
        "geometry_sha256": GEOMETRY_SHA,
        "source_sha256": digest(args.source),
        "summary": analyze(rows),
        "rows": rows,
        "admission": False,
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
