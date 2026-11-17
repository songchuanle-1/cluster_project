"""Measure paired identity controls from the frozen M95 same-forward capture.

This is CPU-only diagnostic analysis. It does not train, admit, or evaluate a
deployable mechanism.
"""
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "pipeline" / "diagnostic_runs" / "m95_same_forward_20260922-0945"
CAPTURE = RUN / "capture.json"
FEATURE_PATHS = (RUN / "features_000.pt", RUN / "features_001.pt")
OUTPUT = ROOT / "pipeline" / "reports" / "m95_paired_identity_diagnosis_20260922-1008.json"

EXPECTED_CAPTURE_SHA256 = (
    "975c718ddefb122ef8368c117439e9562b9893bb40abf8d80d1fc31c05824c80"
)
EXPECTED_FEATURE_SHA256 = {
    "features_000.pt": "3419f1c0c0904f9570f0e419320773ece3e85cb1a3af126fdfa4efeef15e8a01",
    "features_001.pt": "c23e5c0298308b6bc4203049826d2cedfa85f95dc87df74225d8c0218a08a953",
}
EXPECTED_CHECKPOINT_SHA256 = (
    "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
)
AXES = ("raw_3d", "raw_2d", "projected_3d", "projected_2d", "fused", "final")
PAIRS = (
    ("raw_3d", "projected_3d"),
    ("raw_2d", "projected_2d"),
    ("raw_3d", "raw_2d"),
    ("projected_3d", "projected_2d"),
    ("projected_3d", "fused"),
    ("projected_2d", "fused"),
    ("fused", "final"),
)
MIN_INSTANCE_POINTS = 3


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expression_key(record):
    return (
        str(record["scene"]),
        int(record["ann_id"]),
        int(record["expression_slot"]),
    )


def rankdata(values):
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + end - 1) / 2.0 + 1.0
        for index in order[start:end]:
            ranks[index] = rank
        start = end
    return ranks


def spearman(left, right):
    if len(left) != len(right) or len(left) < 2:
        return None
    left_rank = rankdata(left)
    right_rank = rankdata(right)
    left_mean = sum(left_rank) / len(left_rank)
    right_mean = sum(right_rank) / len(right_rank)
    numerator = sum(
        (x - left_mean) * (y - right_mean)
        for x, y in zip(left_rank, right_rank)
    )
    left_norm = math.sqrt(sum((x - left_mean) ** 2 for x in left_rank))
    right_norm = math.sqrt(sum((y - right_mean) ** 2 for y in right_rank))
    if left_norm == 0 or right_norm == 0:
        return None
    return numerator / (left_norm * right_norm)


def dominant_class(labels, semantic_labels, instance_id):
    classes = [
        int(value)
        for value, instance in zip(semantic_labels, labels)
        if int(instance) == int(instance_id) and int(value) >= 0
    ]
    if not classes:
        return None
    return min(Counter(classes).items(), key=lambda item: (-item[1], item[0]))[0]


def instance_centroids(features, labels, min_points=MIN_INSTANCE_POINTS):
    labels = labels.long().flatten()
    valid = labels >= 0
    if not bool(valid.any()):
        return {}
    counts = torch.bincount(labels[valid], minlength=int(labels[valid].max()) + 1)
    sums = torch.zeros(
        counts.numel(), features.shape[-1], dtype=torch.float32, device=features.device
    )
    sums.index_add_(0, labels[valid], features[valid].float())
    means = sums / counts.clamp_min(1).unsqueeze(-1)
    ids = torch.nonzero(counts >= min_points, as_tuple=False).flatten()
    if ids.numel() < 2:
        return {}
    selected = means[ids]
    selected = selected - selected.mean(dim=0, keepdim=True)
    selected = torch.nn.functional.normalize(selected, dim=-1)
    return {int(instance): selected[index] for index, instance in enumerate(ids)}


def pairwise_similarity(centroids):
    ids = sorted(centroids)
    matrix = torch.stack([centroids[instance] for instance in ids])
    return ids, matrix @ matrix.T


