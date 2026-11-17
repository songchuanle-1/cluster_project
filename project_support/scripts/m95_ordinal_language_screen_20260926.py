"""Frozen TRAIN explicit ordinal incidence and matched scene census."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from m95_color_language_screen_20260926 import group


MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
OUTCOME_SHA = "44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a"
ORDINAL = frozenset("first second third last middle center".split())
DIRECTION = frozenset("left right".split())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(rows):
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene"]].append(row)
    pairs = [(a, b) for scene in by_scene.values() for i, a in enumerate(scene)
             for b in scene[i + 1:]
             if bool(a["ordinal_words"]) != bool(b["ordinal_words"])]
    return {
        "all": {f: group(rows, f) for f in ("ordinal_words", "direction_words")},
        "by_stratum": {
            s: {f: group([r for r in rows if r["stratum"] == s], f)
                for f in ("ordinal_words", "direction_words")}
            for s in sorted({r["stratum"] for r in rows})},
        "same_scene_discordant_pairs": len(pairs),
        "same_scene_ordinal_failures": sum(
            a["failed"] if a["ordinal_words"] else b["failed"] for a, b in pairs),
        "same_scene_nonordinal_failures": sum(
            b["failed"] if a["ordinal_words"] else a["failed"] for a, b in pairs),
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
    prior = {int(r["manifest_index"]): r for r in
             json.loads(a.outcomes.read_text(encoding="utf-8"))["rows"]}
    source = json.loads(a.source.read_text(encoding="utf-8"))
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]), str(item["object_id"]))].append(
            item["description"])
    rows = []
    for entry in manifest["rows"]:
        index = int(entry["manifest_index"])
        key = (entry["scene_id"], int(entry["ann_id"]), str(entry["target_object_id"]))
        if len(descriptions[key]) != 1 or prior[index]["scene"] != key[0]:
            raise ValueError("Frozen identity differs")
        tokens = set(re.findall(r"[a-z]+", descriptions[key][0].lower()))
        rows.append({
            "manifest_index": index, "scene": key[0], "stratum": entry["stratum"],
            "failed": bool(prior[index]["failed"]),
            "ordinal_words": sorted(tokens & ORDINAL),
            "direction_words": sorted(tokens & DIRECTION),
        })
    if len(rows) != 256 or len({r["manifest_index"] for r in rows}) != 256:
        raise ValueError("Incomplete frozen cohort")
    rows.sort(key=lambda r: r["manifest_index"])
    result = {"contract": "m95_explicit_ordinal_language_screen_v1",
              "manifest_sha256": MANIFEST_SHA, "outcome_sha256": OUTCOME_SHA,
              "source_sha256": digest(a.source), "summary": analyze(rows),
              "rows": rows, "admission": False}
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
