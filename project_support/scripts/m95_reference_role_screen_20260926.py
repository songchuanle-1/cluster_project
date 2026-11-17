"""Bounded role ownership eligibility audit on frozen TRAIN summaries."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROLE_SHA = "65e110e0a11c7486c5f552b94c917525412d6cfc8e52a10974f709a69cafc01e"
JOIN_SHA = "ea63f5e141a6a1687fd9d8a1f33768540daa22f9a537c8ef3191ac67c234802d"
GROUPS = ("explicit_other_cue", "sentence_initial_definite_repeat", "unknown")


def audit(role, join):
    entries = defaultdict(list)
    for item in role["control_manifest"]:
        entries[(str(item["scene"]), int(item["ann_id"]))].append(item)
    joined = defaultdict(list)
    for item in join["role_join"]:
        joined[(str(item["scene"]), int(item["ann_id"]))].append(item)
    if set(joined) != set(entries) or sum(map(len, joined.values())) != sum(
        map(len, entries.values())):
        raise ValueError("Role manifest join differs")
    rows = []
    for key, mentions in sorted(entries.items()):
        roles = joined[key]
        seen = set()
        for mention in mentions:
            identity = int(mention["node_id"]), mention["cue"]
            if identity in seen:
                raise ValueError("Duplicate role mention")
            seen.add(identity)
            matches = [r for r in roles if int(r["node_id"]) == identity[0]
                       and r["cue"] == identity[1]]
            if len(matches) != 1:
                raise ValueError("Role mention binding differs")
        if len({bool(m["confident_wrong"]) for m in mentions}) != 1:
            raise ValueError("Conflicting expression outcome")
        rows.append({
            "scene": key[0], "ann_id": key[1],
            "confident_wrong": bool(mentions[0]["confident_wrong"]),
            "cues": sorted({m["cue"] for m in mentions}),
            "mentions": len(mentions),
            "same_mention_intervened": any(
                r["same_mention_intervened"] for r in roles),
        })
    summary = {}
    for cue in GROUPS:
        subset = [r for r in rows if cue in r["cues"]]
        summary[cue] = {
            "expressions": len(subset),
            "scenes": len({r["scene"] for r in subset}),
            "wrong": sum(r["confident_wrong"] for r in subset),
            "same_mention_intervened": sum(
                r["same_mention_intervened"] for r in subset),
        }
    return {
        "contract": "m95_reference_role_screen_v1", "admission": False,
        "source_sha256": [ROLE_SHA, JOIN_SHA],
        "summary": summary, "rows": rows,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--role", type=Path, required=True)
    p.add_argument("--join", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or any(hashlib.sha256(path.read_bytes()).hexdigest()
                                   != expected for path, expected in (
                                       (args.role, ROLE_SHA), (args.join, JOIN_SHA))):
        raise ValueError("Output exists or frozen input hash differs")
    result = audit(json.loads(args.role.read_text(encoding="utf-8")),
                   json.loads(args.join.read_text(encoding="utf-8")))
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
