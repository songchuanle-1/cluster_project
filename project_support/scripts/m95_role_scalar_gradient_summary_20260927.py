"""Audit native scalar focal signs against shared-feature vector conflicts."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "pipeline/reports"
SOURCE = REPORT / "m95_role_gradient_scalar_native_20260927.json"
PRIOR = REPORT / "m95_role_gradient_native_20260927.json"
OUTPUT = REPORT / "m95_role_scalar_gradient_summary_20260927.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError("Output exists")
    current = json.loads(SOURCE.read_text(encoding="utf-8"))
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    if (len(current["rows"]) != 128
            or len(current["role_gradient_rows"]) != 266
            or len(prior["role_gradient_rows"]) != 266
            or current["checkpoint_sha256"] != prior["checkpoint_sha256"]
            or current["role_triples_sha256"] != prior["role_triples_sha256"]):
        raise ValueError("Frozen capture mismatch")
    for new, old in zip(current["rows"], prior["rows"]):
        if (new["batch_input_sha256"] != old["batch_input_sha256"]
                or new["selected_seed"] != old["selected_seed"]):
            raise ValueError("Expression fingerprint/selection changed")
    by_scene = defaultdict(list)
    by_physical = defaultdict(list)
    for new, old in zip(current["role_gradient_rows"], prior["role_gradient_rows"]):
        key = tuple(new[k] for k in (
            "scene", "instance", "target_ann", "context_ann",
            "zero_ann", "fps_position"))
        if (key != tuple(old[k] for k in (
                "scene", "instance", "target_ann", "context_ann",
                "zero_ann", "fps_position"))
                or abs(new["target_final_label"] -
                       old["target_final_label"]) > 1e-6):
            raise ValueError("Physical binding changed")
        if any(x == 0 for x in new["scalar_gradients"]):
            raise ValueError("Zero scalar gradient")
        by_scene[new["scene"]].append(new)
        by_physical[tuple(new[k] for k in (
            "scene", "instance", "fps_position"))].append(new)
    rows = current["role_gradient_rows"]
    result = {
        "contract": "m95_role_scalar_gradient_summary_v1",
        "admission": False, "source_sha256": digest(SOURCE),
        "prior_sha256": digest(PRIOR),
        "comparisons": len(rows), "unique_physical_positions": len(by_physical),
        "scenes": len(by_scene),
        "target_scalar_positive": sum(r["scalar_gradients"][0] > 0 for r in rows),
        "context_scalar_positive": sum(r["scalar_gradients"][1] > 0 for r in rows),
        "zero_scalar_positive": sum(r["scalar_gradients"][2] > 0 for r in rows),
        "zero_vector_negative": sum(r["dots"][1] < 0 for r in rows),
        "zero_vector_negative_scalar_opposite": sum(
            r["dots"][1] < 0 and
            r["scalar_gradients"][0] * r["scalar_gradients"][2] < 0
            for r in rows),
        "context_vector_negative": sum(r["dots"][0] < 0 for r in rows),
        "context_vector_negative_scalar_opposite": sum(
            r["dots"][0] < 0 and
            r["scalar_gradients"][0] * r["scalar_gradients"][1] < 0
            for r in rows),
        "scene_details": [
            {"scene": scene, "comparisons": len(group),
             "target_scalar_positive": sum(
                 r["scalar_gradients"][0] > 0 for r in group),
             "zero_vector_negative_scalar_same": sum(
                 r["dots"][1] < 0 and
                 r["scalar_gradients"][0] * r["scalar_gradients"][2] > 0
                 for r in group)}
            for scene, group in sorted(by_scene.items())
        ],
        "limits": "Scalar sign explains most but not all vector-dot signs; "
                  "the Jacobian differs by expression. This is not a matched "
                  "causal training intervention or an independent new mechanism.",
    }
    if len(by_physical) != 133 or len(by_scene) != 13:
        raise ValueError("Physical/scene denominator changed")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "comparisons", "target_scalar_positive",
        "zero_vector_negative_scalar_opposite",
        "context_vector_negative_scalar_opposite")}))


if __name__ == "__main__":
    main()
