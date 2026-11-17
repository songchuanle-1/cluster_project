================================================================================
  N1 Novelty Finding - cluster_project
  Candidate class: per-bank ranking / candidate-competition supervision
  Tick #20260911-2207, 2026-09-11 22:07
================================================================================

## 1. What Was Checked

The D2 diagnostic (`reports/d2_competition_20260911-2207/`) shows the dominant
residual is wrong-instance selection that scales with same-category distractor
count (M95 fail rate 0.088 / 0.324 / 0.625 / 0.826 at 0 / 1-2 / 3-5 / 6-10
distractors). The obvious response is a supervision change that ranks each
candidate against competing same-category candidates. Before any derivation or
config, this pass asks whether that class is already established prior art.

Method: arXiv API title/abstract probe (`arxiv_probe.json`, six queries, run
2026-09-11 22:07). This is an abstract-level screen, **not** full-text
verification. No quotes or claims are attributed beyond the retrieved
abstracts.

## 2. Closest Prior Art

| Source | What it already does | Overlap with a competition-loss proposal |
|--------|----------------------|-------------------------------------------|
| Rank & Sort Loss for Object Detection and Instance Segmentation, arXiv 2107.11669 (2021) | Supervises the detector classifier to rank each positive above all negatives **and** sort positives among themselves by localization quality (IoU) | Direct. This is per-bank ranking supervision with IoU-derived ordering, i.e. the proposed mechanism class in its plain form. |
| TransRefer3D, arXiv 2108.02388 (2021) | States the task as identifying the referred object "from other distractive objects of the same category"; entity-and-relation aware transformer | The problem statement (same-category distractor competition) is already explicit in 3D VG, not a new problem framing. |
| LSVG, arXiv 2505.04058 (2025) | Language-guided scene graphs with "referred object discrimination" to distinguish multiple similar objects through described spatial relations | Same-category disambiguation via relational evidence is already a published 3D VG mechanism. |
| ConcreteNet / Four Ways to Improve Verbo-visual Fusion, arXiv 2309.04561 (2023) | Dense 3D visual grounding (referral-based 3D instance segmentation), four fusion improvements, distractor-aware supervision | Occupies the dense-3D-Referring-segmentation slot this project targets. |

## 3. Finding

**A plain per-bank ranking / contrastive / IoU-sorted competition loss is not a
novel core contribution.** RS Loss already supervises exactly that, including
sorting by localization quality, and same-category distractor disambiguation is
an explicit, long-standing framing in 3D VG (TransRefer3D) and in recent work
(LSVG). Proposing it as the project's core novelty would not survive review.

This is a rejection of a mechanism class, recorded before any GPU time, model
package or config was created.

## 4. What Remains Admissible (Not Yet A Proposal)

The D2 evidence still stands: the residual is wrong-instance selection under
same-category competition, and the score margin is large (median 0.546 logits
on recoverable vs 0.095 on success), so calibration of the existing score is
provably insufficient. A future candidate must therefore change the score
*field*. The only structurally distinctive asset this project has that the
above prior art does not assume is its learned multi-scale cluster hierarchy
(CTF/HCG/CSORT).

A candidate that derives its competitor set from that hierarchy (e.g. siblings
sharing a learned ancestor) and its evidence from within-candidate occupancy
structure would need its own N1 check against part-based / hierarchical
discrimination literature before it can be admitted. That check has **not**
been run. No derivation, config or queue entry exists for it.

## 5. Missing Prerequisites (must stay visible)

- Abstract-level screen only; no full-text reading of 2107.11669, 2108.02388,
  2505.04058, 2309.04561. Semantic Scholar / OpenReview / CVF full text not checked.
- No check yet for hierarchical or part-based competitor-set losses in 3D VG or
  in point-cloud instance segmentation.
- No derivation, gradient/degeneracy test, matched control or preregistered
  rejection threshold for any successor mechanism.
- Therefore: no mechanism is admitted this tick; no training, config, model
  package, checkpoint or queue change was made.

================================================================================

## 6. Follow-up Screen: Hierarchy-Derived Competitor Sets (tick 23:07)

Second abstract-level arXiv probe, `pipeline/headless/n1_hierarchy_litprobe_20260911.py`
-> `pipeline/reports/litprobe_hierarchy_20260911-2307/arxiv_probe.json`, six
queries on hierarchical/part-based competitor sets, part-aware 3D grounding,
hierarchical grouping + discrimination, and superpoint contrastive learning.

Result: **no direct hit** on "competitor set derived from a learned multi-scale
hierarchy, used to discriminate same-category instances in 3D visual grounding".
Nearest neighbours are hierarchical contrastive learning in other domains
(text classification 2310.05128, relation extraction 2205.02225, time series
2212.01141, multi-level SupCon 2502.02202), part-aware 3D grounding on a
different axis (Kestrel 2405.18937, PAR3D 2606.06485), and superpoint
contrastive/relation work (Relation3D 2506.17891, graph-structured deep metric
learning 1904.02113).

**This is a negative screen, not a novelty pass.** Six relevance-sorted queries
returning no direct hit is weak evidence of absence. D3
(`reports/d2_competition_20260911-2207/mask_overlap_analysis.md`) has since shown
that the wrong candidates are spatially *disjoint* other objects (80.2%), not
parts or merges; so a hierarchy-derived competitor set would have to group
genuinely different objects at a coarse level, which is a much weaker story than
grouping parts of one object. The hierarchy angle is **unresolved and not
admitted**; it is not a novelty claim.

================================================================================
