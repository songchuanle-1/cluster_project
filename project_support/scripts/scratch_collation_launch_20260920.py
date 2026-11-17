"""Build the sandbox-to-bridge handoff; no public native execution CLI.

The host caller still owes runtime/GPU checks, external dependency attestation
and a verified bubblewrap binary. Command construction grants no authorization.
"""
from pathlib import PurePosixPath

from pinned_diagnostic_imports_20260920 import checked_digest
from scratch_cpu_boundary_20260920 import canonical, probe_command


INFRASTRUCTURE = (
    "cpu_diagnostic_bootstrap_20260920",
    "scratch_cpu_boundary_20260920",
    "pinned_diagnostic_imports_20260920",
    "same_child_collation_20260920",
)

# This bootstrap needs only stdlib and compiles the exact verified bytes. It
# deliberately adds no producer directory to sys.path.
CHILD = r'''
import hashlib, importlib.util, json, os, pathlib, sys
infra, infra_sha, bundle, bundle_sha, scratch, sentinel = sys.argv[1:]
infra, bundle, scratch, sentinel = map(pathlib.Path, (infra, bundle, scratch, sentinel))
names = (
    "cpu_diagnostic_bootstrap_20260920", "scratch_cpu_boundary_20260920",
    "pinned_diagnostic_imports_20260920", "same_child_collation_20260920")
def read(path):
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.is_file():
        raise ValueError("Missing or redirected bootstrap input")
    return path.read_bytes()
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
if not sys.flags.isolated or not sys.dont_write_bytecode:
    raise ValueError("Isolated bytecode-disabled child required")
if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
    raise ValueError("CPU child required")
manifest_raw = read(infra / "bootstrap.json")
if sha(manifest_raw) != infra_sha:
    raise ValueError("Bootstrap manifest hash differs")
manifest = json.loads(manifest_raw)
if (set(manifest) != {"contract", "files"}
        or manifest["contract"] != "collation-bootstrap-v1"
        or set(manifest["files"]) != {name + ".py" for name in names}):
    raise ValueError("Exact bootstrap source inventory required")
sources = {}
for name in names:
    raw = read(infra / (name + ".py"))
    if sha(raw) != manifest["files"][name + ".py"]:
        raise ValueError("Bootstrap source hash differs")
    sources[name] = raw
producer_raw = read(bundle / "manifest.json")
if sha(producer_raw) != bundle_sha:
    raise ValueError("Producer manifest hash differs")
producer = json.loads(producer_raw)
if any(pathlib.PurePosixPath(row["path"]).stem in names for row in producer["files"]):
    raise ValueError("Bootstrap and producer inventories overlap")
if any(path.exists() or path.is_symlink()
       for path in (scratch / "same_child.json", scratch / "collated")):
    raise FileExistsError("Fresh bootstrap output required")
owned = {}
def verify():
    if read(infra / "bootstrap.json") != manifest_raw:
        raise ValueError("Bootstrap manifest changed")
    for name, raw in sources.items():
        if read(infra / (name + ".py")) != raw or sys.modules.get(name) is not owned[name]:
            raise ValueError("Bootstrap bytes or module identity changed")
try:
    for name in names:
        if name in sys.modules:
            raise ValueError("Bootstrap module already imported")
        path = infra / (name + ".py")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = owned[name] = module
        exec(compile(sources[name], str(path), "exec"), module.__dict__)
    result = owned[names[-1]].run_same_child(
        bundle, bundle_sha, "relocated_native_factory_20260920", scratch, sentinel)
    verify()
    print(json.dumps(result, allow_nan=False))
except BaseException:
    # A fresh private run directory belongs to this invocation, not another job.
    (scratch / "same_child.json").unlink(missing_ok=True)
    (scratch / "collated" / "collation.json").unlink(missing_ok=True)
    raise
finally:
    for name, module in owned.items():
        if sys.modules.get(name) is module:
            del sys.modules[name]
'''


def collation_command(executable, bwrap, run, infrastructure, infrastructure_sha256,
                      bundle, manifest_sha256):
    """Build argv with the existing scratch-only mounts and pinned child.

    Inputs must be outside the writable run tree. The bootstrap inventory is
    separate from the producer manifest, preventing preimport conflicts.
    """
    run, infrastructure, bundle = map(canonical, (run, infrastructure, bundle))
    checked_digest(infrastructure_sha256)
    checked_digest(manifest_sha256)
    for value in (infrastructure, bundle):
        if value == PurePosixPath("/") or value.is_relative_to(run):
            raise ValueError("Pinned inputs must be outside writable run tree")
    if infrastructure == bundle:
        raise ValueError("Separate bootstrap and producer inventories required")
    args = probe_command(executable, bwrap, str(run))
    separator = args.index("--")
    return args[:separator + 5] + [
        CHILD, str(infrastructure), infrastructure_sha256, str(bundle),
        manifest_sha256, str(run / "output"), str(run / "sentinel")]


def bootstrap_manifest(sources):
    """Return a serializable manifest for independently pinned source bytes."""
    import hashlib
    if set(sources) != set(INFRASTRUCTURE):
        raise ValueError("Exact bootstrap source inventory required")
    return dict(contract="collation-bootstrap-v1", files={
        name + ".py": hashlib.sha256(sources[name]).hexdigest()
        for name in INFRASTRUCTURE})


