"""Prepare exact relocated batches; caller owns native authorization and loading."""
import copy
import json
from pathlib import Path, PurePosixPath

from frozen_capture_contract_20260916 import fingerprint
from relocated_saved_collation_20260920 import require_cpu
from saved_geometry_replay_20260920 import verify_payload
from scratch_collation_launch_20260920 import verify_completion


def prepare_relocated_replay(
        location, exporter, registry_ids, read_json, load_item, load_batch, *,
        completed, output, manifest_sha256, expected_binding,
        expected_full_binding_sha256, expected_indices):
    """Recheck child receipts and original provenance before returning CPU batches.

    Original expectations must be independently obtained, not copied from child
    output. No dataset sampling, collation, model allocation or gate promotion.
    Load callbacks are trusted and must be used only on an authorized host.
    """
    binding = copy.deepcopy(expected_binding)
    indices = copy.deepcopy(expected_indices)
    completed = copy.deepcopy(completed)
    registry_ids = list(registry_ids)
    output = Path(output).absolute()

    def verify_receipt():
        return verify_completion(
            completed, output, manifest_sha256, binding,
            expected_full_binding_sha256, indices)

    receipt = verify_receipt()
    collation = json.loads((output / "collated" / "collation.json").read_text(
        encoding="utf-8"))
    contract = copy.deepcopy(location.contract)
    physical_indices = [row["dataset_index"] for row in location.physical["items"]]
    if (binding != contract["original_binding"]
            or list(indices) != physical_indices
            or collation["source_locations"] != contract["artifact_transfers"]
            or collation["binding_counts"] != contract["bundle_binding_counts"]):
        raise ValueError("Original location, saved indices or counts differ")
    # Reconstruct the original full registry using saved items, never __getitem__.
    inputs, joins = location.load_items(exporter, registry_ids, read_json, load_item)
    if (fingerprint(joins) != expected_full_binding_sha256
            or [payload["dataset_index"] for payload, _ in inputs] != list(indices)):
        raise ValueError("Independent full registry or saved item order differs")
    source = {k: v for k, v in binding.items()
              if k not in ("dataset_source_sha256", "registry_sha256")}
    item_hashes = {
        PurePosixPath(row["source"]).name: row["sha256"]
        for row in contract["artifact_transfers"]}
    prepared = []
    for (payload, original_digest), expected in zip(inputs, collation["items"]):
        require_cpu(payload)
        index = payload["dataset_index"]
        saved = load_batch(output / "collated" / ("batch_%d.pth" % index))
        require_cpu(saved)
        digest = verify_payload(
            payload, saved, expected, item_hashes["item_%d.pth" % index], source)
        if fingerprint(payload) != original_digest:
            raise ValueError("Replay loader mutated original saved input")
        prepared.append((saved, digest))
    location.verify()
    if (location.contract != contract or exporter.manifest() != joins
            or fingerprint(joins) != expected_full_binding_sha256
            or any(fingerprint(p) != d for p, d in inputs)
            or any(fingerprint(p) != d for p, d in prepared)
            or verify_receipt() != receipt):
        raise ValueError("Replay inputs, location or receipts changed during preparation")
    return prepared, joins
