================================================================================
  Motivation Review - Relation-Conditioned Identity Transport Rejection
  2026-09-18 05:17:00 Asia/Shanghai
================================================================================

## 1. Goal
pipeline/goal.json remains authoritative: ScanRefer mIoU must reach 0.51,
champion M95 is 0.5020, and Phase 1 remains below target. The goal excludes
selector, pooling, readback, and scale-count changes as the main line. A new
mechanism must identify a concrete error, expose a new causal information path
or supervision unit, and remain falsifiable and lightweight.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Referent identity is the actionable failure | confirmed | Restricting selection to native positives raises scene-balanced success from 68.75% to 86.7%; objectness-only control is null | no admissible new causal unit |
| Raw paired 2D has better instance identity structure | bounded positive | 2D top-3 72.7% vs 3D 48.5% on the same 33 failures | rank structure is not language alignment |
| 2D identity can be routed by relation text | rejected | same-forward top-5 is 6.1% for 2D mean/max and prefers-target is 51.5%/57.6% | no measured referential relation signal |
| Relation-conditioned mask/sub-cloud fusion is novel | rejected | RefMask3D already combines language with geometric groups and mask-level target identification | prior art |

## 3. Experiment Assessment
| Experiment or Audit | Result | Relation to motivation | Contribution |
|---|---|---|---|
| Modality identity separability | 20/33 paired failures favor 2D rank | establishes a bounded identity-structure lead | diagnostic only |
| Modality-language alignment | 2D top-5 6.1%, prefers-target 51.5%-57.6% | removes the assumed relation-to-identity bridge | rejects transport premise |
| RefMask3D primary source | group-word cross-modal attention and target identification | covers the proposed relation/mask interaction | novelty rejection |
| NS3D/relation contract | generic target-supervised latent relations are prior art | covers relation routing under another name | novelty rejection |

## 4. Gap Analysis
- Verified: the deployed model can discard a correct query even when one exists.
- Verified: the final fused 3D representation can lose a bounded identity
  separability advantage present in the paired 2D input.
- Verified: the available forward-only evidence does not show that 2D identity
  evidence is aligned to the referring language on the failures.
- Therefore, routing that evidence through relation tokens or predicted masks
  is not a derived causal repair. It would test a prior-art interaction on a
  signal whose referential meaning is unverified.

## 5. Design Rationale
The audited candidate, relation-conditioned identity transport, would use
relation-bearing text tokens to aggregate raw 2D identity evidence over each
candidate mask before producing the referent decision.

It is rejected before implementation. First, the same-forward alignment audit
shows that the 2D evidence is at chance for referent-language matching, so the
proposed path has no established target signal. Second, RefMask3D already uses
language-guided geometric group attention and target identification at the mask
decision; NS3D and the project relation contract cover relation-routing
variants. Third, the proposal is a recombination of features already present
in the forward pass and falls on the closed fusion/readback/selector axis.

## 6. Next Batch
Admit no candidate. The one open design slot remains empty. Do not reopen this
axis as a modality gate, relation router, mask-mediated fusion, or compact
relational attention variant. Continue only the blocked native referent
diagnostics after the recorded GPU-cap unblock condition is met.

Evidence: pipeline/reports/relation_conditioned_identity_transport_source_audit_20260918-0517.json
================================================================================
  Status: MOTIVATION REVIEW COMPLETE (NO CANDIDATE ADMITTED)
  Reviewed by: Research Pipeline (autonomous)
  Created: 2026-09-18 05:17
================================================================================
