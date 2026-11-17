"""Persist the CPU paired identity diagnosis against the due research routes."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline" / "research_work.json"
REPORT = "pipeline/reports/m95_paired_identity_diagnosis_20260922-1008.json"
ANALYZER = "scripts/m95_paired_identity_diagnosis_20260922.py"
TEST = "scripts/test_m95_paired_identity_diagnosis_20260922.py"
TARGETS = {
    "referent-causality-audit",
    "referent-discrimination",
    "instance-identity-representation",
    "modality-identity-preservation",
}
EXPECTED = {
    REPORT: "5720c57f63deeaf0010df2e544fa7d81be09db2fc41e1a8124ac8047ce9b1cc7",
    ANALYZER: "b85ad4c5765961b7b344cc81fc00c0ce8df392c8946ebcde7638d8985ee65497",
    TEST: "d347e9562d32de9d5462b4a8dc20de5bd3e0fc85a3d8335f79f06f946c43345c",
}


def sha256(relative_path):
    digest = hashlib.sha256()
    with (ROOT / relative_path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_evidence(candidate, path, digest):
    evidence = candidate.setdefault("evidence", [])
    for item in evidence:
        if item.get("path") == path:
            item["sha256"] = digest
            return
    evidence.append({"path": path, "sha256": digest})


def main():
    hashes = {path: sha256(path) for path in EXPECTED}
    if hashes != EXPECTED:
        raise ValueError("Diagnosis artifact hashes differ from the frozen receipt")
    report = json.loads((ROOT / REPORT).read_text(encoding="utf-8"))
    summary = report["summary"]
    if summary["expressions"] != 16 or summary["selected_failures"] != 8:
        raise ValueError("Unexpected paired diagnosis denominator")
    identity = summary["identity_by_axis"]
    preservation = summary["modality_preservation"]
    progress = (
        "2026-09-22T10:08:00+08:00: completed CPU-only paired feature diagnosis "
        "on the frozen 16-expression/four-scene M95 same-forward capture. Of eight "
        "selected failures, zero have known target-vs-wrong class confusion, two "
        "have known same-class identity failure, and six are class-unresolved "
        "because the native per-point semantic label is missing. Seven failures "
        "retain eligible instance centroids: target-nearest-to-wrong counts were "
        "raw3d 1/7, raw2d 4/7, projected3d 1/7, projected2d 2/7, fused 3/7 and "
        "final 1/7; final median target rank was 9. Pairwise similarity preservation "
        "was raw2d->projected2d Spearman %.3f with nearest agreement %.3f, "
        "raw3d->projected3d %.3f/%.3f, and fused->final %.3f/%.3f. This is bounded "
        "diagnosis only, not population, admission, efficacy or novelty evidence."
        % (
            preservation["raw_2d->projected_2d"]["spearman"]["mean"],
            preservation["raw_2d->projected_2d"]["nearest_agreement"]["mean"],
            preservation["raw_3d->projected_3d"]["spearman"]["mean"],
            preservation["raw_3d->projected_3d"]["nearest_agreement"]["mean"],
            preservation["fused->final"]["spearman"]["mean"],
            preservation["fused->final"]["nearest_agreement"]["mean"],
        )
    )
    next_actions = {
        "referent-causality-audit": (
            "Pre-register a larger same-forward manifest that separates native "
            "referent identity from an objectness control matched on candidate "
            "class and physical support. Do not enqueue or claim admission."
        ),
        "referent-discrimination": (
            "Expand the pre-registered same-forward capture with complete native "
            "target/wrong/acceptable-query semantic identities. Treat the six "
            "missing-semantic failures as unresolved, not class confusion. No "
            "queue mutation."
        ),
        "instance-identity-representation": (
            "Use the feature-only result to pre-register a larger identity "
            "separability test with adequate per-instance support and paired "
            "same-class controls; retain final-stage identity preservation as a "
            "falsifiable hypothesis, not an admitted mechanism."
        ),
        "modality-identity-preservation": (
            "Pre-register a larger same-forward preservation test for raw versus "
            "projected/fused identity relations, with per-modality controls and "
            "predefined degradation criteria. No queue mutation or fusion variant."
        ),
    }

    work = json.loads(WORK.read_text(encoding="utf-8"))
    touched = []
    for candidate in work["candidates"]:
        candidate_id = candidate.get("id")
        if candidate_id not in TARGETS:
            continue
        if candidate.get("stage") != "diagnosis":
            raise ValueError("Expected diagnosis stage for " + candidate_id)
        candidate["latest_progress"] = progress
        candidate["next_action"] = next_actions[candidate_id]
        candidate["paired_identity_diagnosis_20260922"] = {
            "report": REPORT,
            "report_sha256": hashes[REPORT],
            "analyzer": ANALYZER,
            "analyzer_sha256": hashes[ANALYZER],
            "test": TEST,
            "test_sha256": hashes[TEST],
            "tests_passed": 6,
            "expressions": 16,
            "scenes": 4,
            "known_class_confusion_failures": summary[
                "known_class_confusion_failures"
            ],
            "known_same_class_identity_failures": summary[
                "known_same_class_identity_failures"
            ],
            "class_unresolved_failures": summary["class_unresolved_failures"],
            "identity_eligible_failures": identity["final"]["eligible_failures"],
            "final_target_nearest_to_wrong": identity["final"][
                "target_nearest_to_wrong"
            ],
            "final_median_target_rank_to_wrong": identity["final"][
                "median_target_rank_to_wrong"
            ],
            "admission": False,
        }
        for path, digest in hashes.items():
            add_evidence(candidate, path, digest)
        touched.append(candidate_id)
    if set(touched) != TARGETS:
        raise ValueError("Target set mismatch: %s" % sorted(touched))

    for candidate in work["candidates"]:
        if candidate.get("id") != "referent-supervision-axis":
            continue
        candidate["latest_progress"] = (
            "2026-09-22T10:08:00+08:00: paired diagnosis completed, but no "
            "queue-ready successor exists. Six of eight failures have unresolved "
            "semantics and final-stage identity controls remain bounded to seven "
            "eligible failures; do not promote a design candidate or fill capacity."
        )
        add_evidence(candidate, REPORT, hashes[REPORT])
        break

    work["next_action"] = (
        "Continue the four diagnosis routes with a larger pre-registered "
        "same-forward manifest and complete semantic identities. Do not enqueue "
        "or launch a mechanism from the bounded paired result."
    )
    work["updated_at"] = "2026-09-22T10:08:00+08:00"
    with WORK.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(work, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(
        "updated %d diagnosis candidates; report=%s"
        % (len(touched), hashes[REPORT][:12])
    )


if __name__ == "__main__":
    main()
