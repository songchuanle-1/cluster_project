"""Metadata-only migration contract; no SSH, native imports or deserialization."""
import argparse
import copy
import json
from pathlib import Path, PurePosixPath

from frozen_capture_contract_20260916 import file_sha256

ROOT = Path(__file__).resolve().parents[1]
SOURCE = PurePosixPath("/data3/songcl/Project/Cluster_project")
DESTINATION = PurePosixPath("/data/songcl/Project/Cluster_project")
SOURCE_DATA = PurePosixPath("/data3/songcl/data/data_cluster")
DESTINATION_DATA = PurePosixPath("/home/songcl/data/data")
PHYSICAL = "pipeline/reports/recovery_physical_20260920-0915.json"
PRIOR = "pipeline/reports/cpu_recovery_progress_20260920-0915.json"


def checked_path(value):
    if (not isinstance(value, str) or "\\" in value
            or any(part in ("", ".", "..") for part in value.split("/")[1:])):
        raise ValueError("Noncanonical absolute artifact path")
    path = PurePosixPath(value)
    if not path.is_absolute() or str(path) != value:
        raise ValueError("Noncanonical absolute artifact path")
    return path


def checked_hash(value):
    if (not isinstance(value, str) or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)):
        raise ValueError("Expected SHA256")
    return value


def mapped_path(value, source, destination):
    path = checked_path(value)
    if not path.is_relative_to(source) or path == source:
        raise ValueError("Artifact outside bounded source")
    return str(destination / path.relative_to(source))


def build_contract(physical, prior):
    """Keep hashed provenance unchanged; destination locations are a separate map."""
    if physical.get("error") or physical.get("returncode") != 0:
        raise ValueError("Physical capture incomplete")
    for key in ("physical_items_completed", "sources_stable",
                "annotation_and_cache_stable", "previous_artifacts_stable"):
        if physical.get(key) is not True:
            raise ValueError("Physical gate incomplete: " + key)
    if (physical.get("gpu_initialized") is not False
            or physical.get("model_forward_completed") is not False):
        raise ValueError("Expected CPU-only physical provenance")
    indices = [row["dataset_index"] for row in physical["items"]]
    if (indices != [3040, 3893] or any(type(i) is not int for i in indices)
            or physical["selected_indices"] != indices):
        raise ValueError("Require exact saved groups 3040/3893")
    if (physical["binding_counts"] != {"bound": 4, "missing_capture": 27}
            or prior["registry_denominator"] != 31
            or prior["physical_bindings_verified"] != 9
            or prior["model_geometry_captures"] != 0
            or physical["observed_binding"] != prior["observed_binding"]):
        raise ValueError("Denominator or producer binding differs")
    for value in physical["observed_binding"].values():
        checked_hash(value)
    pairs = [row["pair_id"] for row in physical["physical_pair_summary"]]
    cumulative = prior["cumulative_pair_ids"]
    if (len(pairs) != 4 or len(set(pairs)) != 4
            or len(cumulative) != 9 or len(set(cumulative)) != 9
            or not set(pairs).issubset(cumulative)):
        raise ValueError("Physical union identity differs")
    scratch = checked_path(physical["scratch"])
    if scratch != SOURCE / (
            "pipeline/diagnostic_bundles/"
            "registry_geometry_20260920_0315_88b51c997a74_physical_20260920_0915"):
        raise ValueError("Unexpected saved scratch")
    expected_names = {"item_3040.pth", "item_3893.pth", "physical_bindings.json"}
    names, transfers = set(), []
    for row in physical["artifacts"]:
        path = checked_path(row["path"])
        if path.parent != scratch or path.name in names:
            raise ValueError("Unexpected or duplicate saved artifact")
        if type(row["bytes"]) is not int or row["bytes"] <= 0:
            raise ValueError("Positive artifact byte count required")
        names.add(path.name)
        transfers.append(dict(
            source=str(path), destination=mapped_path(str(path), SOURCE, DESTINATION),
            bytes=row["bytes"], sha256=checked_hash(row["sha256"])))
    if names != expected_names:
        raise ValueError("Exact saved artifact inventory required")
    inputs = list(physical["input_files"]) + [
        dict(path=path, sha256=sha)
        for path, sha in physical["annotation_and_cache_before"].items()]
    destinations, data_checks = set(), []
    for row in inputs:
        destination = mapped_path(row["path"], SOURCE_DATA, DESTINATION_DATA)
        if destination in destinations:
            raise ValueError("Duplicate destination data path")
        destinations.add(destination)
        data_checks.append(dict(source=row["path"], destination=destination,
                                sha256=checked_hash(row["sha256"])))
    return dict(
        schema_version=1, kind="metadata_only_saved_replay_migration",
        source_server="server-6", destination_server="server-4",
        authorized_gpus=[0, 1], max_tasks_per_gpu=1,
        native_execution_authorized=False, transfer_authorized=False,
        destination_bytes_verified=False, native_replay_completed=False,
        scientific_validation_complete=False, admission=False,
        original_dataset_indices=indices, registry_denominator=31,
        bundle_binding_counts=copy.deepcopy(physical["binding_counts"]),
        cumulative_physical_count=9, model_geometry_captures=0,
        physical_pair_ids=pairs, original_binding=copy.deepcopy(physical["observed_binding"]),
        original_scratch=str(scratch), artifact_transfers=transfers,
        data_verification=data_checks,
        required_before_transfer=[
            "server-4 SSH, GPU0/1 occupancy/memory, code, environment and data verified",
            "read-only retrieval permission only on server-6; no diagnostic execution",
            "fresh destination; reject symlinks, collisions and changed source bytes"],
        required_before_native_replay=[
            "all destination artifact bytes and data hashes verified on server-4",
            "immutable producer/model/checkpoint/dataset source hashes verified",
            "separate location adapter tested without rewriting hashed provenance",
            "replace legacy hardcoded GPU7 capacity/CLI path with server-4 guard",
            "collate exact saved groups, preserve all31 rows; no resampling",
            "no new scientific admission inferred from migration or static tests"])


