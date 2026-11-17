"""Read-only role-transition incidence on an existing native capture."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or digest(args.source) != args.expected_sha:
        raise ValueError("Source identity differs or output already exists")
    source = json.loads(args.source.read_text(encoding="utf-8"))
    if not source.get("role_census") or len(source["rows"]) != 128:
        raise ValueError("Native role census population incomplete")
    scenes = defaultdict(list)
    for row in source["rows"]:
        scenes[row["scene"]].append(row)
    if len(scenes) != 32 or any(len(group) != 4 for group in scenes.values()):
        raise ValueError("Scene/expression population differs")

    pairs = context_pairs = zero_pairs = context_seeds = zero_seeds = 0
    selected_context_failures = 0
    physical_roles = set()
    context_scenes = set()
    same_batch = 0
    same_input_fingerprint = 0
    for scene, group in scenes.items():
        for a in group:
            if len(a["target_instances"]) != 1:
                raise ValueError("Expected one native target instance")
            target = int(a["target_instances"][0])
            for b in group:
                if a is b or target in b["target_instances"]:
                    continue
                pairs += 1
                same_batch += a["batch"] == b["batch"]
                same_input_fingerprint += (
                    a["batch_input_sha256"] == b["batch_input_sha256"])
                roles = [
                    role for role in b["unprotected_seed_roles"]
                    if int(role[1]) == target
                ]
                context = sum(float(role[2]) == .25 for role in roles)
                zero = sum(float(role[2]) == 0 for role in roles)
                if context:
                    context_pairs += 1
                    context_seeds += context
                    context_scenes.add(scene)
                    physical_roles.add((scene, target))
                    selected_context_failures += int(
                        bool(b["selected_seed_is_context"])
                        and int(b["selected_seed_instance"]) == target
                        and float(b["selected_mask_iou"]) <= .5)
                if zero:
                    zero_pairs += 1
                    zero_seeds += zero
    output = {
        "contract": "m95_role_transition_incidence_v1",
        "admission": False,
        "source_sha256": digest(args.source),
        "expressions": 128,
        "scenes": len(scenes),
        "distinct_target_ordered_pairs": pairs,
        "same_batch_pairs": same_batch,
        "same_collated_input_fingerprint_pairs": same_input_fingerprint,
        "target_to_context_pairs": context_pairs,
        "target_to_context_scenes": len(context_scenes),
        "distinct_physical_target_context_roles": len(physical_roles),
        "target_to_context_seed_positions": context_seeds,
        "target_to_zero_pairs": zero_pairs,
        "target_to_zero_seed_positions": zero_seeds,
        "selected_context_failures_with_role_pair": selected_context_failures,
        "limits": "Role incidence only: no identical seed correspondence, causal control, "
                  "new gradient, prior-art distinction or efficacy.",
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
