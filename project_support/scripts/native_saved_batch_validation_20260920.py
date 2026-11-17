"""Native saved-batch checks; Torch is supplied only by an authorized caller."""
from frozen_capture_contract_20260916 import fingerprint
from relocated_saved_collation_20260920 import require_cpu


def require_cpu_runtime(torch):
    # Checking initialization does not probe devices or initialize CUDA.
    if torch.cuda.is_initialized():
        raise ValueError("CUDA already initialized in CPU collation process")


class NativeBatchValidator:
    """Validate the one-scene scannetv2 collate contract without resampling."""

    def __init__(self, torch, use_xyz):
        if type(use_xyz) is not bool:
            raise ValueError("Explicit native use_xyz boolean required")
        self.torch = torch
        self.use_xyz = use_xyz

    def __call__(self, item, batch, axes):
        require_cpu_runtime(self.torch)
        require_cpu((item, batch, axes))
        if not isinstance(item, (tuple, list)) or len(item) != 16:
            raise ValueError("Expected native sixteen-field saved item")
        count = len(item[0])
        if count == 0 or len(axes) != count:
            raise ValueError("Native expression count differs")
        for slot, axis in enumerate(axes):
            if (axis["scene"] != item[1] or axis["ann_id"] != item[0][slot]
                    or axis["expression_slot"] != slot
                    or type(axis["scene_occurrence"]) is not int
                    or axis["scene_occurrence"] < 0):
                raise ValueError("Native expression axis identity differs")
        if (batch["batch_offsets"].tolist() != [0, len(item[11])]
                or batch["scenes_len"].tolist() != [count]
                or batch["scan_ids"] != [item[1]] or batch["ann_ids"] != item[0]):
            raise ValueError("Native index/count identity differs")
        expected_fields = {
            "coords_float": item[3], "superpoints": item[5],
            "feats_2d": item[15], "gt_pmasks": item[7],
            "gt_spmasks": item[8], "sp_ref_masks": item[9],
            "sp_ins_labels": [item[11]], "object_idss": item[6],
            "meta_datas": item[12], "dense_maps": item[13],
            "view_dependents": item[14],
        }
        for field, expected in expected_fields.items():
            if fingerprint(batch[field]) != fingerprint(expected):
                raise ValueError("Native collated field differs: " + field)
        expected_features = (
            self.torch.cat((item[4], item[3]), dim=1) if self.use_xyz else item[4])
        # Fingerprint includes dtype and shape; torch.equal alone ignores dtype.
        if fingerprint(batch["feats"]) != fingerprint(expected_features):
            raise ValueError("Native feature concatenation/dtype differs")
        points = len(item[3])
        for field in ("coords_float", "feats", "feats_2d"):
            if len(batch[field].shape) != 2 or batch[field].shape[0] != points:
                raise ValueError("Native point feature shape differs: " + field)
        if (tuple(batch["superpoints"].shape) != (points,)
                or tuple(batch["p2v_map"].shape) != (points,)):
            raise ValueError("Native point map shape differs")
        for field in ("object_idss", "gt_pmasks", "gt_spmasks", "sp_ref_masks",
                      "meta_datas", "dense_maps", "view_dependents"):
            if len(batch[field]) != count:
                raise ValueError("Native expression field count differs: " + field)
        token_shape = tuple(batch["lang_tokenss"].shape)
        if (len(token_shape) != 2 or token_shape[0] != count or token_shape[1] < 1
                or tuple(batch["lang_masks"].shape) != token_shape):
            raise ValueError("Native token/mask expression shape differs")
        require_cpu_runtime(self.torch)


def native_callbacks(native, torch, capture_id, producer_sha256):
    """Bind existing FrozenDataset collation; does not construct/read a dataset.

    This is not host authorization or a filesystem sandbox. The future native
    entrypoint must verify server-4, immutable imports and scratch-only writes.
    """
    require_cpu_runtime(torch)
    from native_frozen_capture_20260916 import FrozenDataset

    collator = FrozenDataset(native, capture_id, producer_sha256)
    validator = NativeBatchValidator(torch, native.use_xyz)

    def collate(samples):
        require_cpu_runtime(torch)
        require_cpu(samples)
        result = collator.collate_fn(samples)
        require_cpu_runtime(torch)
        require_cpu(result)
        return result

    def load(path):
        require_cpu_runtime(torch)
        result = torch.load(path, map_location="cpu", weights_only=False)
        require_cpu_runtime(torch)
        require_cpu(result)
        return result

    def save(value, stream):
        require_cpu_runtime(torch)
        require_cpu(value)
        torch.save(value, stream)
        require_cpu_runtime(torch)

    return dict(collate=collate, validate_batch=validator, save=save, load_batch=load)
