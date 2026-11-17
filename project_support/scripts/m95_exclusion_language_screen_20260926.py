"""Frozen-cohort explicit exclusion phrase incidence."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from m95_color_language_screen_20260926 import group


MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
OUTCOME_SHA = "44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a"
EXCLUSION = ("not the", "not a", "not an", "but not", "instead of",
             "other than", "except", "neither", "without")
CONTROL = {"but", "also", "and"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def features(text):
    tokens = re.findall(r"[a-z]+", text.lower())
    normalized = " ".join(tokens)
    return (sorted(p for p in EXCLUSION if re.search(
                r"\b" + re.escape(p) + r"\b", normalized)),
            sorted(set(tokens) & CONTROL))


def analyze(rows):
    scenes = defaultdict(list)
    for row in rows:
        scenes[row["scene"]].append(row)
    pairs = [(a, b) for same in scenes.values() for i, a in enumerate(same)
             for b in same[i + 1:]
             if bool(a["exclusion_phrases"]) != bool(b["exclusion_phrases"])]
    return {
        "all": {f: group(rows, f) for f in ("exclusion_phrases", "contrast_words")},
        "by_stratum": {
            s: {f: group([r for r in rows if r["stratum"] == s], f)
                for f in ("exclusion_phrases", "contrast_words")}
            for s in sorted({r["stratum"] for r in rows})},
        "same_scene_discordant_pairs": len(pairs),
        "same_scene_discordant_scenes": len({a["scene"] for a, _ in pairs}),
        "same_scene_exclusion_failures": sum(
            a["failed"] if a["exclusion_phrases"] else b["failed"] for a, b in pairs),
        "same_scene_nonexclusion_failures": sum(
            b["failed"] if a["exclusion_phrases"] else a["failed"] for a, b in pairs),
    }


def main():
    p = argparse.ArgumentParser()
    for name in ("manifest", "outcomes", "source", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if digest(a.manifest) != MANIFEST_SHA or digest(a.outcomes) != OUTCOME_SHA:
        raise ValueError("Frozen input differs")
    manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
    outcomes = {int(r["manifest_index"]): r for r in
                json.loads(a.outcomes.read_text(encoding="utf-8"))["rows"]}
    source = json.loads(a.source.read_text(encoding="utf-8"))
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]), str(item["object_id"]))].append(
            item["description"])
    rows = []
    for item in manifest["rows"]:
        index = int(item["manifest_index"])
        key = (item["scene_id"], int(item["ann_id"]), str(item["target_object_id"]))
        if len(descriptions[key]) != 1 or outcomes[index]["scene"] != key[0]:
            raise ValueError("Frozen identity differs")
        exclusion, contrast = features(descriptions[key][0])
        rows.append({
            "manifest_index": index, "scene": key[0], "stratum": item["stratum"],
            "failed": bool(outcomes[index]["failed"]),
            "exclusion_phrases": exclusion, "contrast_words": contrast,
        })
    if len(rows) != 256 or len({r["manifest_index"] for r in rows}) != 256:
        raise ValueError("Incomplete cohort")
    rows.sort(key=lambda r: r["manifest_index"])
    result = {"contract": "m95_exclusion_language_screen_v1",
              "manifest_sha256": MANIFEST_SHA, "outcome_sha256": OUTCOME_SHA,
              "source_sha256": digest(a.source), "summary": analyze(rows),
              "rows": rows, "admission": False}
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
