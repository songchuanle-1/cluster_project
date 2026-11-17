"""Internal saved-input driver; trusted native callbacks are not authorization."""
import copy
from pathlib import Path

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from native_registry_geometry_runner_20260920 import dump_new, require_expected
from referent_geometry_registry_20260919 import evaluate
from relocated_saved_replay_20260921 import prepare_relocated_replay
from saved_geometry_replay_20260920 import replay_forward
from saved_physical_location_20260920 import check_server4_capacity
from scratch_collation_launch_20260920 import verify_completion


CONTRACT = "relocated-saved-geometry-v1"


def run_relocated(
        location, exporter, registry, registry_ids, read_json, load_item, load_batch,
        *, completed, collation_output, manifest_sha256, expected_binding,
        expected_full_binding_sha256, expected_indices, gpu, observe_capacity,
        clock, required_memory_mib, coordinated_slot, execution_check,
        source_check, model_factory, forward_context, output):
    """No CLI, sampling, sync, reservation, checkpoint recovery or admission.

    execution_check must verify actual authorized runtime/dependencies before
    loading. The caller holds coordination through model teardown and owns the
    forward context. Capacity observations alone cannot grant a reservation.
    """
    output = Path(output).absolute()
    collation_output = Path(collation_output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if (output.resolve().is_relative_to(collation_output.resolve())
            or collation_output.resolve().is_relative_to(output.resolve())):
        raise ValueError("Capture output must be separate from saved collation")
    if type(gpu) is not int or gpu not in (0, 1) or coordinated_slot is not True:
        raise ValueError("Coordinated server-4 GPU0/1 required")
    expected = copy.deepcopy(expected_binding)
    indices = copy.deepcopy(expected_indices)
    completed = copy.deepcopy(completed)
    registry = copy.deepcopy(registry)
    registry_ids = list(registry_ids)
    registry_digest = fingerprint(registry)
    source = {k: v for k, v in expected.items()
              if k not in ("dataset_source_sha256", "registry_sha256")}
    execution_check("server-4", gpu)
    require_expected(expected, source_check())
    prepared, joins = prepare_relocated_replay(
        location, exporter, registry_ids, read_json, load_item, load_batch,
        completed=completed, output=collation_output, manifest_sha256=manifest_sha256,
        expected_binding=expected,
        expected_full_binding_sha256=expected_full_binding_sha256,
        expected_indices=indices)
    original_contract = copy.deepcopy(location.contract)

    def recheck():
        require_expected(expected, source_check())
        location.verify()
        if (location.contract != original_contract
                or exporter.source_binding != source
                or exporter.manifest() != joins
                or fingerprint(joins) != expected_full_binding_sha256
                or fingerprint(registry) != registry_digest
                or [p["dataset_index"] for p, _ in prepared] != indices
                or any(fingerprint(p) != d for p, d in prepared)):
            raise ValueError("Saved capture inputs or provenance changed")
        verify_completion(
            completed, collation_output, manifest_sha256, expected,
            expected_full_binding_sha256, indices)

    recheck()
    execution_check("server-4", gpu)
    capacity = check_server4_capacity(
        "server-4", gpu, observe_capacity(gpu), clock(), required_memory_mib,
        coordinated_slot)
    output.mkdir(parents=True, exist_ok=False)
    try:
        model = model_factory()

        def sink(step, index, record):
            dump_new(output / ("geometry_%03d.json" % step), record)

        with forward_context():
            records = replay_forward(model, prepared, source, sink)
        if len(records) != len(indices):
            raise ValueError("Incomplete saved capture")
        result = evaluate(registry, expected["registry_sha256"], records, source, joins)
        recheck()
        dump_new(output / "bindings.json", joins)
        dump_new(output / "evaluation.json", result)
        names = ["bindings.json", "evaluation.json"] + [
            "geometry_%03d.json" % i for i in range(len(records))]
        report = dict(
            contract=CONTRACT, expected_binding=expected, capacity=capacity,
            original_dataset_indices=indices, completed_items=len(records),
            saved_payload_sha256=[digest for _, digest in prepared],
            full_binding_sha256=expected_full_binding_sha256,
            registry_denominators=result["overall"],
            saved_capture_completed=True, native_execution_verified=False,
            scientific_validation_complete=False, admission=False,
            training_launch=False, new_train_transforms=False,
            artifacts=[dict(path=n, sha256=file_sha256(output / n)) for n in names])
        dump_new(output / "capture.json", report)
        return report
    except Exception as exc:
        dump_new(output / "failure.json", dict(
            contract=CONTRACT, error_type=type(exc).__name__, message=str(exc),
            saved_capture_completed=False, native_execution_verified=False,
            scientific_validation_complete=False, admission=False))
        raise
