"""Persist CPU evidence; no scientific or training admission claim."""
import hashlib
import json
from pathlib import Path
import unittest
from paired_capture_evaluation_20260916 import control_manifest, paired_summary

root = Path(__file__).resolve().parents[1]
result = unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(
    str(root / "scripts"), "test_paired_capture_evaluation_20260916.py"))
if not result.wasSuccessful():
    raise SystemExit(1)


def read(name):
    return json.loads((root / name).read_text(encoding="utf-8"))


def evidence(name):
    return dict(path=name, sha256=hashlib.sha256((root / name).read_bytes()).hexdigest())


source = "pipeline/reports/native_support_capture_20260916-1517.json"
contract = "pipeline/reports/evaluation_contract_20260916-1310.json"
rows = read(source)["rows"]
controls = control_manifest(read(contract)["connected_control_ids"])
observed = {(r["scene"], r["ann_id"]) for r in rows}
names = [source, contract, "scripts/paired_capture_evaluation_20260916.py",
         "scripts/test_paired_capture_evaluation_20260916.py",
         "scripts/persist_paired_evaluation_20260916.py",
         "pipeline/decisions/20260916-191100_other.md"]
report_name = "pipeline/reports/paired_evaluation_20260916-1912.json"
blocker = dict(
    blocker="GPU7 occupied by PIRS and foreign training; no third process authorized.",
    retry_after="2026-09-16T20:07:00+08:00",
    unblock_condition="GPU7 below two processes and sufficient measured free memory.",
    alternatives_attempted="Executed CPU evaluator, eight tests, self-check and control audit.")
report = dict(
    scope="Executed CPU tooling and control audit; not native validation",
    tests_passed=result.testsRun, archive_self_comparison=paired_summary(rows, rows),
    control_expression_manifest=controls,
    control_nodes=sum(len(r["node_ids"]) for r in controls),
    unique_control_expressions=len(controls),
    missing_control_expressions=[r for r in controls
                                 if (r["scene"], r["ann_id"]) not in observed],
    remote_observation=dict(timestamp="2026-09-16T19:10:00+08:00",
                            ssh_recovered=True, gpu=7, free_mib=18607,
                            used_mib=62473, utilization_percent=100,
                            pirs_pid=1134192, foreign_pid=3827570,
                            foreign_command="das_foundation/scripts/train_das_mae.py",
                            native_epoch=8, native_steps=[4059, 4070],
                            capture_launched=False),
    native_blocker=blocker, evidence=[evidence(n) for n in names],
    limitations=["No expanded sample, native semantic validation or PIRS efficacy.",
                 "Seven nodes correspond to six expressions, not seven independent controls.",
                 "Support indices cannot certify identical coordinate transformations."])
(root / report_name).write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
work = read("pipeline/research_work.json")
due = read("pipeline/headless/.tick_context.json")["research_work"]["due_ids"]
for candidate in work["candidates"]:
    if candidate["id"] not in due:
        continue
    candidate["evidence"].extend(evidence(n) for n in names[2:] + [report_name])
    candidate["paired_evaluation_progress"] = dict(
        tests_passed=result.testsRun, archive_self_check=True,
        scientific_validation_complete=False, report=report_name,
        limitation="Shared tooling; no candidate-specific native result.")
    candidate["native_capture_blocker"] = blocker
    if candidate["id"] in ("modality-identity-preservation",
                           "instance-identity-representation", "input-modality-distinguishability"):
        candidate["next_action"] = (
            "Retry GPU7 capacity after2026-09-16T20:07:00+08:00; require fewer than two "
            "processes and measured memory. Execute v2 frozen TRAIN semantic capture "
            "then recoverable same-class feature contrasts. Preserve both jobs.")
    elif candidate["id"] == "same-target-description-grounding":
        candidate["next_action"] = (
            "Use six scene/annotation keys and seven node_ids in paired_evaluation_"
            "20260916-1912.json; bind native physical endpoints when GPU7 permits. "
            "Duplicate expression is not an independent control.")
    elif candidate["id"] == "referent-causality-audit":
        candidate["next_action"] = (
            "Await terminal PIRS; freeze matched sample, transform and checkpoint identities; "
            "capture paired axes and run tested scene-balanced evaluator. Self-check is not efficacy.")
(root / "pipeline/research_work.json").write_text(
    json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
print(json.dumps(dict(report=report_name, tests=result.testsRun,
                      controls=len(controls), missing=len(report["missing_control_expressions"]))))
