# Motivation Review - cluster_project

## 1. Goal
- Authoritative complete goal: pipeline/goal.json, SHA256 d7296cbb4cfc0742e92ccccc65a17b36513dcd8940c98c90e38801e79f14b21b; all18 constraints/11 bans reviewed unchanged.
- Phase1 ScanRefer mIoU target0.5100, champion M95=0.5020, baseline0.4894, gap0.0080.
- Research concrete candidate coverage/boundary, same-category discrimination/relation binding and repeated scale evidence; do not fill capacity with pooling/selector/routing variants.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Native within-SP point detail | training | M198-PDC verified launch | trained efficacy unknown |
| Missing78-token native window | rejected realization | full TRAIN36665/36665 retained,20 over78,max137 | not a real information deficit |
| Undirected boundary XOR | degenerate realization | complement symmetry,zero half-probability gradient | cannot anchor target side by itself |
| Directed native boundary supervision | under validation |32 scenes/128 expressions,123 with cut edges; new oriented operator | native repeat,resources,independence before admission |

## 3. Experiment Assessment
| Experiment | mIoU | Relation To Motivation | Contribution |
|---|---|---|---|
| M95-CTF-HCG-CSORT |0.5020| light parent/reference | benchmark,not proof of new loss |
| M198-PDC | unknown | raw point resolution | distinct active hypothesis; unchanged sources |
| Proposed BEI | unknown | joint directed supervision at existing spatial supports | no additional refinement or inference graph |

## 4. Gap Analysis
- Native parent criterion optimizes unary mask BCE/Dice and other existing objectives, not directed endpoint likelihood across a fixed sparse spatial cut.
- Native TRAIN diagnosis has789 crossing edges among74768 expression-edge observations; denominator includes all128 expressions,including5 with no cuts. Exact geometry/label repeat verified.
- This demonstrates eligible task units,not that the units are a performance bottleneck or that post-training benefit is guaranteed.
- Undirected XOR contracts expose an ambiguity. Directed likelihood is proposed under the same stable ID; the old negative result is retained.

## 5. Design Rationale
- Directed preference uses the native matched target mask to identify the correct side. A two-node softplus produces a mixed Hessian,unlike degree-weighted independent BCE. At an uncertain pair its gradient is nonzero and oriented; native unary losses remain the absolute-label anchor.
- Original ADGM paper, Sec3.1-3.4, uses a separate neighboring-pixel affinity predictor plus undirected graph merge. Verified original: https://www.ecva.net/papers/eccv_2018/papers_ECCV/papers/Yiding_Liu_Affinity_Derivation_and_ECCV_2018_paper.pdf . Generic affinity supervision is prior art.
- Original RefMask3D, Sec3.5/Eqs10-11, combines Hungarian score/BCE/Dice matching and pooled text-object contrast. Verified original: https://arxiv.org/html/2407.18244v1 . Neither object matching nor generic contrast is claimed new.
- Task-specific increment: existing query logits,instance-matched orientation,sparse1NN support cut,loss-only training path,no affinity head/no graph merge/no query reassignment. Exhaustive novelty and training improvement are NOT established.
- Existing BCCA component-grouping/cardinality and PDC point-refinement paths remain independent and untouched. No historical bans are renamed.

## 6. Next Batch
- Candidate m95-native-mask-boundary-incidence only; budget1.
- Final native first attempt failed strict repeat with mask delta2.29e-5; preserve output. Complete candidate-local sorted reductions before retesting,never relax1e-6.
- Formal design: pipeline/designs/exp_design_20261009-1032.md. Admit only after actual six-gate outputs,source commit/ff sync and launch-progress verification.
