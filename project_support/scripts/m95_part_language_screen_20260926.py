"""Frozen TRAIN object-part language incidence, read-only."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
OUTCOME_SHA = "44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a"
PARTS = frozenset(
    "arm arms armrest armrests leg legs drawer drawers shelf shelves "
    "handle handles door doors wheel wheels cushion cushions seat backrest".split())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def counts(rows, key):
    exposed = [r for r in rows if r[key]]
    other = [r for r in rows if not r[key]]
    return {"exposed": len(exposed),
            "exposed_failures": sum(r["failed"] for r in exposed),
            "unexposed": len(other),
            "unexposed_failures": sum(r["failed"] for r in other)}


def analyze(manifest, outcomes, source, material):
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]),
                      str(item["object_id"]))].append(item["description"])
    prior = {int(r["manifest_index"]): r for r in outcomes["rows"]}
    material_rows = {int(r["manifest_index"]): r for r in material["rows"]}
    rows = []
    for entry in manifest["rows"]:
        index = int(entry["manifest_index"])
        key = (entry["scene_id"], int(entry["ann_id"]),
               str(entry["target_object_id"]))
        if (len(descriptions[key]) != 1 or prior[index]["scene"] != key[0]
                or material_rows[index]["scene"] != key[0]):
            raise ValueError("Frozen description/outcome binding differs")
        tokens = set(re.findall(r"[a-z]+", descriptions[key][0].lower()))
        rows.append({"manifest_index": index, "scene": key[0],
                     "stratum": entry["stratum"],
                     "part_words": sorted(tokens & PARTS),
                     "material_words": material_rows[index]["material_words"],
                     "failed": bool(prior[index]["failed"])})
    rows.sort(key=lambda r: r["manifest_index"])
    if [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Manifest index coverage differs")
    by_scene = defaultdict(list)
    for r in rows:
        by_scene[r["scene"]].append(r)
    pairs = [(a, b) for scene in by_scene.values() for i, a in enumerate(scene)
             for b in scene[i + 1:]
             if bool(a["part_words"]) != bool(b["part_words"])]
    return {"rows": rows,
            "summary": {"all": {key: counts(rows, key) for key in
                                ("part_words", "material_words")},
                        "by_stratum": {
                            stratum: counts([r for r in rows
                                             if r["stratum"] == stratum], "part_words")
                            for stratum in ("ambiguous", "class_unique")},
                        "same_scene_discordant_pairs": len(pairs),
                        "same_scene_part_failures": sum(
                            a["failed"] if a["part_words"] else b["failed"]
                            for a, b in pairs),
                        "same_scene_no_part_failures": sum(
                            b["failed"] if a["part_words"] else a["failed"]
                            for a, b in pairs)}}


def main():
    parser = argparse.ArgumentParser()
    for field in ("manifest", "outcomes", "material", "source", "output"):
        parser.add_argument("--" + field, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    if digest(args.manifest) != MANIFEST_SHA or digest(args.outcomes) != OUTCOME_SHA:
        raise ValueError("Frozen inputs differ")
    result = analyze(
        json.loads(args.manifest.read_text(encoding="utf-8")),
        json.loads(args.outcomes.read_text(encoding="utf-8")),
        json.loads(args.source.read_text(encoding="utf-8")),
        json.loads(args.material.read_text(encoding="utf-8")))
    result.update({"contract": "m95_part_language_screen_v1",
                   "manifest_sha256": MANIFEST_SHA, "outcome_sha256": OUTCOME_SHA,
                   "source_sha256": digest(args.source),
                   "material_sha256": digest(args.material), "admission": False})
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
