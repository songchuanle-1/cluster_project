"""Collate verified relocated inputs via callbacks; no host or GPU launch path."""
import copy
import os
from pathlib import Path

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from native_registry_geometry_runner_20260920 import dump_new
from saved_geometry_replay_20260920 import verify_payload


def require_cpu(value):
    if hasattr(value, "device"):
        device = value.device
        kind = device if isinstance(device, str) else getattr(device, "type", None)
        if kind != "cpu":
            raise ValueError("CPU-only collation required")
    if isinstance(value, dict):
        for child in value.values():
            require_cpu(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            require_cpu(child)


def run_collation(location, exporter, registry_ids, read_json, load_item,
                  collate, validate_batch, save, load_batch, output):
    """Publish a completion marker last; callbacks must not launch native work."""
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if any(parent.is_symlink() for parent in output.parents):
        raise ValueError("Symlink output ancestor")
    prepared, joins = location.load_items(exporter, registry_ids, read_json, load_item)
    # No output is created until all original input/provenance checks succeed.
    output.mkdir(exist_ok=False)
    owned = []
    try:
        rows, artifacts = [], []
        for payload, original_digest in prepared:
            require_cpu(payload)
            index = payload["dataset_index"]
            item, axes = payload["item"], payload["axes"]
            axes_digest = fingerprint(axes)
            batch, batch_axes = collate([(item, axes)])
            require_cpu((batch, batch_axes))
            if fingerprint(payload) != original_digest or fingerprint(batch_axes) != axes_digest:
                raise ValueError("Collation mutated original item or expression axes")
            before_validation = fingerprint((batch, batch_axes))
            validate_batch(item, batch, batch_axes)
            if fingerprint((batch, batch_axes)) != before_validation:
                raise ValueError("Batch validator mutated output")
            first_digest = fingerprint(batch)
            again, again_axes = collate([(item, axes)])
            require_cpu((again, again_axes))
            if (fingerprint(again) != first_digest or fingerprint(batch) != first_digest
                    or fingerprint(again_axes) != axes_digest
                    or fingerprint(payload) != original_digest):
                raise ValueError("Repeated collation differs or mutates input")
            source_artifact = next(
                row for row in location.contract["artifact_transfers"]
                if Path(row["source"]).name == "item_%d.pth" % index)
            saved = dict(
                batch=batch, axes=batch_axes, dataset_index=index,
                source_binding=copy.deepcopy(exporter.source_binding),
                saved_item_sha256=source_artifact["sha256"],
                item_fingerprint=fingerprint(item), axes_fingerprint=axes_digest)
            expected = dict(
                dataset_index=index, payload_sha256=original_digest,
                native_input_sha256=fingerprint(item), axes_sha256=axes_digest,
                batch_sha256=first_digest, expressions=len(axes),
                fields={name: dict(sha256=fingerprint(value))
                        for name, value in batch.items()})
            saved_digest = verify_payload(
                payload, saved, expected, source_artifact["sha256"], exporter.source_binding)
            path = output / ("batch_%d.pth" % index)
            with path.open("xb") as stream:
                owned.append(path)
                save(saved, stream)
                stream.flush()
                os.fsync(stream.fileno())
            digest = file_sha256(path)
            size = path.stat().st_size
            roundtrip = load_batch(path)
            require_cpu(roundtrip)
            if (fingerprint(roundtrip) != saved_digest or fingerprint(saved) != saved_digest
                    or file_sha256(path) != digest or path.stat().st_size != size):
                raise ValueError("Saved batch serialization or readback differs")
            verify_payload(payload, roundtrip, expected,
                           source_artifact["sha256"], exporter.source_binding)
            rows.append(expected)
            artifacts.append(dict(path=str(path), sha256=digest, bytes=size))
        location.verify()
        if (exporter.manifest() != joins
                or any(fingerprint(p) != digest for p, digest in prepared)):
            raise ValueError("Final input or full binding differs")
        for row in artifacts:
            if (file_sha256(row["path"]) != row["sha256"]
                    or Path(row["path"]).stat().st_size != row["bytes"]):
                raise ValueError("Output changed before publication")
        report = dict(
            schema_version=1, contract="relocated_saved_collation_v1",
            scratch=str(output), artifacts=artifacts, items=rows,
            observed_binding=copy.deepcopy(location.contract["original_binding"]),
            source_locations=copy.deepcopy(location.contract["artifact_transfers"]),
            full_binding_sha256=fingerprint(joins), binding_counts=joins["counts"],
            registry_denominator=31, original_dataset_indices=[p["dataset_index"] for p, _ in prepared],
            callback_collation_completed=True, native_execution_verified=False,
            scientific_validation_complete=False, new_train_transforms=False,
            model_forward_completed=False, training_launch=False, admission=False)
        dump_new(output / "collation.json", report)
        return report
    except Exception as exc:
        # Remove only files created by this invocation; retain a failure marker.
        for path in owned:
            path.unlink(missing_ok=True)
        dump_new(output / "failure.json", dict(
            error_type=type(exc).__name__, message=str(exc),
            callback_collation_completed=False, scientific_validation_complete=False))
        raise
