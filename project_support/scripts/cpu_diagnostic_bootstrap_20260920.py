"""Server-4 CPU preflight and fresh-process imports; not native authorization."""
import argparse
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


SERVER_ADDRESS = "192.168.1.137"
CODE_ROOT = "/data/songcl/Project/Cluster_project/Cluster"
DATA_ROOT = "/home/songcl/data/data"
WORK_ROOT = "/data/songcl/Project/Cluster_project/Cluster_checkpoints"
SCRATCH_ROOT = "/data/songcl/Project/Cluster_project/pipeline/diagnostic_bundles"


def local_addresses():
    """Observe interfaces directly, rather than trusting SSH environment text."""
    result = subprocess.run(
        ["ip", "-j", "address", "show"], capture_output=True, text=True,
        check=True, timeout=10)
    interfaces = json.loads(result.stdout)
    return sorted({
        address["local"] for interface in interfaces
        for address in interface.get("addr_info", [])
        if address.get("family") == "inet"
    })


def inspect_path(value):
    path = Path(value).absolute()
    return dict(
        path=str(path), resolved=str(path.resolve()),
        directory=path.is_dir(), regular_file=path.is_file(),
        symlink=path.is_symlink() or any(p.is_symlink() for p in path.parents))


def observe_runtime():
    if platform.system() != "Linux":
        raise ValueError("Native preflight requires Linux server-4")
    import pwd

    return dict(
        platform=platform.system(), addresses=local_addresses(),
        user=pwd.getpwuid(os.geteuid()).pw_name,
        conda_env=os.environ.get("CONDA_DEFAULT_ENV"),
        conda_prefix=os.environ.get("CONDA_PREFIX"),
        sys_prefix=sys.prefix, executable=sys.executable,
        cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),
        isolated=bool(sys.flags.isolated),
        dont_write_bytecode=sys.dont_write_bytecode,
        paths={path: inspect_path(path) for path in
               (CODE_ROOT, DATA_ROOT, WORK_ROOT, SCRATCH_ROOT, sys.executable, sys.prefix)})


def validate_host_runtime(observation, expected_executable):
    """Shared host/path checks; neither CUDA mode nor launch authorization."""
    if (observation.get("platform") != "Linux"
            or SERVER_ADDRESS not in observation.get("addresses", [])
            or observation.get("user") != "songcl"):
        raise ValueError("Require observed server-4 interface and songcl identity")
    prefix = observation.get("sys_prefix")
    if (not isinstance(prefix, str) or not prefix.startswith("/")
            or prefix.rstrip("/").split("/")[-1] != "project_cluster"
            or observation.get("conda_env") != "project_cluster"
            or observation.get("conda_prefix") != prefix
            or not isinstance(expected_executable, str)
            or not expected_executable.startswith(prefix + "/")
            or observation.get("executable") != expected_executable):
        raise ValueError("Require independently verified project_cluster executable")
    # Lexical checks stay POSIX even when synthetic tests run on Windows.
    from pathlib import PurePosixPath
    for value in (prefix, expected_executable):
        if (str(PurePosixPath(value)) != value or "\\" in value
                or ".." in PurePosixPath(value).parts):
            raise ValueError("Noncanonical runtime path")
    if (observation.get("isolated") is not True
            or observation.get("dont_write_bytecode") is not True):
        raise ValueError("Require fresh isolated CPU process or GPU child with bytecode disabled")
    required = {CODE_ROOT, DATA_ROOT, WORK_ROOT, SCRATCH_ROOT, prefix, expected_executable}
    paths = observation.get("paths", {})
    if set(paths) != required:
        raise ValueError("Runtime path inventory differs")
    for value in required:
        row = paths[value]
        kind = "regular_file" if value == expected_executable else "directory"
        # Executables can legitimately be symlinks inside a verified conda prefix.
        # Until that exact deployment layout is audited, fail closed here too.
        if (row.get("path") != value or row.get("resolved") != value
                or row.get("symlink") is not False or row.get(kind) is not True):
            raise ValueError("Runtime path absent, redirected or unverified: " + value)
    return dict(
        server="server-4", host_runtime_verified=True,
        native_execution_authorized=False)


def validate_runtime(observation, expected_executable):
    """CPU contract stays CUDA-hidden; shared host checks do not relax it."""
    if observation.get("cuda_visible_devices") != "":
        raise ValueError("Require fresh isolated CPU process with CUDA hidden")
    validate_host_runtime(observation, expected_executable)
    return dict(
        server="server-4", runtime_preflight_passed=True,
        native_execution_authorized=False, data_bytes_verified=False,
        gpu_occupancy_verified=False, scratch_write_enforcement_verified=False)


def checked_imports(bundle, manifest_sha256, required_modules, operation):
    """Run inside a caller-provided filesystem boundary in a fresh child only.

    This does NOT supply that boundary or host authorization. No production CLI
    exposes this operation until scratch-only writes have a verified boundary.
    Synthetic tests exercise it with generated modules in an isolated subprocess.
    """
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ValueError("Fresh isolated child with bytecode disabled required")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise ValueError("CPU child must hide CUDA devices before imports")
    if any(name in sys.modules for name in ("torch", "framework", "gorilla")):
        raise ValueError("Native dependencies imported before producer verification")
    from pinned_diagnostic_imports_20260920 import PinnedDiagnosticImports

    with PinnedDiagnosticImports(bundle, manifest_sha256, required_modules) as boundary:
        modules = {name: importlib.import_module(name) for name in required_modules}
        result = operation(modules)
        boundary.verify()
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only CPU runtime preflight only")
    parser.add_argument("--expected-executable", required=True)
    args = parser.parse_args(argv)
    observation = observe_runtime()
    result = validate_runtime(observation, args.expected_executable)
    result["observation"] = observation
    result["remaining_gates"] = [
        "scratch-only filesystem write boundary before producer/native imports",
        "fresh-process native collation integration and pinned source/data bytes",
        "separate location-aware saved replay and actual GPU coordination"]
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
