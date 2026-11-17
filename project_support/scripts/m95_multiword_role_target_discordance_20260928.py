"""Join frozen graph phrase roles with physical targets without model outcomes."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


POP_SHA = "325626925578df183ef3f8ffdce2b7cb7f010ccefa87de70db0b4b1353f0d664"
ROLE_SHA = "6d3e95e3e29a243152a6f5b7e73b893df96d16e2ee3432c8bf07a3f8418698f7"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--population", type=Path, required=True)
    parser.add_argument("--role", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or digest(args.population) != POP_SHA or digest(args.role) != ROLE_SHA:
        raise ValueError("Frozen inputs changed or output exists")
    pop = json.loads(args.population.read_text())
    role = json.loads(args.role.read_text())
    if (pop["contract"] != "m95_multiword_population_v1"
            or role["contract"] != "m95_multiword_population_role_v1"
            or role["population_sha256"] != POP_SHA):
        raise ValueError("Source contracts differ")
    physical = {(item["scene"], int(item["ann_id"])): item for item in pop["rows"]
                if item["other_curtain_instances"]}
    spans = {(item["scene"], int(item["ann_id"])): item for item in role["rows"]}
    if len(physical) != 102 or physical.keys() != spans.keys():
        raise ValueError("Physical/graph identity parity differs")
    grouped = defaultdict(set)
    mention_counts = Counter()
    rows = []
    for key in sorted(physical):
        scene, aid = key
        item, linguistic = physical[key], spans[key]
        has_target = any("target" in m["roles"] for m in linguistic["mentions"])
        has_other = any("other_object" in m["roles"] for m in linguistic["mentions"])
        has_unbound = any("unbound" in m["roles"] for m in linguistic["mentions"])
        for mention in linguistic["mentions"]:
            mention_counts.update(mention["roles"])
        kind = "target_span" if has_target else "unbound" if has_unbound else "other_only"
        for iid in item["target_instances"]:
            grouped[kind].add((scene, int(iid)))
        rows.append({
            "scene": scene, "ann_id": aid, "target_instances": item["target_instances"],
            "physical_target_is_curtain": bool(item["target_is_curtain"]),
            "non_target_curtain_instances": item["other_curtain_instances"],
            "has_graph_target_span": has_target, "has_graph_other_object_span": has_other,
            "has_unbound_span": has_unbound,
        })
    summary = {
        "physical_nontarget_expressions": len(rows),
        "physical_target_curtain_expressions": sum(r["physical_target_is_curtain"] for r in rows),
        "graph_target_span_expressions": sum(r["has_graph_target_span"] for r in rows),
        "graph_target_span_physical_noncurtain_expressions": sum(
            r["has_graph_target_span"] and not r["physical_target_is_curtain"] for r in rows),
        "graph_other_only_expressions": sum(
            r["has_graph_other_object_span"] and not r["has_graph_target_span"]
            and not r["has_unbound_span"] for r in rows),
        "graph_unbound_expressions": sum(r["has_unbound_span"] for r in rows),
        "mention_role_counts": dict(mention_counts),
        "unique_scene_physical_target_units_by_role": {
            label: len(units) for label, units in sorted(grouped.items())
        },
    }
    result = {
        "contract": "m95_multiword_role_target_discordance_v1",
        "admission": False,
        "inputs": {"population": POP_SHA, "role": ROLE_SHA},
        "summary": summary, "rows": rows,
        "limits": "Graph target-node spans need not bind physical curtain; no native outcome, intervention or admission.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
