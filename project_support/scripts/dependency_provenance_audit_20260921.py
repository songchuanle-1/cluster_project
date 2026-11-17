"""Validate static installed-dependency provenance; not an ABI attestation.

The input is a read-only observation manifest for server-4. Validation proves
that exact roots, module files, bootstrap rows and ELF declarations were
recorded. It does not prove runtime loading, loader resolution, ABI
compatibility, sandbox enforcement or authorization to execute native work.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath

from pinned_diagnostic_imports_20260920 import checked_digest, digest, regular_bytes


INPUT_CONTRACT = "installed-dependency-observation-v1"
RECEIPT_CONTRACT = "installed-dependency-provenance-v1"
NATIVE_EXTENSION = "pointgroup_ops.pointgroup_ops_ext"
DIRECT_PACKAGES = frozenset({
    "dgl", "gorilla", "numpy", "scipy", "sng_parser", "torch",
    "torch_scatter", "tqdm", "transformers",
})
MAX_RECEIPT_BYTES = 4 * 1024 * 1024
TOP_KEYS = frozenset({
    "contract", "observed_at", "runtime", "roots", "bootstrap", "packages",
    "extension",
})
RUNTIME_KEYS = frozenset({"executable", "python", "torch", "cuda"})
ROOT_KEYS = frozenset({
    "conda_source", "environment_root", "site_packages", "code_root",
    "data_root", "work_root",
})
FILE_ROW_KEYS = frozenset({"path", "sha256"})
EXTENSION_KEYS = frozenset({
    "module", "artifact", "elf", "declared_needed", "cache_candidates",
})
ELF_KEYS = frozenset({"class", "byte_order", "machine"})
CANDIDATE_KEYS = frozenset({"soname", "path", "sha256"})
FALSE_GATE_KEYS = (
    "abi_compatibility_checked",
    "runtime_loader_resolution_verified",
    "native_data_loaded",
    "external_dependency_attestation",
    "native_execution_completed",
    "scientific_validation_complete",
    "admission",
)


def _strict_json(raw):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Nonfinite JSON value: " + value)

    if isinstance(raw, bytes):
        raw = raw.decode("ascii")
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def _object(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError("Invalid " + label + " schema")
    return value


def _canonical_path(value, label):
    if (not isinstance(value, str) or not value.startswith("/")
            or str(PurePosixPath(value)) != value or "\\" in value
            or ".." in PurePosixPath(value).parts):
        raise ValueError("Canonical absolute POSIX " + label + " required")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Nonempty " + label + " required")
    return value


def _file_row(value, label):
    row = _object(value, FILE_ROW_KEYS, label)
    return dict(path=_canonical_path(row["path"], label + " path"),
                sha256=checked_digest(row["sha256"]))


def _unique_rows(rows, key, label):
    seen = set()
    for row in rows:
        value = row[key]
        if value in seen:
            raise ValueError("Duplicate " + label + ": " + value)
        seen.add(value)
    return rows


def validate_observation(document):
    """Normalize one complete static observation; never touch observed files."""
    document = _object(document, TOP_KEYS, "dependency observation")
    if document["contract"] != INPUT_CONTRACT:
        raise ValueError("Unsupported dependency observation contract")
    observed_at = document["observed_at"]
    if (type(observed_at) not in (int, float)
            or not math.isfinite(observed_at) or observed_at <= 0):
        raise ValueError("Positive finite observation time required")

    runtime = _object(
        document["runtime"], RUNTIME_KEYS, "runtime observation")
    executable = _file_row(runtime["executable"], "runtime executable")
    python = _object(
        runtime["python"], {"version", "soabi", "platform"}, "Python runtime")
    python = {key: _text(python[key], "Python " + key)
              for key in ("version", "soabi", "platform")}
    torch = _object(runtime["torch"], {"version", "module"}, "Torch runtime")
    torch = dict(
        version=_text(torch["version"], "Torch version"),
        module=_file_row(torch["module"], "Torch module"))
    cuda = _object(
        runtime["cuda"], {"version", "visible_devices"}, "CUDA runtime")
    visible = cuda["visible_devices"]
    if (not isinstance(visible, list) or not visible
            or any(not isinstance(value, str) or not value for value in visible)
            or len(set(visible)) != len(visible)):
        raise ValueError("Unique observed CUDA device identities required")
    cuda = dict(
        version=_text(cuda["version"], "CUDA version"),
        visible_devices=list(visible))

    roots = _object(document["roots"], ROOT_KEYS, "dependency roots")
    conda_source = _file_row(roots["conda_source"], "conda source")
    normalized_roots = dict(conda_source=conda_source)
    for key in ("environment_root", "code_root", "data_root", "work_root"):
        normalized_roots[key] = _canonical_path(roots[key], key)
    site_packages = roots["site_packages"]
    if not isinstance(site_packages, list) or not site_packages:
        raise ValueError("At least one site-packages root required")
    normalized_roots["site_packages"] = [
        _canonical_path(value, "site-packages root") for value in site_packages]
    _unique_rows(
        [dict(root=value) for value in normalized_roots["site_packages"]],
        "root", "site-packages root")

    bootstrap = document["bootstrap"]
    if not isinstance(bootstrap, list) or not bootstrap:
        raise ValueError("Nonempty bootstrap inventory required")
    normalized_bootstrap = []
    for value in bootstrap:
        row = _object(value, {"name", "path", "sha256"}, "bootstrap row")
        name = _text(row["name"], "bootstrap module")
        if any(not part.isidentifier() for part in name.split(".")):
            raise ValueError("Invalid bootstrap module name")
        normalized_bootstrap.append(dict(
            name=name, **_file_row(
                {"path": row["path"], "sha256": row["sha256"]},
                "bootstrap module")))
    _unique_rows(normalized_bootstrap, "name", "bootstrap module")

    packages = document["packages"]
    if not isinstance(packages, list) or not packages:
        raise ValueError("Nonempty direct package inventory required")
    normalized_packages = []
    for value in packages:
        row = _object(
            value, {"import_root", "distribution", "version", "module",
                    "metadata"},
            "package row")
        normalized_packages.append(dict(
            import_root=_text(row["import_root"], "package import root"),
            distribution=_text(row["distribution"], "distribution name"),
            version=_text(row["version"], "distribution version"),
            module=_file_row(row["module"], "package module"),
            metadata=_file_row(row["metadata"], "package metadata")))
    _unique_rows(normalized_packages, "import_root", "package import root")
    _unique_rows(normalized_packages, "distribution", "distribution name")
    observed_packages = {row["import_root"] for row in normalized_packages}
    if observed_packages != DIRECT_PACKAGES:
        raise ValueError(
            "Direct package drift: missing=%s added=%s" % (
                sorted(DIRECT_PACKAGES - observed_packages),
                sorted(observed_packages - DIRECT_PACKAGES)))

    extension = _object(
        document["extension"], EXTENSION_KEYS, "native extension")
    if extension["module"] != NATIVE_EXTENSION:
        raise ValueError("Unexpected native extension module")
    artifact = _file_row(extension["artifact"], "extension artifact")
    elf = _object(extension["elf"], ELF_KEYS, "ELF header")
    elf = {key: _text(elf[key], "ELF " + key) for key in ELF_KEYS}
    if elf["class"] not in {"ELF32", "ELF64"}:
        raise ValueError("Invalid ELF class")
    if elf["byte_order"] not in {"little", "big"}:
        raise ValueError("Invalid ELF byte order")
    needed = extension["declared_needed"]
    if (not isinstance(needed, list) or not needed
            or any(not isinstance(value, str) or not value for value in needed)):
        raise ValueError("Nonempty declared ELF dependencies required")
    needed = sorted(needed)
    if len(set(needed)) != len(needed):
        raise ValueError("Duplicate declared ELF dependency")
    candidates = extension["cache_candidates"]
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Nonempty shared-library candidates required")
    normalized_candidates = []
    for value in candidates:
        row = _object(value, CANDIDATE_KEYS, "shared-library candidate")
        normalized_candidates.append(dict(
            soname=_text(row["soname"], "shared-library soname"),
            path=_canonical_path(row["path"], "shared-library path"),
            sha256=checked_digest(row["sha256"])))
    _unique_rows(normalized_candidates, "soname", "shared-library soname")
    if {row["soname"] for row in normalized_candidates} != set(needed):
        raise ValueError("Declared/cache shared-library sets differ")

    receipt = dict(
        contract=RECEIPT_CONTRACT,
        source_contract=INPUT_CONTRACT,
        observed_at=observed_at,
        runtime=dict(
            executable=executable, python=python, torch=torch, cuda=cuda),
        roots=normalized_roots,
        bootstrap=normalized_bootstrap,
        packages=normalized_packages,
        extension=dict(
            module=NATIVE_EXTENSION, artifact=artifact, elf=elf,
            declared_needed=needed,
            cache_candidates=normalized_candidates),
        audit=dict(
            direct_package_count=len(normalized_packages),
            bootstrap_count=len(normalized_bootstrap),
            shared_library_count=len(normalized_candidates)),
        **{key: False for key in FALSE_GATE_KEYS},
        limitations=[
            "A file hash proves observed bytes, not loaded bytes.",
            "ELF and ldconfig-cache declarations do not prove runtime linker resolution.",
            "Recorded Python SOABI and Torch version do not establish compatibility.",
            "Bootstrap rows do not attest execution before the observation child.",
            "No sandbox, GPU slot, model, data, backward or scientific claim is made.",
        ])
    return receipt


def load_receipt(path, expected_sha256):
    """Load one immutable receipt and revalidate its schema."""
    raw = regular_bytes(Path(path))
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError("Dependency receipt is too large")
    if digest(raw) != checked_digest(expected_sha256):
        raise ValueError("Dependency receipt hash differs")
    document = _strict_json(raw)
    if (not isinstance(document, dict)
            or document.get("contract") != RECEIPT_CONTRACT):
        raise ValueError("Invalid dependency receipt contract")
    return copy.deepcopy(document)


def write_receipt(observation_path, observation_sha256, output_path):
    """Validate pinned observation bytes and write one canonical receipt."""
    source = Path(observation_path).absolute()
    raw = regular_bytes(source)
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError("Dependency observation is too large")
    if digest(raw) != checked_digest(observation_sha256):
        raise ValueError("Dependency observation hash differs")
    receipt = validate_observation(_strict_json(raw))
    output = Path(output_path).absolute()
    if (output.is_symlink() or any(parent.is_symlink() for parent in output.parents)
            or not output.parent.is_dir()):
        raise ValueError("Canonical fresh receipt path required")
    encoded = json.dumps(
        receipt, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("ascii")
    descriptor = os.open(
        output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return output, hashlib.sha256(encoded).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output, sha256 = write_receipt(
        args.input, args.input_sha256, args.output)
    print("%s %s" % (output, sha256))


if __name__ == "__main__":
    main()
