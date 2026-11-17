# Experiment Design - Terminal Point-Neighbor Alignment
## 1. Motivation
- Diagnose actual fine-feature target/background contamination on the authorized hierarchical point-feature mainline,after failed trained FLE and inconclusive valid early content control. No modification to goal or masks at inference.
## 2. Current Best Results
| ID | State | mIoU | Epochs |
|---|---|---|---|
| M95historical | complete | .5020 |22/50 |
| M203FLE | normalearlystop | .4885315597 |23/50,best13 |
- Current early content-diagnostic normal-minus-permutedPiou-.0079658,8scene exploratoryCIcross0;not VAL/generalization.
## 3. Analysis And Direction
- Compare actual learned fine weights to uniform weights over identical nonself edges. Correctly handle original whole-leaf cutoff-tie fallback. Target-recipient cross-target fraction is primary;GTnever selects the cohort or enters returned features.
## 4. Experiment Plan
| ID | Native checkpoint | Cohort | Readout |
|---|---|---|---|
| fle-native-nonself-target-mixing-audit | Unique originalbestepoch13,SHAin original terminal evidence |32SHA-ranked TRAINscenes/first4expressiongroup each,frozen before forward | Scene mean weighted-minus-uniform target cross-fraction;5000bootstrap/seed1999 if>=10knownscenes |
- CPUcontrols beforeCUDA:source reconstruction,uniform-feature equality,all-labels-equal null,complement invariance. Native hook is observational and original output remains unchanged. Unknown labels/support explicitly counted. No VAL/TEST/train/selection.
## 5. GPU Allocation Plan
- server4physicalGPU0 only,pinned UUID/liveidle/threeflocks/currentlease beforeCUDA. server3GPU1foreignwork preserved;server4GPU1unauthorized.
## 6. Implementation Checklist
- Register diagnosis before test;freeze source/assets/producers/cohort. Reuse original safety runtime,change checkpoint only to preregistered terminalbest for this distinct diagnosis.
- No production source/config changes,no admission/commit/sync/trainlaunch. Persist results and a concrete matched-causal followup if observational evidence warrants it.
## 7. Risk Assessment
-32TRAINscenes are not a held-out/generalization set and may overlap earlier8. Lower cross-label mixing is not necessarily useful contextual semantics;high mixing is not causal harm. No fixed task-gain gate or novelty claim. Resource/noise unknowns unchanged.
Status: PREREGISTERED_OBSERVATIONAL_DIAGNOSTIC
