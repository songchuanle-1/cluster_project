"""Audit archived rank evidence, without native data access or model changes."""
import ast
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pipeline/reports/modality_identity_separability_20260916.json"
SCRIPT = ROOT / "scripts/modality_identity_separability_20260916.py"
OUT = ROOT / "pipeline/reports/modality_identity_claim_audit_20260916.json"


def counterexample(cosine):
    # Opposite pairs make the scene mean exactly zero in both constructions.
    w = (1.0, 0.0)
    t = (cosine, math.sqrt(1 - cosine * cosine))
    vectors = [w, t, (-w[0], -w[1]), (-t[0], -t[1])]
    similarities = [sum(a * b for a, b in zip(w, v)) for v in vectors[1:]]
    return {
        "target_rank": 1 + sum(v > similarities[0] for v in similarities[1:]),
        "target_wrong_squared_distance": sum((a - b) ** 2 for a, b in zip(w, t)),
        "scene_mean": [sum(v[j] for v in vectors) / 4 for j in range(2)],
    }


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = data["rows"]
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    filters = [ast.unparse(node.test) for node in ast.walk(tree)
               if isinstance(node, ast.If)
               and any(isinstance(child, ast.Continue) for child in node.body)]
    collapsed, separated = counterexample(1.0), counterexample(0.2)
    assert collapsed["target_rank"] == separated["target_rank"] == 1
    assert collapsed["target_wrong_squared_distance"] == 0
    assert separated["target_wrong_squared_distance"] > 1.5
    assert collapsed["scene_mean"] == separated["scene_mean"] == [0.0, 0.0]
    assert "float(iou[chosen]) > 0.5" in filters
    assert not any("max" in expr and "iou" in expr for expr in filters)
    counts = Counter(r["scene"] for r in rows)
    better = sum(r["feat2d_best_target_rank"] < r["feat3d_best_target_rank"] for r in rows)
    worse = sum(r["feat2d_best_target_rank"] > r["feat3d_best_target_rank"] for r in rows)
    report = {
        "scope": "Static archived evidence and mathematical counterexample only.",
        "rows": len(rows), "unique_scenes": len(counts), "rows_per_scene": dict(counts),
        "paired_rank": {"lower_2d": better, "higher_2d": worse,
                        "ties": len(rows) - better - worse},
        "collapsed_counterexample": collapsed, "separated_counterexample": separated,
        "native_filter_expressions": filters,
        "findings": [
            "Rank is of target similarity to the wrong instance, not text-to-target discrimination.",
            "Identical and distinguishable target/wrong features can both produce rank one.",
            "The identity-loss conclusion is not identified; raw rank measurements remain valid.",
            "The producer excludes successful selections and correct instance owners, but does not test oracle-best mask IoU.",
            "Recoverable membership cannot be inferred from a matching aggregate count of 33.",
            "Rows lack annotation ID, target IDs, physical support hashes, and per-query IoU/score arrays.",
            "Cross-capture physical or annotation joins must not be inferred from scene and expression_slot alone.",
        ],
        "required_single_capture": [
            "scene, annotation ID, object IDs, point/superpoint support hashes and expression slot",
            "selected and oracle-best IoU plus all query IoUs, indis and score ranks",
            "native positive membership and best rank over every mask with IoU above .5",
            "paired raw/projected/fused/final target and distractor features on identical support",
            "same-class and different-class controls; phrase-conditioned contrast, not neighbour retrieval",
            "owned/relocated/disabled endpoint map for seven connected controls; preserve twelve disconnected controls",
            "report all 85/33/5 strata only after same-forward membership verification",
        ],
        "disposition": "Reject the current proof of identity loss, not the untested hypothesis. No admission.",
        "sources": {str(p.relative_to(ROOT)).replace("\\", "/"):
                    hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (SOURCE, SCRIPT, Path(__file__))},
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
