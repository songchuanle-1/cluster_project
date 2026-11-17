"""Resolve the eight event-mode referent work items without duplicating reviews.

The audit consumes only existing hashed evidence. It closes two axes whose
candidate mechanisms are unsupported, preserves one open design axis, and
records four native-evidence blockers with explicit unblock conditions.
"""

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_WORK = ROOT / "pipeline" / "research_work.json"
OUTPUT = ROOT / "pipeline" / "reports" / "referent_due_consolidation_20260922.json"
SHANGHAI = timezone(timedelta(hours=8))

SOURCE_EVIDENCE = (
    "pipeline/headless/.tick_context.json",
    "pipeline/reports/same_target_description_consistency_source_audit_20260917-1207.json",
    "pipeline/reports/modality_language_alignment_20260916.json",
    "pipeline/reports/modality_mean_summary_20260916.json",
    "pipeline/reports/modality_identity_claim_audit_20260916.json",
    "pipeline/reports/referent_control_coverage_20260918-1618.json",
    "pipeline/reports/design_admissibility_audit_20260919-0510.json",
)

RESOLUTIONS = (
    {
        "id": "same-target-description-grounding",
        "stage": "rejected",
        "disposition": "rejected_before_design",
        "reason": (
            "The same-target alternate-description set is already the explicit "
            "positive-supervision unit in TrackRef3D, and ViewRefer already "
            "constructs geometry-consistent alternate descriptions. The fixed "
            "sample has only 8 observable success disagreements, so the "
            "diagnostic does not create a distinct causal unit."
        ),
        "next_action": (
            "Do not reopen under same-target grounding, agreement, invariance, "
            "variance, multi-positive, or consistency naming."
        ),
        "evidence": (
            "pipeline/reports/same_target_description_consistency_source_audit_20260917-1207.json",
            "pipeline/reports/same_target_summary_20260916_metadata_corrected.json",
        ),
    },
    {
        "id": "referent-query-selection",
        "stage": "rejected",
        "disposition": "diagnosis_complete_not_admissible",
        "reason": (
            "Positive-only restriction confirms query selection is the "
            "actionable bottleneck, but selector and candidate-initialization "
            "changes are explicitly outside the research main line. Keep the "
            "diagnostic finding without treating another selector as a mechanism."
        ),
        "next_action": (
            "Retain selection as diagnostic context only. Do not create LGQS, "
            "selector, candidate-initialization, or renamed query-selection variants."
        ),
        "evidence": (
            "pipeline/reports/design_admissibility_audit_20260919-0510.json",
            "pipeline/reports/referent_control_coverage_20260918-1618.json",
        ),
    },
    {
        "id": "input-modality-distinguishability",
        "stage": "rejected",
        "disposition": "diagnosis_complete_not_admissible",
        "reason": (
            "The fixed native sample shows weak 2D language-instance alignment "
            "and no physical correspondence supplied by textual distinctions; "
            "broad modality perturbations harm more expressions than they "
            "rescue. Fusion and relation-conditioned identity transport are "
            "already closed or prior art, so separating inputs is not itself a mechanism."
        ),
        "next_action": (
            "Keep the measurements as diagnostic evidence. Do not reopen under "
            "modality preservation, cancelation, fusion, gating, or identity transport."
        ),
        "evidence": (
            "pipeline/reports/modality_language_alignment_20260916.json",
            "pipeline/reports/modality_mean_summary_20260916.json",
            "pipeline/reports/modality_identity_claim_audit_20260916.json",
        ),
    },
    {
        "id": "referent-supervision-axis",
        "stage": "open_no_candidate",
        "disposition": "open_axis",
        "reason": (
            "The supervision axis remains open under USER-SCOPE-B, but no "
            "candidate currently passes the causal-unit, novelty, control, and "
            "constraint gates."
        ),
        "next_action": (
            "Use the normal design-mode admission chain before admitting any "
            "successor. Do not fill capacity with a PIRS rename or tuning-only variant."
        ),
        "evidence": (
            "pipeline/reports/design_admissibility_audit_20260919-0510.json",
        ),
    },
    {
        "id": "referent-causality-audit",
        "stage": "blocked",
        "disposition": "external_blocker",
        "reason": (
            "The fail-closed target-rank evaluator and native projection are "
            "implemented, but the complete 123-expression native candidate-rank "
            "capture has not run. The current preflight reports server-6 unreachable."
        ),
        "next_action": (
            "When server-6 is reachable, verify code/data identity and GPU7 "
            "capacity, run the frozen native capture, project all rank-eligible "
            "expressions, and evaluate without imputation."
        ),
        "blocker": "server-6 was unreachable in the 05:07 monitor preflight.",
        "retry_after": "2026-09-22T06:20:00+08:00",
        "unblock_condition": (
            "Server-6 SSH succeeds and the allowed GPU7 has measured capacity "
            "without evicting foreign work."
        ),
        "alternatives_attempted": (
            "The read-only monitor preflight attempted reachability. The local "
            "projection/evaluator is already complete, and no unauthorized host fallback exists."
        ),
        "evidence": (
            "pipeline/reports/referent_target_rank_evaluator_20260919.json",
            "pipeline/reports/referent_native_expression_producer_20260919.json",
        ),
    },
    {
        "id": "referent-discrimination",
        "stage": "blocked",
        "disposition": "external_blocker",
        "reason": (
            "Exact same-class controls exist, but model-confusability and target "
            "rank require the frozen native candidate-rank capture. The current "
            "fixed support capture covers only 16 expressions and lacks the "
            "required target-independent objectness axis."
        ),
        "next_action": (
            "After the native capture unblocks, report target and same-class "
            "candidate ranks on the complete predeclared cohort with ties and "
            "missing coverage handled by the frozen fail-closed contract."
        ),
        "blocker": "server-6 was unreachable in the 05:07 monitor preflight.",
        "retry_after": "2026-09-22T06:20:00+08:00",
        "unblock_condition": (
            "Server-6 reachable, allowed GPU7 capacity measured, and complete "
            "same-forward candidate-rank evidence available."
        ),
        "alternatives_attempted": (
            "Reviewed the existing fixed-support evidence locally; it covers only "
            "16 expressions and lacks the required target-independent objectness axis."
        ),
        "evidence": (
            "pipeline/reports/referent_control_coverage_20260918-1618.json",
            "pipeline/reports/referent_target_rank_evaluator_20260919.json",
        ),
    },
    {
        "id": "instance-identity-representation",
        "stage": "blocked",
        "disposition": "external_blocker",
        "reason": (
            "The archived identity-loss proof was rejected, not the underlying "
            "hypothesis. A valid test needs paired raw/projected/fused/final "
            "features on identical physical support, including explicit controls."
        ),
        "next_action": (
            "Run the predeclared same-forward feature and candidate-rank capture "
            "before proposing any representation or identity-loss structure."
        ),
        "blocker": "server-6 was unreachable in the 05:07 monitor preflight.",
        "retry_after": "2026-09-22T06:20:00+08:00",
        "unblock_condition": (
            "Server-6 reachable and complete same-forward identity evidence "
            "captured against one frozen code/config/checkpoint identity."
        ),
        "alternatives_attempted": (
            "The archived identity-loss proof was independently rejected; the "
            "remaining hypothesis cannot be tested on the incomplete archived rows."
        ),
        "evidence": (
            "pipeline/reports/modality_identity_claim_audit_20260916.json",
            "pipeline/reports/modality_identity_separability_20260916.json",
        ),
    },
    {
        "id": "modality-identity-preservation",
        "stage": "blocked",
        "disposition": "external_blocker",
        "reason": (
            "Archived modality interventions prove that both paths affect "
            "grounding, but they are GT perturbations rather than a same-forward "
            "identity-preservation control. The current identity-loss proof is rejected."
        ),
        "next_action": (
            "Capture paired modality endpoints on exact physical support and "
            "test preservation with same-class controls before design."
        ),
        "blocker": "server-6 was unreachable in the 05:07 monitor preflight.",
        "retry_after": "2026-09-22T06:20:00+08:00",
        "unblock_condition": (
            "Server-6 reachable and the same-forward modality/identity control "
            "chain completes with hashed inputs and native backward evidence."
        ),
        "alternatives_attempted": (
            "Reviewed the completed GT-based modality interventions locally; "
            "they are not a same-forward identity-preservation control."
        ),
        "evidence": (
            "pipeline/reports/modality_mean_summary_20260916.json",
            "pipeline/reports/modality_identity_claim_audit_20260916.json",
        ),
    },
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _evidence(paths):
    records = []
    for relative_path in paths:
        absolute_path = ROOT / relative_path
        if not absolute_path.is_file():
            raise FileNotFoundError(absolute_path)
        records.append(
            {
                "path": relative_path.replace("\\", "/"),
                "sha256": file_sha256(absolute_path),
            }
        )
    return records


def build_resolution_report():
    timestamp = datetime.now(SHANGHAI).isoformat(timespec="seconds")
    resolutions = []
    for specification in RESOLUTIONS:
        item = dict(specification)
        item["evidence"] = _evidence(item["evidence"])
        resolutions.append(item)
    return {
        "schema_version": 1,
        "generated_at": timestamp,
        "scope": (
            "Event-mode bounded evidence consolidation; no model forward, "
            "training launch, admission, queue mutation, or efficacy claim."
        ),
        "source_evidence": _evidence(SOURCE_EVIDENCE),
        "resolutions": resolutions,
        "summary": {
            "due_items_reviewed": len(resolutions),
            "rejected": sum(item["stage"] == "rejected" for item in resolutions),
            "blocked": sum(item["stage"] == "blocked" for item in resolutions),
            "open_no_candidate": sum(
                item["stage"] == "open_no_candidate" for item in resolutions
            ),
            "queue_mutated": False,
            "training_launched": False,
        },
        "next_action": (
            "No due item remains actionable in event mode. External blockers "
            "record the required server-6 unblock condition; a later design-mode "
            "tick may review the open supervision axis without filling capacity "
            "with an inadmissible variant."
        ),
    }


def apply_resolution(research_work, resolution_report):
    candidates = {
        candidate["id"]: candidate for candidate in research_work["candidates"]
    }
    timestamp = resolution_report["generated_at"]
    for resolution in resolution_report["resolutions"]:
        candidate = candidates[resolution["id"]]
        candidate["stage"] = resolution["stage"]
        candidate["latest_progress"] = (
            timestamp
            + ": event-mode due resolution: "
            + resolution["disposition"]
            + ". "
            + resolution["reason"]
        )
        candidate["next_action"] = resolution["next_action"]
        candidate["due_resolution_20260922"] = {
            "disposition": resolution["disposition"],
            "reason": resolution["reason"],
            "evidence": resolution["evidence"],
            "blocker": resolution.get("blocker"),
            "retry_after": resolution.get("retry_after"),
            "unblock_condition": resolution.get("unblock_condition"),
            "alternatives_attempted": resolution.get("alternatives_attempted"),
        }

    research_work["last_event_tick"] = {
        "timestamp": timestamp,
        "mode": "event",
        "due_ids": [],
        "evidence": resolution_report["source_evidence"],
        "result": (
            "Reviewed all eight due axes without repeated gate work: three were "
            "rejected as candidate mechanisms, four were recorded as explicit "
            "external blockers, and the supervision axis remains open with no "
            "admissible candidate. The queue was not mutated."
        ),
        "next_action": resolution_report["next_action"],
    }
    research_work["next_action"] = resolution_report["next_action"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--research-work", type=Path, default=RESEARCH_WORK)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    research_work = json.loads(args.research_work.read_text(encoding="utf-8"))
    report = build_resolution_report()
    apply_resolution(research_work, report)

    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        report_relative_path = str(args.output.resolve().relative_to(ROOT)).replace(
            "\\", "/"
        )
        research_work["last_event_tick"]["evidence"] = [
            item
            for item in research_work["last_event_tick"]["evidence"]
            if item["path"] != report_relative_path
        ]
        research_work["last_event_tick"]["evidence"].append(
            {
                "path": report_relative_path,
                "sha256": file_sha256(args.output),
            }
        )
        args.research_work.write_text(
            json.dumps(research_work, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
    else:
        print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
