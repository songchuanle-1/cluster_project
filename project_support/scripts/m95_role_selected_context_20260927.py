"""Frozen same-population role coverage of selected wrong-context outcomes."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "pipeline/reports/m95_target_seed_size_native_20260927.json"
ROLE = ROOT / "pipeline/reports/m95_role_gradient_native_20260927.json"
SEED_SHA = "97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c"
ROLE_SHA = "b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0"


def analyze(seed, role):
    if (seed["checkpoint_sha256"] != role["checkpoint_sha256"]
            or seed["population_manifest_sha256"] != role["population_manifest_sha256"]
            or seed["transform_seed"] != role["transform_seed"]
            or not seed["exact_input_fingerprints"]
            or not role["exact_input_fingerprints"]):
        raise ValueError("Frozen capture provenance differs")
    cohort = {}
    for row in seed["rows"]:
        key = (row["scene"], row["ann_id"])
        if key in cohort:
            raise ValueError("Duplicate seed identity")
        cohort[key] = row
    if len(cohort) != 128:
        raise ValueError("Frozen population differs")
    matched = set()
    for row in role["rows"]:
        key = (row["scene"], row["ann_id"])
        if key in matched or key not in cohort:
            raise ValueError("Missing or duplicate role expression")
        other = cohort[key]
        if (row["batch_input_sha256"] != other["batch_input_sha256"]
                or abs(row["selected_mask_iou"] -
                       other["selected_mask_iou"]) > 1e-6):
            raise ValueError("Same-population fingerprint/outcome drift")
        matched.add(key)
    if matched != set(cohort):
        raise ValueError("Incomplete role population")
    covered = {(row["scene"], row["target_ann"])
               for row in role["role_gradient_rows"]}
    if len(covered) != 20 or not covered.issubset(cohort):
        raise ValueError("Frozen target role cohort differs")
    arms = defaultdict(lambda: defaultdict(int))
    exposed = []
    for key, row in cohort.items():
        arm = "covered" if key in covered else "uncovered"
        failure = row["selected_mask_iou"] <= 0.5
        wrong_context = bool(row["selected_seed_is_context"]) and failure
        arms[arm]["expressions"] += 1
        arms[arm]["failures"] += int(failure)
        arms[arm]["selected_context_failures"] += int(wrong_context)
        arms[arm]["nonexposed_failures"] += int(failure and not wrong_context)
        arms[arm]["successes"] += int(not failure)
        if wrong_context:
            exposed.append({"scene": key[0], "ann_id": key[1],
                            "role_covered": key in covered})
    if len(exposed) != 17:
        raise ValueError("Frozen selected-context failure count differs")
    return {
        "contract": "m95_role_selected_context_v1",
        "admission": False,
        "seed_sha256": SEED_SHA,
        "role_sha256": ROLE_SHA,
        "arms": {name: dict(arms[name]) for name in ("covered", "uncovered")},
        "exposed": sorted(exposed, key=lambda r: (r["scene"], r["ann_id"])),
        "covered_exposed_scenes": len({r["scene"] for r in exposed if r["role_covered"]}),
        "coverage_hypothesis_supported": sum(r["role_covered"] for r in exposed) > 0,
        "limits": "Frozen TRAIN representativeness only; no causal intervention, new mechanism, admission or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or any(
            hashlib.sha256(path.read_bytes()).hexdigest() != sha
            for path, sha in ((SEED, SEED_SHA), (ROLE, ROLE_SHA))):
        raise ValueError("Existing output or changed source hash")
    result = analyze(json.loads(SEED.read_text(encoding="utf-8")),
                     json.loads(ROLE.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"arms": result["arms"],
                      "coverage_hypothesis_supported": result["coverage_hypothesis_supported"]}))


if __name__ == "__main__":
    main()
