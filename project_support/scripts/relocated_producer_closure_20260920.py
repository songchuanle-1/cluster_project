"""Static local-producer closure, separate from original capture provenance."""
from pathlib import Path

from frozen_capture_contract_20260916 import fingerprint
from native_geometry_runtime_20260919 import source_manifest


ENTRIES = (
    "relocated_factory_core_20260920.py",
    "saved_physical_location_20260920.py",
    "native_saved_batch_validation_20260920.py",
    "relocated_saved_collation_20260920.py",
    "native_frozen_capture_20260916.py",
)


def producer_closure(directory=None, entries=ENTRIES):
    """Reuse the existing AST traversal; never import scanned producer sources.

    External packages and dynamic imports are unresolved deployment dependencies,
    not an assertion of a complete Python environment.
    """
    directory = Path(directory or Path(__file__).parent).resolve()
    entries = tuple(entries)
    if not entries or len(set(entries)) != len(entries):
        raise ValueError("Distinct producer entry files required")
    files, external = {}, set()
    for entry in entries:
        manifest = source_manifest(directory=directory, entry=entry)
        for row in manifest["sources"]:
            prior = files.setdefault(row["path"], row["sha256"])
            if prior != row["sha256"]:
                raise ValueError("Source changed during closure traversal")
        external.update(manifest["external_imports"])
    rows = [dict(path=name, sha256=sha) for name, sha in sorted(files.items())]
    # Rewalk to detect drift between overlapping entry traversals.
    for entry in entries:
        for row in source_manifest(directory=directory, entry=entry)["sources"]:
            if files.get(row["path"]) != row["sha256"]:
                raise ValueError("Source changed during closure traversal")
    return dict(
        contract="relocated-producer-static-closure-v1", files=rows,
        entries=list(entries), closure_sha256=fingerprint(rows),
        external_imports=sorted(external), native_environment_verified=False,
        dynamic_imports_verified=False, deployment_ready=False,
        original_capture_producer_unchanged=True,
        limitations=[
            "Closure covers statically named local imports, including function bodies.",
            "Dynamic imports, native extensions and external packages need runtime attestation.",
            "Bootstrap/launcher and zero-argument deployment factory are separate inputs.",
            "This manifest must not replace the original physical producer hash."])
