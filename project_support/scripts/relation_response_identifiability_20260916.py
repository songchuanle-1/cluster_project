"""Static joins and finite controls for the saved noun-response evidence."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "pipeline/reports" / name).read_text(encoding="utf-8"))


def key(row):
    return row["scene"], int(row["ann_id"])


def main():
    names = [
        "anchor_noun_intervention_20260916.json",
        "vertical_relation_bounds_20260916.json",
        "mention_role_objective_20260916.json",
        "modality_cancellation_20260916.json",
    ]
    noun, vertical, role, modality = map(load, names)
    index = {key(r): r for r in noun["rows"]}
    assert len(index) == len(noun["rows"]) == 107
    relation_join = []
    for row in vertical["rows"]:
        intervention = index.get(key(row))
        relation_join.append({
            "scene": row["scene"], "ann_id": row["ann_id"],
            "anchor_name": row["anchor_name"], "confident_wrong": row["confident_wrong"],
            "intervened_noun": intervention["old"] if intervention else None,
            "same_anchor_string": bool(intervention and intervention["old"] == row["anchor_name"]),
            "final_tv": intervention["layers"][-1]["tv"] if intervention else None,
        })
    role_join = []
    for row in role["control_manifest"]:
        intervention = index.get(key(row))
        role_join.append({
            "scene": row["scene"], "ann_id": row["ann_id"], "node_id": row["node_id"],
            "cue": row["cue"],
            "intervention_present": intervention is not None,
            "same_mention_intervened": bool(intervention and intervention["node_id"] == row["node_id"]),
        })
    modality_index = {key(r): r for r in modality["rows"]}
    assert len(modality_index) == len(modality["rows"])
    assert set(index).issubset(modality_index)
    # For normalized attention, zero-sum signed changes give a sharp TV bound.
    # Enumerate a rational simplex and monotone geometric CDF values.
    simplex = [tuple(x / 4 for x in counts)
               for counts in itertools.product(range(5), repeat=3) if sum(counts) == 4]
    profiles = list(itertools.combinations_with_replacement((0, .5, 1), 3))
    bound_checks = 0
    for a, b, f in itertools.product(simplex, simplex, profiles):
        tv = sum(abs(x - y) for x, y in zip(a, b)) / 2
        delta = sum((y - x) * z for x, y, z in zip(a, b, f))
        assert abs(delta) <= tv * (max(f) - min(f)) + 1e-12
        bound_checks += 1
    f = (0, .5, 1)
    a = (.25, .5, .25)
    alternatives = ((.5, 0, .5), (.75, 0, .25), (.25, 0, .75))
    witnesses = []
    for b in alternatives:
        witnesses.append({
            "a": a, "b": b, "f": f,
            "tv": sum(abs(x - y) for x, y in zip(a, b)) / 2,
            "delta_R": sum((y - x) * z for x, y, z in zip(a, b, f)),
        })
    assert [w["tv"] for w in witnesses] == [.5, .5, .5]
    assert [w["delta_R"] for w in witnesses] == [0, -.25, .25]
    # TV and unchanged peak can both hold while a downstream result is invariant.
    a2, b2, f2 = (.6, .3, .1), (.6, .1, .3), (0, 1, 1)
    assert max(range(3), key=a2.__getitem__) == max(range(3), key=b2.__getitem__)
    assert abs(sum((y-x)*z for x,y,z in zip(a2,b2,f2))) < 1e-12
    exact = [r for r in relation_join if r["same_anchor_string"]]
    result = {
        "scope": "Static archived TRAIN evidence joins and exact finite arithmetic; no native execution.",
        "relation_join": relation_join,
        "role_join": role_join,
        "summary": {
            "noun_expressions": len(index),
            "replacement_counts": {n: sum(r["new"] == n for r in noun["rows"])
                                   for n in sorted({r["new"] for r in noun["rows"]})},
            "vertical_edges": len(relation_join),
            "vertical_with_noun_intervention": sum(r["final_tv"] is not None for r in relation_join),
            "same_anchor_string_edges": len(exact),
            "same_anchor_string_wrong_edges": sum(r["confident_wrong"] for r in exact),
            "role_mentions": len(role_join),
            "role_mentions_actually_intervened": sum(r["same_mention_intervened"] for r in role_join),
            "modality_expression_overlap": len(set(index) & set(modality_index)),
            "bound_checks": bound_checks,
        },
        "derivation": [
            "For fixed target mass/geometry let f_j=P_t(z<z_j), R(a)=sum_j a_j*f_j.",
            "For normalized a,b, d=b-a has sum zero. Center f by its midrange.",
            "|d dot f| <= (max(f)-min(f))*sum(abs(d))/2 = range(f)*TV(a,b).",
            "This is an upper bound, not a positive lower bound; TV alone cannot establish relation response.",
            "Saved scalar TV/peak flags omit signed d and f; identical TV allows zero/opposite relation changes.",
        ],
        "witnesses": witnesses,
        "next_actions": {
            "same-forward-coverage-diagnosis":
                "Use relation_join exact-anchor rows as bounded eligibility, not anchor labels. "
                "Extend the existing native noun helper to record signed attention and fixed physical support/CDF "
                "for original/replacement/repeat; compute relation delta with target/geometry fixed. "
                "Do not repeat attention-only capture. First verify attention axes map to physical support; "
                "if not, reject this readout rather than pretending TV is a relation result.",
            "same-target-description-grounding":
                "Use role_join to separate actually intervened mentions from merely same-expression overlap. "
                "Do not claim same-noun ownership is tested by a helper excluding main words. "
                "Derive instance-identifying input for the untested role mentions from existing graph/scene evidence; "
                "no binary-mixture, lexical merge, new labels or duplicate role audit.",
            "input-modality-distinguishability":
                "107 expression joins do not align modality feature coordinates with anchor attention support. "
                "Inspect the existing modality capture and attention producer for a shared physical index "
                "before defining correspondence; do not correlate TV with cancellation as causal correspondence "
                "or admit generic fusion.",
        },
        "limitations": [
            "String equality is an eligibility check, not referent truth.",
            "No attention vectors, target CDFs or cross-modal support alignment are present in these JSON summaries.",
            "The bound is a diagnostic mathematical fact, not a novel model or efficacy claim.",
            "No additional candidate meets admission; three slots remain scientifically unfilled.",
        ],
        "evidence": [
            {"path": "pipeline/reports/" + n,
             "sha256": hashlib.sha256((ROOT / "pipeline/reports" / n).read_bytes()).hexdigest()}
            for n in names
        ],
    }
    path = ROOT / "pipeline/reports/relation_response_identifiability_20260916.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(json.dumps(relation_join, indent=2))


if __name__ == "__main__":
    main()
