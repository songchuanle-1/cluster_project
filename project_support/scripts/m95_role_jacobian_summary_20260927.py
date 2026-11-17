"""Factor native scalar focal signs from sampler-input gradients."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pipeline/reports/m95_role_gradient_scalar_native_20260927.json"
OUTPUT = ROOT / "pipeline/reports/m95_role_jacobian_summary_20260927.json"
EXPECTED = "cec227e442bcf490f9e6304c242376864b9a27f0590ea15390d71d7acc120fc6"


def main():
    if OUTPUT.exists() or hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("Source changed or output exists")
    rows = json.loads(SOURCE.read_text(encoding="utf-8"))["role_gradient_rows"]
    groups = defaultdict(list)
    for row in rows:
        scalars = row["scalar_gradients"]
        if any(value == 0 for value in scalars):
            raise ValueError("Zero focal scalar derivative")
        jacobian_cos = [
            row["cosines"][arm] *
            (1 if scalars[0] * scalars[arm + 1] > 0 else -1)
            for arm in (0, 1)]
        groups[(row["scene"], row["instance"], row["fps_position"])].append(
            jacobian_cos)
    scenes = defaultdict(list)
    for (scene, _, _), pairs in groups.items():
        if len(pairs) != 2:
            raise ValueError("Physical position multiplicity changed")
        scenes[scene].append([sum(p[arm] for p in pairs) / len(pairs)
                              for arm in (0, 1)])
    detail = [
        {"scene": scene, "physical_positions": len(pairs),
         "target_context_jacobian_cos": sum(p[0] for p in pairs) / len(pairs),
         "target_zero_jacobian_cos": sum(p[1] for p in pairs) / len(pairs),
         "target_zero_jacobian_positive": sum(p[1] > 0 for p in pairs)}
        for scene, pairs in sorted(scenes.items())
    ]
    result = {
        "contract": "m95_role_jacobian_direction_v1",
        "admission": False, "source_sha256": EXPECTED,
        "comparisons": len(rows), "unique_physical_positions": len(groups),
        "scenes": len(detail),
        "scene_target_zero_jacobian_positive_mean": sum(
            r["target_zero_jacobian_cos"] > 0 for r in detail),
        "scene_target_context_jacobian_positive_mean": sum(
            r["target_context_jacobian_cos"] > 0 for r in detail),
        "target_zero_jacobian_positive_comparisons": sum(
            row["cosines"][1] * (
                1 if row["scalar_gradients"][0] *
                     row["scalar_gradients"][2] > 0 else -1) > 0
            for row in rows),
        "detail": detail,
        "limits": "Chain-rule directional factorization only; expression "
                  "language changes the Jacobian. No randomized intervention, "
                  "new method, resource check or trained efficacy.",
    }
    if len(groups) != 133 or len(detail) != 13:
        raise ValueError("Frozen denominator changed")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "unique_physical_positions", "scenes",
        "scene_target_zero_jacobian_positive_mean",
        "target_zero_jacobian_positive_comparisons")}))


if __name__ == "__main__":
    main()
