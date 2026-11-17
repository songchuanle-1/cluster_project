"""Aggregate repeated frozen role triples at the physical seed/scene unit."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "pipeline/reports/m95_role_gradient_native_20260927.json"
OUTPUT = ROOT / "pipeline/reports/m95_role_gradient_dedup_20260927.json"
EXPECTED = "b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0"


def main():
    if OUTPUT.exists():
        raise ValueError("Dedup output exists")
    if hashlib.sha256(INPUT.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("Native input changed")
    rows = json.loads(INPUT.read_text(encoding="utf-8"))["role_gradient_rows"]
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["scene"], row["instance"], row["fps_position"])].append(row)
    by_scene = defaultdict(list)
    for (scene, _, _), repeats in grouped.items():
        if len(repeats) != 2 or any(
                any(n <= 0 for n in row["norms"]) for row in repeats):
            raise ValueError("Unexpected multiplicity or zero gradient")
        by_scene[scene].append({
            "context_negative": sum(row["dots"][0] < 0 for row in repeats) / 2,
            "zero_negative": sum(row["dots"][1] < 0 for row in repeats) / 2,
            "cos_difference": sum(
                row["cosines"][0] - row["cosines"][1] for row in repeats) / 2,
        })
    detail = []
    for scene, positions in sorted(by_scene.items()):
        count = len(positions)
        detail.append({
            "scene": scene, "physical_positions": count,
            "context_negative_fraction": sum(
                r["context_negative"] for r in positions) / count,
            "zero_negative_fraction": sum(
                r["zero_negative"] for r in positions) / count,
            "context_minus_zero_cosine": sum(
                r["cos_difference"] for r in positions) / count,
        })
    result = {
        "contract": "m95_role_gradient_dedup_v1",
        "admission": False, "source_sha256": EXPECTED,
        "comparisons": len(rows), "physical_positions": len(grouped),
        "scenes": len(detail), "multiplicity": 2,
        "scenes_context_more_negative": sum(
            r["context_negative_fraction"] > r["zero_negative_fraction"]
            for r in detail),
        "scenes_zero_more_negative": sum(
            r["zero_negative_fraction"] > r["context_negative_fraction"]
            for r in detail),
        "scenes_context_higher_cosine": sum(
            r["context_minus_zero_cosine"] > 0 for r in detail),
        "detail": detail,
        "limitations": "Repeated physical seeds aggregated; distinct scenes are the "
                       "independent descriptive unit. No randomized identity control.",
    }
    if len(grouped) != 133 or len(detail) != 13:
        raise ValueError("Frozen cohort differs")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "physical_positions", "scenes", "scenes_context_more_negative",
        "scenes_zero_more_negative", "scenes_context_higher_cosine")}))


if __name__ == "__main__":
    main()
