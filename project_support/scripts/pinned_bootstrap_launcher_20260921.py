"""Pinned bootstrap/launcher preparation, not a native execution permit.

The launcher source is passed inline to an isolated interpreter and must match
an independently supplied SHA256. Source files inside the bundle are hashed
before launch and again by the child before they are imported. The child runs a
pinned driver entrypoint with a constructed PreIdentityHandoff instance and
publishes one immutable JSON artifact for parent-side verification.

This is a trusted-code provenance boundary. It is not a sandbox, dependency/ABI
provenance proof, GPU reservation, or authorization for model/native work.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath

from bounded_collation_process_20260921 import bounded_process


CONTRACT = "pinned-bootstrap-launcher-v1"
RESULT_CONTRACT = "pinned-handoff-child-result-v1"
LAUNCHER_NAME = "pinned_bootstrap_launcher_runtime_20260921.py"
HANDOFF_MODULE = "preidentity_handoff_20260921"
HANDOFF_CLASS = "PreIdentityHandoff"
POSITIVE_FALSE_CLAIMS = frozenset({
    "admission", "training_launch", "native_execution_authorized",
    "native_execution_verified", "scientific_validation_complete",
    "native_backward_verified", "resources_verified",
})


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_digest(value):
    if (not isinstance(value, str) or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)):
        raise ValueError("Expected lowercase SHA256")
    return value


def _regular_bytes(path, *, allow_hardlink=False):
    path = Path(path)
    if (not path.is_absolute() or path.is_symlink()
            or any(parent.is_symlink() for parent in path.parents)
            or not path.is_file()
            or (not allow_hardlink and path.stat().st_nlink != 1)):
        raise ValueError("Canonical regular non-hardlinked file required")
    return path.read_bytes()


def _checked_file(path, expected, *, allow_hardlink=False):
    checked_digest(expected)
    raw = _regular_bytes(path, allow_hardlink=allow_hardlink)
    if digest(raw) != expected:
        raise ValueError("Pinned file hash differs")
    return raw


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

    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def _manifest_name(name):
    if not isinstance(name, str) or "\\" in name or ":" in name:
        raise ValueError("Canonical flat bundle name required")
    relative = PurePosixPath(name)
    if (relative.is_absolute() or str(relative) != name
            or len(relative.parts) != 1 or name in ("", ".", "..")):
        raise ValueError("Canonical flat bundle name required")
    return relative.name


def build_launcher_manifest(sources, required_modules):
    """Hash exact source/data bytes into a serializable launch manifest."""
    if not isinstance(sources, dict) or not sources:
        raise ValueError("Nonempty source mapping required")
    if (not isinstance(required_modules, (tuple, list))
            or not required_modules
            or any(not isinstance(name, str) or not name.isidentifier()
                   for name in required_modules)
            or len(set(required_modules)) != len(required_modules)):
        raise ValueError("Unique module inventory required")
    rows = []
    modules = set()
    for name, source in sorted(sources.items()):
        name = _manifest_name(name)
        raw = _regular_bytes(source)
        if name.endswith(".py"):
            module = Path(name).stem
            if not module.isidentifier() or module == "__init__":
                raise ValueError("Invalid flat producer module")
            modules.add(module)
        rows.append(dict(path=name, sha256=digest(raw)))
    required = sorted(required_modules)
    if not set(required).issubset(modules):
        raise ValueError("Required producer module absent")
    return dict(contract=CONTRACT, modules=required, files=rows)


def produce_launcher_bundle(bundle, sources, required_modules):
    """Copy exact sources into a fresh bundle and write its manifest."""
    bundle = Path(bundle).absolute()
    if (not bundle.is_dir() or bundle.is_symlink()
            or any(parent.is_symlink() for parent in bundle.parents)
            or any(bundle.iterdir())):
        raise ValueError("Fresh unredirected empty bundle directory required")
    if LAUNCHER_NAME in sources:
        raise ValueError("Launcher runtime is supplied by the producer")
    copied = {}
    for source_name, source in sorted(sources.items()):
        source_name = _manifest_name(source_name)
        copied[source_name] = _regular_bytes(source)
    for name, raw in sorted(copied.items()):
        destination = bundle / name
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                             0o600)
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            try:
                destination.unlink()
            except FileNotFoundError:
                pass
            raise
    runtime = CHILD.encode("ascii")
    descriptor = os.open(bundle / LAUNCHER_NAME,
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb", closefd=True) as stream:
        stream.write(runtime)
        stream.flush()
        os.fsync(stream.fileno())
    manifest = build_launcher_manifest(
        {name: bundle / name for name in copied}, required_modules)
    # The runtime is data from PinnedDiagnosticImports' point of view: it is
    # executed as __main__, never imported as a producer module.
    manifest["files"].append(dict(path=LAUNCHER_NAME, sha256=digest(runtime)))
    manifest["files"].sort(key=lambda row: row["path"])
    raw = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode("ascii")
    descriptor = os.open(bundle / "manifest.json",
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb", closefd=True) as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return digest(raw)


def verify_launcher_bundle(bundle, manifest_sha256):
    """Verify the exact manifest inventory and every referenced file."""
    checked_digest(manifest_sha256)
    bundle = Path(bundle).absolute()
    raw = _checked_file(bundle / "manifest.json", manifest_sha256)
    manifest = _strict_json(raw)
    if (not isinstance(manifest, dict)
            or set(manifest) != {"contract", "modules", "files"}
            or manifest["contract"] != CONTRACT
            or not isinstance(manifest["modules"], list)
            or not manifest["modules"]
            or any(not isinstance(name, str) or not name.isidentifier()
                   for name in manifest["modules"])
            or len(set(manifest["modules"])) != len(manifest["modules"])
            or not isinstance(manifest["files"], list)
            or not manifest["files"]):
        raise ValueError("Invalid launcher manifest schema")
    seen = set()
    modules = set()
    for row in manifest["files"]:
        if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
            raise ValueError("Invalid launcher manifest row")
        name = _manifest_name(row["path"])
        if name in seen:
            raise ValueError("Duplicate launcher manifest row")
        seen.add(name)
        expected = checked_digest(row["sha256"])
        _checked_file(bundle / name, expected)
        if name.endswith(".py"):
            module = Path(name).stem
            if not module.isidentifier() or module == "__init__":
                raise ValueError("Invalid flat producer module")
            modules.add(module)
    if not set(manifest["modules"]).issubset(modules):
        raise ValueError("Required producer module absent")
    if HANDOFF_MODULE not in modules:
        raise ValueError("Pre-identity handoff module absent")
    runtime_rows = [row for row in manifest["files"]
                    if row["path"] == LAUNCHER_NAME]
    if len(runtime_rows) != 1 or runtime_rows[0]["sha256"] != LAUNCHER_SHA256:
        raise ValueError("Launcher runtime row differs")
    return manifest


def _manifest_row(bundle, manifest, path, expected_sha256):
    bundle = Path(bundle).absolute()
    path = Path(path).absolute()
    if path.parent != bundle or path.name not in {row["path"] for row in manifest["files"]}:
        raise ValueError("Path must name a bundled manifest file")
    row = next(row for row in manifest["files"] if row["path"] == path.name)
    if row["sha256"] != checked_digest(expected_sha256):
        raise ValueError("Handoff pin hash differs from manifest")
    _checked_file(path, expected_sha256)
    return row["sha256"]


def _checked_output(output):
    output = Path(output).absolute()
    if (not output.is_dir() or output.is_symlink()
            or any(parent.is_symlink() for parent in output.parents)):
        raise ValueError("Fresh unredirected output directory required")
    result = output / "result.json"
    if result.exists() or result.is_symlink():
        raise ValueError("Fresh result artifact path required")
    return output


# The parent passes these exact bytes as argv to an isolated interpreter. The
# independently supplied launcher hash prevents a changed source string from
# reaching the child command.
CHILD = r'''
import hashlib, importlib.util, json, os, pathlib, sys
bundle, manifest_sha, handoff_path, handoff_sha, driver_module, driver_entry, context_path, context_sha, output = sys.argv[1:]
bundle, handoff_path, context_path, output = map(pathlib.Path, (bundle, handoff_path, context_path, output))

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path):
    if (not path.is_absolute() or path.is_symlink()
            or any(parent.is_symlink() for parent in path.parents)
            or not path.is_file() or path.stat().st_nlink != 1):
        raise ValueError("Canonical regular non-hardlinked file required")
    return path.read_bytes()

def strict_json(raw):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("Nonfinite JSON value: " + value)
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)

if not sys.flags.isolated or not sys.dont_write_bytecode or not sys.flags.no_site:
    raise ValueError("Isolated bytecode-disabled no-site child required")
if pathlib.Path(sys.modules["__main__"].__file__).absolute() != bundle / "pinned_bootstrap_launcher_runtime_20260921.py":
    raise ValueError("Launcher must run as the pinned __main__ file")
manifest_raw = read(bundle / "manifest.json")
if digest(manifest_raw) != manifest_sha:
    raise ValueError("Launcher manifest hash differs")
manifest = strict_json(manifest_raw)
if (not isinstance(manifest, dict)
        or set(manifest) != {"contract", "modules", "files"}
        or manifest["contract"] != "pinned-bootstrap-launcher-v1"
        or not isinstance(manifest["modules"], list)
        or not manifest["modules"]
        or not isinstance(manifest["files"], list)
        or not manifest["files"]):
    raise ValueError("Invalid launcher manifest schema")
files = {}
modules = set()
for row in manifest["files"]:
    if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
        raise ValueError("Invalid launcher manifest row")
    name, expected = row["path"], row["sha256"]
    relative = pathlib.PurePosixPath(name)
    if ("\\" in name or ":" in name or relative.is_absolute()
            or str(relative) != name or len(relative.parts) != 1
            or name in files):
        raise ValueError("Canonical unique flat bundle name required")
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("Expected lowercase SHA256")
    files[name] = expected
    if name.endswith(".py"):
        module = pathlib.Path(name).stem
        if not module.isidentifier() or module == "__init__":
            raise ValueError("Invalid flat producer module")
        modules.add(module)
requested = driver_module + "," + ",".join(manifest["modules"])
if sorted(set(requested.split(","))) != sorted(manifest["modules"]):
    raise ValueError("Driver module must belong to exact required inventory")
if "preidentity_handoff_20260921" not in modules:
    raise ValueError("Pre-identity handoff module absent")

def verify():
    if read(bundle / "manifest.json") != manifest_raw:
        raise ValueError("Launcher manifest changed")
    for name, expected in files.items():
        if digest(read(bundle / name)) != expected:
            raise ValueError("Pinned bundle file changed: " + name)

verify()
if digest(read(context_path)) != context_sha:
    raise ValueError("Driver context hash differs")
if digest(read(handoff_path)) != handoff_sha:
    raise ValueError("Handoff file hash differs")
if handoff_path.parent != bundle or handoff_path.name not in files:
    raise ValueError("Handoff must be a bundled manifest file")
handoff_document = strict_json(read(handoff_path))
if (not isinstance(handoff_document, dict)
        or not isinstance(handoff_document.get("bootstrap"), list)):
    raise ValueError("Invalid pre-identity handoff")
main_rows = [row for row in handoff_document["bootstrap"]
             if isinstance(row, dict) and row.get("name") == "__main__"]
if (len(main_rows) != 1
        or main_rows[0].get("path") != str(bundle / "pinned_bootstrap_launcher_runtime_20260921.py")
        or main_rows[0].get("sha256") != files["pinned_bootstrap_launcher_runtime_20260921.py"]):
    raise ValueError("Pinned launcher bootstrap row required")

pinned_name = "pinned_diagnostic_imports_20260920"
pinned_path = bundle / (pinned_name + ".py")
pinned_raw = read(pinned_path)
if digest(pinned_raw) != files[pinned_name + ".py"]:
    raise ValueError("Pinned import bootstrap hash differs")
spec = importlib.util.spec_from_file_location(pinned_name, pinned_path)
pinned_module = importlib.util.module_from_spec(spec)
sys.modules[pinned_name] = pinned_module
exec(compile(pinned_raw, str(pinned_path), "exec"), pinned_module.__dict__)
PinnedDiagnosticImports = pinned_module.PinnedDiagnosticImports
del sys.modules[pinned_name]

context = strict_json(read(context_path))
with PinnedDiagnosticImports(bundle, manifest_sha, tuple(manifest["modules"])):
    handoff_module = __import__("preidentity_handoff_20260921")
    boundary = handoff_module.PreIdentityHandoff(handoff_path, handoff_sha)
    driver = __import__(driver_module)
    entry = getattr(driver, driver_entry)
    if not callable(entry):
        raise ValueError("Driver entrypoint must be callable")
    driver_result = entry(boundary, context)
    if not isinstance(driver_result, dict):
        raise ValueError("Driver result must be an object")
    document = {
        "contract": "pinned-handoff-child-result-v1",
        "manifest_sha256": manifest_sha,
        "handoff_sha256": handoff_sha,
        "driver_module": driver_module,
        "driver_entry": driver_entry,
        "context_sha256": context_sha,
        "driver_result": driver_result,
    }
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode("ascii")
    result_path = output / "result.json"
    descriptor = os.open(result_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb", closefd=True) as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
verify()
print(digest(raw))
'''
LAUNCHER_SHA256 = digest(CHILD.encode("ascii"))


def launcher_command(executable, executable_sha256, bundle, manifest_sha256,
                     handoff_path, handoff_sha256, driver_module, driver_entry,
                     context_path, context_sha256, output,
                     expected_launcher_sha256=LAUNCHER_SHA256):
    """Build the exact isolated child command after verifying every pin."""
    if expected_launcher_sha256 != LAUNCHER_SHA256:
        raise ValueError("Launcher source hash differs")
    checked_digest(executable_sha256)
    _checked_file(executable, executable_sha256, allow_hardlink=True)
    bundle = Path(bundle).absolute()
    manifest = verify_launcher_bundle(bundle, manifest_sha256)
    if (not isinstance(driver_module, str) or not driver_module.isidentifier()
            or driver_module not in manifest["modules"]
            or not isinstance(driver_entry, str) or not driver_entry.isidentifier()):
        raise ValueError("Pinned driver module/entrypoint required")
    handoff_sha256 = _manifest_row(
        bundle, manifest, handoff_path, handoff_sha256)
    _checked_file(context_path, context_sha256)
    output = _checked_output(output)
    return [
        str(Path(executable).absolute()), "-I", "-B", "-S",
        str(bundle / LAUNCHER_NAME),
        str(bundle), manifest_sha256, str(Path(handoff_path).absolute()),
        handoff_sha256, driver_module, driver_entry,
        str(Path(context_path).absolute()), context_sha256, str(output),
    ]


def _reject_positive_claims(document):
    if isinstance(document, dict):
        for key, value in document.items():
            if key in POSITIVE_FALSE_CLAIMS and value is True:
                raise ValueError("Preparation launcher cannot claim: " + key)
            _reject_positive_claims(value)
    elif isinstance(document, list):
        for value in document:
            _reject_positive_claims(value)


def verify_child_result(output, completed, manifest_sha256, handoff_sha256,
                        driver_module, driver_entry, context_sha256):
    """Verify child output and the one immutable result artifact."""
    output = Path(output).absolute()
    result_path = output / "result.json"
    if type(completed.returncode) is not int or completed.returncode != 0:
        detail = completed.stderr.strip()
        raise ValueError("Launcher child did not complete successfully" +
                         (": " + detail if detail else ""))
    if completed.stderr != "":
        raise ValueError("Launcher child emitted stderr")
    raw = _regular_bytes(result_path)
    observed = digest(raw)
    if completed.stdout not in (observed + "\n", observed + "\r\n"):
        raise ValueError("Child stdout digest differs from artifact")
    document = _strict_json(raw)
    if (not isinstance(document, dict)
            or set(document) != {
                "contract", "manifest_sha256", "handoff_sha256",
                "driver_module", "driver_entry", "context_sha256",
                "driver_result"}
            or document["contract"] != RESULT_CONTRACT
            or document["manifest_sha256"] != manifest_sha256
            or document["handoff_sha256"] != handoff_sha256
            or document["driver_module"] != driver_module
            or document["driver_entry"] != driver_entry
            or document["context_sha256"] != context_sha256
            or not isinstance(document["driver_result"], dict)):
        raise ValueError("Launcher child result contract differs")
    _reject_positive_claims(document)
    if digest(_regular_bytes(result_path)) != observed:
        raise ValueError("Result artifact changed during verification")
    return dict(contract=CONTRACT, result_path=str(result_path),
                result_sha256=observed, launcher_sha256=LAUNCHER_SHA256,
                manifest_sha256=manifest_sha256,
                driver_result=document["driver_result"])


def launch_pinned_handoff(
        executable, executable_sha256, bundle, manifest_sha256,
        handoff_path, handoff_sha256, driver_module, driver_entry,
        context_path, context_sha256, output, *, validate_execution,
        expected_launcher_sha256=LAUNCHER_SHA256,
        timeout=300, max_output_bytes=1024 * 1024):
    """Run the pinned child once with bounded time/output and no retries.

    validate_execution(request) must raise unless the caller has separately
    verified runtime, allocation, dependencies, assets and isolation. Returning
    None is a control-flow contract, not a pass flag or native evidence.
    """
    if not callable(validate_execution):
        raise ValueError("External execution validator required")
    if (type(timeout) not in (int, float) or not math.isfinite(timeout)
            or not 0 < timeout <= 3600
            or type(max_output_bytes) is not int
            or not 0 < max_output_bytes <= 16 * 1024 * 1024):
        raise ValueError("Finite timeout and bounded output budget required")
    request = dict(
        executable=str(Path(executable).absolute()),
        executable_sha256=executable_sha256,
        bundle=str(Path(bundle).absolute()), manifest_sha256=manifest_sha256,
        handoff_path=str(Path(handoff_path).absolute()),
        handoff_sha256=handoff_sha256, driver_module=driver_module,
        driver_entry=driver_entry, context_path=str(Path(context_path).absolute()),
        context_sha256=context_sha256, output=str(Path(output).absolute()),
        timeout=timeout, max_output_bytes=max_output_bytes)
    command = launcher_command(
        executable, executable_sha256, bundle, manifest_sha256,
        handoff_path, handoff_sha256, driver_module, driver_entry,
        context_path, context_sha256, output,
        expected_launcher_sha256=expected_launcher_sha256)
    result = validate_execution(copy.deepcopy(request))
    if result is not None:
        raise ValueError("Execution validator must raise or return None, not a pass flag")
    # Repeat all pins after a potentially slow external validation.
    command = launcher_command(
        executable, executable_sha256, bundle, manifest_sha256,
        handoff_path, handoff_sha256, driver_module, driver_entry,
        context_path, context_sha256, output,
        expected_launcher_sha256=expected_launcher_sha256)
    completed = bounded_process(
        command, str(Path(output).absolute()),
        timeout=timeout, max_output_bytes=max_output_bytes)
    return verify_child_result(
        output, completed, manifest_sha256, handoff_sha256,
        driver_module, driver_entry, context_sha256)
