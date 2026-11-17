"""CPU-only, support-bound instance retrieval on existing native captures."""
import argparse
import hashlib
import json
from pathlib import Path

import torch

from native_support_capture_20260916 import physical_join


def retrieval(features, labels, target):
    x = torch.as_tensor(features, dtype=torch.float64)
    y = torch.as_tensor(labels).reshape(-1)
    target = torch.as_tensor(target).bool().reshape(-1)
    if x.ndim != 2 or len(x) != len(y) or len(y) != len(target):
        raise ValueError("Mismatched support")
    if not torch.isfinite(x).all():
        raise ValueError("Nonfinite features")
    ids = torch.unique(y[y >= 0])
    if len(ids) < 2:
        return dict(eligible=0, target_eligible=0, accuracy=None, target_accuracy=None)
    sums = torch.stack([x[y == i].sum(0) for i in ids])
    counts = torch.stack([(y == i).sum() for i in ids])
    centroids = torch.nn.functional.normalize(sums / counts[:, None], dim=1)
    scores = torch.nn.functional.normalize(x, dim=1) @ centroids.T
    eligible = torch.zeros(len(x), dtype=torch.bool)
    truth = torch.full((len(x),), -1, dtype=torch.long)
    # Remove the evaluated superpoint from its own class prototype.
    for j, instance in enumerate(ids):
        mask = y == instance
        truth[mask] = j
        if counts[j] > 1:
            own = (sums[j] - x[mask]) / (counts[j] - 1)
            scores[mask, j] = (torch.nn.functional.normalize(x[mask], dim=1)
                               * torch.nn.functional.normalize(own, dim=1)).sum(1)
            eligible[mask] = True
    correct = scores.argmax(1) == truth
    selected = eligible & target
    margins = []
    for i in torch.where(selected)[0]:
        rivals = scores[i].clone()
        rivals[truth[i]] = -torch.inf
        margins.append(float(scores[i, truth[i]] - rivals.max()))
    return dict(eligible=int(eligible.sum()), target_eligible=int(selected.sum()),
                accuracy=float(correct[eligible].double().mean()) if eligible.any() else None,
                target_accuracy=float(correct[selected].double().mean()) if selected.any() else None,
                target_mean_margin=sum(margins) / len(margins) if margins else None,
                instances=len(ids))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    path = Path(args.capture)
    capture = json.loads(path.read_text(encoding="utf-8"))
    rows = capture["rows"]
    key = lambda r: (r["capture_id"], r["scene"], r["scene_occurrence"],
                     r["dataset_index"], r["ann_id"], r["expression_slot"])
    indexed = {key(r): r for r in rows}
    if len(indexed) != len(rows):
        raise ValueError("Duplicate observation keys")
    results, seen = [], set()
    for artifact in capture["feature_artifacts"]:
        tensor_path = path.parent / artifact["path"]
        if hashlib.sha256(tensor_path.read_bytes()).hexdigest() != artifact["sha256"]:
            raise ValueError("Feature checksum mismatch")
        payload = torch.load(tensor_path, map_location="cpu", weights_only=False)
        for item in payload:
            axis = item["axis"]
            row = indexed[key(axis)]
            physical_join(row, axis)
            if key(axis) in seen:
                raise ValueError("Repeated artifact observation")
            seen.add(key(axis))
            if item["instance_labels"].tolist() != row["instance_labels"]:
                raise ValueError("Instance endpoints differ")
            target_ids = set(row["target_instances"])
            actual = set(item["instance_labels"][item["target"].bool()].tolist())
            if not actual.issubset(target_ids):
                raise ValueError("Target endpoints differ")
            results.append(dict(scene=row["scene"], ann_id=row["ann_id"],
                                expression_slot=row["expression_slot"],
                                recoverable=max(row["ious"]) > .5,
                                selected_success=row["ious"][row["selected_query"]] > .5,
                                stages={tag: retrieval(value, item["instance_labels"], item["target"])
                                        for tag, value in item["features"].items()}))
    if seen != set(indexed):
        raise ValueError("Incomplete feature coverage")
    summary = {}
    for tag in results[0]["stages"]:
        by_scene = {}
        for row in results:
            value = row["stages"][tag]["target_accuracy"]
            if value is not None:
                by_scene.setdefault(row["scene"], []).append(value)
        means = {s: sum(v) / len(v) for s, v in by_scene.items()}
        summary[tag] = dict(scene_target_accuracy=means,
                            scene_balanced_target_accuracy=sum(means.values()) / len(means)
                            if means else None)
    report = dict(scope="Exploratory all-instance leave-one-superpoint-out cosine retrieval",
                  expressions=len(results), scenes=len({r["scene"] for r in results}),
                  capture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  feature_artifacts=capture["feature_artifacts"], summary=summary, rows=results,
                  limitations=["Four-scene smoke sample, not a predefined same-class stratum.",
                               "No language score or selected wrong-instance mask is captured.",
                               "Cosine retrieval is a diagnostic, not causal identity loss or efficacy.",
                               "Repeated descriptions share scene geometry; scene means are descriptive.",
                               "Instance labels are privileged evaluation endpoints, never model inputs."])
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps(dict(expressions=len(results), summary=summary)))


if __name__ == "__main__":
    main()