def modality_preservation(left, right):
    left_ids, left_sim = pairwise_similarity(left)
    right_ids, right_sim = pairwise_similarity(right)
    if left_ids != right_ids or len(left_ids) < 3:
        return None
    upper = torch.triu_indices(len(left_ids), len(left_ids), offset=1)
    left_values = left_sim[upper[0], upper[1]].tolist()
    right_values = right_sim[upper[0], upper[1]].tolist()
    nearest_left = {}
    nearest_right = {}
    for row in range(len(left_ids)):
        candidates = [column for column in range(len(left_ids)) if column != row]
        nearest_left[left_ids[row]] = left_ids[max(
            candidates, key=lambda column: float(left_sim[row, column])
        )]
        nearest_right[right_ids[row]] = right_ids[max(
            candidates, key=lambda column: float(right_sim[row, column])
        )]
    agreements = sum(
        nearest_left[instance] == nearest_right[instance] for instance in left_ids
    )
    return {
        "instances": len(left_ids),
        "spearman": spearman(left_values, right_values),
        "nearest_agreement": agreements / len(left_ids),
    }


def identity_metrics(centroids, target_ids, wrong_id, class_by_id):
    if wrong_id in target_ids:
        return None
    if wrong_id not in centroids:
        return None
    present_targets = [instance for instance in target_ids if instance in centroids]
    if not present_targets:
        return None
    ids, similarity = pairwise_similarity(centroids)
    if wrong_id not in ids:
        return None
    wrong_pos = ids.index(wrong_id)
    target_positions = [ids.index(instance) for instance in present_targets]
    target_similarities = [float(similarity[wrong_pos, position])
                           for position in target_positions]
    target_similarity = max(target_similarities)
    target_id = present_targets[target_similarities.index(target_similarity)]
    ordered = [
        (position, instance)
        for position, instance in enumerate(ids)
        if instance != wrong_id
    ]
    if not ordered:
        return None
    ordered.sort(
        key=lambda item: (-float(similarity[wrong_pos, item[0]]), item[1]),
    )
    target_rank = next(
        index + 1 for index, (_, instance) in enumerate(ordered)
        if instance in present_targets
    )
    nearest_id = ordered[0][1]
    nearest_other_similarity = float(similarity[wrong_pos, ordered[0][0]])
    same_class = [
        (position, instance)
        for position, instance in ordered
        if instance not in set(present_targets)
        if class_by_id.get(instance) == class_by_id.get(target_id)
    ]
    same_class_top = max(
        (float(similarity[wrong_pos, position]) for position, _ in same_class),
        default=None,
    )
    return {
        "instances": len(ids),
        "target_instance": target_id,
        "target_similarity_to_wrong": target_similarity,
        "target_rank_to_wrong": target_rank,
        "nearest_other_to_wrong": nearest_id,
        "nearest_other_similarity_to_wrong": nearest_other_similarity,
        "target_nearest_to_wrong": target_rank == 1,
        "margin_over_nearest_other": (
            target_similarity - nearest_other_similarity
        ),
        "same_class_competitor_count": len(same_class),
        "same_class_top_similarity_to_wrong": same_class_top,
        "margin_over_same_class": (
            None if same_class_top is None else target_similarity - same_class_top
        ),
    }


def mean(values):
    values = [value for value in values if value is not None]
    return sum(values) / len(values) if values else None


