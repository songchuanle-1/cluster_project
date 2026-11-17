================================================================================
  D3 Geometry Analysis - cluster_project
  What shape is the wrong-instance error?
  Tick #20260911-2307, 2026-09-11 23:07
================================================================================

## 1. Question

D2 established that recoverable failures are wrong-instance selections that grow
with same-category competition. Before designing anything, the mechanism shape
depends on the geometry: is the wrong candidate a *part* of the correct object,
a *merge* of several objects, a near-duplicate the ranking could not separate,
or a *different, disjoint* object?

These four cases need four completely different mechanisms (part-whole
comparison, merge suppression, tie-breaking/deduplication, cross-object
discrimination). Measuring which one dominates eliminates the other three.

## 2. Method

CPU-only pass over the same 568 frozen banks, no model load, no inference, no
CUDA, no dataset sample:

    pipeline/headless/d3_mask_overlap_20260911.py
    -> pipeline/reports/d2_competition_20260911-2207/mask_overlap.json
    (sha256 ef916609ae3b11b28f237c0970cc7e9d9851418ed2ee679ce4b30f78d6f96742)

Masks are binarized at `sigmoid(logit) >= 0.5` on the bank's 1946 superpoints.
`relation` compares the selected candidate's binary mask with the oracle
candidate's binary mask: `disjoint` (empty intersection), `small_overlap`
(intersection below half of either mask), `partial_overlap`, `strict_subpart`
(selected covers >=90% of oracle but is itself <60% of oracle's size),
`superset_or_merge` (the mirror), `near_duplicate` (mutual coverage >=90%).

## 3. Result

M95-CTF-HCG-CSORT, recoverable banks (n = 111, the actual error population):

| Relation of selected mask to oracle mask | Banks | Fraction |
|------------------------------------------|-------|----------|
| disjoint - a different object entirely   | 89    | 0.802    |
| small_overlap                            | 11    | 0.099    |
| partial_overlap                          | 7     | 0.063    |
| superset_or_merge                        | 2     | 0.018    |
| strict_subpart                           | 2     | 0.018    |

    median selected-mask precision inside GT : 0.000
    mean   selected-mask precision inside GT : 0.057
    fraction of wrong masks <50% inside GT   : 0.946
    median containment of oracle by selected : 0.000

model_base1, recoverable banks (n = 90): disjoint 77 (0.856), small_overlap 6,
partial_overlap 5, superset_or_merge 2, strict_subpart 0; median selected-mask
precision inside GT 0.000; 0.944 of wrong masks are <50% inside GT.

For contrast, M95 success banks (n = 158) are 0.722 near_duplicate and 0.234
partial_overlap: when selection succeeds, the selected mask *is* essentially the
oracle mask. So the bank already contains the right mask in both strata; only
the ranking differs.

## 4. What This Eliminates

| Mechanism family | Verdict | Evidence |
|------------------|---------|----------|
| Part-vs-whole / sub-part selection | eliminated | strict_subpart is 2/111 = 0.018 |
| Merge / over-cover suppression | eliminated | superset_or_merge is 2/111 = 0.018 |
| Near-duplicate tie-breaking or dedup | eliminated here | those cases are the *success* stratum (0.722); no error to fix |
| Overlap-based re-scoring (soft-NMS family) | eliminated | 80.2% of wrong masks have empty intersection with the correct mask, so any overlap-derived penalty is identically zero |
| Per-bank calibration / normalization | eliminated (D2 proof) | argmax is invariant under strictly increasing score transforms |
| Plain per-bank ranking / contrastive loss | not novel (N1) | RS Loss 2107.11669 already ranks positives above negatives and sorts by IoU |

The residual is therefore, precisely: **the wrong candidate is a spatially
disjoint, different physical object of the same category, it wins by a large
score margin (median 0.546 logits), and its mask has essentially no overlap with
the correct one.** The bank contains the right mask; the score field does not
identify it.

## 5. Limitation

- Binarization threshold 0.5 matches the frozen protocol; a probabilistic
  overlap measure might move some borderline cases between `small_overlap` and
  `partial_overlap`, but cannot create sub-part or merge cases at the observed
  scale (2/111 each).
- `near_duplicate` on success banks partly reflects that the oracle and the
  selected candidate are often both fine local refinements of the same region.
- Same 568 validation-derived banks as D1/D2; exploratory, not independent.

================================================================================
