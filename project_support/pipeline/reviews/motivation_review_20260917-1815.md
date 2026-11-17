================================================================================
  Motivation Review - Language-Guided Query Selection Rejection
  2026-09-17 18:15:00 Asia/Shanghai
================================================================================

## 1. Goal
pipeline/goal.json remains authoritative: target mIoU >= .51, champion M95 at
.5020, baseline at .4894, Phase 1 NOT YET. The 16 constraints and 11 bans remain
unchanged. The goal explicitly excludes selector changes as the research main
line, and the confirmed defect remains selected-referent identity.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Referent selection is a causal failure axis | confirmed | restricted native-positive selection raises scene-balanced TRAIN success from 68.75% to 86.7%, 22 fixed / 0 broken | no deployable non-prior-art mechanism |
| PIRS score targets repair the training contradiction | prior art | SPFormer/RG-SAN and VarifocalNet use mask-quality or IoU-derived score targets | engineering evidence only |
| Listwise referent ranking is a new core mechanism | rejected | Rank & Sort Loss already orders positives by localisation quality | objective reparameterisation |
| Same-target description consistency is new | rejected | TrackRef3D/ViewRefer already use multi-positive descriptions and expanded views | renamed consistency family |
| Counterfactual evidence supervision is new | rejected | SwapMix already swaps context features and uses factual/counterfactual training | renamed perturbation family |
| Language-guided query selection is new | rejected | UniSpace-3D 2506.14238v1 defines LGQS on ScanRefer and attributes it to Grounding DINO | selector prior art plus explicit selector ban |

## 3. Experiment Assessment
| Candidate | Intended effect | Assessment | Contribution |
|---|---|---|---|
| PIRS | regress query scores toward detached mask IoU | prior-art score-target supervision | engineering evidence only |
| decision-aligned ranking | place an acceptable query first | covered by Rank & Sort Loss | rejected before implementation |
| counterfactual evidence supervision | make selection depend on target evidence | covered by SwapMix-style factual/counterfactual training | rejected before implementation |
| language-guided query selection | initialize/select candidates from aligned text and point features | published on ScanRefer and explicitly outside the project's selector line | rejected before implementation |

## 4. Gap Analysis
The measured defect remains referent-query selection, but the remaining obvious
repairs are known mechanisms. Another selector or candidate-initialization module
would not supply a new causal supervision unit and would violate goal.json. A
future candidate must add a structurally new information path or supervision
unit while preserving the fixed schedule, seed, FLOPs, memory, and validation
constraints.

## 5. Design Rationale
The candidate considered this tick was language-guided query selection using
aligned positional and semantic text-point features. UniSpace-3D already
describes this mechanism, reports ScanRefer gains, outputs selected candidate
indices, and cites Grounding DINO as its inspiration. Changing the local module
name or host architecture would not make the selector mechanism novel. The
project goal also explicitly rejects selector changes as the research main line.
No motivation-review-to-implementation chain is justified.

## 6. Next Batch
No candidate admitted; the one open design slot remains empty. The rejected
remainder and source hash are recorded in
pipeline/reports/language_guided_query_selection_source_audit_20260917-1815.json.
→ No design/enqueue action this tick.
================================================================================
