"""Run evaluator tests and persist a CPU-only validation receipt."""
import hashlib
import json
from pathlib import Path
import unittest


root = Path(__file__).resolve().parents[1]
module_names = [
    "test_referent_target_rank_evaluator_20260919",
]
suite = unittest.TestSuite(
    unittest.defaultTestLoader.loadTestsFromName(name)
    for name in module_names
)
result = unittest.TextTestRunner().run(suite)
if not result.wasSuccessful():
    raise SystemExit(1)


def evidence(relative_path):
    path = root / relative_path
    return {
        "path": relative_path,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


source_paths = [
    "scripts/referent_target_rank_evaluator_20260919.py",
    "scripts/test_referent_target_rank_evaluator_20260919.py",
]
registry_path = "pipeline/reports/referent_outcome_independent_registry_20260918-2311.json"
report_path = "pipeline/reports/referent_target_rank_evaluator_20260919.json"
report = {
    "schema_version": 1,
    "scope": (
        "CPU-only static implementation and tests for fail-closed evaluation of "
        "the frozen outcome-independent referent registry; no model forward, "
        "native capture, GPU execution, queue mutation, admission, or efficacy "
        "claim"
    ),
    "candidate_id": "referent-causality-audit",
    "registry": evidence(registry_path),
    "implementation": evidence(source_paths[0]),
    "tests": {
        **evidence(source_paths[1]),
        "tests_passed": result.testsRun,
        "tests_failed": len(result.failures) + len(result.errors),
    },
    "contract": {
        "score_direction": "lower_is_better",
        "required_score_names": ["referent", "objectness"],
        "missing_data_policy": "reject_expression_no_imputation",
        "tie_policy": "reject",
        "required_per_expression_evidence": [
            "native candidate key coverage",
            "referent and objectness scores",
            "target and candidate mask hashes",
            "native input hash",
            "hierarchical partition hash",
        ],
        "scene_balance": (
            "equal scene means over expressions that pass complete native "
            "coverage; rejected expressions are not imputed"
        ),
    },
    "remote_observation": {
        "server": "server-6",
        "gpu": 7,
        "retry_after": "2026-09-19T00:15:00+08:00",
        "unblock_condition": (
            "M197-PIRS reaches terminal state or GPU7 has fewer than two "
            "processes with sufficient measured free memory"
        ),
        "native_capture_launched": False,
    },
    "status": {
        "stage_completed": "Static fail-closed rank-evaluation implementation",
        "native_execution_completed": False,
        "scientific_validation_complete": False,
        "next_action": (
            "At the recorded GPU retry deadline, run the frozen native capture "
            "for every target and all 312 predeclared same-class candidates on "
            "the 73 eligible expressions, then evaluate without imputation."
        ),
    },
    "limitations": [
        "Unit tests validate implementation behavior, not scientific validity.",
        "No native score, candidate coverage, rank, or efficacy result exists.",
        "The evaluator intentionally rejects ties and any incomplete expression.",
        "The fixed TRAIN cohort is diagnostic and not a held-out population sample.",
        "M197-PIRS remains prior-art engineering evidence pending terminal analysis.",
    ],
}
(root / report_path).write_text(
    json.dumps(report, indent=2, ensure_ascii=True) + "\n",
    encoding="ascii",
)
print(json.dumps(report, indent=2))
