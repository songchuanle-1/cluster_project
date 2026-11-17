# Experiment Design - cluster_project
2026-10-18 | Diagnostic continuation and frozen terminal evaluation

## 1. Motivation
- Unchanged goal: hierarchical interactions must update inst_feats used with queries for masks;efficiency is a constraint,not the sole research axis. Complete original M203evaluation and distinguish invalid controls from negative efficacy.
- Begin snapshot12:09:37Shanghai/design,one active of two slots,candidate_budget1. Stable native-exit diagnosis was registered and tested before broad review. No extra train launch.

## 2. Current Best Results
| ID | Structure | State | Best mIoU | Acc50 | spmIoU | Epochs |
|---|---|---|---|---|---|---|
| M95 | CTF-HCG-CSORT | historical earlystop | .5020 | unknown | unknown |22/50 |
| M202-HDS | Disjoint hierarchy readout | earlystop | .4946560264 | cached .54743374 | unknown |29/50 |
| M203-FLE | Fine-recipient point exchange | normal earlystop | .4885315597 | see native log | see native log |23/50 |
- Available M95epoch16 paired reference .5024607182 is not verified historical champion weights.

## 3. Analysis And Direction
- Frozen fullVAL9508/141 confirms M203bestepoch13 .4885315597;paired delta-.0139291520 with scene95%CI[-.0223369116,-.0054631474]. No trained improvement over baseline/champion/target. Original branch convergence stop applies to this realization,not all possible hierarchical point updates.
- Diagnostic norm revision1 improves true norm accuracy but fails unchanged native control. Neighborhood usefulness remains inconclusive. Do not treat changed partial masks as useful transfer.
- Geometry:24nativeFPS calls,64fine-kernel calls,56transform comparisons pass with fixed native memberships and synthetic features;not whole-hierarchy equivariance or trained robustness.

## 4. Experiment Plan
| Stable ID | Actual test | Result / Next action | Admission |
|---|---|---|---|
| fle-native-run-exit-disposition-audit | Exact native log/checkpoint/PID disposition | Normal earlystop verified;finite diagnostic complete | None |
| fine-leaf-local-point-exchange | Original frozen fullVAL and paired subgroups | Trained realization negative;no automatic restart or variant selection | No new admission |
| fle-fixed-membership-metric-geometry-audit | Frozen8TRAIN geometry nativeFPS/fine-kernel controls | Finite diagnostic complete;retain synthetic counterexample | None |
| fle-self-neighbor-content-separation | Original,capture-only,and one preregistered arithmetic diagnostic revision | Strict norm controls fail;derive a valid bounded diagnostic before another native run | Not a new model |
- Same scene-bootstrap5000/seed1999 and original-.003subgroup rule. Full identity join,not row order. No TEST,new training or validation-based config choice.

## 5. GPU Allocation Plan
| Server | Physical GPU | This tick | Condition |
|---|---|---|---|
| server4 | 0,pinned UUID | Finite native diagnostics and fullVAL only | Identity/live occupation/3lifetime locks checked beforeCUDA |
| server3 | 1,pinned UUID | Preserve foreign job | No sharing/eviction/reset |
- server4GPU1 remains unauthorized despite previous idle observation/question. No host migration or scheduler changes.

## 6. Implementation Checklist
- DONE: exact terminal reconciliation;full native geometry diagnostic;failed native diagnostic and capture/forensics;one preregistered diagnostic arithmetic revision;fullVAL and original paired analysis.
- DONE: no model/config/seed/schedule/optimizer/data/source modification,no code commit/deployment/new admission/training launch.
- PENDING until verified: final independent statistics/source/resource audit,guarded ledger/memory/report,canonical finish and released owned lease. Do not preclaim postflight.
- NEXT: retain the same failed-control ID;before any repair2 state defect,causal change,prediction,unchanged controls and evidence hash. No unregistered arithmetic search.

## 7. Risk Assessment
- The failed arithmetic diagnostic cannot support a causal efficacy conclusion. A single trained seed establishes this screen's outcome,not generalization or universal mechanism failure.
- Macro-scene and expression-weighted intervals differ;subgroup strict-harm criteria are not met. Noise floor remains unknown without independent repeats.
- Full-training allocator peak/original resource increment unknown. Cached sampled resource results are not new measurements. All foreign jobs and unrelated dirty files preserved.

Status: DIAGNOSTIC_RESULTS_RECORDED; NO_NEW_TRAIN_ADMISSION
