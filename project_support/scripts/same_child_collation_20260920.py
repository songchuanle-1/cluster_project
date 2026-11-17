"""Same-child CPU probe/import/collation bridge; no public native launch CLI.

The caller must supply the verified Linux filesystem boundary and host checks.
Local tests replace only the probe and use synthetic data/native dependencies.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import sys

from cpu_diagnostic_bootstrap_20260920 import checked_imports
from scratch_cpu_boundary_20260920 import PROBE


REQUIRED = (
    "native_saved_batch_validation_20260920",
    "relocated_saved_collation_20260920",
    "native_frozen_capture_20260916",
)
PROBE_RECEIPT = dict(
    contract="scratch-probe-v1", denied_opens=3, denied_mkdir=True,
    scratch_write=True, native_imports=False)


def filesystem_probe(scratch, sentinel):
    """Execute the existing probe here, not in a separate disposable process."""
    original_argv = sys.argv
    stream = io.StringIO()
    try:
        sys.argv = ["scratch-probe", str(scratch), str(sentinel)]
        with contextlib.redirect_stdout(stream):
            exec(compile(PROBE, "<same-child-scratch-probe>", "exec"), {})
    finally:
        sys.argv = original_argv
    receipt = json.loads(stream.getvalue())
    if receipt != PROBE_RECEIPT:
        raise ValueError("Incomplete same-child scratch probe")
    return receipt


def run_same_child(bundle, manifest_sha256, factory_module, scratch, sentinel):
    """Use a pinned factory's inputs without exposing an unsandboxed CLI.

    factory.build_inputs() must return location/exporter/registry_ids/read_json/
    load_item/native/torch/capture_id/producer_sha256. It must never sample anew.
    A real factory and native dependency provenance remain deployment gates.
    """
    if (not sys.flags.isolated or not sys.dont_write_bytecode
            or os.environ.get("CUDA_VISIBLE_DEVICES") != ""):
        raise ValueError("Require isolated CPU child with bytecode disabled")
    if (not isinstance(factory_module, str) or not factory_module.isidentifier()
            or factory_module in REQUIRED):
        raise ValueError("Require distinct pinned factory module")
    scratch, sentinel = Path(scratch).absolute(), Path(sentinel).absolute()
    if (not scratch.is_dir() or scratch.is_symlink()
            or any(p.is_symlink() for p in scratch.parents)
            or sentinel.parent != scratch.parent or not sentinel.is_file()
            or sentinel.is_symlink()):
        raise ValueError("Require existing scratch and adjacent sentinel")
    output = scratch / "collated"
    receipt_path = scratch / "same_child.json"
    if any(p.exists() or p.is_symlink() for p in (output, receipt_path)):
        raise FileExistsError("Fresh same-child output required")
    probe = filesystem_probe(scratch, sentinel)
    # Reject incomplete mocked receipts too; only the actual probe can establish
    # enforcement on the authorized host. This is not a host authorization token.
    if probe != PROBE_RECEIPT:
        raise ValueError("Incomplete same-child scratch probe")

    def operation(modules):
        inputs = modules[factory_module].build_inputs()
        required_inputs = {
            "location", "exporter", "registry_ids", "read_json", "load_item",
            "native", "torch", "capture_id", "producer_sha256"}
        if not isinstance(inputs, dict) or set(inputs) != required_inputs:
            raise ValueError("Pinned factory input contract differs")
        callbacks = modules[REQUIRED[0]].native_callbacks(
            inputs["native"], inputs["torch"], inputs["capture_id"],
            inputs["producer_sha256"])
        return modules[REQUIRED[1]].run_collation(
            inputs["location"], inputs["exporter"], inputs["registry_ids"],
            inputs["read_json"], inputs["load_item"], output=output, **callbacks)

    try:
        result = checked_imports(
            bundle, manifest_sha256, (*REQUIRED, factory_module), operation)
        if (result.get("callback_collation_completed") is not True
                or result.get("registry_denominator") != 31
                or result.get("native_execution_verified") is not False
                or result.get("scientific_validation_complete") is not False):
            raise ValueError("Collation completion contract differs")
        receipt = dict(
            contract="same-child-collation-v1", pid=os.getpid(),
            probe=probe, collation=result, same_child_integration_completed=True,
            manifest_sha256=manifest_sha256, native_execution_verified=False,
            scientific_validation_complete=False, admission=False)
        with receipt_path.open("x", encoding="ascii") as stream:
            json.dump(receipt, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        return receipt
    except BaseException:
        # Both paths were absent at entry and are owned by this invocation.
        # Keep batch bytes for diagnosis but never retain a success marker.
        (output / "collation.json").unlink(missing_ok=True)
        receipt_path.unlink(missing_ok=True)
        raise
