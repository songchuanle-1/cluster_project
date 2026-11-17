"""Preregistered query-state controls on a future native M95 capture."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    as_list, bool_list, file_sha256, float_list, int_list, load_artifacts,
    validate_artifact_header,
)
from m95_failure_partition_20260923 import EXPECTED_MANIFEST_SHA256
from m95_match_cause_contract_20260923 import check_row

ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = ROOT / "pipeline/reports/m95_discordance_provenance_20260923-1107.json"
PROVENANCE_SHA256 = "6ed69abe4d26a2bd20283bb59119c2ebf30d4c0e73e2252903c210925292e372"
COHORT = {11, 23, 79, 253}
PRODUCER_FILES = (
    "native_manifest_capture_20260922.py",
    "m95_match_cause_contract_20260923.py",
    "native_frozen_capture_20260916.py",
    "frozen_capture_contract_20260916.py",
    "hierarchical_partition_contract_20260916.py",
    "native_endpoint_capture_20260916.py",
    "native_support_capture_v2_20260916.py",
    "capture_support_20260916.py",
    "physical_mask_endpoints_20260916.py",
)


def _cosine_distance(a, b):
    a, b = float_list(a, "query state"), float_list(b, "query state")
    if len(a) != len(b) or not a:
        raise ValueError("Query state dimension differs")
    aa = sum(x * x for x in a)
    bb = sum(x * x for x in b)
    if aa <= 0 or bb <= 0:
        return None
    return 1 - sum(x * y for x, y in zip(a, b)) / math.sqrt(aa * bb)


def _causes(record):
    cause = [set() for _ in record["sampled_pos"]]
    for gt, q in enumerate(record["nearest_query_per_gt"]):
        cause[q].add(("nearest_gt", gt))
    for gt, group in enumerate(record["member_queries_per_gt"]):
        for q in group:
            cause[q].add(("instance_member", gt))
    return [sorted(tags) for tags in cause]


def analyze_class(frozen, row, artifact):
    validate_artifact_header(artifact, EXPECTED_MANIFEST_SHA256)
    if not (frozen["manifest_index"] == row["manifest_index"] ==
            artifact["manifest_index"]):
        raise ValueError("Manifest index differs")
    if frozen["scene_id"] != row["scene"] or frozen["scene_id"] != artifact["axis"]["scene"]:
        raise ValueError("Scene binding differs")
    cause = row["native_match_cause"]
    check_row(cause)
    identity = artifact["identity_query"]
    states = as_list(identity["query_states"])
    positive = bool_list(artifact["native_positive"], "native positive")
    scores = float_list(artifact["query_scores"], "score")
    masks = [bool_list(mask, "query mask") for mask in as_list(artifact["query_masks"])]
    labels = int_list(artifact["physical_instance_labels"], "instance label")
    fps = int_list(row["fps_superpoints"], "FPS superpoint")
    samples = int_list(row["sampled_seed_indices"], "sampled seed index")
    ids = int_list(identity["sampled_superpoint_ids"], "sampled superpoint")
    n = len(states)
    if not all(len(v) == n for v in (positive, scores, masks, samples, ids, cause["sampled_pos"])):
        raise ValueError("Query axis differs")
    if positive != cause["native_positive"] or samples != identity["sampled_seed_indices"]:
        raise ValueError("Native label or sampled seed binding differs")
    if any(s < 0 or s >= len(fps) or fps[s] < 0 or fps[s] >= len(labels)
           for s in samples):
        raise ValueError("Physical seed out of range")
    if ids != [fps[s] for s in samples]:
        raise ValueError("Physical superpoint binding differs")
    indices = int_list(frozen["query_indices"], "frozen query")
    if len(set(indices)) != len(indices) or any(q < 0 or q >= n for q in indices):
        raise ValueError("Frozen query indices differ")
    if hashlib.sha256(bytes(masks[indices[0]])).hexdigest() != frozen["mask_sha256"]:
        raise ValueError("Frozen mask hash differs")
    if any(masks[q] != masks[indices[0]] for q in indices):
        raise ValueError("Frozen exact-mask class differs")
    frozen_seeds = {s["query"]: s for s in frozen["seeds"]}
    if set(indices) != set(frozen_seeds):
        raise ValueError("Frozen query cohort differs")
    for q in indices:
        old = frozen_seeds[q]
        if (positive[q] != old["positive"] or
                labels[ids[q]] != old["seed_physical_id"] or
                not math.isclose(scores[q], old["score"], abs_tol=1e-6)):
            raise ValueError("Frozen label, seed or score differs")

    tags = _causes(cause)
    positions = cause["sampled_pos"]
    same, controls = [], []
    for p in indices:
        if not positive[p]:
            continue
        for q in indices:
            if positive[q]:
                continue
            distance = math.dist(positions[p], positions[q])
            pair = dict(
                positive_query=p, negative_query=q,
                coordinate_distance=distance,
                same_coordinate=positions[p] == positions[q],
                same_seed_index=samples[p] == samples[q],
                cosine_distance=_cosine_distance(states[p], states[q]),
                score_difference=scores[p] - scores[q],
                positive_cause=tags[p], negative_cause=tags[q],
            )
            if labels[ids[p]] == labels[ids[q]]:
                same.append(pair)
        for q in range(n):
            if positive[q] or labels[ids[p]] == labels[ids[q]]:
                continue
            controls.append(dict(
                positive_query=p, negative_query=q,
                coordinate_distance=math.dist(positions[p], positions[q]),
                same_coordinate=positions[p] == positions[q],
                same_seed_index=samples[p] == samples[q],
                same_mask=masks[p] == masks[q],
                cosine_distance=_cosine_distance(states[p], states[q]),
                score_difference=scores[p] - scores[q],
                positive_cause=tags[p], negative_cause=tags[q],
            ))
    if not same:
        raise ValueError("Frozen same-physical-ID support differs")
    # Match within the expression, preserving exact-mask status as an observable.
    matched = []
    for pair in same:
        eligible = [c for c in controls
                    if c["positive_query"] == pair["positive_query"] and
                    c["positive_cause"] == pair["positive_cause"] and
                    c["negative_cause"] == pair["negative_cause"]]
        if eligible:
            matched.append(min(
                eligible,
                key=lambda c: (abs(c["coordinate_distance"] -
                                   pair["coordinate_distance"]),
                               c["negative_query"]),
            ))
    return dict(manifest_index=row["manifest_index"], scene_id=row["scene"],
                mask_sha256=frozen["mask_sha256"], same_id_pairs=same,
                matched_distinct_id_controls=matched,
                missing_control_pairs=len(same) - len(matched))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if file_sha256(PROVENANCE) != PROVENANCE_SHA256:
        raise ValueError("Frozen provenance changed")
    old = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    frozen = {r["manifest_index"]: r for r in old["rows"] if r["manifest_index"] in COHORT}
    if set(frozen) != COHORT:
        raise ValueError("Preregistered cohort differs")
    capture_path = Path(args.capture)
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    producer_hash = hashlib.sha256(b"".join(
        (Path(__file__).parent / name).read_bytes() for name in PRODUCER_FILES
    )).hexdigest()
    if (capture.get("manifest", {}).get("sha256") != EXPECTED_MANIFEST_SHA256 or
            capture.get("producer_sha256") != producer_hash or
            capture.get("selected_expressions") != 256 or
            capture.get("native_match_cause_completed") is not True or
            capture.get("identity_query_completed") is not True or
            capture.get("checkpoint_sha256") !=
            "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"):
        raise ValueError("Native capture identity or completeness differs")
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    if len(rows) != 256 or set(frozen) - set(rows):
        raise ValueError("Native manifest rows differ")
    artifacts = load_artifacts(capture_path, capture, EXPECTED_MANIFEST_SHA256)
    if set(artifacts) != set(rows):
        raise ValueError("Native artifact coverage differs")
    results = [analyze_class(frozen[i], rows[i], artifacts[i]) for i in sorted(frozen)]
    document = dict(
        contract="m95_identity_query_controls_v1",
        scope="Four outcome-selected TRAIN scenes; descriptive only",
        rows=results,
        summary=dict(scenes=len({r["scene_id"] for r in results}),
                     same_id_pairs=sum(len(r["same_id_pairs"]) for r in results),
                     matched_control_pairs=sum(len(r["matched_distinct_id_controls"])
                                               for r in results),
                     missing_control_pairs=sum(r["missing_control_pairs"] for r in results)),
        evidence=[dict(path=str(path), sha256=file_sha256(path))
                  for path in (PROVENANCE, capture_path)],
        admission=False,
        limitations=[
            "Distance-nearest controls can differ in absolute distance; report every pair.",
            "Four outcome-selected TRAIN scenes do not establish population or causal efficacy.",
        ],
    )
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
