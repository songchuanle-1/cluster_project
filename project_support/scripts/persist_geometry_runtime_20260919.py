"""Persist executed static checks and durable dispositions for the 21:07 event."""
import io
import json
import os
from datetime import datetime
from pathlib import Path
import unittest

from frozen_capture_contract_20260916 import file_sha256
from native_geometry_runtime_20260919 import source_manifest
from referent_native_chain_selftest_20260919 import run_selftest

ROOT = Path(__file__).resolve().parents[1]
REPORT = "pipeline/reports/geometry_runtime_20260919-2118.json"
MODULES = (
    "test_native_geometry_runtime_20260919",
    "test_referent_geometry_capture_20260919",
    "test_referent_geometry_control_20260919",
    "test_referent_native_expression_producer_20260919",
    "test_referent_object_rank_capture_20260919",
    "test_referent_target_rank_evaluator_20260919",
    "test_native_endpoint_capture_20260916",
    "test_frozen_capture_contract_20260916",
)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8")


def main():
    context = json.loads((ROOT / "pipeline/headless/.tick_context.json").read_text("utf-8"))
    if context["generated_at"] != "2026-09-19T13:07:11.745596+00:00":
        raise ValueError("Persistence belongs only to the 21:07 event")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(
        unittest.defaultTestLoader.loadTestsFromNames(MODULES))
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise ValueError("Static validation failed")
    chain = run_selftest()
    chain_path = "pipeline/reports/referent_native_chain_selftest_20260919-2118.json"
    write_json(ROOT / chain_path, chain)
    manifest = source_manifest()
    manifest_path = "pipeline/reports/geometry_runtime_sources_20260919-2118.json"
    write_json(ROOT / manifest_path, manifest)
    now = datetime.now().astimezone().isoformat()
    retry = "2026-09-19T22:07:00+08:00"
    next_action = (
        "Validate the geometry runtime on synthetic native-layout Torch modules "
        "and add a fixed-registry join/evaluator for sidecar outputs, including "
        "per-scene missing/tied/near-tied denominators and query-selection sensitivity. "
        "This is executable local static work, not a new candidate. After " + retry +
        ", recheck only authorized server-6 GPU7. When fewer than two processes "
        "and measured memory suffice, verify exact remote source/model/config/"
        "checkpoint binding and deploy the separate bounded geometry diagnostic "
        "without modifying the frozen seven-file producer; record increasing "
        "native step outputs and native dtype/layout. Do not equate two-batch "
        "smoke completion with coverage of the31-pair failure registry. Independent "
        "objectness and candidate-specific evidence remain unresolved; retain all "
        "admission, coverage and selection gates."
    )
    blocker = (
        "21:10 read-only GPU7 check: M197 PID1134192 uses19956MiB; foreign "
        "PID3827570 uses42488MiB; free18597MiB, two-process cap reached. Runtime "
        "hook implemented and statically tested; native execution, fixed-registry "
        "evaluation and independent objectness remain incomplete."
    )
    paths = [
        "scripts/native_geometry_runtime_20260919.py",
        "scripts/test_native_geometry_runtime_20260919.py",
        "scripts/referent_geometry_capture_20260919.py",
        "scripts/persist_geometry_runtime_20260919.py",
        "Cluster/framework/dataset/scannetv2.py",
        "Cluster/framework/dataset/__init__.py",
        "Cluster/framework/model/Quard_model/" +
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/network.py",
        "pipeline/bugfixes/bugfix_20260919-2117.md",
        "pipeline/decisions/20260919-211653_other.md", chain_path, manifest_path,
    ]
    evidence = [dict(path=p, sha256=file_sha256(ROOT / p)) for p in paths]
    due = set(context["research_work"]["due_ids"])
    report = dict(
        schema_version=1, generated_at=now, scope="Shared static runtime implementation",
        runtime_contract="criterion_geometry_runtime_v1",
        geometry_contract="criterion_geometry_nuisance_v2",
        validation=dict(tests_run=result.testsRun, failures=len(result.failures),
                        errors=len(result.errors), new_tests=16, modules=MODULES,
                        synthetic_chain_checks=len(chain["checks"]), output=stream.getvalue()),
        producer_manifest=manifest, evidence=evidence, resumed_due_ids=sorted(due),
        gpu_observation=dict(
            observed_at="2026-09-19T21:10:06+08:00", server="server-6", gpu=7,
            total_mib=81559, used_mib=62483, free_mib=18597, utilization_percent=100,
            process_count=2, processes=[
                dict(pid=1134192, memory_mib=19956, role="M197"),
                dict(pid=3827570, memory_mib=42488, role="foreign")]),
        training_progress=dict(
            epoch=24, steps_observed=[2404, 2405, 2406, 2407, 2408],
            total_steps=4686, previous_tick_last_step=1062,
            pid_config_and_log_fd_verified=True, best_miou_preflight=.4924),
        findings=[
            "Read-only criterion observer; exact identity and finally cleanup tested.",
            "Native float labels validated losslessly; raw labels and dtype hash retained.",
            "Geometry v2 does not silently accept older synthetic v1 schema.",
            "Transitive local source manifest lists, but does not attest, external imports.",
            "Synthetic EndpointDataset/FrozenDataset to criterion integration passes.",
        ],
        blocker=blocker, retry_after=retry, next_action=next_action,
        native_execution_completed=False, scientific_validation_complete=False,
        independent_objectness_resolved=False, frozen_seven_file_producer_modified=False,
        queue_changed=False, deployment_performed=False,
        limitations=[
            "No actual Torch/native forward or GPU allocation occurred this event.",
            "Synthetic checks do not establish native coverage, specificity or efficacy.",
            "Hashes establish identity, not execution; external environment not attested.",
            "Annotation-assisted geometry is not objectness or deployment inference.",
            "Two-batch smoke cannot claim full fixed-registry coverage.",
            "Shared implementation does not validate seven separate candidates.",
            "Capacity precheck is not a reservation; coordinate immediately before launch.",
        ],
    )
    write_json(ROOT / REPORT, report)
    entry = dict(path=REPORT, sha256=file_sha256(ROOT / REPORT))
    path = ROOT / "pipeline/research_work.json"
    work = json.loads(path.read_text("utf-8"))
    if due - {c["id"] for c in work["candidates"]}:
        raise ValueError("Due candidate missing")
    adapter_path = "scripts/referent_geometry_capture_20260919.py"
    adapter_hash = file_sha256(ROOT / adapter_path)
    for candidate in work["candidates"]:
        for item in candidate.get("evidence", []):
            if item["path"] == adapter_path:
                item["sha256"] = adapter_hash
        if candidate["id"] not in due:
            continue
        by_path = {item["path"]: item for item in candidate["evidence"]}
        for item in evidence + [entry]:
            by_path[item["path"]] = item
        candidate.update(
            evidence=list(by_path.values()), next_action=next_action, blocker=blocker,
            retry_after=retry, unblock_condition=(
                "GPU7 fewer than two processes with enough measured memory and exact "
                "remote source binding; independent objectness and scientific gates remain."),
            latest_progress=now + ": runtime hook, manifest and native float-label "
            "correction;118 static tests and6 synthetic checks pass; no native run.",
            geometry_runtime_progress=dict(
                timestamp=now, report=REPORT, report_sha256=entry["sha256"],
                tests_passed=result.testsRun, native_execution_completed=False,
                scientific_validation_complete=False,
                alternatives_attempted="Dataset/criterion source audit, synthetic physical "
                "binding integration, failure cleanup and layout tests while GPU7 capped; "
                "bounded live training steps verified."),
        )
    work["last_event_tick"] = dict(timestamp=now, mode="event", due_ids=sorted(due),
                                   evidence=[entry], next_action=next_action,
                                   result="Runtime implementation; native and admission incomplete")
    temp = path.with_suffix(".json.tmp")
    write_json(temp, work)
    os.replace(temp, path)
    print(json.dumps(dict(report=entry, tests_passed=result.testsRun,
                          synthetic_checks=len(chain["checks"]),
                          producer_files=len(manifest["sources"]), resumed=sorted(due)), indent=2))


if __name__ == "__main__":
    main()
