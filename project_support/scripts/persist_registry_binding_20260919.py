"""Persist this event's executed static checks without advancing admission."""
from datetime import datetime
import io
import json
import os
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256
from native_geometry_runtime_20260919 import source_manifest
from persist_geometry_runtime_20260919 import MODULES
from referent_geometry_registry_20260919 import registry_pairs

ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/registry_binding_20260919-2315.json"
DECISION = "pipeline/decisions/20260919-231332_other.md"
REGISTRY = "pipeline/reports/referent_control_pairing_20260918-1812.json"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write(path, value):
    (ROOT / path).write_text(json.dumps(value, indent=2, ensure_ascii=True,
                                      allow_nan=False) + "\n", encoding="ascii")


def main():
    context = read("pipeline/headless/.tick_context.json")
    if context["generated_at"] != "2026-09-19T15:07:11.064267+00:00":
        raise ValueError("Wrong event snapshot")
    if (ROOT / REPORT).exists():
        raise ValueError("Evidence report already exists")
    queue_hash = file_sha256(ROOT / "pipeline/queue.json")
    modules = ("test_referent_registry_binding_20260919",
               "test_referent_geometry_registry_20260919",
               "test_geometry_torch_static_20260919") + MODULES
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Static tests failed")
    previous = read("pipeline/reports/geometry_runtime_20260919-2118.json")
    manifest = source_manifest()
    if manifest != previous["producer_manifest"]:
        raise ValueError("Frozen runtime source manifest changed")
    pairs = registry_pairs(read(REGISTRY))
    if len(pairs) != 31 or len({r["scene"] for r in pairs}) != 17:
        raise ValueError("Fixed registry changed")
    now = datetime.now().astimezone().isoformat()
    retry = "2026-09-20T00:07:00+08:00"
    blocker = (
        "23:11 GPU7 server observation: M197 PID1134192 19956MiB and foreign "
        "PID3827570 42488MiB; free18597MiB, two-process cap reached. Native "
        "binding/capture not executed; no verified native scene_inputs metadata "
        "or transformed observations. Independent objectness unresolved. Local "
        "Torch absent, two synthetic module checks skipped."
    )
    next_action = (
        "Continue the same diagnostic, no duplicate review or new variant. "
        "Integrate BindingExporter into a separate versioned registry-aware "
        "native runner: use actual dataset.scene_inputs, FrozenDataset outputs "
        "before collation and unchanged physical axes; preserve original dataset "
        "indices/slots and retain ambiguous/missing metadata and absent object "
        "support. Verify exporter/source manifests and synthetic integration "
        "without native local execution. Do not promote metadata plans to "
        "physical bindings or claim new transforms reproduce historical captures. "
        "After " + retry + " recheck server-6 GPU7; only with fewer than two "
        "processes, enough measured memory and coordinated authorization verify "
        "remote model/config/checkpoint/source binding and run bounded capture. "
        "Record increasing outputs and dtype/layout; smoke is not31-pair coverage. "
        "Independent objectness and each mechanism's science/admission remain "
        "separate unresolved requirements."
    )
    paths = [
        "scripts/referent_registry_binding_20260919.py",
        "scripts/test_referent_registry_binding_20260919.py",
        "scripts/persist_registry_binding_20260919.py",
        "Cluster/framework/dataset/scannetv2.py", REGISTRY, DECISION,
    ]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    due = context["research_work"]["due_ids"]
    report = dict(
        schema_version=1, generated_at=now, scope="Shared static binding implementation",
        validation=dict(tests_run=result.testsRun,
                        tests_passed=result.testsRun - len(result.skipped),
                        failures=len(result.failures), errors=len(result.errors),
                        skipped=[dict(test=str(test), reason=reason)
                                 for test, reason in result.skipped],
                        modules=modules, output=stream.getvalue()),
        evidence=evidence, resumed_due_ids=due,
        fixed_registry=dict(requested=31, scenes=17, verified_native_bindings=0,
                            captured_pairs=0, missing_binding_pairs=31,
                            native_metadata_plan_executed=False),
        producer_manifest=manifest, producer_manifest_changed=False,
        gpu_observation=dict(
            raw_server_timestamp="2026/09/19 15:11:19.668",
            server="server-6", gpu=7, total_mib=81559, used_mib=62483,
            free_mib=18597, utilization_percent=100,
            processes=[dict(pid=1134192, memory_mib=19956, role="M197"),
                       dict(pid=3827570, memory_mib=42488, role="foreign")],
            timestamp_note="Server UTC corresponds to23:11 Asia/Shanghai; local clock differed."),
        training_progress=dict(
            phase="Val", epoch=24, total_steps=363,
            steps_observed=list(range(256, 264)),
            previous_tick_phase="Train", previous_tick_step=3791,
            previous_tick_total_steps=4686, pid_config_log_verified=True,
            preflight_best_miou=.4924, completed_current_epoch_claimed=False),
        operational_recoveries=[
            "Initial SSH multiline shell ended with syntax error after GPU/PID/log "
            "output; targeted read-only log-tail retry succeeded. No GPU requery.",
            "rg unavailable: used bounded PowerShell source reads.",
            "Initial Bash path absent: resolved installed Bash and logged decision.",
        ],
        findings=[
            "Metadata key includes scene, exact slot, annotation and target object.",
            "Duplicate metadata locations remain ambiguous, never first-match.",
            "Export checks full transformed item and physical labels/support.",
            "Failed multi-expression observation leaves no partial bindings.",
            "Zero target/control physical support remains explicit in denominators.",
            "Native199 sentinel versus real199 disambiguation tested.",
            "Synthetic exporter-to-existing-evaluator integration passed.",
            "Original frozen11-file runtime manifest unchanged.",
        ],
        blocker=blocker, retry_after=retry, next_action=next_action,
        native_execution_completed=False, scientific_validation_complete=False,
        independent_objectness_resolved=False, queue_changed=False,
        queue_sha256=queue_hash, deployment_performed=False,
        limitations=[
            "No real native scene_inputs metadata or physical observations consumed.",
            "Hashes identify artifacts, not truthful native observation or execution.",
            "New transforms do not reproduce historical failure inputs.",
            "Failure-selected31-pair registry is not population evidence.",
            "Shared implementation does not validate seven mechanisms.",
        ],
    )
    write(REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    work = read("pipeline/research_work.json")
    if set(due) - {c["id"] for c in work["candidates"]}:
        raise ValueError("Missing due candidates")
    for candidate in work["candidates"]:
        if candidate["id"] not in due:
            continue
        by_path = {e["path"]: e for e in candidate["evidence"]}
        by_path.update({e["path"]: e for e in evidence + [entry]})
        candidate.update(
            evidence=list(by_path.values()), blocker=blocker, retry_after=retry,
            next_action=next_action,
            unblock_condition="GPU7 fewer than two processes and enough memory; "
            "verified remote source/model/config/checkpoint and native registry "
            "bindings. Mechanism-specific scientific gates remain independent.",
            latest_progress=now + ": explicit registry binding exporter; "
            "%d static tests passed,%d skipped; no native validation."
            % (result.testsRun - len(result.skipped), len(result.skipped)),
            registry_binding_progress=dict(
                timestamp=now, report=REPORT, report_sha256=entry["sha256"],
                tests_passed=result.testsRun - len(result.skipped),
                tests_skipped=len(result.skipped),
                native_execution_completed=False, scientific_validation_complete=False,
                alternatives_attempted="Audited dataset target/slot source; implemented "
                "metadata planning and full physical exporter; tested collisions, "
                "atomic failures, missing support and existing evaluator integration. "
                "Read live capacity and increasing native validation steps."))
    work["last_event_tick"] = dict(
        timestamp=now, mode="event", due_ids=due, evidence=[entry],
        next_action=next_action, result="Shared static progress; native/admission gates incomplete")
    if file_sha256(ROOT / "pipeline/queue.json") != queue_hash:
        raise ValueError("Queue changed during event")
    write("pipeline/research_work.json.tmp", work)
    os.replace(ROOT / "pipeline/research_work.json.tmp", ROOT / "pipeline/research_work.json")
    print(json.dumps(dict(report=entry, resumed=due, native_pairs=0), indent=2))


if __name__ == "__main__":
    main()
