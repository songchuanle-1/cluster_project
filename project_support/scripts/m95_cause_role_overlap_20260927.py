"""Fail-closed overlap of immutable M95 cause and role-gradient cohorts."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAUSE = ROOT / "pipeline/reports/m95_exact_match_cause_partition_20260925-0715.json"
SEED = ROOT / "pipeline/reports/m95_target_seed_size_native_20260927.json"
ROLE = ROOT / "pipeline/reports/m95_role_gradient_native_20260927.json"
HASHES = (
    "dc37eccc36a6903075ba26952f2be2ef664f728424101f2eb7960718b1de5bef",
    "97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c",
    "b01b4f0423ec08177cd8d1c4544f5615f1bd8b0abe80b31e8cb17cbe377b50a0",
)


def analyze(cause, seed, role):
    by_cause = {}
    for row in cause["rows"]:
        key = (row["scene_id"], row["ann_id"])
        if key in by_cause:
            raise ValueError("Duplicate cause expression")
        by_cause[key] = row
    if len(by_cause) != 256:
        raise ValueError("Cause cohort changed")
    by_seed = {}
    for row in seed["rows"]:
        key = (row["scene"], row["ann_id"])
        if key in by_seed or key not in by_cause:
            raise ValueError("Seed binding missing or duplicate")
        if abs(row["selected_mask_iou"] -
               by_cause[key]["selections"]["deployed"]["iou"]) > 1e-6:
            raise ValueError("Cross-capture selected IoU drift")
        by_seed[key] = row
    if len(by_seed) != 128:
        raise ValueError("Seed cohort changed")
    covered = set()
    for row in role["role_gradient_rows"]:
        key = (row["scene"], row["target_ann"])
        if key not in by_seed:
            raise ValueError("Unbound role target")
        covered.add(key)
    if len(covered) != 20:
        raise ValueError("Role cohort changed")
    counts = defaultdict(lambda: defaultdict(int))
    scenes = defaultdict(lambda: {True: [], False: []})
    for key, seed_row in by_seed.items():
        failure = seed_row["selected_mask_iou"] <= 0.5
        native_positive = by_cause[key]["selections"]["all_native_positive"]
        recoverable = failure and native_positive is not None and (
            native_positive["iou"] > 0.5)
        arm = key in covered
        counts[arm]["expressions"] += 1
        counts[arm]["failures"] += failure
        counts[arm]["selection_recoverable_failures"] += recoverable
        scenes[key[0]][arm].append(recoverable)
    pairs = []
    for scene, arms in sorted(scenes.items()):
        if arms[True] and arms[False]:
            pairs.append({
                "scene": scene,
                "covered_recoverable": sum(arms[True]),
                "uncovered_recoverable": sum(arms[False]),
                "covered_count": len(arms[True]),
                "uncovered_count": len(arms[False]),
            })
    return {
        "contract": "m95_cause_role_overlap_v1",
        "admission": False,
        "sources_sha256": HASHES,
        "arms": {"covered": dict(counts[True]),
                 "uncovered": dict(counts[False])},
        "within_scene_pairs": pairs,
        "limits": "TRAIN cohort overlap only; no mechanism, causality or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = (CAUSE, SEED, ROLE)
    if args.output.exists() or any(
        hashlib.sha256(p.read_bytes()).hexdigest() != sha
        for p, sha in zip(sources, HASHES)
    ):
        raise ValueError("Existing output or source hash changed")
    result = analyze(*(json.loads(p.read_text(encoding="utf-8"))
                       for p in sources))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result["arms"]))


if __name__ == "__main__":
    main()
