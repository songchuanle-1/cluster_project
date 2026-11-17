"""Persist the CPU-only manifest identity-analysis implementation."""
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = (
    ROOT
    / "pipeline"
    / "reports"
    / "manifest_identity_analysis_implementation_20260922-1615.json"
)
RESEARCH_WORK_PATH = ROOT / "pipeline" / "research_work.json"
ANALYZER_PATH = (
    ROOT / "scripts" / "analyze_m95_manifest_identity_controls_20260922.py"
)
TEST_PATH = (
    ROOT / "scripts" / "test_analyze_m95_manifest_identity_controls_20260922.py"
)
MANIFEST_PATH = (
    ROOT / "pipeline" / "diagnostic_runs" / "m95_identity_controls_20260922"
    / "manifest.json"
)
MANIFEST_SHA256 = (
    "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
)
REMOTE_BUNDLE = (
    "/data3/songcl/Project/Cluster_project/Cluster/"
    "pipeline/diagnostic_bundles/manifest_identity_analysis_20260922"
)
DUE_IDS = {
    "referent-supervision-axis": (
        "When GPU7 is safe, run native_manifest_capture_20260922.py, then run "
        "analyze_m95_manifest_identity_controls_20260922.py and inspect the "
        "pre-registered score-matched primary estimand."
    ),
    "referent-causality-audit": (
        "When GPU7 is safe, run native_manifest_capture_20260922.py, then run "
        "the deployed identity analyzer and require the paired causality gates "
        "before any mechanism claim."
    ),
    "modality-identity-preservation": (
        "When GPU7 is safe, run native_manifest_capture_20260922.py, then run "
        "the identity analyzer and inspect per-stage target-minus-peer margins."
    ),
    "referent-discrimination": (
        "When GPU7 is safe, run native_manifest_capture_20260922.py, then run "
        "the identity analyzer and compare class-matched selector and "
        "score-matched non-target controls."
    ),
    "instance-identity-representation": (
        "When GPU7 is safe, run native_manifest_capture_20260922.py, then run "
        "the identity analyzer and report target-versus-same-class margins "
        "with support gates."
    ),
}


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evidence(path, digest):
    return {"path": path, "sha256": digest}


def write_json(path, document):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(document, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )
    os.replace(temporary, path)


