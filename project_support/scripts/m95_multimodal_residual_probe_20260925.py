"""Probe for target-selection information beyond the deployed query score.

This is a read-only diagnostic over the frozen M95 exact capture. It evaluates
whether captured query and modality features add scene-held-out information
about target mask success beyond the deployed score. It does not train a model
or establish a deployable selector.
"""
import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold


EXPECTED_CAPTURE_SHA256 = (
    "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
)
EXPECTED_MANIFEST_SHA256 = (
    "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
)
EXPECTED_PRODUCER_SHA256 = (
    "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a"
)
EXPECTED_ROWS = 256
EXPECTED_QUERIES = 128
EXPECTED_ARTIFACT_CONTRACT = "m95_manifest_native_query_artifact_v1"
PROBE_SEED = 1999
BOOTSTRAP_DRAWS = 10000
MIN_FOLD_GROUPS = 5


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_capture(capture):
    if capture.get("producer_sha256") != EXPECTED_PRODUCER_SHA256:
        raise ValueError("Capture producer differs from frozen contract")
    if capture.get("checkpoint_sha256") != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Capture checkpoint differs from M95")
    if capture.get("manifest", {}).get("sha256") != EXPECTED_MANIFEST_SHA256:
        raise ValueError("Capture manifest differs from frozen contract")
    if capture.get("capture_mode") != "full_train_scan":
        raise ValueError("Capture is not the exact full-train scan")
    for key in (
        "native_capture_completed",
        "native_match_cause_completed",
        "identity_query_completed",
    ):
        if capture.get(key) is not True:
            raise ValueError("Capture completion flag differs: %s" % key)
    rows = capture.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        raise ValueError("Capture does not contain 256 rows")
    indices = [int(row["manifest_index"]) for row in rows]
    if sorted(indices) != list(range(EXPECTED_ROWS)):
        raise ValueError("Capture manifest coverage differs")
    return rows


def load_artifacts(capture, capture_dir):
    entries = capture.get("feature_artifacts")
    if not isinstance(entries, list):
        raise ValueError("Capture lacks feature artifacts")
    torch = __import__("torch")
    artifacts = {}
    for entry in entries:
        path = Path(capture_dir) / str(entry["path"])
        if file_sha256(path) != entry["sha256"]:
            raise ValueError("Feature artifact hash differs")
        loaded = torch.load(path, map_location="cpu", weights_only=False)
        if len(loaded) != int(entry["rows"]):
            raise ValueError("Feature artifact row count differs")
        for artifact in loaded:
            index = int(artifact["manifest_index"])
            if index in artifacts:
                raise ValueError("Duplicate feature artifact row")
            if artifact.get("artifact_contract") != EXPECTED_ARTIFACT_CONTRACT:
                raise ValueError("Feature artifact contract differs")
            artifacts[index] = artifact
    if set(artifacts) != set(range(EXPECTED_ROWS)):
        raise ValueError("Feature artifact coverage differs")
    return artifacts


def masked_mean_features(masks, features, device="cpu"):
    """Aggregate point features over each query's predicted binary mask."""
    if device != "cpu":
        torch = __import__("torch")
        mask_t = torch.as_tensor(
            np.asarray(masks), dtype=torch.float32, device=device
        )
        feature_t = torch.as_tensor(
            np.asarray(features), dtype=torch.float32, device=device
        )
        counts = mask_t.sum(dim=1, keepdim=True)
        return (
            (mask_t @ feature_t) / counts.clamp_min(1.0)
        ).cpu().numpy()
    masks = np.asarray(masks, dtype=bool)
    features = np.asarray(features, dtype=np.float32)
    if masks.ndim != 2 or features.ndim != 2:
        raise ValueError("Masks and features must be matrices")
    if masks.shape[1] != features.shape[0]:
        raise ValueError("Mask and feature point axes differ")
    counts = masks.sum(axis=1, keepdims=True)
    return np.divide(
        masks.astype(np.float32) @ features,
        counts,
        out=np.zeros((masks.shape[0], features.shape[1]), dtype=np.float32),
        where=counts > 0,
    )


