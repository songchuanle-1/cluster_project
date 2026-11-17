"""Internal prepared-to-completed handoff; no CLI or deployment authorization.

The caller owns the execution validator: it must raise unless current allocation,
runtime, dependencies, assets and Linux enforcement have actually been verified.
Calling a hook is not evidence that those checks were performed. Local tests use
synthetic children; this adapter does not establish scientific or native gates.
"""
import copy
import json
import math

from bounded_collation_process_20260921 import complete_handoff
from pinned_diagnostic_imports_20260920 import checked_digest
from prepare_collation_handoff_20260921 import pinned_file, prepare_handoff


def prepare_and_complete(
        executable, executable_sha256, bwrap, bwrap_sha256,
        infrastructure, infrastructure_sha256, bundle, manifest_sha256,
        expected_binding, expected_full_binding_sha256, expected_indices, *,
        validate_execution, timeout=300, max_output_bytes=1024 * 1024):
    """Connect existing preparation and receipt verification without retries.

    Expectations must come from original capture evidence, never child output.
    validate_execution(phase, request, prepared) must return None or raise;
    phases are before_prepare and before_launch. Copies prevent a validator
    from rewriting the contract. A private failed run remains diagnostic evidence.
    """
    if not callable(validate_execution):
        raise ValueError("External execution validator required")
    if (not isinstance(expected_binding, dict) or not expected_binding
            or not isinstance(expected_indices, (list, tuple))
            or not expected_indices
            or any(type(i) is not int or i < 0 for i in expected_indices)
            or len(set(expected_indices)) != len(expected_indices)):
        raise ValueError("Independent original binding and unique saved indices required")
    for digest in (executable_sha256, bwrap_sha256, infrastructure_sha256,
                   manifest_sha256, expected_full_binding_sha256):
        checked_digest(digest)
    if (type(timeout) not in (int, float) or not math.isfinite(timeout)
            or not 0 < timeout <= 3600
            or type(max_output_bytes) is not int
            or not 0 < max_output_bytes <= 16 * 1024 * 1024):
        raise ValueError("Finite timeout and bounded output budget required")
    binding = copy.deepcopy(expected_binding)
    json.dumps(binding, allow_nan=False)
    indices = list(expected_indices)
    request = dict(
        executable=executable, executable_sha256=executable_sha256,
        bwrap=bwrap, bwrap_sha256=bwrap_sha256,
        infrastructure=infrastructure, infrastructure_sha256=infrastructure_sha256,
        bundle=bundle, manifest_sha256=manifest_sha256,
        expected_binding=binding,
        expected_full_binding_sha256=expected_full_binding_sha256,
        expected_indices=indices, timeout=timeout, max_output_bytes=max_output_bytes)

    def validate(phase, prepared):
        result = validate_execution(phase, copy.deepcopy(request), copy.deepcopy(prepared))
        if result is not None:
            raise ValueError("Execution validator must raise or return None, not a pass flag")

    validate("before_prepare", None)
    prepared = prepare_handoff(
        executable, executable_sha256, bwrap, bwrap_sha256,
        infrastructure, infrastructure_sha256, bundle, manifest_sha256)
    validate("before_launch", prepared)
    # Check the original pins again after potentially slow external validation.
    for row in prepared["pinned_host_inputs"]:
        pinned_file(row["path"], row["sha256"])
    return complete_handoff(
        prepared["command"], prepared["run"], manifest_sha256, binding,
        expected_full_binding_sha256, indices,
        timeout=timeout, max_output_bytes=max_output_bytes)
