"""Prepare the existing saved-only handoff; never execute native producers.

This is internal host orchestration, not an admission or dependency attestation.
The caller must still validate external assets/dependencies before execution.
"""
import hashlib
import os
from pathlib import Path
import platform
import stat
import uuid

from cpu_diagnostic_bootstrap_20260920 import (
    SCRATCH_ROOT, observe_runtime, validate_runtime)
from pinned_diagnostic_imports_20260920 import checked_digest
from scratch_collation_launch_20260920 import collation_command
from scratch_cpu_boundary_20260920 import canonical, checked_path


def pinned_file(path, digest):
    checked_digest(digest)
    path = checked_path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("Pinned host input digest differs: " + str(path))
    return path


def private_directory(path):
    path.mkdir(mode=0o700)
    if os.name == "posix" and (
            stat.S_IMODE(path.stat().st_mode) != 0o700
            or path.stat().st_uid != os.geteuid()):
        raise ValueError("Private owned scratch directory required")


def prepare_handoff(executable, executable_sha256, bwrap, bwrap_sha256,
                    infrastructure, infrastructure_sha256, bundle, manifest_sha256):
    """Validate host inputs and provision one fresh run without launching it.

    Failures retain any newly owned scratch as diagnostic evidence. Never clean
    another run or retry outside the sandbox. Digests must be independently
    obtained, not manufactured from destination files by a production caller.
    """
    if platform.system() != "Linux":
        raise ValueError("Handoff preparation requires Linux server-4")
    validate_runtime(observe_runtime(), executable)
    for value in (executable, bwrap, infrastructure, bundle):
        canonical(value)
    root = checked_path(SCRATCH_ROOT, directory=True)
    infrastructure_path = checked_path(infrastructure, directory=True)
    bundle_path = checked_path(bundle, directory=True)
    pins = (
        (executable, executable_sha256),
        (bwrap, bwrap_sha256),
        (infrastructure_path / "bootstrap.json", infrastructure_sha256),
        (bundle_path / "manifest.json", manifest_sha256),
    )
    for path, digest in pins:
        pinned_file(path, digest)
    run = root / ("cpu-probe-" + uuid.uuid4().hex)
    command = collation_command(
        executable, bwrap, str(run), infrastructure, infrastructure_sha256,
        bundle, manifest_sha256)
    private_directory(run)
    output = run / "output"
    private_directory(output)
    for name in ("tmp", "home", "cache"):
        private_directory(output / name)
    with (run / "sentinel").open("xb") as stream:
        stream.write(b"read-only-sentinel")
    # Provisioning must not silently change checked executables or input manifests.
    for path, digest in pins:
        pinned_file(path, digest)
    return dict(
        contract="prepared-collation-handoff-v1",
        run=str(run), command=command,
        infrastructure_sha256=infrastructure_sha256, manifest_sha256=manifest_sha256,
        pinned_host_inputs=[dict(path=str(path), sha256=digest) for path, digest in pins],
        host_preparation_completed=True,
        external_dependency_attestation=False, scratch_write_enforcement_verified=False,
        native_execution_verified=False, scientific_validation_complete=False,
        execution_authorized=False, admission=False,
        next_action="Verify external dependency/asset closure and Linux enforcement; "
                    "then connect this exact command/run to complete_handoff with "
                    "the independent original binding/full31 digest/saved indices.")
