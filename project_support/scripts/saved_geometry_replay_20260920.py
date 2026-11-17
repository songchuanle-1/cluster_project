"""Exact saved-batch adapter; caller owns native capacity and model lifecycle."""
from pathlib import Path

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from native_geometry_runtime_20260919 import capture_forward, verify_batch_axis


def verify_artifacts(artifacts, parent):
    parent = Path(parent)
    paths = set()
    for row in artifacts:
        path = Path(row["path"])
        if (path.parent != parent or path.is_symlink() or path in paths
                or path.resolve().parent != parent.resolve()):
            raise ValueError("Untrusted or duplicate saved artifact")
        paths.add(path)
        if (path.stat().st_size != row["bytes"]
                or file_sha256(path) != row["sha256"]):
            raise ValueError("Saved artifact bytes differ")
    return paths


def verify_payload(payload, saved, expected, item_sha256, binding):
    index = expected["dataset_index"]
    if type(index) is not int:
        raise ValueError("Integer original dataset index required")
    for value in (payload, saved):
        if (type(value["dataset_index"]) is not int
                or value["dataset_index"] != index
                or value["source_binding"] != binding):
            raise ValueError("Saved source/index differs")
    item, axes, batch = payload["item"], payload["axes"], saved["batch"]
    if (fingerprint(payload) != expected["payload_sha256"]
            or fingerprint(item) != expected["native_input_sha256"]
            or fingerprint(axes) != expected["axes_sha256"]
            or fingerprint(saved["axes"]) != expected["axes_sha256"]
            or fingerprint(batch) != expected["batch_sha256"]
            or saved["saved_item_sha256"] != item_sha256
            or saved["item_fingerprint"] != expected["native_input_sha256"]
            or saved["axes_fingerprint"] != expected["axes_sha256"]):
        raise ValueError("Saved payload fingerprint differs")
    if set(batch) != set(expected["fields"]):
        raise ValueError("Saved batch field inventory differs")
    for name, value in batch.items():
        if fingerprint(value) != expected["fields"][name]["sha256"]:
            raise ValueError("Saved batch field differs: " + name)
    if len(axes) != expected["expressions"]:
        raise ValueError("Saved expression count differs")
    verify_batch_axis(batch, saved["axes"])
    return fingerprint(saved)


def prepare_replay(request, exporter, load):
    """Verify every byte before trusted deserialization; never call a dataset."""
    physical, collated = request["physical"], request["collated"]
    physical_paths = verify_artifacts(physical["artifacts"], physical["scratch"])
    batch_paths = verify_artifacts(collated["artifacts"], collated["scratch"])
    items = collated["items"]
    if not 1 <= len(items) <= 2:
        raise ValueError("Require one or two saved groups")
    indices = [row["dataset_index"] for row in items]
    if (any(type(i) is not int for i in indices)
            or len(set(indices)) != len(indices)):
        raise ValueError("Duplicate or invalid original dataset indices")
    expected_items = {Path(physical["scratch"]) / ("item_%d.pth" % i) for i in indices}
    joins_path = Path(physical["scratch"]) / "physical_bindings.json"
    expected_batches = {Path(collated["scratch"]) / ("batch_%d.pth" % i) for i in indices}
    if physical_paths != expected_items | {joins_path} or batch_paths != expected_batches:
        raise ValueError("Saved artifact inventory differs")
    import json
    joins = json.loads(joins_path.read_text(encoding="utf-8"))
    if fingerprint(joins) != collated["full_binding_sha256"]:
        raise ValueError("Full physical binding fingerprint differs")
    binding = exporter.source_binding
    if collated["observed_binding"] != physical["observed_binding"]:
        raise ValueError("Saved producer/data binding differs")
    if any(collated["observed_binding"].get(k) != v for k, v in binding.items()):
        raise ValueError("Current producer binding differs")
    for key, value in (
            ("dataset_source_sha256", exporter.dataset_source_sha256),
            ("registry_sha256", exporter.plan["registry_sha256"])):
        if collated["observed_binding"].get(key) != value:
            raise ValueError("Current data binding differs")
    prepared = []
    for row in items:
        index = row["dataset_index"]
        item_path = Path(physical["scratch"]) / ("item_%d.pth" % index)
        payload = load(item_path)
        saved = load(Path(collated["scratch"]) / ("batch_%d.pth" % index))
        digest = verify_payload(payload, saved, row, file_sha256(item_path), binding)
        exporter.export_item(index, payload["item"], payload["axes"])
        prepared.append((saved, digest))
    if exporter.manifest() != joins:
        raise ValueError("Reconstructed complete physical bindings differ")
    # Detect concurrent input replacement while loading.
    verify_artifacts(physical["artifacts"], physical["scratch"])
    verify_artifacts(collated["artifacts"], collated["scratch"])
    return prepared, joins


def replay_forward(model, prepared, binding, sink=None):
    """Keep saved capture identities; criterion/FPS/query checks stay native."""
    if not 1 <= len(prepared) <= 2:
        raise ValueError("Require one or two verified saved groups")
    indices = [saved["dataset_index"] for saved, _ in prepared]
    if len(set(indices)) != len(indices):
        raise ValueError("Duplicate saved groups")
    for saved, digest in prepared:
        if fingerprint(saved) != digest or saved["source_binding"] != binding:
            raise ValueError("Prepared saved input mutated")
    records = []
    for step, (saved, digest) in enumerate(prepared):
        record = capture_forward(model, saved["batch"], saved["axes"], binding)
        if fingerprint(saved) != digest:
            raise ValueError("Replay mutated saved inputs")
        records.append(record)
        if sink is not None:
            sink(step, saved["dataset_index"], record)
    return records