def median(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return None
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2.0


def scene_bootstrap(values_by_scene, draws=10000, seed=1999):
    groups = [values for values in values_by_scene.values() if values]
    if len(groups) < 2:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(draws):
        sampled_groups = rng.choices(groups, k=len(groups))
        means.append(sum(mean(group) for group in sampled_groups) / len(groups))
    means.sort()
    return {
        "mean": sum(means) / len(means),
        "lo": means[int(0.025 * (draws - 1))],
        "hi": means[int(0.975 * (draws - 1))],
    }


def validate_inputs():
    capture_hash = file_sha256(CAPTURE)
    if capture_hash != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Capture hash differs from the frozen receipt")
    feature_hashes = {}
    for path in FEATURE_PATHS:
        digest = file_sha256(path)
        if digest != EXPECTED_FEATURE_SHA256[path.name]:
            raise ValueError("Feature hash differs for " + path.name)
        feature_hashes[path.name] = digest
    document = json.loads(CAPTURE.read_text(encoding="utf-8"))
    if document.get("checkpoint_sha256") != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Capture checkpoint identity differs")
    if document.get("native_capture_completed") is not True:
        raise ValueError("Capture is incomplete")
    if len(document.get("rows", [])) != 16:
        raise ValueError("Expected 16 captured expressions")
    records = []
    for path in FEATURE_PATHS:
        payload = torch.load(path, map_location="cpu", weights_only=False)
        if not isinstance(payload, list):
            raise ValueError(path.name + " must contain a list")
        records.extend(payload)
    if len(records) != 16:
        raise ValueError("Expected 16 paired feature records")
    by_key = {}
    for record in records:
        axis = record.get("axis", {})
        key = expression_key(axis)
        if key in by_key:
            raise ValueError("Duplicate feature expression " + repr(key))
        by_key[key] = record
    missing = [expression_key(row) for row in document["rows"]
               if expression_key(row) not in by_key]
    if missing:
        raise ValueError("Missing feature records: " + repr(missing))
    return document, feature_hashes, by_key


def main():
    document, feature_hashes, features_by_key = validate_inputs()
    rows = []
    preservation = defaultdict(lambda: defaultdict(list))
    axis_identity = defaultdict(list)
    known_class_confusion = 0
    known_same_class_identity = 0
    class_unresolved = 0
    no_acceptable = 0

    for row in document["rows"]:
        record = features_by_key[expression_key(row)]
        labels = record["instance_labels"].long().flatten()
        target = record["target"].bool().flatten()
        semantic_labels = [
            int(value) for value in record["axis"]["semantic_labels"]
        ]
        native_labels = [int(value) for value in row["instance_labels"]]
        if len(labels) != len(target) or len(labels) != len(semantic_labels):
            raise ValueError("Feature axes differ")
        if native_labels != labels.tolist():
            raise ValueError("Native row and feature instance labels differ")
        if record["axis"].get("native_input_sha256") != row.get("native_input_sha256"):
            raise ValueError("Native input identity differs")

        target_ids = sorted(int(value) for value in torch.unique(labels[target]))
        selected = torch.tensor(row["selected_mask"], dtype=torch.bool)
        if selected.numel() != labels.numel():
            raise ValueError("Selected mask length differs")
        labeled = labels >= 0
        overlap = torch.bincount(
            labels[labeled & selected], minlength=int(labels.max().item()) + 1
        )
        wrong_count, wrong_id = int(overlap.max()), int(overlap.argmax())
        if wrong_count == 0:
            raise ValueError("Selected mask has no physical-instance overlap")
        class_by_id = {
            int(instance): dominant_class(labels.tolist(), semantic_labels, instance)
            for instance in torch.unique(labels[labeled]).tolist()
        }
        target_classes = {
            class_by_id[instance] for instance in target_ids
            if class_by_id.get(instance) is not None
        }
        wrong_class = class_by_id.get(wrong_id)
        if target_classes and wrong_class is not None:
            is_class_confusion = wrong_class not in target_classes
            class_status = (
                "class_confusion" if is_class_confusion
                else "same_class_identity"
            )
        else:
            is_class_confusion = None
            class_status = "class_unresolved"
        deployed_success = bool(row["ious"][int(row["selected_query"])] > 0.5)
        if not deployed_success:
            if class_status == "class_confusion":
                known_class_confusion += 1
            elif class_status == "same_class_identity":
                known_same_class_identity += 1
            else:
                class_unresolved += 1
            if row.get("best_acceptable_rank") is None:
                no_acceptable += 1

        centroids = {}
        identity = {}
        for axis in AXES:
            centroids[axis] = instance_centroids(record["features"][axis], labels)
            metrics = identity_metrics(
                centroids[axis], target_ids, wrong_id, class_by_id
            )
            if metrics is not None:
                identity[axis] = metrics
                if not deployed_success:
                    axis_identity[axis].append(metrics)

        for left, right in PAIRS:
            measured = modality_preservation(centroids[left], centroids[right])
            if measured is None:
                continue
            scene = str(row["scene"])
            if measured["spearman"] is not None:
                preservation[(left, right)]["spearman"].append(
                    (scene, measured["spearman"])
                )
            preservation[(left, right)]["nearest_agreement"].append(
                (scene, measured["nearest_agreement"])
            )
        rows.append({
            "scene": row["scene"],
            "ann_id": int(row["ann_id"]),
            "expression_slot": int(row["expression_slot"]),
            "deployed_success": deployed_success,
            "selected_query": int(row["selected_query"]),
            "best_acceptable_rank": row.get("best_acceptable_rank"),
            "target_instances": target_ids,
            "target_classes": sorted(target_classes),
            "wrong_instance": wrong_id,
            "wrong_class": wrong_class,
            "class_status": class_status if not deployed_success else None,
            "known_class_confusion": (
                is_class_confusion if not deployed_success else None
            ),
            "identity": identity,
        })

    preservation_summary = {}
    for pair, fields in preservation.items():
        entry = {}
        for field, scene_values in fields.items():
            grouped = defaultdict(list)
            for scene, value in scene_values:
                grouped[scene].append(value)
            flattened = [value for values in grouped.values() for value in values]
            entry[field] = {
                "mean": mean(flattened),
                "median": median(flattened),
                "expressions": len(flattened),
                "scene_bootstrap_95ci": scene_bootstrap(grouped),
            }
        preservation_summary["->".join(pair)] = entry

    identity_summary = {}
    for axis, metrics in axis_identity.items():
        identity_summary[axis] = {
            "eligible_failures": len(metrics),
            "target_nearest_to_wrong": sum(
                item["target_nearest_to_wrong"] for item in metrics
            ),
            "median_target_rank_to_wrong": median(
                [item["target_rank_to_wrong"] for item in metrics]
            ),
            "mean_margin_over_nearest_other": mean(
                [item["margin_over_nearest_other"] for item in metrics]
            ),
            "mean_margin_over_same_class": mean(
                [item["margin_over_same_class"] for item in metrics]
            ),
        }

    result = {
        "contract": "m95_paired_identity_diagnosis_v1",
        "generated_at": "2026-09-22T10:08:00+08:00",
        "scope": (
            "CPU-only paired analysis of the frozen M95 same-forward capture. "
            "It compares raw/projected/fused/final features on identical native "
            "samples and separates target-vs-wrong class confusion from "
            "same-class instance identity. Diagnosis only."
        ),
        "source": {
            "capture": CAPTURE.relative_to(ROOT).as_posix(),
            "capture_sha256": EXPECTED_CAPTURE_SHA256,
            "feature_sha256": feature_hashes,
            "checkpoint_sha256": document["checkpoint_sha256"],
            "model_source_sha256": document["model_source_sha256"],
            "config_sha256": document["config_sha256"],
            "producer_sha256": document["producer_sha256"],
        },
        "summary": {
            "expressions": len(rows),
            "selected_success": sum(row["deployed_success"] for row in rows),
            "selected_failures": sum(not row["deployed_success"] for row in rows),
            "known_class_confusion_failures": known_class_confusion,
            "known_same_class_identity_failures": known_same_class_identity,
            "class_unresolved_failures": class_unresolved,
            "no_acceptable_failures": no_acceptable,
            "identity_by_axis": identity_summary,
            "modality_preservation": preservation_summary,
        },
        "rows": rows,
        "interpretation": (
            "Known class confusion means both the selected wrong instance and "
            "the referred target instance have semantic labels and their classes "
            "differ. A missing semantic label on either instance is class "
            "unresolved, not evidence of same-class identity failure. Identity "
            "ranks use centred instance-feature centroids and exclude "
            "self-similarity. Preservation is the agreement between pairwise "
            "instance-similarity orderings before and after a projection/fusion "
            "stage. All results are bounded to 16 TRAIN expressions and four "
            "scenes."
        ),
        "not_evidence_of": [
            "admission",
            "deployable efficacy",
            "population effect",
            "independence",
            "novelty",
            "target-independent objectness",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    print(json.dumps(result["summary"], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
