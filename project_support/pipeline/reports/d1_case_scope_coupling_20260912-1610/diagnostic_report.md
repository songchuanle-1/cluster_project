# D1 Fixed Case-Scope Coupling Audit

Completed 2026-09-12T16:11:43.601952 Asia/Shanghai. CPU-only join of frozen artifacts;
no inference, training, checkpoint write, GPU allocation, queue mutation, or
mechanism admission.

## Question

Does the narrow shared-anchor binding hypothesis explain the fixed M95
relation/attribute casebook, or do those errors remain candidate-score ordering
discrepancies outside that applicability domain?

## Sources And Integrity

| Artifact | SHA-256 |
|---|---|
| `scope_audit.json` | `08440c9ad7e359287e8f9a857ecde81eecdd3da485f8635e12f9d5ebba4be3ff` |
| `margin.json` | `8ae72f0a4b8e8ace386ae32b853848e5f5f27f3ccb7189f6d75538931be3c6eb` |
| `identity_geometry.json` | `ed61c14728a966720cff87904a3ac5a839f7423188c600dbed87b76fed86f6bd` |

The audit found and joined all 21 casebook descriptions for both models
(42 records) with no missing ID. The earlier authoring constraint is retained:
these are outcome-selected text readings, not a population sample or independent
annotation.

## Result

| Model / role | Cases | Recoverable | Success | Selected positive | Positive-usable correction | Same-semantic wrong instance |
|---|---:|---:|---:|---:|---:|---:|
| baseline / error | 12 | 7 | 5 | 6 | 5 | 3 |
| m95 / error | 12 | 12 | 0 | 0 | 12 | 7 |
| baseline / control | 9 | 0 | 9 | 9 | 0 | 0 |
| m95 / control | 9 | 0 | 9 | 9 | 0 | 0 |

For every fixed M95 error:

- a usable positive candidate exists;
- the target candidate's score gap to the selected candidate has a positive
  correction margin;
- the source selection objective's local margin velocity is negative; and
- none of the 21 text readings confirms two predicates bound to one shared
  anchor.

The M95 errors span
`{'comparison_domain_missing': 1, 'different_referents': 1, 'different_referents_attachment_ambiguous': 2, 'nested_chain': 1, 'scope_ambiguous': 1, 'single_relation': 5, 'unary_or_scene_relative': 1}`. The subset with one explicit relation
or a unary/comparison phrase contains
7 errors and 6 controls. All
6 controls succeed, while all 7 errors
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
