"""Execute focused static tests and persist this event's shared evidence."""
import io
import json
import unittest
from datetime import datetime
from pathlib import Path

from frozen_capture_contract_20260916 import file_sha256
from referent_native_chain_selftest_20260919 import run_selftest


ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/geometry_capture_contract_20260919-2014.json"
MODULES = (
    "test_referent_geometry_capture_20260919",
    "test_referent_geometry_control_20260919",
    "test_referent_native_expression_producer_20260919",
    "test_referent_object_rank_capture_20260919",
    "test_referent_target_rank_evaluator_20260919",
    "test_native_endpoint_capture_20260916",
    "test_frozen_capture_contract_20260916",
)


def main():
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text("utf-8"))
    if context["generated_at"] != "2026-09-19T12:07:10.718987+00:00":
        raise ValueError("Persistence belongs only to the 20:07 event")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(MODULES))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Static test suite failed")
    chain = run_selftest()
    chain_path = "pipeline/reports/referent_native_chain_selftest_20260919-2014.json"
    (ROOT / chain_path).write_text(json.dumps(chain, indent=2) + "\n", encoding="utf-8")
    now = datetime.now().astimezone().isoformat()
    retry = "2026-09-19T21:07:00+08:00"
    blocker = (
        "Read-only GPU7 observation at 20:08 Asia/Shanghai: M197 PID1134192 "
        "19956MiB and foreign PID3827570 42488MiB, free18597MiB; two-process "
        "capacity reached. Independent objectness unresolved. Versioned geometry "
        "runtime hook/native validation still incomplete, executable CPU work remains."
    )
    next_action = (
        "Implement and statically test a separately versioned runtime geometry hook "
        "and complete producer-source manifest without modifying frozen seven-file "
        "producer. Capture exact criterion input4/7/8/9 and pred.sample_inds, join "
        "EndpointDataset physical labels and native input identity, exercise hook "
        "cleanup and tensor layout with synthetic adapters. Then on authorized "
        "GPU7 with fewer than two processes and measured sufficient memory run "
        "bounded native capture, verify step evidence and quantify missing/tied/near-"
        "tied contrasts and query-selection sensitivity. Recheck capacity after "
        + retry + ". Geometry does not resolve independent objectness; retain "
        "coverage, failure-selection, scene uncertainty and candidate admission gates."
    )
    sources = [
        "scripts/referent_geometry_capture_20260919.py",
        "scripts/test_referent_geometry_capture_20260919.py",
        "scripts/persist_geometry_capture_20260919.py",
        "scripts/referent_geometry_control_20260919.py",
        "scripts/native_endpoint_capture_20260916.py",
        "scripts/capture_support_20260916.py",
        "scripts/frozen_capture_contract_20260916.py",
        "pipeline/reports/geometry_capture_contract_20260919-2014.md",
        "pipeline/decisions/20260919-201509_other.md",
        chain_path,
    ]
    evidence = [dict(path=path, sha256=file_sha256(ROOT / path)) for path in sources]
    due = set(context["research_work"]["due_ids"])
    report = dict(
        schema_version=1, generated_at=now, scope="Shared CPU contract implementation",
        contract="criterion_geometry_nuisance_v1",
        validation=dict(tests_run=result.testsRun, failures=len(result.failures),
                        errors=len(result.errors), modules=list(MODULES),
                        synthetic_chain_checks=len(chain["checks"]),
                        output=stream.getvalue()),
        new_test_count=20,
        evidence=evidence, resumed_due_ids=sorted(due),
        gpu_observation=dict(server="server-6", gpu=7, process_count=2,
                             total_mib=81559, used_mib=62483, free_mib=18597,
                             utilization_percent=64,
                             processes=[dict(pid=1134192, memory_mib=19956, role="M197"),
                                        dict(pid=3827570, memory_mib=42488, role="foreign")]),
        training_progress=dict(
            verified_pid=1134192, epoch=24, last_observed_step=1062,
            total_steps=4686, best_miou_preflight=.4924,
            previous_tick="Val[23/50]217..233/363",
            observation="Exact PID/config and fd1 verified; Train[24/50]1047..1062/4686"),
        blocker=blocker, retry_after=retry, next_action=next_action,
        native_execution_completed=False, scientific_validation_complete=False,
        independent_objectness_resolved=False, native_producer_modified=False,
        queue_changed=False,
        limitations=[
            "No runtime hook or actual native tensor observation executed.",
            "Hashes bind artifacts; they do not prove truthful native observations.",
            "Physical sentinel199 mapping requires captured EndpointDataset binding.",
            "Geometry remains annotation-assisted and conditional on selected seeds.",
            "Near-tie flag is numerical diagnostic only; native frequencies unknown.",
            "Shared progress is not seven candidate-specific validations.",
        ],
    )
    (ROOT / REPORT).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work_path = ROOT / "pipeline/research_work.json"
    work = json.loads(work_path.read_text("utf-8"))
    if due - {candidate["id"] for candidate in work["candidates"]}:
        raise ValueError("Due candidate missing")
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        by_path = {item["path"]: item for item in candidate["evidence"]}
        for item in evidence + [entry]:
            by_path[item["path"]] = item
        candidate.update(
            evidence=list(by_path.values()), blocker=blocker, retry_after=retry,
            unblock_condition="GPU7 below two processes and enough measured memory; "
            "native geometry requires versioned runtime adapter; independent "
            "objectness and candidate-specific scientific gates still unresolved.",
            next_action=next_action,
            latest_progress=now + ": versioned geometry criterion adapter and "
            "physical sentinel binding implemented; " + str(result.testsRun)
            + " static tests and6 synthetic checks pass; no native execution.",
            geometry_capture_progress=dict(
                timestamp=now, report=REPORT, report_sha256=entry["sha256"],
                tests_passed=result.testsRun, native_execution_completed=False,
                scientific_validation_complete=False,
                alternatives_attempted="Implemented separate CPU adapter with "
                "physical binding, source hashes, coordinate slicing, index composition "
                "and missing/tie evaluation while GPU capped; verified training steps."),
        )
    work_path.write_text(json.dumps(work, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(report=entry, tests_passed=result.testsRun,
                          synthetic_checks=len(chain["checks"]), resumed=sorted(due)), indent=2))


if __name__ == "__main__":
    main()
