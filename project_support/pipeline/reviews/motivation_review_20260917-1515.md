# Motivation Review - Counterfactual Evidence Supervision Rejection
2026-09-17 15:15 Asia/Shanghai. Candidate budget 1; no candidate admitted.

## 1. Goal
pipeline/goal.json remains authoritative: target mIoU >= .51; champion M95 at
.5020; Phase 1 NOT YET. The 16 constraints and 11 bans remain unchanged.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Referent selection is a causal failure axis | confirmed | positive restriction +17.9 pp scene-balanced, 22 fixed / 0 broken | deployable non-prior-art mechanism still absent |
| Mask-quality score targets repair the training contradiction | prior art | SPFormer/RG-SAN/VarifocalNet | cannot be the core contribution |
| Listwise/top-1 quality ranking is distinct | rejected | Rank & Sort Loss | objective reparameterisation, not new mechanism |
| Counterfactual evidence substitution is distinct | rejected | SwapMix 2204.02285v1 and project decision 20260916-024658 | known factual/counterfactual regularization mechanism |

## 3. Experiment Assessment
| Candidate | Intended effect | Assessment | Contribution |
|---|---|---|---|
| PIRS | replace provenance labels with detached mask-IoU targets | prior-art score-target supervision | engineering evidence only |
| decision-aligned ranking | optimize deployed top-1 acceptable-query decision | covered by Rank & Sort Loss | rejected before implementation |
| counterfactual evidence supervision | contrast original and object-removed/swapped scenes | covered by SwapMix-style factual/counterfactual regularization | rejected before implementation |

## 4. Gap Analysis
The measured defect is still referent-query selection. The missing contribution is
not another scalar target, ranking rule, consistency constraint, or perturbation
objective. Those are existing mechanisms. What remains missing is a genuinely new
structural information path or causal supervision unit that is not a rename of the
closed families and can be tested under the existing resource and no-tuning rules.

## 5. Design Rationale
The only candidate considered this tick would add a second training view and
contrast factual and counterfactual object evidence. SwapMix already establishes the
core mechanism: swapping visual context features, using the perturbation to diagnose
reliance, and training with it as a regularizer. The 3D ScanRefer application changes
the object representation and intervention target, but not the causal mechanism.
No motivation review to implementation chain is justified for a renamed prior-art
family.

## 6. Next Batch
No candidate admitted and the one open design slot remains empty. The rejected
remainder is documented in
pipeline/reports/counterfactual_evidence_supervision_source_audit_20260917-1515.json.
