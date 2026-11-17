"""Hash-bound TRAIN material-word incidence screen."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from m95_color_language_screen_20260926 import group


MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
OUTCOME_SHA = "44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a"
MATERIAL = frozenset("wooden wood metal metallic plastic glass fabric leather stone brick ceramic".split())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(rows):
    scenes = defaultdict(list)
    for row in rows:
        scenes[row["scene"]].append(row)
    pairs = [(a, b) for same in scenes.values() for i, a in enumerate(same)
             for b in same[i + 1:]
             if bool(a["material_words"]) != bool(b["material_words"])]
    return {
        "all": {f: group(rows, f) for f in ("material_words", "color_words")},
        "by_stratum": {
            s: {f: group([r for r in rows if r["stratum"] == s], f)
                for f in ("material_words", "color_words")}
            for s in sorted({r["stratum"] for r in rows})},
        "same_scene_discordant_pairs": len(pairs),
        "same_scene_discordant_scenes": len({a["scene"] for a, _ in pairs}),
        "same_scene_material_failures": sum(
            a["failed"] if a["material_words"] else b["failed"] for a, b in pairs),
        "same_scene_nonmaterial_failures": sum(
            b["failed"] if a["material_words"] else a["failed"] for a, b in pairs),
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
            "material_words": sorted(tokens & MATERIAL),
            "color_words": prior[index]["color_words"],
        })
    if len(rows) != 256 or len({r["manifest_index"] for r in rows}) != 256:
        raise ValueError("Frozen cohort incomplete")
    rows.sort(key=lambda r: r["manifest_index"])
    result = {"contract": "m95_material_language_screen_v1",
              "manifest_sha256": MANIFEST_SHA, "outcome_sha256": OUTCOME_SHA,
              "source_sha256": digest(a.source), "summary": analyze(rows),
              "rows": rows, "admission": False}
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
