"""Saved-only factory assembly; native construction belongs to the pinned caller.

No CLI, dataset sampling, model imports or host authorization is supplied here.
The deployment wrapper must create the native dataset after the same-child probe.
"""
import copy
import hashlib
import inspect
import json
from pathlib import Path

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from native_saved_batch_validation_20260920 import require_cpu_runtime
from referent_geometry_registry_20260919 import registry_pairs
from referent_registry_binding_20260919 import BindingExporter
from saved_replay_migration_20260920 import DESTINATION_DATA


def assemble_inputs(location, registry_bytes, native, torch, capture_id,
                    dataset_source_path):
    """Assemble the real exporter and CPU loader without requesting any items.

    Source/data verification is delegated to the existing location object.
    Registry bytes must be the original file, not a reserialized reconstruction.
    Dataset class source is independently checked against the original binding.
    """
    require_cpu_runtime(torch)
    if not isinstance(capture_id, str) or not capture_id.strip():
        raise ValueError("Explicit saved capture identity required")
    observed = location.contract["original_binding"]
    if (not isinstance(registry_bytes, bytes)
            or hashlib.sha256(registry_bytes).hexdigest() != observed["registry_sha256"]):
        raise ValueError("Original registry bytes differ")
    registry = json.loads(registry_bytes)
    ids = [row["pair_id"] for row in registry_pairs(registry)]
    if len(ids) != 31 or len(set(ids)) != 31:
        raise ValueError("Full31 registry required")
    path = Path(dataset_source_path).absolute()
    if (path.is_symlink() or any(p.is_symlink() for p in path.parents)
            or Path(inspect.getfile(type(native))).absolute() != path
            or file_sha256(path) != observed["dataset_source_sha256"]):
        raise ValueError("Native dataset class source differs")
    if (native.training is not True or type(native.use_xyz) is not bool
            or str(native.data_root).rstrip("/") != str(DESTINATION_DATA)
            or not callable(native.collate_fn)):
        raise ValueError("Relocated native TRAIN collation configuration required")
    location.verify()
    metadata_digest = fingerprint(native.scene_inputs)
    source = {k: v for k, v in observed.items()
              if k not in ("dataset_source_sha256", "registry_sha256")}
    exporter = BindingExporter(
        registry, observed["registry_sha256"], native.scene_inputs, source,
        observed["dataset_source_sha256"])
    # Compare the complete metadata plan before permitting tensor deserialization.
    joins_path = location.locations["physical_bindings.json"]

    def read_json(value):
        if str(value) != joins_path:
            raise ValueError("Unexpected saved JSON location")
        location.verify()
        return json.loads(Path(value).read_bytes())

    joins = read_json(joins_path)
    location.validate_denominator(joins, ids)
    planned = exporter.manifest()
    expected_dispositions = [
        dict(row, status="missing_capture" if row["status"] == "bound" else row["status"])
        for row in joins["dispositions"]]
    if (planned["dispositions"] != expected_dispositions
            or planned["dataset_metadata_sha256"] != joins["dataset_metadata_sha256"]):
        raise ValueError("Original native metadata plan differs")
    paths = {
        location.locations["item_%d.pth" % index]
        for index in location.contract["original_dataset_indices"]}

    def load_item(value):
        if str(value) not in paths:
            raise ValueError("Unexpected saved tensor location")
        require_cpu_runtime(torch)
        location.verify()
        if fingerprint(native.scene_inputs) != metadata_digest:
            raise ValueError("Native metadata changed before saved loading")
        # The hashes must be verified before trusted native pickle deserialization.
        item = torch.load(value, map_location="cpu", weights_only=False)
        require_cpu_runtime(torch)
        location.verify()
        return item

    if fingerprint(native.scene_inputs) != metadata_digest:
        raise ValueError("Factory mutated native metadata")
    require_cpu_runtime(torch)
    return dict(
        location=location, exporter=exporter, registry_ids=copy.deepcopy(ids),
        read_json=read_json, load_item=load_item, native=native, torch=torch,
        capture_id=capture_id, producer_sha256=source["producer_sha256"])
