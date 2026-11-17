"""Read-only explicit comparative-size incidence in a frozen TRAIN cohort."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from m95_color_language_screen_20260926 import group


MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
OUTCOME_SHA = "44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a"
LARGER = {"larger", "bigger", "largest", "biggest"}
SMALLER = {"smaller", "tinier", "smallest", "tiniest"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def size_direction(text):
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    directions = [name for name, words in
                  (("larger", LARGER), ("smaller", SMALLER)) if tokens & words]
    return directions[0] if len(directions) == 1 else ("both" if directions else None)


def analyze(rows):
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene"]].append(row)
    pairs = [(a, b) for same in by_scene.values() for i, a in enumerate(same)
             for b in same[i + 1:]
             if bool(a["size_direction"]) != bool(b["size_direction"])]
    return {
        "all": group(rows, "size_direction"),
        "by_stratum": {
            s: group([r for r in rows if r["stratum"] == s], "size_direction")
            for s in sorted({r["stratum"] for r in rows})},
        "directions": {d: sum(r["size_direction"] == d for r in rows)
                       for d in ("larger", "smaller", "both")},
        "same_scene_discordant_pairs": len(pairs),
        "same_scene_discordant_scenes": len({a["scene"] for a, _ in pairs}),
        "same_scene_size_failures": sum(
            a["failed"] if a["size_direction"] else b["failed"] for a, b in pairs),
        "same_scene_nonsize_failures": sum(
            b["failed"] if a["size_direction"] else a["failed"] for a, b in pairs),
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
    indexed = defaultdict(list)
    for item in source:
        indexed[(item["scene_id"], int(item["ann_id"]), str(item["object_id"]))].append(item)
    rows = []
    for entry in manifest["rows"]:
        index = int(entry["manifest_index"])
        key = (entry["scene_id"], int(entry["ann_id"]), str(entry["target_object_id"]))
        if len(indexed[key]) != 1 or outcomes[index]["scene"] != key[0]:
            raise ValueError("Manifest/description/outcome identity differs")
        rows.append({
            "manifest_index": index, "scene": key[0], "stratum": entry["stratum"],
            "failed": bool(outcomes[index]["failed"]),
            "size_direction": size_direction(indexed[key][0]["description"]),
        })
    if len(rows) != 256 or len({r["manifest_index"] for r in rows}) != 256:
        raise ValueError("Frozen cohort incomplete")
    rows.sort(key=lambda r: r["manifest_index"])
    result = {"contract": "m95_explicit_size_language_screen_v1",
              "manifest_sha256": MANIFEST_SHA, "outcome_sha256": OUTCOME_SHA,
              "source_sha256": digest(a.source), "summary": analyze(rows),
              "rows": rows, "admission": False}
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
