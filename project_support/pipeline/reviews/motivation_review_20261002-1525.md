# Motivation Review - Native Objectives And Joint Ownership
2026-10-02 15:25 Asia/Shanghai. Diagnostic review; no training proposal.

## 1. Goal
Authoritative goal: `pipeline/goal.json`, SHA256
`d7296cbb4cfc0742e92ccccc65a17b36513dcd8940c98c90e38801e79f14b21b`.
All 18 constraints/11 bans unchanged. Phase1 target ScanRefer mIoU 0.5100,
M95 champion 0.5020, baseline 0.4894. Only server-6 GPU7, two slots.
Goal description requires concrete errors and falsifiable lightweight
structural mechanisms, not pooling/selector/routing successors.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Actual multi-task antagonism explains referent failures | Not supported by this realization | Native 102-expression/28-scene Jacobians | No independent structural causal mechanism |
| Distinct-target categorical ownership adds missing correction | Rejected realization | 121 native distinct-target pairs | Independent BCE already supplies the correction |
| A new method is training-ready | No | No model/config or admission receipt | All new-candidate gates remain incomplete |

## 3. Experiment Assessment
| Experiment | mIoU | Goal relationship | Contribution |
|---|---:|---|---|
| model_base1 | 0.4894 | Historical baseline | Unchanged |
| M95 | 0.5020 | Historical champion | Frozen checkpoint diagnostic only |
| M197-PIRS | 0.4920 | stopped_unknown | No automatic restart |
| Native task Jacobian | Not training | Corrects oracle-only objective limitation | Referent/semantic aligned; no adverse referent sum-update |
| Distinct-target ownership | Not training | Tests joint physical ownership | Joint/BCE directions nearly identical |

## 4. Gap Analysis
Three captures execute native TRAIN forwards, exact checkpoint/source
bindings and native matching. They do not execute a new candidate's full
backward, optimizer or evaluation. Derived-readout strict repeat checks fail
at frozen 1e-6 tolerance; same input fingerprints and discrete outcomes
match. No gate is passed by relaxing that failure.
Full-cohort Jacobians: referent/semantic mean cosine 0.57143, mask/referent
0.00634, adverse summed query updates referent 0/102, mask 1/102,
semantic 1/102. Final FFN gradient cosines are weak.
Categorical ownership/BCE mean gradient cosine 0.99738; both correct all
121 pair margins. Only two pairs show target-region coassignment.
These are narrow TRAIN diagnostics, not population effects or efficacy.

## 5. Design Rationale
The two causal units are independent: native objective interaction versus
cross-expression physical occupancy. Neither supplies the distinct new
information path needed for implementation. Do not substitute PCGrad,
scalar weighting, listwise ranking or generic joint softmax.
SetCon, MDETR and RefMask3D remain relevant original comparators; no
whole-mechanism novelty claim is made from this limited search.

## 6. Next Batch
See `pipeline/designs/exp_design_20261002-1525.md`.
No admitted batch. Evidence-sensitive two-hour research cooldown follows
these tested realizations; resume on genuinely new independent mechanism
evidence or expiry, not an identical probe. Monitor/goal checks continue.
