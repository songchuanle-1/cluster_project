"""Explicit dataset/physical bindings for the fixed failure-local registry.

Metadata planning is not native evidence. Feed export_item the unchanged item
and axes returned by FrozenDataset, before collation, on the authorized host.
The frozen producer and existing runtime remain untouched.
"""
import copy
from collections import Counter

from frozen_capture_contract_20260916 import fingerprint
from referent_geometry_capture_20260919 import (
    check_binding, identity, native_labels, plain, require_hash,
)
from referent_geometry_registry_20260919 import canonical_id, registry_pairs


CONTRACT = "fixed_registry_native_binding_v1"


def metadata_identity(data):
    scene = data["scene_id"]
    if not isinstance(scene, str) or not scene:
        raise ValueError("Metadata scene required")
    ann = canonical_id(data["ann_id"])
    if "object_ids" in data:
        targets = [canonical_id(x) for x in data["object_ids"]]
        if "object_id" in data and targets != [canonical_id(data["object_id"])]:
            raise ValueError("Conflicting metadata targets")
    else:
        targets = [canonical_id(data["object_id"])]
    if len(targets) != 1:
        raise ValueError("Single-target ScanRefer binding required")
    return scene, ann, targets[0]


def plan_bindings(registry, registry_sha256, scene_inputs):
    """Resolve full metadata keys; retain absent and ambiguous pairs explicitly."""
    require_hash(registry_sha256)
    if not isinstance(scene_inputs, list):
        raise ValueError("Explicit native scene_inputs list required")
    locations = {}
    for index, group in enumerate(scene_inputs):
        if not isinstance(group, list) or not group:
            raise ValueError("Nonempty native metadata group required")
        scene = None
        for slot, data in enumerate(group):
            current, ann, target = metadata_identity(data)
            if scene is not None and current != scene:
                raise ValueError("Mixed scenes in native dataset item")
            scene = current
            locations.setdefault((scene, slot, ann, target), []).append(index)
    rows = []
    for pair in registry_pairs(registry):
        key = (pair["scene"], canonical_id(pair["expression_slot"]),
               canonical_id(pair["ann_id"]), canonical_id(pair["target_object_id"]))
        matches = locations.get(key, [])
        rows.append(dict(
            pair_id=pair["pair_id"],
            status=("missing_metadata" if not matches else
                    "ambiguous_metadata" if len(matches) != 1 else "planned"),
            dataset_indices=matches[:],
            dataset_index=matches[0] if len(matches) == 1 else None,
            scene=key[0], expression_slot=key[1], ann_id=key[2],
            target_object_id=key[3],
            control_object_id=canonical_id(pair["observed_control_object_id"]),
        ))
    return dict(
        contract=CONTRACT, registry_sha256=registry_sha256,
        dataset_metadata_sha256=fingerprint(scene_inputs), rows=rows,
        counts=dict(Counter(row["status"] for row in rows)),
        native_execution_verified=False,
    )


