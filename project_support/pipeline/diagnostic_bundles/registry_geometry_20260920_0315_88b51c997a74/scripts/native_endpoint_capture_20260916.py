"""Versioned native capture with exact sampled instance-to-semantic provenance."""
from pathlib import Path
from numbers import Integral

from capture_support_20260916 import CaptureDataset, plain
from native_support_capture_v2_20260916 import main
from physical_mask_endpoints_20260916 import (
    mask_endpoints, recoverable_same_class_stratum,
)


def semantic_binding(inverse, point_instances, point_semantics, native_instances):
    inverse, points, semantics, native = map(
        plain, (inverse, point_instances, point_semantics, native_instances))
    if len(inverse) != len(points) or len(points) != len(semantics):
        raise ValueError("Point semantic/instance support differs")
    if not native or set(inverse) != set(range(len(native))):
        raise ValueError("Superpoint axis differs")
    if any(not isinstance(x, Integral) or isinstance(x, bool)
           for x in inverse + points + semantics):
        raise ValueError("Integer point axes required")
    classes, counts = {}, [{} for _ in native]
    for sp, instance, semantic in zip(inverse, points, semantics):
        classes.setdefault(instance, set()).add(semantic)
        counts[sp][instance] = counts[sp].get(instance, 0) + 1
    physical = []
    for label, count in zip(native, counts):
        majority = [k for k, v in count.items() if v * 2 > sum(count.values())]
        expected = majority[0] if majority else 199
        if label != expected:
            raise ValueError("Native majority-instance axis mismatch")
        physical.append(expected if majority else -1)
    bound = [next(iter(classes[x])) if x >= 0 and len(classes.get(x, ())) == 1
             else -1 for x in physical]
    return dict(physical_instance_labels=physical, semantic_labels=bound,
                semantic_binding="unique class per sampled physical instance; unknown=-1",
                unresolved_superpoints=sum(not any(v * 2 > sum(c.values()) for v in c.values())
                                           for c in counts))


class EndpointDataset(CaptureDataset):
    def __getitem__(self, index):
        dataset = self.dataset
        native = dataset.get_sp_label
        had_override = "get_sp_label" in vars(dataset)
        override = vars(dataset).get("get_sp_label")
        captured = []

        def bind(superpoint, instances, semantics):
            result = native(superpoint, instances, semantics)
            captured.append(semantic_binding(superpoint, instances, semantics, result[0]))
            return result

        dataset.get_sp_label = bind
        try:
            item, axes = super().__getitem__(index)
        finally:
            if had_override:
                dataset.get_sp_label = override
            else:
                delattr(dataset, "get_sp_label")
        if len(captured) != 1:
            raise ValueError("Expected one native semantic binding per scene")
        for axis in axes:
            axis.update(captured[0])
        return item, axes


def enrich_row(row, selected_mask):
    endpoints = mask_endpoints(
        row, selected_mask, row["physical_instance_labels"],
        row["target_instances"], row["semantic_labels"])
    row.update(endpoint_schema_version=2, selected_mask=selected_mask,
               selected_mask_endpoints=endpoints,
               recoverable_same_class=recoverable_same_class_stratum(
                   row["ious"], row["selected_query"], endpoints))


if __name__ == "__main__":
    directory = Path(__file__).parent
    sources = [directory / name for name in (
        "native_endpoint_capture_20260916.py", "native_support_capture_v2_20260916.py",
        "capture_support_20260916.py", "physical_mask_endpoints_20260916.py")]
    main(dataset_class=EndpointDataset, enrich_row=enrich_row, producer_files=sources)
