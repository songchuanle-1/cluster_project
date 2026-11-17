"""Prediction-blind native IoU export and identity-safe paired alignment."""
import math
import numbers

import numpy as np


class EvidenceError(ValueError):
    pass


def scalar(value):
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise EvidenceError("Expected a real scalar")
    value = float(value)
    if not math.isfinite(value):
        raise EvidenceError("Nonfinite scalar")
    return value


def identity_number(value):
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, str) and value.isdecimal():
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, numbers.Integral) or value < 0:
        raise EvidenceError("Identity must be a nonnegative integer")
    return int(value)


def key(split, scene, objects, annotation):
    if split not in ("train", "val", "test"):
        raise EvidenceError("Unknown dataset split")
    if not isinstance(scene, str) or not scene or scene.strip() != scene:
        raise EvidenceError("Missing or invalid scene identity")
    if not isinstance(objects, (list, tuple)) or not objects:
        raise EvidenceError("Object identities must be a nonempty sequence")
    objects = tuple(sorted(identity_number(value) for value in objects))
    if len(objects) != len(set(objects)):
        raise EvidenceError("Duplicate object identity")
    return split, scene, objects, identity_number(annotation)


def record_key(record):
    return key(record["split"], record["scene_id"], record["object_ids"], record["ann_id"])


def expected_keys(batch, split):
    scenes = batch["scan_ids"]
    lengths = batch["scenes_len"]
    if hasattr(lengths, "tolist"):
        lengths = lengths.tolist()
    lengths = [identity_number(value) for value in lengths]
    if len(scenes) != 1 or len(lengths) != 1:
        raise EvidenceError("Native predict requires one scene per batch")
    objects, annotations = batch["object_idss"], batch["ann_ids"]
    if lengths[0] == 0 or not (lengths[0] == len(objects) == len(annotations)):
        raise EvidenceError("Input expression lengths disagree")
    result = [key(split, scenes[0], obj, ann) for obj, ann in zip(objects, annotations)]
    if len(set(result)) != len(result):
        raise EvidenceError("Duplicate input expression identity")
    return result


def native_mean(values):
    values = np.asarray([scalar(value) for value in values], dtype=np.float32)
    if not values.size or not np.isfinite(values).all():
        raise EvidenceError("Missing or invalid native IoUs")
    if ((values < 0) | (values > 1)).any():
        raise EvidenceError("IoU out of range")
    return float(values.mean())


def export_prediction(prediction, batch, split):
    """Read only; preserve native expression order and float32 aggregation."""
    expected = expected_keys(batch, split)
    fields = ("scan_id", "object_ids", "ann_id", "piou")
    if any(field not in prediction or len(prediction[field]) != len(expected) for field in fields):
        raise EvidenceError("Prediction expression lengths disagree")
    records = []
    for index, wanted in enumerate(expected):
        actual = key(split, prediction["scan_id"][index],
                     prediction["object_ids"][index], prediction["ann_id"][index])
        if actual != wanted:
            raise EvidenceError("Prediction identity conflicts with native input order")
        value = scalar(prediction["piou"][index])
        if not 0 <= value <= 1 or float(np.float32(value)) != value:
            raise EvidenceError("IoU must preserve the native float32 scalar exactly")
        records.append({"split": actual[0], "scene_id": actual[1],
                        "object_ids": list(actual[2]), "ann_id": actual[3], "piou": value})
    return records, native_mean([record["piou"] for record in records])


def index_records(records):
    result = {}
    for record in records:
        identity = record_key(record)
        value = scalar(record["piou"])
        if not 0 <= value <= 1 or float(np.float32(value)) != value:
            raise EvidenceError("Invalid persisted float32 IoU")
        if identity in result:
            raise EvidenceError("Duplicate expression identity")
        result[identity] = record
    if not result:
        raise EvidenceError("Empty evidence cohort")
    return result


def align_pairs(reference, candidate):
    """Join by full identity, never by row position or annotation ID alone."""
    left, right = index_records(reference), index_records(candidate)
    if set(left) != set(right):
        raise EvidenceError("Missing, extra, or conflicting paired identities")
    return [(left[identity], right[identity]) for identity in left]
