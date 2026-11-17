"""Opposing top/upper control for independent group-cue geometry."""
import argparse
import json
import re
from pathlib import Path

from m95_group_holdout_20260926 import (
    GROUP, MANIFEST_SHA, SOURCE_SHA, digest, key, physical,
)

LOWER_SHA = "ecf6d9fe21f254e512b4fc490bc8a843a256a0a8c9e8ae5cab79c86bbf894edc"
TOP = frozenset(("top", "upper"))


def select(source, manifest, lower):
    excluded = {(r["scene_id"], int(r["ann_id"]), str(r["target_object_id"]))
                for r in manifest["rows"]}
    excluded.update((r["scene"], int(r["ann_id"]), str(r["target"]))
                    for r in lower["rows"])
    selected = {}
    for item in source:
        identity = key(item)
        tokens = set(re.findall(r"[a-z]+", item["description"].lower()))
        if identity in excluded or not (tokens & TOP and tokens & GROUP):
            continue
        if identity in selected:
            raise ValueError("Duplicate selected description identity")
        selected[identity] = item
    return [{"scene": k[0], "ann_id": k[1], "target": k[2],
             "object_name": item["object_name"], "description": item["description"]}
            for k, item in sorted(selected.items())]


def main():
    p = argparse.ArgumentParser()
    for name in ("manifest", "source", "lower", "data-root", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    for path, expected in ((a.manifest, MANIFEST_SHA), (a.source, SOURCE_SHA),
                           (a.lower, LOWER_SHA)):
        if digest(path) != expected:
            raise ValueError("Frozen input hash differs: " + str(path))
    source = json.loads(a.source.read_text(encoding="utf-8"))
    rows = select(source, json.loads(a.manifest.read_text(encoding="utf-8")),
                  json.loads(a.lower.read_text(encoding="utf-8")))
    results = physical(rows, source, a.data_root)
    document = {
        "contract": "m95_group_upper_control_v1", "admission": False,
        "manifest_sha256": MANIFEST_SHA, "source_sha256": SOURCE_SHA,
        "lower_sha256": LOWER_SHA, "rows": results,
        "summary": {
            "selected": len(results),
            "scenes": len({r["scene"] for r in results}),
            "resolvable": sum(r["target_below_peer"] is not None for r in results),
            "target_above": sum(r["reverse_z_control"] is True for r in results),
            "reverse_below": sum(r["target_below_peer"] is True for r in results),
        },
    }
    a.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps(document["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
