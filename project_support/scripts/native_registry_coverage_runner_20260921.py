"""Coverage wrapper for the frozen registry geometry diagnostic.

The frozen runner intentionally selects the first one or two planned dataset
indices. This wrapper preserves its capture and evaluation code while allowing
an explicit, validated subset of original dataset indices. It never launches
training or changes the model.
"""
import argparse
from pathlib import Path

import native_registry_geometry_runner_20260920 as base


CONTRACT = "registry_geometry_coverage_runner_v1"


def validate_selection(requested, planned):
    """Return a canonical selection without reindexing or inventing indices."""
    if not isinstance(requested, (list, tuple)) or not 1 <= len(requested) <= 2:
        raise ValueError("Require one or two explicit dataset indices")
    if any(type(index) is not int or index < 0 for index in requested):
        raise ValueError("Dataset indices must be nonnegative integers")
    if len(set(requested)) != len(requested):
        raise ValueError("Dataset indices must be unique")
    canonical = tuple(requested)
    planned = set(planned)
    if any(type(index) is not int or index < 0 for index in planned):
        raise ValueError("Planned dataset indices must be nonnegative integers")
    if not set(canonical).issubset(planned):
        raise ValueError("Selected dataset index is not an unambiguous planned item")
    return canonical


def runner_manifest():
    result = base.source_manifest(entry=Path(__file__).name)
    result["contract"] = CONTRACT
    return result


class SelectedRegistryDataset(base.RegistryDataset):
    selected_indices = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        planned = {
            row["dataset_index"]
            for row in self.exporter.plan["rows"]
            if row["status"] == "planned"
        }
        self.indices = validate_selection(self.selected_indices, planned)


def assign_selection(indices):
    SelectedRegistryDataset.selected_indices = tuple(indices)


def base_arguments(args):
    return [
        "--root", args.root,
        "--checkpoint", args.checkpoint,
        "--registry", args.registry,
        "--expected-binding", args.expected_binding,
        "--output", args.output,
        "--items", str(args.items),
    ]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-indices", nargs="+", type=int, required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--expected-binding", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--items", type=int, default=2)
    args = parser.parse_args(argv)
    if len(args.dataset_indices) != args.items:
        raise ValueError("Dataset index count must equal --items")
    base.runner_manifest = runner_manifest
    base.RegistryDataset = SelectedRegistryDataset
    assign_selection(validate_selection(args.dataset_indices, args.dataset_indices))
    return base.main(base_arguments(args))


if __name__ == "__main__":
    main()
