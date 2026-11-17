"""Correct frozen M95 sampled query seed -> superpoint mapping read-only."""
import argparse
import hashlib
import json
from pathlib import Path

CAPTURE_SHA = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or sha(args.capture) != CAPTURE_SHA:
        raise ValueError("Capture identity or fresh output differs")
    import torch
    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    if len(rows) != 256:
        raise ValueError("Incomplete frozen capture")
    counts = {key: 0 for key in (
        "all_queries", "old_membership", "corrected_membership",
        "indices_different", "negative_selected",
        "negative_old_membership", "negative_corrected_membership",
        "bound_sampled_ids")}
    examples = []
    seen = set()
    for entry in capture["feature_artifacts"]:
        path = args.directory / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("Feature artifact hash mismatch")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in seen:
                raise ValueError("Duplicate expression")
            seen.add(index)
            row = rows[index]
            masks = artifact["query_masks"]
            old_inverse = row["sample_inverse"]
            fps = row["fps_superpoints"]
            selected = int(row["selected_query"])
            for query, seed in enumerate(row["sampled_seed_indices"]):
                correct = int(fps[seed])
                old = int(old_inverse[seed])
                if not 0 <= correct < len(masks[query]):
                    raise ValueError("Corrected superpoint out of mask axis")
                captured = artifact.get("identity_query", {}).get("sampled_superpoint_ids")
                if captured is not None:
                    if int(captured[query]) != correct:
                        raise ValueError("Native captured query binding differs")
                    counts["bound_sampled_ids"] += 1
                counts["all_queries"] += 1
                counts["indices_different"] += old != correct
                counts["old_membership"] += bool(masks[query][old])
                counts["corrected_membership"] += bool(masks[query][correct])
                if query == selected and not bool(row["native_positive"][query]):
                    counts["negative_selected"] += 1
                    counts["negative_old_membership"] += bool(masks[query][old])
                    counts["negative_corrected_membership"] += bool(masks[query][correct])
                    if len(examples) < 12:
                        examples.append({
                            "manifest_index": index, "seed": seed,
                            "old_superpoint": old, "correct_superpoint": correct,
                            "old_inside": bool(masks[query][old]),
                            "correct_inside": bool(masks[query][correct]),
                        })
    if seen != set(range(256)) or counts["all_queries"] != 32768:
        raise ValueError("Frozen query coverage differs")
    output = {
        "contract": "m95_seed_axis_correction_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA,
        "counts": counts, "selected_examples": examples,
        "limits": "Corrects a diagnostic mapping only; no new model, training, efficacy or admission.",
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
