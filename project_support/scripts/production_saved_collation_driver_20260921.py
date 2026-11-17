"""Pinned production driver for production execution receipt checks.

This module runs inside the isolated launcher child. It constructs the
externally supplied held-slot and execution callbacks, then delegates to the
single-use PreIdentityHandoff. It does not load saved data, authorize CUDA or
perform model work.
"""


def _reject_positive_claims(document):
    from server4_execution_validator_20260921 import _reject_positive_claims

    _reject_positive_claims(document)


def run(boundary, context):
    from server4_execution_validator_20260921 import (
        make_child_checks, validate_driver_context,
    )

    config = validate_driver_context(context)
    slot_check, execution_check = make_child_checks(context)
    if not callable(getattr(boundary, "collect", None)):
        raise ValueError("PreIdentityHandoff collect boundary required")
    result = boundary.collect(
        config["expected_executable"],
        gpu=config["gpu"],
        capacity=config["receipt"]["capacity"],
        required_memory_mib=config["required_memory_mib"],
        slot_check=slot_check,
        execution_check=execution_check,
    )
    if not isinstance(result, dict):
        raise ValueError("Handoff collection result must be an object")
    _reject_positive_claims(result)
    for key in ("native_execution_authorized", "scientific_validation_complete",
                "admission", "training_launch"):
        if result.get(key) is not False:
            raise ValueError("Production driver cannot promote gate: " + key)
    return result
