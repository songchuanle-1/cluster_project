"""Exact input identity for paired diagnostics; historical archives fail closed."""
import hashlib
import json
import math
from pathlib import Path

from paired_capture_evaluation_20260916 import paired_summary

FROZEN_MODEL_CLASSES = (
    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort",
    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs",
)


def fingerprint(value):
    """Hash nested native inputs with dtype, shape, order and container boundaries."""
    digest = hashlib.sha256()

    def emit(tag, payload):
        digest.update(tag.encode("ascii") + b":" + str(len(payload)).encode("ascii") + b":")
        digest.update(payload)

    def visit(item):
        if hasattr(item, "detach"):
            item = item.detach().cpu().numpy()
        if hasattr(item, "dtype") and hasattr(item, "tobytes"):
            if item.dtype.hasobject:
                raise ValueError("Object arrays cannot identify native input")
            emit("array", json.dumps([str(item.dtype), list(item.shape)]).encode("ascii"))
            emit("data", item.tobytes(order="C"))
        elif isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ValueError("Input dictionary keys must be strings")
            emit("dict", str(len(item)).encode("ascii"))
            for key in sorted(item):
                visit(key)
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            emit(type(item).__name__, str(len(item)).encode("ascii"))
            for child in item:
                visit(child)
        elif item is None or isinstance(item, (str, bool, int, float)):
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError("Nonfinite native input")
            emit(type(item).__name__, json.dumps(item, ensure_ascii=True).encode("ascii"))
        else:
            raise ValueError("Unsupported native input type: " + type(item).__name__)

    visit(value)
    return digest.hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_package_sha256(root, model_class):
    """Hash every Python source file in one bound, physically independent package."""
    if model_class not in FROZEN_MODEL_CLASSES:
        raise ValueError("Unbound model class")
    package = Path(root) / "framework/model/Quard_model" / model_class
    if not package.is_dir():
        raise ValueError("Bound model package is missing")
    sources = sorted(package.rglob("*.py"))
    if not sources:
        raise ValueError("Bound model package has no Python sources")
    digest = hashlib.sha256()
    for path in sources:
        relative = path.relative_to(package).as_posix().encode("ascii")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def strict_paired_summary(left, right, *, baseline_checkpoint, candidate_checkpoint,
                          draws=2000):
    for rows, expected in ((left, baseline_checkpoint), (right, candidate_checkpoint)):
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError("Frozen checkpoint hash required")
        int(expected, 16)
        for row in rows:
            actual = row.get("native_input_sha256", "")
            if len(actual) != 64:
                raise ValueError("Missing exact native input identity")
            int(actual, 16)
            if row.get("checkpoint_sha256") != expected:
                raise ValueError("Checkpoint differs from frozen evaluation manifest")
    key_fields = ("scene", "ann_id", "scene_occurrence", "dataset_index", "expression_slot")
    rhs = {tuple(row[k] for k in key_fields): row for row in right}
    for row in left:
        other = rhs.get(tuple(row[k] for k in key_fields))
        if other is not None and row["native_input_sha256"] != other["native_input_sha256"]:
            raise ValueError("Transformed native inputs differ")
    result = paired_summary(left, right, draws=draws)
    result["exact_native_input_verified"] = True
    result["checkpoint_identities"] = [baseline_checkpoint, candidate_checkpoint]
    result["limitations"] = [
        "Exact dataset inputs do not certify identical model-internal random draws.",
        "Producer/model code and sampling protocol still require a frozen manifest.",
        "Superpoint success and small-sample bootstrap are not goal mIoU or efficacy."]
    return result
