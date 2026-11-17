"""Persist the executed 22:07 event checks without advancing scientific gates."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256
from referent_geometry_registry_20260919 import evaluate
from persist_geometry_runtime_20260919 import MODULES


ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/geometry_registry_20260919-2215.json"
REGISTRY = "pipeline/reports/referent_control_pairing_20260918-1812.json"
DECISION = "pipeline/decisions/20260919-221211_other.md"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write(path, value):
    (ROOT / path).write_text(
        json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="ascii")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if context["generated_at"] != "2026-09-19T14:07:10.414261+00:00":
        raise ValueError("Wrong event snapshot")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    output = io.StringIO()
    modules = ("test_referent_geometry_registry_20260919",
               "test_geometry_torch_static_20260919") + MODULES
    result = unittest.TextTestRunner(stream=output).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    if not result.wasSuccessful():
        raise ValueError(output.getvalue())
    previous = read("pipeline/reports/geometry_runtime_20260919-2118.json")
    for source in previous["producer_manifest"]["sources"]:
        if file_sha256(ROOT / "scripts" / source["path"]) != source["sha256"]:
            raise ValueError("Existing producer source changed")
    # No captured rows or verified native bindings exist in this event.
    registry_hash = file_sha256(ROOT / REGISTRY)
    missing = evaluate(read(REGISTRY), registry_hash, [], None,
                       dict(registry_sha256=registry_hash, bindings=[]))
    if missing["overall"]["requested"] != 31 or len(missing["per_scene"]) != 17:
        raise ValueError("Fixed registry denominator changed")
    missing["source_binding_available"] = False
    missing["source_binding_note"] = "Unavailable; no native inputs evaluated."
    coverage_path = "pipeline/reports/geometry_registry_missing_20260919-2215.json"
    write(coverage_path, missing)
    now = datetime.now().astimezone()
    retry = "2026-09-19T23:07:00+08:00"
    next_action = (
        "Continue the same diagnostic: implement an explicit fixed-registry to "
        "native-dataset binding exporter (including target/object identity, "
        "dataset index, scene occurrence, transformed input and physical support), "
        "with collision/missing checks and synthetic static tests. Do not infer "
        "identity from scene/ann alone or equate smoke capture with31-pair coverage. "
        "The two synthetic Torch-module tests are unexecuted because local Torch "
        "is absent; retain as pending, do not install/run native model locally. "
        "After " + retry + " recheck authorized server-6 GPU7 capacity. With fewer "
        "than two processes and sufficient measured memory, verify remote source/"
        "model/config/checkpoint binding and run the separate bounded diagnostic "
        "through the authorized coordinated path, recording increasing native "
        "outputs and dtype/layout. GPU availability does not resolve independent "
        "objectness, fixed-registry coverage or candidate-specific admission gates."
    )
    blocker = (
        "22:11 GPU7 observation still has M1971134192 at19956MiB and foreign"
        "3827570 at42488MiB, free18597MiB; two-process cap prevents native execution. "
        "No verified registry/native bindings; independent objectness unresolved. "
        "Local Torch unavailable, so two synthetic Torch checks remain skipped."
    )
    paths = [
        "scripts/referent_geometry_registry_20260919.py",
        "scripts/test_referent_geometry_registry_20260919.py",
        "scripts/test_geometry_torch_static_20260919.py",
        "scripts/persist_geometry_registry_20260919.py",
        REGISTRY, DECISION, coverage_path,
    ]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    due = context["research_work"]["due_ids"]
    report = dict(
        schema_version=1, generated_at=now.isoformat(), scope="Shared static diagnostic",
        validation=dict(tests_run=result.testsRun,
                        tests_passed=result.testsRun - len(result.skipped),
                        skipped=[dict(test=str(test), reason=reason)
                                 for test, reason in result.skipped],
                        failures=len(result.failures), errors=len(result.errors),
                        output=output.getvalue(), modules=modules),
        fixed_registry=dict(primary_pairs=31, scenes=17, captured_pairs=0,
                            verified_bindings=0, missing_binding_pairs=31,
                            report=coverage_path),
        evidence=evidence, resumed_due_ids=due,
        gpu_observation=dict(
            observed_at="2026-09-19T22:11:18+08:00",
            raw_server_timestamp="2026/09/19 14:11:18.488",
            server="server-6", gpu=7, total_mib=81559, used_mib=62483,
            free_mib=18597, utilization_percent=27,
            processes=[dict(pid=1134192, memory_mib=19956, role="M197"),
                       dict(pid=3827570, memory_mib=42488, role="foreign")]),
        training_progress=dict(
            epoch=24, total_steps=4686, steps_observed=list(range(3786, 3792)),
            previous_tick_last_step=2408, pid_config_log_verified=True,
            preflight_best_miou=.4924),
        findings=[
            "Strict physical identity join; no scene/annotation fallback.",
            "Missing, tied and near-tied counts retained per scene and overall.",
            "Fixed31-pair registry across17 scenes has zero captured/bound pairs this tick.",
            "Synthetic query-selection coverage loss and order reversal detected.",
            "%s static tests passed;%s Torch tests skipped, not native evidence."
            % (result.testsRun - len(result.skipped), len(result.skipped)),
            "Existing11-file runtime manifest including frozen7-file producer unchanged.",
        ],
        initial_test_failure="Exact-tie synthetic fixture suffered floating-point translation "
        "roundoff. Replaced exact-tie case with symmetric integer coordinates; "
        "near-tie fixture retained; production equality rule unchanged.",
        blocker=blocker, retry_after=retry, next_action=next_action,
        native_execution_completed=False, scientific_validation_complete=False,
        independent_objectness_resolved=False, queue_changed=False,
        deployment_performed=False, frozen_seven_file_producer_modified=False,
        limitations=missing["limitations"],
    )
    write(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    if set(due) - {c["id"] for c in work["candidates"]}:
        raise ValueError("Missing due candidate")
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        by_path = {item["path"]: item for item in candidate["evidence"]}
        by_path.update({item["path"]: item for item in evidence + [entry]})
        candidate.update(
            evidence=list(by_path.values()), next_action=next_action, blocker=blocker,
            retry_after=retry, unblock_condition=(
                "GPU7 fewer than two processes and sufficient measured memory, "
                "verified source and native registry bindings. Independent objectness "
                "and candidate-specific science remain separate requirements."),
            latest_progress=now.isoformat() + ": shared registry evaluator;%s static "
            "tests passed,%s skipped; no native capture or candidate-specific validation."
            % (result.testsRun - len(result.skipped), len(result.skipped)),
            geometry_registry_progress=dict(
                timestamp=now.isoformat(), report=REPORT, report_sha256=entry["sha256"],
                tests_passed=result.testsRun - len(result.skipped),
                tests_skipped=len(result.skipped), native_execution_completed=False,
                scientific_validation_complete=False,
                alternatives_attempted="Implemented strict joins, missing/tie denominators "
                "and FPS selection sensitivity; tested synthetic collision and order "
                "reversal; measured live GPU capacity and native training steps."))
    work["last_event_tick"] = dict(
        timestamp=now.isoformat(), mode="event", due_ids=due, evidence=[entry],
        next_action=next_action, result="Shared static progress; native gates remain incomplete")
    write("pipeline/research_work.json.tmp", work)
    os.replace(ROOT / "pipeline/research_work.json.tmp", ROOT / "pipeline/research_work.json")
    if file_sha256(ROOT / "pipeline/queue.json") != queue_hash:
        raise ValueError("Queue changed during event; reconcile before closing")
    print(output.getvalue())
    print(json.dumps(dict(report=entry, primary_pairs=31, scenes=17,
                          verified_native_pairs=0, resumed=due), indent=2))


if __name__ == "__main__":
    main()
