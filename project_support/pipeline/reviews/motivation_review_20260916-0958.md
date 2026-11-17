# Motivation Review - Which Existing Evidence Can Identify The Referent?
2026-09-16 09:58 Asia/Shanghai. Diagnostics only; nothing admitted.

## 1. Goal
pipeline/goal.json authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact .5024607181549072@16; Phase 1 NOT YET.
The previously established bottleneck is referent identification: 33 of 38
fixed-forward failures already contain a query whose mask exceeds IoU 0.5 with the
target, and 28 of 33 selected masks have exactly zero overlap with it.

## 2. Question This Review Settles
Before deriving a mechanism, decide whether the missing discrimination is already
present in some trained signal that is simply not used by the deployed argmax. If
it is, the fix is a readout change. If it is not present anywhere, the mechanism
must *create* discriminative evidence, which is a supervision/landscape change.

## 3. Evidence: Query-Level Scalars Fail
| Signal | median rank of correct query | top-1 rate |
|---|---|---|
| indis (deployed) | 12 | 0% |
| mask-score head | 13 | 6.1% |
| sampling language-point correlation | 13 | 9.1% |

## 4. Evidence: Region-Level Language Scoring Fails
Mask-weighted pooling of the final encoder features, scored by the model's own
trained projections:

| Variant | median rank of correct query | top-5 rate |
|---|---|---|
| trained text projection, region feature (sem_region) | 101 | 3.0% |
| trained sampling matcher, region pooling (camap_region) | 55 | 12.1% |
| trained sampling matcher, max over mask points | 60 | 9.1% |
| trained sampling matcher, mean over mask points | 66 | 12.1% |
| unprojected region vs text centroid | 70 | 15.2% |
| unprojected query vs text centroid | 103 | 0% |

Score margins are ~1e-3, i.e. noise. Region-level language scoring, the obvious
"known-good" repair, does not rank the correct query either. Two consequences: it
cannot be assumed to fix efficacy here, and it is anyway prior art.

## 5. Evidence: Phrase-Group Scoring Fails
15 combinations of the dataset's own token maps (referent mention, modifiers,
pronouns, other entities, relations) with three operators (trained query/text
projection, trained point-language matcher pooled over the predicted mask,
unprojected cosine to the group centroid):

| Group | tokens present (of 33) | best median rank across operators | best top-1 |
|---|---|---|---|
| referent mention | 33 | 14 | 0% |
| modifiers | 26 | 22 | 7.7% |
| pronouns | 24 | 22 | 4.2% |
| other entities | 31 | 14 | 3.2% |
| relations | 29 | 19 | 3.4% |

No group and no operator ranks the correct query usefully. Compositional scoring of
existing features does not recover the discrimination either.

## 6. Evidence: The Structural Signal Exists In The Data
Joining the fixed-forward outcomes with the audited expression structure:

| Outcome | n | has content relation | has other entity | has attribute contrast | no usable signal |
|---|---|---|---|---|---|
| success | 85 | 65 | 83 | 44 | 2 |
| recoverable | 33 | 29 | 31 | 21 | 2 |
| mask-limited | 5 | 3 | 4 | 2 | 0 |

31 of 33 recoverable failures carry a relation, another mentioned entity, or an
attribute contrast, so the information needed to separate the target from a
same-name neighbour is present in the annotation. It is the model that does not
use it.

## 7. Root Cause Located In The Supervision, Not Only The Head
`Criterion.match_sampled_ins` defines the referent positives as
(a) the single query nearest the GT object centroid, plus (b) **every query whose
sampled seed superpoint carries the GT instance id**. Mask agreement is never a
condition. `loss_indi` then trains a two-way classifier on exactly that set.

Consequences:
- The referent head is trained as "is my seed point inside the referred object",
  a *point-level* question, while the deployed decision is an *object-level*
  question among same-name neighbours a median 2.03 m apart.
- The head's only input is the query embedding, which is built from the seed's
  local geometry and the global language representation. It receives no
  information about the extent of the object it hypothesises.
- Every measured scalar fails in the same way because none of them is asked to
  answer the object-level question during training.

## 8. Conclusion And What The Mechanism Must Do
Recombining, re-projecting, re-weighting or re-ranking existing evidence is
exhausted as a route: 8 query/region variants and 15 phrase-group variants all
leave the correct query near uniform rank. This is consistent with the goal's
banned families (ranking, contrastive, IoU competition, semantic projection,
reranking) having failed historically.

A candidate mechanism must therefore change what the referent decision is
*trained* to be: an object-hypothesis question rather than a seed-point question,
without adding a separate detection or annotation source, and within the
remaining FLOPs budget (~0.24 G of the 10 G historical cap).

## 9. Next Batch
-> see pipeline/designs/exp_design_20260916-0958.md
Status: DIAGNOSTIC COMPLETE / EXISTING-EVIDENCE ROUTES CLOSED / NOT ADMITTED.