def verify_destination_artifacts(contract, inspect):
    """Inspect is a read-only lstat/hash callback, never a tensor loader."""
    if (contract.get("kind") != "metadata_only_saved_replay_migration"
            or contract.get("destination_server") != "server-4"):
        raise ValueError("Migration contract required")
    seen = set()
    for row in contract["artifact_transfers"]:
        expected = mapped_path(row["source"], SOURCE, DESTINATION)
        if row["destination"] != expected or expected in seen:
            raise ValueError("Destination mapping differs")
        seen.add(expected)
        actual = inspect(expected)
        if (actual.get("regular_file") is not True
                or actual.get("symlink") is not False
                or actual.get("parent_chain_verified") is not True
                or actual.get("bytes") != row["bytes"]
                or actual.get("sha256") != checked_hash(row["sha256"])):
            raise ValueError("Destination bytes/path not verified")
    if len(seen) != 3:
        raise ValueError("Exact three-artifact inventory required")
    return dict(artifact_count=3, destination_artifact_bytes_verified=True,
                native_execution_authorized=False, native_replay_completed=False)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    physical = json.loads((ROOT / PHYSICAL).read_text(encoding="utf-8"))
    prior = json.loads((ROOT / PRIOR).read_text(encoding="utf-8"))
    recorded = next(row["sha256"] for row in prior["evidence"] if row["path"] == PHYSICAL)
    if file_sha256(ROOT / PHYSICAL) != recorded:
        raise ValueError("Recorded physical evidence changed")
    contract = build_contract(physical, prior)
    contract["evidence"] = [dict(path=p, sha256=file_sha256(ROOT / p))
                            for p in (PHYSICAL, PRIOR, "pipeline/goal.json", "SERVERS.yaml")]
    with Path(args.output).open("x", encoding="ascii") as stream:
        json.dump(contract, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(output=args.output, artifact_count=3,
                          data_checks=len(contract["data_verification"]),
                          native_execution=False, registry_denominator=31)))


if __name__ == "__main__":
    main()
