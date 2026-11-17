"""Aggregate covered registry-geometry bundles without imputing missing pairs."""
import argparse
import json
from pathlib import Path

from frozen_capture_contract_20260916 import file_sha256
from referent_geometry_registry_20260919 import evaluate


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def aggregate_bundles(run_root, registry, registry_sha256):
    captures = []
    bindings = []
    source_binding = None
    observed_indices = set()
    bundle_rows = []
    for bundle in sorted(path for path in run_root.iterdir() if path.is_dir()):
        if (bundle / "failure.json").exists():
            raise ValueError("Failed bundle present: " + str(bundle))
        capture_path = bundle / "capture.json"
        bindings_path = bundle / "bindings.json"
        if not capture_path.is_file() or not bindings_path.is_file():
            raise ValueError("Incomplete bundle: " + str(bundle))
        capture = load_json(capture_path)
        if capture.get("native_capture_completed") is not True:
            raise ValueError("Incomplete native capture: " + str(bundle))
        binding = capture.get("binding")
        if source_binding is None:
            source_binding = binding
        elif binding != source_binding:
            raise ValueError("Source binding differs across bundles")
        indices = capture.get("original_dataset_indices")
        if (not isinstance(indices, list) or not indices
                or len(set(indices)) != len(indices)
                or set(indices) & observed_indices):
            raise ValueError("Duplicate or invalid dataset indices")
        observed_indices.update(indices)
        for artifact in capture.get("artifacts", []):
            if artifact["path"].startswith("geometry_"):
                path = bundle / artifact["path"]
                if file_sha256(path) != artifact["sha256"]:
                    raise ValueError("Capture artifact hash differs: " + str(path))
                captures.append(load_json(path))
        joined = load_json(bindings_path)
        if joined.get("registry_sha256") != registry_sha256:
            raise ValueError("Bindings registry hash differs")
        if joined.get("source_binding") != source_binding:
            raise ValueError("Bindings source binding differs")
        bindings.extend(joined.get("bindings", []))
        bundle_rows.append({
            "bundle": bundle.name,
            "dataset_indices": indices,
            "capture_sha256": file_sha256(capture_path),
            "bindings_sha256": file_sha256(bindings_path),
        })
    by_pair = {}
    for row in bindings:
        pair_id = row.get("pair_id")
        if pair_id in by_pair:
            raise ValueError("Duplicate pair binding: " + str(pair_id))
        by_pair[pair_id] = row
    eligible = {
        row["pair_id"]: row
        for row in registry["pairs"]
        if row["primary_same_class_pair_eligible"] is True
    }
    missing = sorted(set(eligible) - set(by_pair))
    joins = {
        "contract": "merged_fixed_registry_native_binding_v1",
        "registry_sha256": registry_sha256,
        "source_binding": source_binding,
        "bindings": [by_pair[key] for key in sorted(by_pair)],
        "requested": len(eligible),
        "bound": len(by_pair),
        "missing": missing,
        "bundles": bundle_rows,
        "native_execution_verified": False,
        "scientific_validation_complete": False,
    }
    return captures, joins


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--output-joins", required=True)
    parser.add_argument("--output-evaluation", required=True)
    args = parser.parse_args(argv)
    run_root = Path(args.run_root).resolve()
    registry_path = Path(args.registry).resolve()
    output_joins = Path(args.output_joins).resolve()
    output_evaluation = Path(args.output_evaluation).resolve()
    if output_joins.exists() or output_evaluation.exists():
        raise ValueError("Refuse to replace existing aggregate outputs")
    registry = load_json(registry_path)
    registry_sha256 = file_sha256(registry_path)
    captures, joins = aggregate_bundles(run_root, registry, registry_sha256)
    result = evaluate(
        registry,
        registry_sha256,
        captures,
        joins["source_binding"],
        joins,
    )
    result["coverage"] = {
        "bundles": len(joins["bundles"]),
        "capture_files": len(captures),
        "bound_pairs": joins["bound"],
        "requested_pairs": joins["requested"],
        "missing_pairs": joins["missing"],
    }
    output_joins.write_text(
        json.dumps(joins, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    output_evaluation.write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps(result["coverage"], sort_keys=True))


if __name__ == "__main__":
    main()
