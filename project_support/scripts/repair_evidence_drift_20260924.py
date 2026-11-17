"""Archive superseded source receipts and bind tested current source bytes."""

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "pipeline/research_work.json"
QUEUE = ROOT / "pipeline/queue.json"
REPORT = ROOT / "pipeline/reports/evidence_drift_repair_20260924-1421.json"
DECISION = ROOT / "pipeline/decisions/20260924-142120_route_change.md"

# Historical hashes are retained, not silently reinterpreted as current bytes.
EXPECTED = {
    "scripts/m95_identity_query_controls_20260923.py": {
        "f2da0bffb84349f3d651f83cd9f9ddcb829c3fb231c2fc972a3c5a9c7f6da41d",
    },
    "scripts/test_m95_identity_query_controls_20260923.py": {
        "0d4db0d5cdca82f03f2913912f17c04088bfc02041f4384dbc797aff48c35120",
    },
    "scripts/m95_exclusion_cause_audit_20260924.py": {
        "83db283b608a30ce3184be8157d46e0769713ea10abe6bcd6b4ddf49568d2ae7",
        "fa39790c57cd7ad1ba33a84d7c2d3899ffc18ac437a3f5ca1e8ae35ffa182d54",
    },
    "scripts/test_m95_exclusion_cause_audit_20260924.py": {
        "626b80b8a6714cec85750cacc7b9095220ac737a8d67e6871742658895784712",
        "956f5705aaa4cd1c421fc0a34bde894cd11958044e1d7494f045a00ea9310d78",
    },
    "scripts/native_manifest_capture_20260922.py": {
        "ce697bfb47de276ecc284558ac72e5e0267291872990eb8ea4118227850c208d",
    },
    "scripts/test_native_manifest_capture_20260922.py": {
        "6706dc733d9a8937f41c3105d79659b111808719087c35e038780df18c8427d5",
    },
}
IDS = {
    "referent-supervision-axis",
    "referent-causality-audit",
    "modality-identity-preservation",
    "referent-discrimination",
    "instance-identity-representation",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_scan(root, work):
    """Fail closed on unrelated drift, including absolute project-local paths."""
    seen = {}
    for candidate in work["candidates"]:
        for item in candidate["evidence"]:
            path = item["path"]
            full = Path(path) if Path(path).is_absolute() else root / path
            full = full.resolve()
            if not full.is_relative_to(root.resolve()) or not full.is_file():
                raise ValueError("Missing or out-of-project evidence: " + path)
            actual = seen.setdefault(str(full), digest(full))
            if actual != item["sha256"]:
                if path not in EXPECTED or item["sha256"] not in EXPECTED[path]:
                    raise ValueError("Unexpected evidence drift: " + path)
                if candidate["id"] not in IDS:
                    raise ValueError("Unexpected candidate: " + candidate["id"])
    return seen


def migrate(work, current, report_entry, decision_entry):
    changed = []
    for candidate in work["candidates"]:
        keep = []
        archive = candidate.setdefault("superseded_source_evidence", [])
        for item in candidate["evidence"]:
            if item["path"] not in EXPECTED or item["sha256"] == current[item["path"]]:
                keep.append(item)
                continue
            archive_entry = {
                "path": item["path"],
                "sha256": item["sha256"],
                "reason": "Source subsequently edited; historical bytes unavailable locally",
                "superseded_by_sha256": current[item["path"]],
                "not_current_proof": True,
            }
            if archive_entry not in archive:
                archive.append(archive_entry)
            if candidate["id"] not in changed:
                changed.append(candidate["id"])
        if candidate["id"] in changed:
            for path in EXPECTED:
                if any(item["path"] == path for item in candidate["evidence"]):
                    entry = {"path": path, "sha256": current[path]}
                    if entry not in keep:
                        keep.append(entry)
            keep.extend((report_entry, decision_entry))
            candidate["evidence"] = keep
            candidate["evidence_drift_repair_20260924"] = {
                "report": report_entry,
                "decision": decision_entry,
                "tests_passed": 34,
                "native_execution": False,
                "admission": False,
                "historical_receipts_not_revalidated": True,
            }
    if set(changed) != IDS:
        raise ValueError("Unexpected affected candidate set: " + repr(changed))
    return changed


def main():
    if REPORT.exists():
        raise ValueError("Repair already recorded")
    if not DECISION.is_file():
        raise ValueError("Canonical decision required before persistence")
    work_hash = digest(WORK)
    queue_hash = digest(QUEUE)
    work = json.loads(WORK.read_text(encoding="utf-8"))
    seen = evidence_scan(ROOT, work)
    current = {path: seen[str((ROOT / path).resolve())] for path in EXPECTED}
    report = {
        "contract": "evidence_drift_repair_v1",
        "timestamp": "2026-09-24T14:21:20+08:00",
        "scope": "Six mutable diagnostic source/test paths, five diagnosis candidates",
        "historical_receipts": {
            path: sorted(hashes) for path, hashes in EXPECTED.items()
        },
        "current_receipts": current,
        "validation": {
            "command": "PYTHONPATH=scripts python -m unittest "
                       "test_m95_identity_query_controls_20260923 "
                       "test_m95_exclusion_cause_audit_20260924 "
                       "test_native_manifest_capture_20260922",
            "passed": 34,
            "native_execution": False,
        },
        "interpretation": (
            "Old source receipts remain archived and do not attest current "
            "bytes; synthetic tests validate current code only. No scientific "
            "admission, training, or previously claimed native result is upgraded."
        ),
        "queue_sha256": queue_hash,
    }
    if digest(WORK) != work_hash or digest(QUEUE) != queue_hash:
        raise ValueError("State changed during repair preflight")
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    report_entry = {"path": REPORT.relative_to(ROOT).as_posix(),
                    "sha256": digest(REPORT)}
    decision_entry = {"path": DECISION.relative_to(ROOT).as_posix(),
                      "sha256": digest(DECISION)}
    affected = migrate(work, current, report_entry, decision_entry)
    if digest(WORK) != work_hash or digest(QUEUE) != queue_hash:
        raise ValueError("State changed before repair commit")
    temporary = WORK.with_suffix(".evidence_repair.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(work, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, WORK)
    evidence_scan(ROOT, work)
    if digest(QUEUE) != queue_hash:
        raise ValueError("Queue unexpectedly changed")
    print(json.dumps({"affected": affected, "report_sha256": digest(REPORT),
                      "queue_sha256": queue_hash}))


if __name__ == "__main__":
    main()
