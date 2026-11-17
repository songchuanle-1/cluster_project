"""Prediction-blind region-word incidence on a frozen M95 TRAIN cohort."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
OUTCOME_SHA = "44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a"
SOURCE_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
REGION_WORDS = frozenset(("corner", "middle", "center", "centre"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count(rows):
    exposed = [row for row in rows if row["region_words"]]
    unexposed = [row for row in rows if not row["region_words"]]
    return {
        "exposed": len(exposed),
        "exposed_failures": sum(row["failed"] for row in exposed),
        "unexposed": len(unexposed),
        "unexposed_failures": sum(row["failed"] for row in unexposed),
    }


def analyze(manifest, outcomes, source, vocabulary=REGION_WORDS):
    descriptions = defaultdict(list)
    for item in source:
        key = (item["scene_id"], int(item["ann_id"]), str(item["object_id"]))
        descriptions[key].append(item["description"])
    frozen = {int(row["manifest_index"]): row for row in outcomes["rows"]}
    entries = manifest["rows"]
    if len(entries) != 256 or len(frozen) != 256:
        raise ValueError("Frozen cohort incomplete")
    rows = []
    exposed_descriptions = []
    for entry in entries:
        index = int(entry["manifest_index"])
        key = (entry["scene_id"], int(entry["ann_id"]),
               str(entry["target_object_id"]))
        if (len(descriptions[key]) != 1 or index not in frozen
                or frozen[index]["scene"] != key[0]):
            raise ValueError("Frozen description/outcome identity differs")
        words = sorted(set(re.findall(r"[a-z]+", descriptions[key][0].lower()))
                       & vocabulary)
        row = {"manifest_index": index, "scene": key[0],
               "stratum": entry["stratum"], "region_words": words,
               "failed": bool(frozen[index]["failed"])}
        rows.append(row)
        if words:
            exposed_descriptions.append({
                **row, "target_class": entry["target_class"],
                "description": descriptions[key][0],
            })
    rows.sort(key=lambda row: row["manifest_index"])
    if [row["manifest_index"] for row in rows] != list(range(256)):
        raise ValueError("Manifest index differs")
    scenes = defaultdict(list)
    for row in rows:
        scenes[row["scene"]].append(row)
    pairs = [(a, b) for group in scenes.values() for i, a in enumerate(group)
             for b in group[i + 1:]
             if bool(a["region_words"]) != bool(b["region_words"])]
    return {
        "summary": {
            "all": count(rows),
            "by_stratum": {name: count([r for r in rows if r["stratum"] == name])
                           for name in ("ambiguous", "class_unique")},
            "same_scene_discordant_pairs": len(pairs),
            "same_scene_exposed_failures": sum(
                a["failed"] if a["region_words"] else b["failed"]
                for a, b in pairs),
            "same_scene_unexposed_failures": sum(
                b["failed"] if a["region_words"] else a["failed"]
                for a, b in pairs),
        },
        "exposed_descriptions": exposed_descriptions,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("manifest", "outcomes", "source", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    for name, expected in (("manifest", MANIFEST_SHA),
                           ("outcomes", OUTCOME_SHA), ("source", SOURCE_SHA)):
        if sha(getattr(args, name)) != expected:
            raise ValueError(name + " hash differs")
    result = analyze(
        json.loads(args.manifest.read_text(encoding="utf-8")),
        json.loads(args.outcomes.read_text(encoding="utf-8")),
        json.loads(args.source.read_text(encoding="utf-8")),
    )
    result.update(contract="m95_region_language_screen_v1",
                  manifest_sha256=MANIFEST_SHA, outcome_sha256=OUTCOME_SHA,
                  source_sha256=SOURCE_SHA, admission=False)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
