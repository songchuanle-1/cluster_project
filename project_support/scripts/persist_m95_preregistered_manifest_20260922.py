"""Persist the hash-bound M95 pre-registration in research_work.json."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK_PATH = ROOT / "pipeline" / "research_work.json"
EVIDENCE_PATHS = (
    "pipeline/diagnostic_runs/m95_identity_controls_20260922/manifest.json",
    "pipeline/reports/m95_preregistered_manifest_20260922-1320.json",
    "scripts/m95_preregistered_identity_controls_20260922.py",
    "scripts/test_m95_preregistered_identity_controls_20260922.py",
)
STATES = (
    (
        "referent-supervision-axis",
        "design",
        (
            "Pre-registered a frozen 256-expression native ScanRefer cohort: "
            "128 target-ambiguous and 128 class-unique expressions across 220 "
            "scenes and 85 normalized object classes. The contract fixes "
            "target-positive, target-objectness, class-matched-selector, "
            "class-matched-non-target, dominant-overlap, score-matched-pair, "
            "unknown-semantics, and no-fallback rules before any model outcome."
        ),
        (
            "Adapt the frozen M95 capture producer to select exactly the "
            "manifest rows and execute only when GPU7 has a safe project slot; "
            "then run the pre-registered paired identity controls. Do not "
            "enqueue a mechanism from the current 16-row cohort."
        ),
    ),
    (
        "referent-causality-audit",
        "diagnosis",
        (
            "The identity-causality route now has an outcome-independent "
            "manifest and a score-matched positive-versus-same-class-negative "
            "estimand. Execution is blocked only by foreign GPU7 occupancy, "
            "not by missing metadata or an undefined control."
        ),
        (
            "Implement manifest-bound row selection in the capture producer, "
            "run it on a safe GPU7 slot, and apply the frozen paired estimand "
            "without fallback; then update or reject the causal route."
        ),
    ),
    (
        "modality-identity-preservation",
        "diagnosis",
        (
            "The larger cohort pre-registers complete native target-class "
            "semantics and same-class non-target controls for raw, projected, "
            "and fused instance-identity analyses."
        ),
        (
            "After manifest-bound capture, test per-stage identity preservation "
            "with the same frozen rows and predeclared degradation criteria."
        ),
    ),
    (
        "referent-discrimination",
        "diagnosis",
        (
            "The cohort balances target-ambiguous and class-unique expressions "
            "so aggregate improvement cannot alone establish same-class "
            "referent discrimination."
        ),
        (
            "Run the class-matched and score-matched controls, retain only "
            "falsifiable same-class discrimination evidence, and do not derive "
            "a ranking variant from the bounded 16-row capture."
        ),
    ),
    (
        "instance-identity-representation",
        "diagnosis",
        (
            "The manifest fixes target and same-class peer identities before "
            "capture, allowing per-instance separability to be tested without "
            "using sampled semantic label -100 as a class substitute."
        ),
        (
            "After capture, require adequate per-instance support and report "
            "the final-stage target-versus-same-class margins on the frozen "
            "cohort before considering a mechanism."
        ),
    ),
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    document = json.loads(WORK_PATH.read_text(encoding="utf-8"))
    evidence = [
        {"path": path, "sha256": file_sha256(ROOT / path)}
        for path in EVIDENCE_PATHS
    ]
    by_id = {candidate["id"]: candidate for candidate in document["candidates"]}
    for candidate_id, stage, progress, next_action in STATES:
        if candidate_id not in by_id:
            raise ValueError("Missing research candidate " + candidate_id)
        candidate = by_id[candidate_id]
        candidate["stage"] = stage
        candidate["latest_progress"] = progress
        candidate["next_action"] = next_action
        existing = {
            item["path"]: item
            for item in candidate.setdefault("evidence", [])
            if isinstance(item, dict) and "path" in item
        }
        for item in evidence:
            existing[item["path"]] = item
        candidate["evidence"] = list(existing.values())
    document["updated_at"] = "2026-09-22T13:20:00+08:00"
    document["next_action"] = (
        "Adapt the frozen M95 capture producer to consume the hash-bound "
        "256-expression identity-control manifest, execute on a safe GPU7 "
        "project slot without evicting foreign work, and apply the frozen "
        "no-fallback paired controls before any mechanism admission."
    )
    document["last_event_tick"] = {
        "timestamp": "2026-09-22T13:20:00+08:00",
        "mode": "event",
        "due_ids": [item[0] for item in STATES],
        "evidence": evidence,
        "result": (
            "Resumed all due diagnosis/design stages on CPU. Generated and "
            "validated an outcome-independent 256-expression pre-registration "
            "with class-matched and score-matched controls. No capture ran "
            "because foreign GPU7 work occupied the device at 100%."
        ),
        "next_action": document["next_action"],
    }
    WORK_PATH.write_text(
        json.dumps(document, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({"updated": [item[0] for item in STATES],
                      "evidence": evidence}, sort_keys=True))


if __name__ == "__main__":
    main()