def verify_completion(completed, output, manifest_sha256, expected_binding,
                      expected_full_binding_sha256, expected_indices):
    """Read-only host verification of a finished child's published artifacts.

    This verifies byte identity and a saved-only contract, not tensor semantics,
    runtime authorization, Linux enforcement or scientific admission.
    """
    import hashlib
    import json
    from pathlib import Path
    from same_child_collation_20260920 import PROBE_RECEIPT

    checked_digest(manifest_sha256)
    checked_digest(expected_full_binding_sha256)
    if (not isinstance(expected_binding, dict) or not expected_binding
            or not isinstance(expected_indices, (tuple, list))
            or not expected_indices
            or any(type(i) is not int or i < 0 for i in expected_indices)
            or len(set(expected_indices)) != len(expected_indices)):
        raise ValueError("Explicit original binding and unique saved indices required")
    if type(completed.returncode) is not int or completed.returncode != 0:
        raise ValueError("Child did not complete successfully")
    output = Path(output).absolute()
    if (not output.is_dir() or output.is_symlink()
            or any(p.is_symlink() for p in output.parents)):
        raise ValueError("Unredirected output directory required")
    observed = {}

    def checked_read(path):
        if (path.is_symlink() or any(p.is_symlink() for p in path.parents)
                or not path.is_file() or path.stat().st_nlink != 1):
            raise ValueError("Missing, redirected or hardlinked output")
        raw = path.read_bytes()
        observed[path] = hashlib.sha256(raw).hexdigest()
        return raw

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate receipt key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Nonfinite receipt value: " + value)

    def parse(raw):
        return json.loads(raw, object_pairs_hook=unique_object,
                          parse_constant=invalid_constant)

    def require_flags(document, flags):
        if not isinstance(document, dict):
            raise ValueError("Receipt object required")
        if any(document.get(name) is not value for name, value in flags.items()):
            raise ValueError("Completion flags differ")

    receipt = parse(checked_read(output / "same_child.json"))
    # JSON equality alone permits true == 1. Identity checks below keep gate
    # fields boolean even when two documents have the same malformed value.
    if parse(completed.stdout) != receipt:
        raise ValueError("Stdout and published receipt differ")
    require_flags(receipt, dict(same_child_integration_completed=True,
                               native_execution_verified=False,
                               scientific_validation_complete=False, admission=False))
    if (receipt.get("contract") != "same-child-collation-v1"
            or type(receipt.get("pid")) is not int or receipt["pid"] <= 0
            or receipt.get("manifest_sha256") != manifest_sha256
            or receipt.get("probe") != PROBE_RECEIPT):
        raise ValueError("Same-child receipt identity differs")
    probe = receipt["probe"]
    require_flags(probe, dict(denied_mkdir=True, scratch_write=True, native_imports=False))
    if type(probe.get("denied_opens")) is not int:
        raise ValueError("Probe count must be an integer")
    if (checked_read(output.parent / "sentinel") != b"read-only-sentinel"
            or (output.parent / "sentinel.new").exists()
            or (output.parent / "sentinel.new").is_symlink()
            or checked_read(output / "probe-output") != b"scratch-write-ok"):
        raise ValueError("Host-side probe bytes differ")
    collation_dir = output / "collated"
    collation = parse(checked_read(collation_dir / "collation.json"))
    if receipt.get("collation") != collation:
        raise ValueError("Published collation differs from child receipt")
    require_flags(collation, dict(
        callback_collation_completed=True, native_execution_verified=False,
        scientific_validation_complete=False, new_train_transforms=False,
        model_forward_completed=False, training_launch=False, admission=False))
    if (collation.get("contract") != "relocated_saved_collation_v1"
            or type(collation.get("registry_denominator")) is not int
            or collation["registry_denominator"] != 31
            or collation.get("scratch") != str(collation_dir)
            or collation.get("observed_binding") != expected_binding
            or collation.get("full_binding_sha256") != expected_full_binding_sha256
            or collation.get("original_dataset_indices") != list(expected_indices)
            or any(type(i) is not int for i in collation["original_dataset_indices"])):
        raise ValueError("Original saved binding, indices or denominator differs")
    items, artifacts = collation.get("items"), collation.get("artifacts")
    if (not isinstance(items, list) or not isinstance(artifacts, list)
            or len(items) != len(expected_indices) or len(artifacts) != len(items)
            or any(not isinstance(row, dict) for row in items + artifacts)
            or [row.get("dataset_index") for row in items] != list(expected_indices)
            or any(type(row.get("dataset_index")) is not int for row in items)):
        raise ValueError("Incomplete or duplicate saved item inventory")
    for index, row in zip(expected_indices, artifacts):
        path = collation_dir / ("batch_%d.pth" % index)
        if (row.get("path") != str(path) or type(row.get("bytes")) is not int
                or row["bytes"] <= 0):
            raise ValueError("Batch must be a nonempty file at its exact output path")
        checked_digest(row.get("sha256"))
        raw = checked_read(path)
        if len(raw) != row["bytes"] or observed[path] != row["sha256"]:
            raise ValueError("Published batch size or digest differs")
    # Recheck the finite inventory after all reads; this is not protection
    # against an actively hostile host racing filesystem accesses.
    for path, digest in list(observed.items()):
        checked_read(path)
        if observed[path] != digest:
            raise ValueError("Output changed during host verification")
    return dict(
        contract="host-collation-receipt-v1", child_pid=receipt["pid"],
        receipt_sha256=observed[output / "same_child.json"],
        verified_files=[dict(path=str(path), sha256=digest)
                        for path, digest in observed.items()],
        saved_indices=list(expected_indices), registry_denominator=31,
        host_artifact_verification_completed=True,
        native_execution_verified=False, scientific_validation_complete=False,
        admission=False)