def main():
    analyzer_hash = file_sha256(ANALYZER_PATH)
    test_hash = file_sha256(TEST_PATH)
    manifest_hash = file_sha256(MANIFEST_PATH)
    if manifest_hash != MANIFEST_SHA256:
        raise ValueError("Frozen manifest hash changed")

    report = {
        "schema_version": 1,
        "contract": "m95_manifest_identity_analysis_implementation_v1",
        "generated_at": "2026-09-22T16:15:00+08:00",
        "status": "implementation_deployed_native_run_gpu_blocked",
        "scope": (
            "CPU-only implementation of the frozen manifest identity analysis "
            "and remote static validation. No model forward, GPU execution, "
            "queue mutation, admission, training, or efficacy result."
        ),
        "analyzer": {
            "path": ANALYZER_PATH.relative_to(ROOT).as_posix(),
            "sha256": analyzer_hash,
            "test_path": TEST_PATH.relative_to(ROOT).as_posix(),
            "test_sha256": test_hash,
            "contract": "m95_manifest_identity_control_analysis_v1",
        },
        "manifest": {
            "path": MANIFEST_PATH.relative_to(ROOT).as_posix(),
            "sha256": manifest_hash,
            "rows": 256,
            "contract": "m95_preregistered_identity_controls_v1",
        },
        "analysis_contract": {
            "source": "capture.json plus hash-bound manifest_selected_*.pt artifacts",
            "completion": (
                "require all 256 manifest rows, exact checkpoint and manifest "
                "hashes, and hash-bound artifact coverage"
            ),
            "primary": (
                "scene-balanced paired target-IoU uplift for native-positive "
                "minus score-matched class-matched non-target; 10000 scene "
                "bootstrap draws with seed 1999"
            ),
            "secondary": [
                "target-objectness and class-matched selector controls",
                "score-matched target-versus-same-class IoU and score margins",
                "per-stage cosine target-minus-peer representation margins",
            ],
            "no_fallback": True,
            "model_or_training_code_changed": False,
            "queue_mutation": False,
        },
        "local_validation": {
            "py_compile": True,
            "focused_tests_passed": 7,
            "targeted_regression_tests_passed": 18,
            "real_manifest_rows_loaded": 256,
            "real_manifest_sha256": manifest_hash,
        },
        "remote_validation": {
            "host": "server-6",
            "bundle": REMOTE_BUNDLE,
            "py_compile": True,
            "focused_tests_passed": 7,
            "analyzer_sha256": analyzer_hash,
            "test_sha256": test_hash,
        },
        "capacity_preflight": {
            "host": "server-6",
            "gpu": 7,
            "utilization_percent": 100,
            "memory_used_mib": 42023,
            "memory_total_mib": 81559,
            "foreign_pid": 3694608,
            "foreign_process": "/home/jiaoh/conda_envs/das_env/bin/python",
            "safe_project_slot": False,
            "action": "do not evict or interfere with foreign work",
        },
        "next_action": (
            "When server-6 GPU7 has a safe project slot, execute the deployed "
            "manifest producer with exact checkpoint and manifest hashes, then "
            "execute this analyzer on its completed capture."
        ),
        "not_evidence_of": [
            "admission",
            "deployable efficacy",
            "population effect",
            "novelty",
            "whole-mechanism benefit",
            "referent-specific causality before the capture passes its gates",
        ],
    }
    write_json(REPORT_PATH, report)
    report_hash = file_sha256(REPORT_PATH)

    document = json.loads(RESEARCH_WORK_PATH.read_text(encoding="ascii"))
    candidates = document.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("research_work candidates must be a list")
    by_id = {candidate.get("id"): candidate for candidate in candidates}
    additions = [
        evidence(REPORT_PATH.relative_to(ROOT).as_posix(), report_hash),
        evidence(ANALYZER_PATH.relative_to(ROOT).as_posix(), analyzer_hash),
        evidence(TEST_PATH.relative_to(ROOT).as_posix(), test_hash),
        evidence(MANIFEST_PATH.relative_to(ROOT).as_posix(), manifest_hash),
    ]
    for candidate_id, next_action in DUE_IDS.items():
        candidate = by_id.get(candidate_id)
        if candidate is None:
            raise ValueError("Missing due candidate: " + candidate_id)
        candidate["stage"] = "implementation"
        candidate["blocker"] = (
            "server-6 GPU7 is occupied by foreign PID 3694608 at 100% "
            "utilization; native capture cannot start without interfering "
            "with foreign work"
        )
        candidate["retry_after"] = "2026-09-22T17:15:00+08:00"
        candidate["unblock_condition"] = (
            "server-6 GPU7 has a safe project slot with the foreign process "
            "unaffected"
        )
        candidate["alternatives_attempted"] = (
            "One targeted read-only GPU query; implemented, deployed and "
            "tested the complete CPU-only analyzer while native execution was "
            "blocked."
        )
        candidate["latest_progress"] = (
            "Implemented and remotely validated the missing CPU-only analyzer "
            "for the frozen 256-row manifest. It binds exact checkpoint, "
            "manifest and artifact hashes; computes the pre-registered "
            "scene-balanced score-matched pair and 10000-draw bootstrap; and "
            "reports class-matched, objectness and per-stage identity controls "
            "without fallback. Native capture did not run because foreign PID "
            "3694608 still occupied GPU7 at 100% utilization."
        )
        candidate["next_action"] = next_action
        updated_paths = {item["path"] for item in additions}
        candidate["evidence"] = [
            item
            for item in candidate.get("evidence", [])
            if item.get("path") not in updated_paths
        ]
        existing = {
            (item.get("path"), item.get("sha256"))
            for item in candidate.get("evidence", [])
        }
        for item in additions:
            key = (item["path"], item["sha256"])
            if key not in existing:
                candidate.setdefault("evidence", []).append(item)
                existing.add(key)
    write_json(RESEARCH_WORK_PATH, document)
    print(json.dumps({"report": str(REPORT_PATH), "sha256": report_hash}))


if __name__ == "__main__":
    main()
