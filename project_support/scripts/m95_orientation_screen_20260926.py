"""Read-only frozen TRAIN orientation-language incidence."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
OUTCOME_SHA = "44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a"
ORIENTATION = frozenset(
    "facing faces face oriented orientation angled slanted tilted leaning "
    "upright vertical horizontal parallel perpendicular".split()
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group(rows):
    exposed = [r for r in rows if r["orientation_words"]]
    other = [r for r in rows if not r["orientation_words"]]
    return {"exposed": len(exposed), "exposed_failures": sum(r["failed"] for r in exposed),
            "unexposed": len(other), "unexposed_failures": sum(r["failed"] for r in other)}


def analyze(manifest, outcomes, source):
    descriptions = defaultdict(list)
    for item in source:
        key = (item["scene_id"], int(item["ann_id"]), str(item["object_id"]))
        descriptions[key].append(item["description"])
    prior = {int(r["manifest_index"]): r for r in outcomes["rows"]}
    if len(prior) != len(manifest["rows"]) or len(prior) != 256:
        raise ValueError("Incomplete frozen cohort")
    rows = []
    for entry in manifest["rows"]:
        index = int(entry["manifest_index"])
        key = (entry["scene_id"], int(entry["ann_id"]), str(entry["target_object_id"]))
        if len(descriptions[key]) != 1 or prior[index]["scene"] != key[0]:
            raise ValueError("Description/outcome identity mismatch")
        tokens = set(re.findall(r"[a-z]+", descriptions[key][0].lower()))
        rows.append({"manifest_index": index, "scene": key[0], "stratum": entry["stratum"],
                     "orientation_words": sorted(tokens & ORIENTATION),
                     "failed": bool(prior[index]["failed"])})
    rows.sort(key=lambda r: r["manifest_index"])
    if [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Manifest index mismatch")
    scenes = defaultdict(list)
    for row in rows:
        scenes[row["scene"]].append(row)
    pairs = [(a, b) for same in scenes.values() for i, a in enumerate(same)
             for b in same[i + 1:]
             if bool(a["orientation_words"]) != bool(b["orientation_words"])]
    return {"rows": rows, "summary": {
        "all": group(rows),
        "by_stratum": {s: group([r for r in rows if r["stratum"] == s])
                       for s in ("ambiguous", "class_unique")},
        "same_scene_discordant_pairs": len(pairs),
        "same_scene_orientation_failures": sum(
            a["failed"] if a["orientation_words"] else b["failed"] for a, b in pairs),
        "same_scene_no_orientation_failures": sum(
            b["failed"] if a["orientation_words"] else a["failed"] for a, b in pairs)}}


def main():
    p = argparse.ArgumentParser()
    for name in ("manifest", "outcomes", "source", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if digest(a.manifest) != MANIFEST_SHA or digest(a.outcomes) != OUTCOME_SHA:
        raise ValueError("Frozen inputs differ")
    result = analyze(json.loads(a.manifest.read_text(encoding="utf-8")),
                     json.loads(a.outcomes.read_text(encoding="utf-8")),
                     json.loads(a.source.read_text(encoding="utf-8")))
    result.update({"contract": "m95_orientation_screen_v1", "admission": False,
                   "manifest_sha256": MANIFEST_SHA, "outcome_sha256": OUTCOME_SHA,
                   "source_sha256": digest(a.source)})
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
