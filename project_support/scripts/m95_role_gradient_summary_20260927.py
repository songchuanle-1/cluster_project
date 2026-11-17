"""Audit frozen native shared-position gradient contrasts without changing training."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "pipeline/reports"
NATIVE = REPORTS / "m95_role_gradient_native_20260927.json"
TRIPLES = REPORTS / "m95_role_triples_20260927.json"
PREVIOUS = REPORTS / "m95_cross_expression_role_1999_20260927.json"
OUTPUT = REPORTS / "m95_role_gradient_summary_20260927.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError("Summary exists")
    native = json.loads(NATIVE.read_text(encoding="utf-8"))
    triples = json.loads(TRIPLES.read_text(encoding="utf-8"))
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (native["role_triples_sha256"] != sha(TRIPLES)
            or native["checkpoint_sha256"] != previous["checkpoint_sha256"]
            or len(native["rows"]) != 128 or len(triples["triples"]) != 38):
        raise ValueError("Native population/checkpoint or preregistration mismatch")
    old = {(row["scene"], row["ann_id"]): row for row in previous["rows"]}
    for row in native["rows"]:
        ref = old.pop((row["scene"], row["ann_id"]))
        if (row["batch_input_sha256"] != ref["batch_input_sha256"]
                or row["selected_seed"] != ref["selected_seed"]):
            raise ValueError("Native input or selection changed")
    if old:
        raise ValueError("Native expression missing")
    rows = native["role_gradient_rows"]
    if len(rows) != 266:
        raise ValueError("Expected physical role triple positions missing")
    grouped = defaultdict(list)
    unique = set()
    for row in rows:
        if (not 0 < row["target_final_label"] <= 1
                or any(x <= 0 for x in row["norms"])
                or any(x is None for x in row["cosines"])):
            raise ValueError("Positive or nonzero-gradient gate failed")
        grouped[row["scene"]].append(row)
        unique.add((row["scene"], row["instance"], row["fps_position"]))
    scenes = []
    for scene, items in sorted(grouped.items()):
        scenes.append({
            "scene": scene, "positions": len(items),
            "context_negative": sum(x["dots"][0] < 0 for x in items),
            "zero_negative": sum(x["dots"][1] < 0 for x in items),
            "context_cosine_mean": sum(x["cosines"][0] for x in items) / len(items),
            "zero_cosine_mean": sum(x["cosines"][1] for x in items) / len(items),
        })
    result = {
        "contract": "m95_role_gradient_summary_v1",
        "admission": False,
        "native_sha256": sha(NATIVE),
        "triple_sha256": sha(TRIPLES),
        "previous_sha256": sha(PREVIOUS),
        "expression_fingerprint_mismatches": 0,
        "role_triples": 38,
        "shared_position_comparisons": len(rows),
        "unique_physical_positions": len(unique),
        "scenes": len(scenes),
        "target_label_positive": len(rows),
        "target_label_exact_one": sum(x["target_final_label"] == 1 for x in rows),
        "nonzero_gradients_all_arms": len(rows),
        "context_negative": sum(x["dots"][0] < 0 for x in rows),
        "zero_negative": sum(x["dots"][1] < 0 for x in rows),
        "scene_context_more_negative": sum(
            x["context_negative"] > x["zero_negative"] for x in scenes),
        "scene_zero_more_negative": sum(
            x["zero_negative"] > x["context_negative"] for x in scenes),
        "scenes_detail": scenes,
        "preregistered_direction_supported": False,
        "limits": (
            "Same physical positions are repeated across ordered triples; "
            "scene is the independent unit. Native gradients are diagnostic, "
            "not a matched training intervention or evidence of efficacy. "
            "The preregistered context-specific conflict direction reverses; "
            "no label shuffle is needed to reject that realization."
        ),
    }
    if (len(unique) != 133 or len(scenes) != 13
            or result["scene_context_more_negative"] != 0
            or result["scene_zero_more_negative"] != 13):
        raise ValueError("Unexpected role-gradient outcome; inspect manually")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "shared_position_comparisons", "unique_physical_positions", "scenes",
        "context_negative", "zero_negative", "scene_zero_more_negative")}))


if __name__ == "__main__":
    main()