class BindingExporter:
    """Serial, fail-closed observer; never calls a dataset or model itself."""

    def __init__(self, registry, registry_sha256, scene_inputs, source_binding,
                 dataset_source_sha256):
        check_binding(source_binding)
        require_hash(dataset_source_sha256)
        self.metadata = copy.deepcopy(scene_inputs)
        self.plan = plan_bindings(registry, registry_sha256, self.metadata)
        self.source_binding = copy.deepcopy(source_binding)
        self.dataset_source_sha256 = dataset_source_sha256
        self.bindings = {}
        self.observations = set()

    def export_item(self, dataset_index, item, axes):
        if type(dataset_index) is not int or not 0 <= dataset_index < len(self.metadata):
            raise ValueError("Invalid dataset index")
        if len(item) != 16:
            raise ValueError("Expected native 16-field dataset item")
        group = self.metadata[dataset_index]
        if not isinstance(axes, list) or len(axes) != len(group):
            raise ValueError("Full native expression axes required")
        anns, targets = plain(item[0]), plain(item[6])
        if len(anns) != len(group) or len(targets) != len(group):
            raise ValueError("Native target/annotation count differs")
        digest = fingerprint(item)
        physical_axes = []
        for slot, (data, axis) in enumerate(zip(group, axes)):
            scene, ann, target = metadata_identity(data)
            physical = identity(axis)
            if (physical["dataset_index"] != dataset_index
                    or physical["expression_slot"] != slot
                    or physical["scene"] != scene or item[1] != scene
                    or physical["ann_id"] != ann
                    or type(anns[slot]) is not int or anns[slot] != ann
                    or not isinstance(targets[slot], list)
                    or len(targets[slot]) != 1
                    or type(targets[slot][0]) is not int
                    or targets[slot][0] != target):
                raise ValueError("Native metadata/target identity mismatch")
            if physical["native_input_sha256"] != digest:
                raise ValueError("Transformed input hash mismatch")
            for field in ("producer_sha256", "checkpoint_sha256"):
                if axis.get(field) != self.source_binding[field]:
                    raise ValueError("Native source binding mismatch")
            if plain(item[5]) != physical["sample_inverse"]:
                raise ValueError("Native sampled support mismatch")
            labels = plain(axis["physical_instance_labels"])
            native = native_labels(plain(item[11]))
            n = len(physical["original_superpoint_ids"])
            if len(native) != n or len(labels) != n or len(item[15]) != n:
                raise ValueError("Native physical support dimensions differ")
            if any(type(x) is not int or x < -1 for x in labels):
                raise ValueError("Invalid physical instance labels")
            if any(x != y and not (x == -1 and y == 199)
                   for x, y in zip(labels, native)):
                raise ValueError("Native physical instance labels differ")
            if physical_axes:
                for field in ("capture_id", "scene_occurrence", "native_input_sha256",
                              "original_superpoint_ids", "sample_inverse"):
                    if physical[field] != physical_axes[0][field]:
                        raise ValueError("Inconsistent scene observation")
                if labels != plain(axes[0]["physical_instance_labels"]):
                    raise ValueError("Inconsistent scene physical labels")
            physical_axes.append(physical)
        observation = (physical_axes[0]["capture_id"],
                       physical_axes[0]["scene_occurrence"])
        if observation in self.observations:
            raise ValueError("Duplicate scene occurrence")
        planned = [row for row in self.plan["rows"]
                   if row["dataset_index"] == dataset_index and row["status"] == "planned"]
        pending = {}
        for row in planned:
            if row["pair_id"] in self.bindings:
                raise ValueError("Repeated native capture for registry pair")
            slot = row["expression_slot"]
            physical = physical_axes[slot]
            labels = plain(axes[slot]["physical_instance_labels"])
            pending[row["pair_id"]] = dict(
                pair_id=row["pair_id"], identity=physical,
                target_object_id=row["target_object_id"],
                control_object_id=row["control_object_id"],
                physical_instance_labels=labels,
                physical_support_sha256=fingerprint(dict(
                    original_superpoint_ids=physical["original_superpoint_ids"],
                    sample_inverse=physical["sample_inverse"],
                    physical_instance_labels=labels)),
                target_support_count=labels.count(row["target_object_id"]),
                control_support_count=labels.count(row["control_object_id"]),
                metadata_expression_sha256=fingerprint(group[slot]),
            )
        # Commit only after the entire observation has passed every check.
        self.bindings.update(copy.deepcopy(pending))
        self.observations.add(observation)
        return copy.deepcopy(list(pending.values()))

    def manifest(self):
        rows = [dict(row, status="bound" if row["pair_id"] in self.bindings
                     else "missing_capture" if row["status"] == "planned"
                     else row["status"]) for row in self.plan["rows"]]
        result = dict(
            contract=CONTRACT, registry_sha256=self.plan["registry_sha256"],
            dataset_metadata_sha256=self.plan["dataset_metadata_sha256"],
            dataset_source_sha256=self.dataset_source_sha256,
            source_binding=copy.deepcopy(self.source_binding),
            bindings=copy.deepcopy(list(self.bindings.values())),
            requested=len(rows), counts=dict(Counter(row["status"] for row in rows)),
            dispositions=rows,
            native_execution_verified=False, scientific_validation_complete=False,
            limitations=[
                "Caller must verify native source provenance and authorized execution.",
                "Hashes identify inputs; they do not attest truthful observation.",
                "Metadata planning is not physical capture or model execution.",
                "Missing object support is recorded, not imputed or excluded.",
                "Binding new captures does not reproduce historical transforms.",
                "Failure-selected pairs are not population-effect evidence.",
            ],
        )
        result["payload_sha256"] = fingerprint(result)
        return result