def feature_matrix(rows, artifacts, device="cpu"):
    blocks = {
        "query_state": [],
        "projected_2d": [],
        "projected_3d": [],
        "final": [],
    }
    scores = []
    labels = []
    ious = []
    scenes = []
    expression_ids = []
    for row in rows:
        index = int(row["manifest_index"])
        artifact = artifacts[index]
        query_count = len(row["scores"])
        if query_count != EXPECTED_QUERIES:
            raise ValueError("Expression query count differs")
        if len(row["ious"]) != query_count:
            raise ValueError("Expression score and IoU axes differ")
        if len(artifact["identity_query"]["query_states"]) != query_count:
            raise ValueError("Identity query count differs")
        row_scores = np.asarray(row["scores"], dtype=np.float64)
        if not np.isfinite(row_scores).all():
            raise ValueError("Non-finite query score")
        blocks["query_state"].append(
            artifact["identity_query"]["query_states"].numpy().astype(np.float32)
        )
        query_masks = artifact["query_masks"].numpy().astype(bool)
        for key in ("projected_2d", "projected_3d", "final"):
            blocks[key].append(
                masked_mean_features(
                    query_masks,
                    artifact["features"][key].numpy(),
                    device=device,
                )
            )
        scores.append(row_scores)
        row_ious = np.asarray(row["ious"], dtype=np.float64)
        ious.append(row_ious)
        labels.append(row_ious > 0.5)
        scenes.extend([str(row["scene"])] * query_count)
        expression_ids.extend([index] * query_count)
    matrices = {key: np.concatenate(value, axis=0) for key, value in blocks.items()}
    return {
        "features": matrices,
        "scores": np.concatenate(scores),
        "labels": np.concatenate(labels).astype(np.int8),
        "ious": np.concatenate(ious),
        "scenes": np.asarray(scenes),
        "expression_ids": np.asarray(expression_ids, dtype=np.int64),
    }


def group_fold_indices(scenes, n_splits=1):
    unique_scenes = np.unique(scenes)
    if len(unique_scenes) < MIN_FOLD_GROUPS:
        raise ValueError("Not enough scene groups")
    if n_splits == 1:
        rng = random.Random(PROBE_SEED)
        shuffled = list(unique_scenes)
        rng.shuffle(shuffled)
        test_count = max(1, int(round(len(shuffled) * 0.2)))
        test_scenes = set(shuffled[:test_count])
        test_mask = np.asarray([scene in test_scenes for scene in scenes])
        train_index = np.flatnonzero(~test_mask)
        test_index = np.flatnonzero(test_mask)
        if set(scenes[train_index]) & set(scenes[test_index]):
            raise ValueError("Scene leaked across folds")
        return [(train_index, test_index)]
    if n_splits < 2:
        raise ValueError("Invalid fold count")
    splitter = GroupKFold(n_splits=n_splits, shuffle=True, random_state=PROBE_SEED)
    dummy = np.zeros(len(scenes), dtype=np.int8)
    folds = []
    for train_index, test_index in splitter.split(dummy, groups=scenes):
        if set(scenes[train_index]) & set(scenes[test_index]):
            raise ValueError("Scene leaked across folds")
        folds.append((train_index, test_index))
    return folds


def fit_ridge_predictions(x_train, y_train, x_test, device="cpu"):
    torch = __import__("torch")
    mean = x_train.mean(axis=0)
    scale = x_train.std(axis=0)
    scale[scale < 1e-6] = 1.0
    x_train = (x_train - mean) / scale
    x_test = (x_test - mean) / scale
    x_train_t = torch.as_tensor(x_train, dtype=torch.float32, device=device)
    y_train_t = torch.as_tensor(y_train, dtype=torch.float32, device=device)
    x_test_t = torch.as_tensor(x_test, dtype=torch.float32, device=device)
    gram = x_train_t.transpose(0, 1) @ x_train_t
    gram.diagonal().add_(10.0)
    rhs = x_train_t.transpose(0, 1) @ y_train_t
    weights = torch.linalg.solve(gram, rhs)
    return (x_test_t @ weights).detach().cpu().numpy()


def scene_balanced(values_by_scene):
    groups = [values for values in values_by_scene.values() if values]
    if not groups:
        return None
    return sum(sum(group) / len(group) for group in groups) / len(groups)


def bootstrap_scene(values_by_scene, draws=BOOTSTRAP_DRAWS, seed=PROBE_SEED):
    groups = [values for values in values_by_scene.values() if values]
    if not groups:
        return None
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        chosen = rng.choices(groups, k=len(groups))
        samples.append(
            sum(sum(group) / len(group) for group in chosen) / len(groups)
        )
    samples.sort()
    return {
        "draws": draws,
        "seed": seed,
        "unit": "scene",
        "scene_count": len(groups),
        "point_estimate": scene_balanced(values_by_scene),
        "lo": samples[int(0.025 * (draws - 1))],
        "hi": samples[int(0.975 * (draws - 1))],
    }


def top1_metrics(expression_ids, labels, ious, scores):
    success = {}
    selected_iou = {}
    for expression in np.unique(expression_ids):
        mask = expression_ids == expression
        choice = np.flatnonzero(mask)[int(np.argmax(scores[mask]))]
        success[int(expression)] = float(labels[choice])
        selected_iou[int(expression)] = float(ious[choice])
    return success, selected_iou


