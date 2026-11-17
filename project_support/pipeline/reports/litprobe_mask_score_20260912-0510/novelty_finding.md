================================================================================
  N1 Novelty Finding - cluster_project
  Candidate class: mask-conditioned candidate score / reranker
  Tick #20260912-0510, 2026-09-12 05:10
================================================================================

## 1. What Was Checked

The measured M95 failure is wrong-instance selection among physically distinct
same-category candidates. The selection score is query-only:

    z_q = indis_embedding(u_q)

while candidate masks are formed from a separate path:

    m_{q,n} = u_q dot f_n

The nearest obvious repair is a mask-conditioned or mask-quality-calibrated
candidate score. Before deriving that mechanism, this pass checked whether the
class is already standard prior art.

Method: read-only arXiv API query
(`pipeline/headless/n1_mask_score_litprobe_20260912.py`). Six relevance-sorted
queries were run and the raw records are in `arxiv_probe.json`. This is an
abstract-level screen, not a full-text verification.

## 2. Closest Prior Art

| Source | Established mechanism | Consequence for this project |
|--------|-----------------------|------------------------------|
| Mask Scoring R-CNN, arXiv 1903.00241 (2019) | A mask-IoU head takes the instance feature and predicted mask together, learns mask quality, and calibrates the classification score that would otherwise be used as the mask score. | Directly covers the simple "use candidate mask evidence to rescore the candidate" idea. The mismatch between classification confidence and mask quality is also its stated problem. |
| TransRefer3D, arXiv 2108.02388 (2021) | Explicit same-category distractor competition in 3D visual grounding. | Confirms that same-category competition is an established task framing, not a new problem statement. |
| Plain per-bank competition/ranking losses, including Rank & Sort Loss, arXiv 2107.11669 (2021) | Rank positives over negatives and order positives by localization quality. | A plain competition loss over candidate scores remains closed. |

The top hits for the 3D-specific mask-scoring queries were empty or unrelated.
That does not establish novelty for a 2D-standard operator transplanted into
3D: the mechanism class is already implemented by Mask Scoring R-CNN, and this
project has not identified a new computation graph beyond mask-conditioned
score calibration.

## 3. Finding

The simple mask-conditioned selector/reranker is not admissible as the core
mechanism. It is the standard null explanation for the measured discrepancy and
is now explicitly closed at the novelty gate.

The existing local coupling audit is consistent with this conclusion: the
selection and mask objectives are near-orthogonal at the frozen query state,
but that only proves that current supervision does not align them. It does not
make their alignment novel.

## 4. What Remains Unresolved

No new mechanism is admitted this tick. The remaining candidate directions are:

1. A primary-source-distinct score-field derivation that does more than attach
   mask quality to a candidate score; it must define a new information path and
   survive matched controls.
2. A bounded upstream decoder parameter-Jacobian protocol that measures whether
   selection and mask objectives conflict through shared decoder parameters,
   rather than only at the final head.

Neither direction is ready for implementation or queue entry. The first still
needs an exact derivation and primary-source distinction. The second still
needs a frozen capture protocol and a preregistered interpretation limit.

## 5. Limits

- Abstract-level arXiv screening only; Mask Scoring R-CNN was not full-text
  verified in this tick.
- No claim is made about all 3D-specific prior work. Absence in these queries
  is not evidence of novelty.
- No model, config, checkpoint, queue, scheduler, or training artifact changed.
- All conclusions remain bounded to validation-derived diagnostics; no test
  data was used for mechanism selection.

================================================================================
  Status: NEGATIVE SCREEN - mask-conditioned reranking not admitted
  Created: 2026-09-12 05:10 +08:00
================================================================================
