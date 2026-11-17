"""Join the fixed relation/attribute casebook to frozen selection diagnostics."""
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path


ROOT = Path("D:/project/cluster_project")
PIPELINE = ROOT / "pipeline"
REPORTS = PIPELINE / "reports"
SCOPE_PATH = REPORTS / "binding_scope_20260911-1012" / "scope_audit.json"
MARGIN_PATH = REPORTS / "d1_margin_20260911-1410" / "margin.json"
IDENTITY_PATH = REPORTS / "d1_identity_20260911-0912" / "identity_geometry.json"
OUT = REPORTS / "d1_case_scope_coupling_20260912-1610"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def key(scene_id, object_id, ann_id):
    return scene_id, str(object_id), str(ann_id)


def main():
    assert not OUT.exists(), OUT
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    margin = json.loads(MARGIN_PATH.read_text(encoding="utf-8"))
    identity = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))

    identity_sha = sha256(IDENTITY_PATH)
    assert scope["source_sha256"] == identity_sha
    assert margin["status"] == "complete"
    assert identity["status"] == "complete"

    margin_index = {
        (row["model"], *key(row["scene_id"], row["object_id"], row["ann_id"])): row
        for row in margin["rows"]
    }
    identity_index = {
        (row["model"], *key(row["scene_id"], row["object_id"], row["ann_id"])): row
        for row in identity["rows"]
    }
    assert len(margin_index) == 568
    assert len(identity_index) == 42

    records = []
    for case in scope["rows"]:
        case_key = key(case["scene_id"], case["object_id"], case["ann_id"])
        for model in ("baseline", "m95"):
            margin_row = margin_index.get((model, *case_key))
            identity_row = identity_index.get((model, *case_key))
            assert margin_row is not None and identity_row is not None
            positive = margin_row.get("positive_usable") or {}
            usable = margin_row.get("usable") or {}
            records.append({
                "model": model,
                "scene_id": case["scene_id"],
                "object_id": case["object_id"],
                "ann_id": case["ann_id"],
                "role": case["role"],
                "scope": case["scope"],
                "description": case["description"],
                "same_pair_shared_witness_confirmed": case["same_pair_shared_witness_confirmed"],
                "stratum": margin_row["stratum"],
                "selected_positive": margin_row["selected_positive"],
                "selected_iou": margin_row["selected_iou"],
                "oracle_iou": margin_row["oracle_iou"],
                "positive_count": margin_row["positive_count"],
                "usable_margin": usable.get("margin"),
                "positive_usable_margin": positive.get("margin"),
                "positive_usable_velocity": positive.get("margin_velocity"),
                "same_semantic_wrong_instance": identity_row.get("overlap_label") == "wrong_instance_same_semantic",
                "winner_label": identity_row.get("winner_label"),
                "target_label": identity_row.get("target_label"),
                "lexical_candidate_count": len(identity_row.get("lexical_object_candidates", [])),
            })

    assert len(records) == 42
    assert Counter((row["role"], row["model"]) for row in records) == {
        ("error", "baseline"): 12,
        ("control", "baseline"): 9,
        ("error", "m95"): 12,
        ("control", "m95"): 9,
    }

    by_model_role = {}
    for model in ("baseline", "m95"):
        for role in ("error", "control"):
            group = [row for row in records if row["model"] == model and row["role"] == role]
            by_model_role[f"{model}_{role}"] = {
                "cases": len(group),
                "recoverable": sum(row["stratum"] == "recoverable" for row in group),
                "success": sum(row["stratum"] == "success" for row in group),
                "selected_positive": sum(row["selected_positive"] for row in group),
                "with_positive_usable": sum(row["positive_usable_margin"] is not None for row in group),
                "with_corrective_margin": sum(
                    row["positive_usable_margin"] is not None
                    and row["positive_usable_margin"] > 0
                    and row["positive_usable_velocity"] is not None
                    and row["positive_usable_velocity"] < 0
                    for row in group
                ),
                "same_semantic_wrong_instance": sum(
                    row["same_semantic_wrong_instance"] for row in group
                ),
                "scopes": dict(sorted(Counter(row["scope"] for row in group).items())),
            }

    m95_errors = [
        row for row in records if row["model"] == "m95" and row["role"] == "error"
    ]
    m95_controls = [
        row for row in records if row["model"] == "m95" and row["role"] == "control"
    ]
    assert len(m95_errors) == 12 and len(m95_controls) == 9
    assert all(row["stratum"] == "recoverable" for row in m95_errors)
    assert all(row["positive_usable_margin"] is not None for row in m95_errors)
    assert all(row["positive_usable_margin"] > 0 for row in m95_errors)
    assert all(row["positive_usable_velocity"] < 0 for row in m95_errors)
    assert all(row["stratum"] == "success" for row in m95_controls)
    assert all(row["selected_positive"] for row in m95_controls)
    assert not any(row["same_pair_shared_witness_confirmed"] for row in records)

    simple_errors = [
        row for row in m95_errors
        if row["scope"] in {
            "single_relation",
            "unary_or_scene_relative",
            "comparison_domain_missing",
        }
    ]
    simple_controls = [
        row for row in m95_controls
        if row["scope"] in {
            "single_relation",
            "unary_or_scene_relative",
            "comparison_domain_missing",
        }
    ]

    result = {
        "status": "complete",
        "created": datetime.now().isoformat(),
        "purpose": (
            "Test whether the fixed M95 relation/attribute errors are explained by "
            "the narrow shared-anchor applicability claim, or remain a broader "
            "candidate-score ordering discrepancy."
        ),
        "sources": {
            "scope_audit": str(SCOPE_PATH),
            "scope_audit_sha256": sha256(SCOPE_PATH),
            "margin": str(MARGIN_PATH),
            "margin_sha256": sha256(MARGIN_PATH),
            "identity_geometry": str(IDENTITY_PATH),
            "identity_geometry_sha256": identity_sha,
        },
        "assertions": {
            "scope_rows": len(scope["rows"]),
            "joined_records": len(records),
            "m95_errors_recoverable": len(m95_errors),
            "m95_errors_with_positive_usable": len(m95_errors),
            "m95_errors_with_corrective_score_margin": sum(
                row["positive_usable_margin"] > 0 and row["positive_usable_velocity"] < 0
                for row in m95_errors
            ),
            "m95_controls_success": len(m95_controls),
            "same_pair_shared_witness_confirmed": 0,
        },
        "model_role_summary": by_model_role,
        "m95_simple_relation_or_attribute": {
            "errors": len(simple_errors),
            "controls": len(simple_controls),
            "error_scopes": dict(sorted(Counter(row["scope"] for row in simple_errors).items())),
            "control_scopes": dict(sorted(Counter(row["scope"] for row in simple_controls).items())),
        },
        "records": records,
    }
    OUT.mkdir(parents=True)
    (OUT / "case_scope_coupling.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )

    report = f"""# D1 Fixed Case-Scope Coupling Audit

Completed {result['created']} Asia/Shanghai. CPU-only join of frozen artifacts;
no inference, training, checkpoint write, GPU allocation, queue mutation, or
mechanism admission.

## Question

Does the narrow shared-anchor binding hypothesis explain the fixed M95
relation/attribute casebook, or do those errors remain candidate-score ordering
discrepancies outside that applicability domain?

## Sources And Integrity

| Artifact | SHA-256 |
|---|---|
| `scope_audit.json` | `{result['sources']['scope_audit_sha256']}` |
| `margin.json` | `{result['sources']['margin_sha256']}` |
| `identity_geometry.json` | `{result['sources']['identity_geometry_sha256']}` |

The audit found and joined all 21 casebook descriptions for both models
(42 records) with no missing ID. The earlier authoring constraint is retained:
these are outcome-selected text readings, not a population sample or independent
annotation.

## Result

| Model / role | Cases | Recoverable | Success | Selected positive | Positive-usable correction | Same-semantic wrong instance |
|---|---:|---:|---:|---:|---:|---:|
| baseline / error | 12 | {by_model_role['baseline_error']['recoverable']} | {by_model_role['baseline_error']['success']} | {by_model_role['baseline_error']['selected_positive']} | {by_model_role['baseline_error']['with_corrective_margin']} | {by_model_role['baseline_error']['same_semantic_wrong_instance']} |
| m95 / error | 12 | {by_model_role['m95_error']['recoverable']} | {by_model_role['m95_error']['success']} | {by_model_role['m95_error']['selected_positive']} | {by_model_role['m95_error']['with_corrective_margin']} | {by_model_role['m95_error']['same_semantic_wrong_instance']} |
| baseline / control | 9 | {by_model_role['baseline_control']['recoverable']} | {by_model_role['baseline_control']['success']} | {by_model_role['baseline_control']['selected_positive']} | {by_model_role['baseline_control']['with_corrective_margin']} | {by_model_role['baseline_control']['same_semantic_wrong_instance']} |
| m95 / control | 9 | {by_model_role['m95_control']['recoverable']} | {by_model_role['m95_control']['success']} | {by_model_role['m95_control']['selected_positive']} | {by_model_role['m95_control']['with_corrective_margin']} | {by_model_role['m95_control']['same_semantic_wrong_instance']} |

For every fixed M95 error:

- a usable positive candidate exists;
- the target candidate's score gap to the selected candidate has a positive
  correction margin;
- the source selection objective's local margin velocity is negative; and
- none of the 21 text readings confirms two predicates bound to one shared
  anchor.

The M95 errors span
`{by_model_role['m95_error']['scopes']}`. The subset with one explicit relation
or a unary/comparison phrase contains
{len(simple_errors)} errors and {len(simple_controls)} controls. All
{len(simple_controls)} controls succeed, while all {len(simple_errors)} errors
are recoverable selection failures. This is a fixed-case contrast, not a
population effect estimate.

## Interpretation

The narrow shared-anchor hypothesis has no confirmed case in this sample and
does not cover the observed M95 failures. The result instead reinforces a
broader discrepancy: some fixed descriptions with a single relation, or even
mostly unary attributes, select a wrong same-label instance despite an
available target candidate that already receives corrective score supervision.

This does not show that the relation/attribute representations are wrong,
that the target candidate should win, or that a new reranker would generalize.
The casebook was selected from M95 outcomes, the text scope notes are not
blinded, and the positive-usable correction is a local objective direction.

## Decision

Do not admit a shared-anchor mechanism. Close the fixed-case applicability
check as a negative diagnostic and make no queue or model change. The next
admissible work must identify a measured error that is non-equivalent to
established mask-conditioned scoring, ranking, relation modeling, or generic
query-selection supervision.
"""
    (OUT / "diagnostic_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(result["assertions"], indent=2))


if __name__ == "__main__":
    main()
