"""Execute static regression and record integration without claiming native validation."""
import hashlib
import json
from pathlib import Path
import unittest

root = Path(__file__).resolve().parents[1]
suite = unittest.TestSuite()
for pattern in ("test_native_endpoint_capture_20260916.py",
                "test_native_support_capture_20260916.py",
                "test_physical_mask_endpoints_20260916.py",
                "test_capture_support_20260916.py"):
    suite.addTests(unittest.defaultTestLoader.discover(str(root / "scripts"), pattern))
result = unittest.TextTestRunner().run(suite)
if not result.wasSuccessful():
    raise SystemExit(1)
names = [
    "scripts/native_endpoint_capture_20260916.py",
    "scripts/native_support_capture_v2_20260916.py",
    "scripts/test_native_endpoint_capture_20260916.py",
    "scripts/persist_endpoint_integration_20260916.py",
    "pipeline/decisions/20260916-181129_other.md",
]


def evidence(name):
    return dict(path=name, sha256=hashlib.sha256((root / name).read_bytes()).hexdigest())


report = dict(
    scope="Local static integration tests; not native execution",
    tests_passed=result.testsRun, native_execution_completed=False,
    finding="Bind unique sampled-instance classes; unresolved native199 is background, real199 retained.",
    remote_attempt=dict(host="100.64.3.28", outcome="SSH port22 connect timeout",
                        remote_command_executed=False,
                        retry_after="2026-09-16T19:07:00+08:00",
                        unblock_condition="Authorized server6 SSH connectivity restored"),
    limitations=["No expanded TRAIN sample", "No seven-control binding",
                 "No terminal PIRS comparison or efficacy claim"],
    evidence=[evidence(name) for name in names])
report_name = "pipeline/reports/endpoint_integration_20260916-1812.json"
(root / report_name).write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
path = root / "pipeline/research_work.json"
work = json.loads(path.read_text(encoding="utf-8"))
context = json.loads((root / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
for candidate in work["candidates"]:
    if candidate["id"] not in context["research_work"]["due_ids"]:
        continue
    candidate["evidence"].extend(evidence(name) for name in names + [report_name]
                                 if name not in {e["path"] for e in candidate["evidence"]})
    candidate["endpoint_native_integration_progress"] = dict(
        stage_completed="Versioned endpoint/semantic integration and static regression",
        tests_passed=result.testsRun, native_execution_completed=False,
        next_action="Retry server6 SSH19:07+08; check GPU7 capacity then execute frozen TRAIN/control capture.",
        limitation="Shared plumbing only; candidate-specific scientific actions remain due.")
    if candidate["id"] in ("modality-identity-preservation", "instance-identity-representation",
                           "input-modality-distinguishability"):
        candidate["next_action"] = (
            "Retry server6 SSH after2026-09-16T19:07:00+08:00; check GPU7 capacity; "
            "deploy v2 helpers and execute predefined TRAIN sample. Verify native semantic "
            "endpoint binding then apply frozen recoverable same-class stratum before feature "
            "contrasts. Static integration is not native or scientific validation.")
path.write_text(json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
print(json.dumps(dict(report=report_name, tests_passed=result.testsRun)))
