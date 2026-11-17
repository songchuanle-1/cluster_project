# Motivation Review - Category Spatial Fields
2026-09-16 05:58 Asia/Shanghai. Not an admission.

## 1. Goal
Authoritative goal: pipeline/goal.json, unchanged (14 constraints, 11 bans).
Phase1 target .51; exact M95 .5024607181549072. check_goal at05:57 NOT YET.
Raw TRAIN category annotations available; no new labels or inference GT allowed.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Category supervision unavailable | corrected | raw_semantic_identity_20260916.json | none; do not re-audit |
| Category field resolves referent identity | insufficient alone | category_field_contract_20260916.json | instance partition |
| Learned geometry improves current failures | unverified | prior fixed123 TRAIN diagnosis | complete trainable mechanism |

## 3. Experiment Assessment
Baseline .4894491136, M95 .5024607182; M195 .4986896217 does not improve champion.
M196 remains running, native log observed epoch22 step2225 at05:57.
No new model or training result this continuation.

## 4. Gap Analysis
Raw semantic labels remove the unavailable-supervision objection, not instance
binding ambiguity. A category union and every deterministic distance transform
of that union discard its instance partition. Target exclusion does not recover
the partition of other instances. Synthetic test gives identical fields for
one versus two objects, with different same-instance conjunction truth.
This is an explicit support-predicate counterexample, not measured ScanRefer
error prevalence and not a rejection of fields used alongside instance features.

## 5. Design Rationale
Original papers downloaded and read:
- Position3D, CVPR2026 pp39488-39490, equations3-29: local proxy aggregation,
  pair relative-coordinate encoding, center refinement and shrinking nearest
  support attention, center supervision. Explicit geometry alone is not novel.
- ORD, CVPR2026 pp30966-30968, equations1-22: object-pair direction/length,
  predicate-only alignment, auxiliary anchor slots and anchor supervision.
  Generic predicate decoupling plus category/anchor supervision is not novel.
- 3D-CG, arXiv2207.06403v1 section3.1: coordinate descriptor/concept similarity,
  filter/query/count operators and slots for instance counting. Category neural
  fields are not themselves new. No claim it implements our distance transform.
These are whole-method comparisons, not automatic rejection of standard pieces.
Position3D author is Wang; initial guessed Li CVF URL404, recovered from index.
Web search returned no usable result; primary CVF/arXiv retrieval succeeded.

## 6. Next Batch
Category-union-only mechanism fails its instance-binding rationale; do not
implement it as a classifier plus distance reranker. Preserve full diagnosis
work as active. Next candidate must retain observable instance evidence, specify
its training objective and inference inputs, and differ from closed shared-witness,
generic relation classification and ORD/CoT3DRef anchor supervision.
Native backward/resources/independence/admission remain incomplete.
