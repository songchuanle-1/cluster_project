# Motivation Review: Point Detail Conservation

## 1. Goal
The full controlling goal is pipeline/goal.json, unchanged this tick: ScanRefer
Phase1 mIoU >=0.5100, baseline0.4894, champion0.5020, gap0.0080.
All18 constraints/11 bans remain; server-6 GPU7/two slots only.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Original partitions cannot represent targets | Rejected historically | Original point-level oracle min0.969 | Not this proposal |
| Two old scenes expose mixed point boundaries | Disconfirmed | 83 expressions,zero mixed SPs | Preserve negative finding |
| Independent TRAIN scenes expose lost point detail | Observed | Hash-frozen32 scenes/128 expressions,19 mixed targets with feature detail | Native intervention/backward/resources |
| New point field improves VAL mIoU | Untested | No training | Full frozen evaluation |

## 3. Experiment Assessment
| Experiment | mIoU | Role | Contribution |
|---|---|---|---|
| model_base1 | .4894 | Baseline | Comparator |
| M95-CTF-HCG-CSORT | .5020 | Champion | Parent structure and checkpoint diagnostic |
| M197-PIRS | .4920@27/50 stopped_unknown | Closed prior axis | No restart/no ranking successor |

## 4. Gap Analysis
The native head predicts constant logits inside every SP, despite raw backbone
point differences and real mixed point labels in independent TRAIN scenes.
This is a representational restriction, not an inference-label bug or an
untrained benefit claim. No need to re-partition or alter candidate selection.
Boundary incidence alone does not establish expected population improvement.

## 5. Design Rationale
Project motivation is to diagnose coverage/boundaries, identity/relations and
repeated evidence before selecting one lightweight structural mechanism.
Select the point-detail null space of mean pooling. Constrain its SP mean to
zero so the new readout cannot simply relearn a coarse score or a scalar shift.
History's centroid-graph/BCCA/repartition and cluster-residual interventions
did not evaluate this raw-point path. It has no cluster message feedback,
routing/gate, new attention, mask-diversity or referent-ranking objective.

PointRend original arXiv1912.08193v2 sections3.1-3.2 verified online: it uses
selected/interpolated fine and coarse features and a per-point MLP. The general
idea of point refinement is prior art, not this project's novelty. Here the
specific experiment is the mean-constrained query field on an unchanged SP
partition, without adaptive selection/subdivision. Exhaustive novelty is
unverified. This is a falsifiable structural experiment, not a proven contribution.
The 3D grounding original2308.11887 abstract confirms an SP mask branch; its
complete original method comparison remains unverified and is a limitation.

## 6. Next Batch
One independent PDC candidate, through six real gates only; no duplicate control
training or new variant to fill the other slot. See exp_design_20261009-0912.md.
