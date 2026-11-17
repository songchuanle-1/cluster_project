"""Persist the manifest-bound capture implementation and due-stage progress."""
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = (
    ROOT
    / "pipeline"
    / "reports"
    / "manifest_capture_implementation_20260922-1412.json"
)
RESEARCH_WORK_PATH = ROOT / "pipeline" / "research_work.json"
PRODUCER_PATH = ROOT / "scripts" / "native_manifest_capture_20260922.py"
TEST_PATH = ROOT / "scripts" / "test_native_manifest_capture_20260922.py"
MANIFEST_PATH = (
    ROOT
    / "pipeline"
    / "diagnostic_runs"
    / "m95_identity_controls_20260922"
    / "manifest.json"
)
MANIFEST_SHA256 = (
    "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
)
REMOTE_BUNDLE = (
    "/data3/songcl/Project/Cluster_project/Cluster/"
    "pipeline/diagnostic_bundles/manifest_capture_20260922"
)
DUE_IDS = {
    "referent-supervision-axis": (
        "Run the deployed manifest producer only when GPU7 is safe, then apply "
        "the frozen identity controls. Do not enqueue a mechanism from the "
        "current 16-row cohort."
    ),
    "referent-causality-audit": (
        "Run the deployed manifest producer only when GPU7 is safe, then "
        "compute the pre-registered score-matched target-causality contrast."
    ),
    "modality-identity-preservation": (
        "Run the deployed manifest producer only when GPU7 is safe, then test "
        "per-stage identity preservation on the same frozen rows."
    ),
    "referent-discrimination": (
        "Run the deployed manifest producer only when GPU7 is safe, then apply "
        "class-matched and score-matched discrimination controls."
    ),
    "instance-identity-representation": (
        "Run the deployed manifest producer only when GPU7 is safe, then "
        "report target-versus-same-class margins with support gates."
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
    producer_hash = file_sha256(PRODUCER_PATH)
    test_hash = file_sha256(TEST_PATH)
    manifest_hash = file_sha256(MANIFEST_PATH)
    if manifest_hash != MANIFEST_SHA256:
        raise ValueError("Frozen manifest hash changed")

    report = {
        "schema_version": 1,
        "contract": "m95_manifest_capture_implementation_v1",
        "generated_at": "2026-09-22T14:12:27+08:00",
        "status": "implementation_deployed_native_run_gpu_blocked",
        "scope": (
            "Manifest-bound capture implementation and remote deployment "
            "validation. No model forward, queue mutation, admission, training, "
            "or efficacy result."
        ),
        "producer": {
            "path": PRODUCER_PATH.relative_to(ROOT).as_posix(),
            "sha256": producer_hash,
            "test_path": TEST_PATH.relative_to(ROOT).as_posix(),
            "test_sha256": test_hash,
            "artifact_contract": "m95_manifest_native_query_artifact_v1",
        },
        "manifest": {
            "path": MANIFEST_PATH.relative_to(ROOT).as_posix(),
            "sha256": manifest_hash,
            "rows": 256,
            "contract": "m95_preregistered_identity_controls_v1",
        },
        "local_validation": {
            "py_compile": True,
            "focused_tests_passed": 50,
            "manifest_contract_tests_passed": 6,
            "supporting_capture_tests_passed": 44,
        },
        "remote_validation": {
            "host": "server-6",
            "bundle": REMOTE_BUNDLE,
            "py_compile": True,
            "producer_sha256": producer_hash,
            "test_sha256": test_hash,
            "manifest_sha256": manifest_hash,
            "focused_tests_passed": 6,
            "manifest_rows_loaded": 256,
        },
        "capture_contract": {
            "selection": "exact scene_id and ann_id pairs from the frozen manifest",
            "completion": "fail closed unless all 256 unique manifest rows are found",
            "persisted_query_evidence": [
                "raw query mask logits and boolean masks",
                "query scores",
                "native-positive flags",
                "FPS seed support inside the target union",
                "physical instance labels",
                "sampled semantic labels",
                "target union",
                "manifest index and manifest SHA256",
            ],
            "model_or_training_code_changed": False,
            "queue_mutation": False,
        },
        "capacity_preflight": {
            "host": "server-6",
            "gpu": 7,
            "utilization_percent": 100,
            "memory_used_mib": 42023,
            "memory_total_mib": 81559,
            "foreign_pid": 3694608,
            "foreign_process": (
                "/home/jiaoh/conda_envs/das_env/bin/python"
            ),
            "safe_project_slot": False,
            "action": "do not evict or interfere with foreign work",
        },
        "next_action": (
            "When server-6 GPU7 has a safe project slot, execute the deployed "
            "manifest producer with the exact checkpoint and manifest hash, "
            "then run the frozen controls and stage-specific analyses."
        ),
        "not_evidence_of": [
            "admission",
            "deployable efficacy",
            "population effect",
            "novelty",
            "referent-specific causality",
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
        evidence(PRODUCER_PATH.relative_to(ROOT).as_posix(), producer_hash),
        evidence(TEST_PATH.relative_to(ROOT).as_posix(), test_hash),
        evidence(MANIFEST_PATH.relative_to(ROOT).as_posix(), manifest_hash),
    ]
    for candidate_id, next_action in DUE_IDS.items():
        candidate = by_id.get(candidate_id)
        if candidate is None:
            raise ValueError("Missing due candidate: " + candidate_id)
        candidate["stage"] = "implementation"
        candidate["latest_progress"] = (
            "Implemented and deployed a separate manifest-bound native capture "
            "producer that requires the exact 256-row manifest hash, scans until "
            "all frozen expressions are found, and persists raw query masks, "
            "scores, positive flags, seed support, physical labels, semantic "
            "labels, target union, and manifest identity. Local and remote tests "
            "pass. A native run did not start because foreign PID 3694608 still "
            "occupies GPU7 at 100% utilization and 42023/81559 MiB."
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