def evaluate(data, device="cpu", n_splits=1):
    folds = group_fold_indices(data["scenes"], n_splits=n_splits)
    feature_blocks = {
        "score_only": (),
        "score_query_state": ("query_state",),
        "score_projected_2d": ("projected_2d",),
        "score_projected_3d": ("projected_3d",),
        "score_final": ("final",),
    }
    predictions = {
        name: np.zeros(len(data["scores"]), dtype=np.float64)
        for name in feature_blocks
    }
    predictions["score_only"][:] = data["scores"]
    fold_rows = []
    for fold_number, (train_index, test_index) in enumerate(folds, start=1):
        for name, block_names in feature_blocks.items():
            if name == "score_only":
                continue
            parts = [data["features"][block][train_index] for block in block_names]
            x_train = np.concatenate(
                parts + [data["scores"][train_index, None]], axis=1
            )
            test_parts = [
                data["features"][block][test_index] for block in block_names
            ]
            x_test = np.concatenate(
                test_parts + [data["scores"][test_index, None]], axis=1
            )
            predictions[name][test_index] = fit_ridge_predictions(
                x_train,
                data["labels"][train_index],
                x_test,
                device=device,
            )
        fold_rows.append({
            "fold": fold_number,
            "train_queries": int(len(train_index)),
            "test_queries": int(len(test_index)),
            "train_scenes": int(len(np.unique(data["scenes"][train_index]))),
            "test_scenes": int(len(np.unique(data["scenes"][test_index]))),
        })

    score_success, score_iou = top1_metrics(
        data["expression_ids"],
        data["labels"],
        data["ious"],
        data["scores"],
    )
    metrics = {}
    for name, predicted in predictions.items():
        auc = float(roc_auc_score(data["labels"], predicted))
        success, selected_iou = top1_metrics(
            data["expression_ids"],
            data["labels"],
            data["ious"],
            predicted,
        )
        delta_by_scene = defaultdict(list)
        iou_delta_by_scene = defaultdict(list)
        scenes_by_expression = {}
        for expression in np.unique(data["expression_ids"]):
            scene = str(data["scenes"][data["expression_ids"] == expression][0])
            scenes_by_expression[int(expression)] = scene
        for expression in success:
            scene = scenes_by_expression[expression]
            delta_by_scene[scene].append(
                success[expression] - score_success[expression]
            )
            iou_delta_by_scene[scene].append(
                selected_iou[expression] - score_iou[expression]
            )
        metrics[name] = {
            "auc": auc,
            "top1_success_rate": sum(success.values()) / len(success),
            "top1_mean_iou": sum(selected_iou.values()) / len(selected_iou),
            "top1_success_delta_vs_score_scene_balanced": scene_balanced(
                delta_by_scene
            ),
            "top1_success_delta_vs_score_scene_bootstrap_95ci": bootstrap_scene(
                delta_by_scene
            ),
            "top1_iou_delta_vs_score_scene_balanced": scene_balanced(
                iou_delta_by_scene
            ),
            "top1_iou_delta_vs_score_scene_bootstrap_95ci": bootstrap_scene(
                iou_delta_by_scene
            ),
        }
    return {
        "fold_metrics": fold_rows,
        "feature_blocks": {
            name: list(blocks) for name, blocks in feature_blocks.items()
        },
        "models": metrics,
        "query_samples": int(len(data["scores"])),
        "expressions": int(len(np.unique(data["expression_ids"]))),
        "scenes": int(len(np.unique(data["scenes"]))),
    }


def analyze_capture(capture_path, capture_dir=None, device="cpu", n_splits=1):
    capture_path = Path(capture_path).resolve()
    capture_dir = Path(capture_dir or capture_path.parent).resolve()
    actual_sha256 = file_sha256(capture_path)
    if actual_sha256 != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Capture SHA256 differs from frozen contract")
    capture = load_json(capture_path)
    rows = validate_capture(capture)
    artifacts = load_artifacts(capture, capture_dir)
    result = evaluate(
        feature_matrix(rows, artifacts, device=device),
        device=device,
        n_splits=n_splits,
    )
    result["capture_sha256"] = actual_sha256
    result["capture_path"] = str(capture_path)
    result["artifact_rows"] = len(artifacts)
    return result


def write_json(path, document):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--capture-dir")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--folds", type=int, default=1)
    args = parser.parse_args()
    result = analyze_capture(
        args.capture,
        args.capture_dir,
        args.device,
        args.folds,
    )
    result["contract"] = "m95_multimodal_residual_probe_v1"
    result["scope"] = (
        "Read-only CPU modality residual probe. No model training, selector, "
        "admission, native backward, resource, novelty, or efficacy claim."
    )
    result["admission"] = False
    write_json(args.output, result)


if __name__ == "__main__":
    main()
