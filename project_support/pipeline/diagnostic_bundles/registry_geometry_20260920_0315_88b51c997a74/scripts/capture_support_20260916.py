"""Diagnostic-only support preservation for the native num_workers=0 loader.

Wrap the dataset before loading; unwrap each collated batch before model.forward.
This records real transform outputs, never reconstructs missing archived axes.
No model code, supervision or training configuration is changed.
"""
import hashlib
import json
from numbers import Integral


def plain(value):
    return value.tolist() if hasattr(value, "tolist") else list(value)


def support_record(original_ids, inverse):
    ids, inverse = plain(original_ids), plain(inverse)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Empty or duplicate original superpoint IDs")
    if any(not isinstance(i, Integral) or isinstance(i, bool) or i < 0 for i in ids):
        raise ValueError("Invalid original superpoint ID")
    if not inverse or any(not isinstance(i, Integral) or isinstance(i, bool)
                          or i < 0 or i >= len(ids) for i in inverse):
        raise ValueError("Invalid point-to-superpoint inverse")
    if set(inverse) != set(range(len(ids))):
        raise ValueError("Unused superpoint row")
    return dict(original_superpoint_ids=ids, sample_inverse=inverse)


class CaptureDataset:
    """Serial diagnostic adapter; use only with num_workers=0, no concurrent calls."""

    def __init__(self, dataset, capture_id, producer_sha256):
        if not capture_id or len(producer_sha256) != 64:
            raise ValueError("Capture identity and producer hash required")
        int(producer_sha256, 16)
        self.dataset = dataset
        self.capture_id = capture_id
        self.producer_sha256 = producer_sha256
        self.occurrence = 0

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        dataset = self.dataset
        name = "transform_train" if dataset.training else "transform_test"
        native = getattr(dataset, name)
        had_override = name in vars(dataset)
        override = vars(dataset).get(name)
        captured = []

        def transform(*args, **kwargs):
            result = native(*args, **kwargs)
            captured.append(support_record(result[6], result[3]))
            return result

        setattr(dataset, name, transform)
        try:
            item = dataset[index]
        finally:
            if had_override:
                setattr(dataset, name, override)
            else:
                delattr(dataset, name)
        if len(captured) != 1:
            raise ValueError("Expected exactly one scene transform per item")
        support = captured[0]
        if plain(item[5]) != support["sample_inverse"]:
            raise ValueError("Returned point support differs from transform")
        if len(item[15]) != len(support["original_superpoint_ids"]):
            raise ValueError("2D feature rows differ from physical support")
        occurrence = self.occurrence
        self.occurrence += 1
        axes = [dict(support, capture_id=self.capture_id, scene=item[1],
                     ann_id=int(ann), expression_slot=slot,
                     scene_occurrence=occurrence, dataset_index=int(index),
                     producer_sha256=self.producer_sha256)
                for slot, ann in enumerate(item[0])]
        return item, axes

    def collate_fn(self, items):
        native = self.dataset.collate_fn([item for item, _ in items])
        axes = [row for _, rows in items for row in rows]
        scenes = [scene for scene, count in zip(native["scan_ids"], native["scenes_len"])
                  for _ in range(int(count))]
        if (len(axes) != len(native["ann_ids"]) or len(scenes) != len(axes)
                or any(row["ann_id"] != int(ann) or row["scene"] != scene
                       for row, ann, scene in zip(axes, native["ann_ids"], scenes))):
            raise ValueError("Native collation changed expression axes")
        return native, axes


def bind_queries(axis, scores, ious, seed_inside, native_positive, instance_labels):
    """Persist contingency on one exact query axis; no truncation or padding."""
    support_record(axis["original_superpoint_ids"], axis["sample_inverse"])
    vectors = [plain(x) for x in (scores, ious, seed_inside, native_positive)]
    if not vectors[0] or len({len(v) for v in vectors}) != 1:
        raise ValueError("Query axes differ")
    labels = plain(instance_labels)
    if len(labels) != len(axis["original_superpoint_ids"]):
        raise ValueError("Instance endpoints differ from superpoint support")
    import math
    if any(not math.isfinite(v) for vector in vectors[:2] for v in vector):
        raise ValueError("Nonfinite score or IoU")
    if any(v < 0 or v > 1 for v in vectors[1]):
        raise ValueError("IoU outside [0,1]")
    order = sorted(range(len(vectors[0])), key=lambda i: (-vectors[0][i], i))
    row = dict(axis, scores=vectors[0], ious=vectors[1],
               seed_inside=vectors[2], native_positive=vectors[3],
               instance_labels=labels, selected_query=order[0],
               best_acceptable_rank=next(
                   (rank for rank, i in enumerate(order, 1) if vectors[1][i] > .5), None),
               tie_convention="descending score, ascending query index")
    row["support_sha256"] = hashlib.sha256(json.dumps(
        axis, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
    return row
