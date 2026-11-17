"""Independent-transform repeatability of frozen M95 wrong-context errors."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST = ROOT / "pipeline/reports/m95_seed_exact_1999_20260927.json"
SECOND = ROOT / "pipeline/reports/m95_seed_exact_2000_20260927.json"
FIRST_SHA = "1dc93b87cf42526f5608fdd74641c949f58bf0fe3b7cc8a5cb90b1960110cbe7"
SECOND_SHA = "4765c45afa2706ddb949020ffab4226214eef80655c19abd5e6af3b19b5a5910"


def analyze(a, b):
    if (a["checkpoint_sha256"] != b["checkpoint_sha256"]
            or a["population_manifest_sha256"] != b["population_manifest_sha256"]
            or a["transform_seed"] != 1999 or b["transform_seed"] != 2000
            or not a["exact_input_fingerprints"]
            or not b["exact_input_fingerprints"]):
        raise ValueError("Native repeat provenance differs")
    maps = []
    for source in (a, b):
        mapping = {}
        for row in source["rows"]:
            key = (row["scene"], row["ann_id"])
            if key in mapping:
                raise ValueError("Duplicate native expression")
            mapping[key] = row
        if len(mapping) != 128:
            raise ValueError("Native population changed")
        maps.append(mapping)
    if set(maps[0]) != set(maps[1]):
        raise ValueError("Cross-transform identity drift")
    transitions = Counter()
    scene_exposure = defaultdict(list)
    exposed = []
    for key in sorted(maps[0]):
        first, second = (m[key] for m in maps)
        if first["batch_input_sha256"] == second["batch_input_sha256"]:
            raise ValueError("Independent transform input unchanged")
        labels = []
        for row in (first, second):
            if not 0 <= row["selected_mask_iou"] <= 1:
                raise ValueError("Invalid selected mask IoU")
            labels.append("context_failure" if (
                row["selected_seed_is_context"]
                and row["selected_mask_iou"] <= .5) else
                "other_failure" if row["selected_mask_iou"] <= .5 else
                "success")
        transitions[tuple(labels)] += 1
        scene_exposure[key[0]].append((labels[0], labels[1]))
        if "context_failure" in labels:
            exposed.append({"scene": key[0], "ann_id": key[1],
                            "seed1999": labels[0], "seed2000": labels[1]})
    return {
        "contract": "m95_context_error_repeat_v1",
        "admission": False,
        "source_sha256": [FIRST_SHA, SECOND_SHA],
        "expressions": 128,
        "scenes": len(scene_exposure),
        "transition_counts": {
            "%s_to_%s" % key: count for key, count in sorted(transitions.items())},
        "context_seed1999": sum(
            count for (x, _), count in transitions.items()
            if x == "context_failure"),
        "context_seed2000": sum(
            count for (_, y), count in transitions.items()
            if y == "context_failure"),
        "persistent_context_failures": transitions[("context_failure", "context_failure")],
        "union_context_failures": len(exposed),
        "exposed": exposed,
        "scene_exposure_count": {
            scene: {
                "seed1999": sum(x == "context_failure" for x, _ in rows),
                "seed2000": sum(y == "context_failure" for _, y in rows),
                "persistent": sum(x == y == "context_failure" for x, y in rows)}
            for scene, rows in sorted(scene_exposure.items())},
        "limits": "Fixed TRAIN repeated transforms; no novel mechanism, causal intervention, admission or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or any(
            hashlib.sha256(path.read_bytes()).hexdigest() != sha
            for path, sha in ((FIRST, FIRST_SHA), (SECOND, SECOND_SHA))):
        raise ValueError("Output exists or frozen source changed")
    result = analyze(json.loads(FIRST.read_text(encoding="utf-8")),
                     json.loads(SECOND.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "context_seed1999", "context_seed2000", "persistent_context_failures",
        "union_context_failures", "scenes")}))


if __name__ == "__main__":
    main()
