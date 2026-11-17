"""Audit what category-set supervision identifies in archived TRAIN captures."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "pipeline/reports/mention_instance_support_20260916.json"
GRAPH = ROOT / "pipeline/reports/mention_graph_observability_20260916.json"
OUT = ROOT / "pipeline/reports/correspondence_identification_20260916.json"


def category_loss(probabilities, candidates):
    return -math.log(sum(probabilities[i] for i in candidates))


def checks():
    # Fixed total category mass leaves all within-category reallocations invisible.
    tests = 0
    for count in range(2, 21):
        mass = 0.6
        base = [mass / count] * count + [1 - mass]
        shifted = base.copy()
        shifted[0] += mass / (2 * count)
        shifted[1] -= mass / (2 * count)
        assert abs(category_loss(base, range(count)) -
                   category_loss(shifted, range(count))) < 1e-12
        assert base != shifted
        tests += 1
    assert category_loss([0.6, 0.4], [0]) == -math.log(0.6)
    tests += 1
    return tests


def run():
    data = json.loads(SUPPORT.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    rows = data["rows"]
    index = {(r["scene"], r["ann_id"], r["node_id"]): r for r in rows}
    assert len(index) == len(rows), "Duplicate mention keys must not be merged."
    groups = {}
    for name, selected in (
        ("all", rows),
        ("success", [r for r in rows if r["success"]]),
        ("confident_wrong", [r for r in rows if r["confident_wrong"]]),
    ):
        counts = [len(r["candidates"]) for r in selected]
        groups[name] = {
            "mentions": len(selected),
            "expressions": len({(r["scene"], r["ann_id"]) for r in selected}),
            "scenes": len({r["scene"] for r in selected}),
            "empty": sum(n == 0 for n in counts),
            "singleton": sum(n == 1 for n in counts),
            "multiple": sum(n > 1 for n in counts),
            "target_containing": sum(r["target_in_candidates"] for r in selected),
            "within_set_probability_degrees_unidentified": sum(max(n - 1, 0) for n in counts),
        }
    joins = []
    for g in graph["rows"]:
        key = (g["scene"], g["ann_id"], g["node_id"])
        r = index.get(key)
        joins.append({
            "key": list(key), "matched": r is not None,
            "candidate_count": len(r["candidates"]) if r else None,
            "target_in_candidates": r["target_in_candidates"] if r else None,
            "isolated": not g["incident_edges"],
            "missing_endpoint": bool(g["dangling_edges"]),
        })
    result = {
        "scope": "Static reanalysis of archived fixed TRAIN captures; no native forward, "
                 "optimizer, inference GT or efficacy evidence.",
        "checks_passed": checks(),
        "derivation": {
            "objective": "L=-log(sum_{i in C} p_i), p=softmax(z)",
            "gradient": "dL/dz_j=p_j-1[j in C]*p_j/sum_{i in C}p_i",
            "null_space": "For |C|=k>1 and interior probabilities, any perturbation "
                          "supported on C with sum zero preserves L exactly; k-1 "
                          "probability directions are unobserved.",
            "empty": "C empty gives infinite loss, not a negative/background label.",
            "singleton": "Algebra reduces to CE, but exact-name uniqueness does not "
                         "establish parser correctness or intended physical referent.",
            "consequence": "Neither graph-distinct mention tokens nor paired modalities "
                           "remove this objective ambiguity unless they provide a "
                           "validated instance-specific constraint. This is an "
                           "objective-specific limitation, not impossibility of learning.",
        },
        "groups": groups,
        "graph_joins": joins,
        "limitations": [
            "Exact-name sets use existing raw TRAIN annotation for diagnosis only.",
            "No claim that the actual model optimizes this hypothetical objective.",
            "Repeated mention/scene counts are not independent observations.",
            "No complete mechanism or novelty claim; no new standalone candidate.",
        ],
        "sources": [
            {"path": p.relative_to(ROOT).as_posix(),
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in (SUPPORT, GRAPH, Path(__file__))
        ],
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": result["checks_passed"], "groups": groups,
                      "graph_matched": sum(r["matched"] for r in joins),
                      "graph_total": len(joins),
                      "isolated": sum(r["isolated"] for r in joins),
                      "missing_endpoint": sum(r["missing_endpoint"] for r in joins)}, indent=2))


if __name__ == "__main__":
    run()
