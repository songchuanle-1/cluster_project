# Missed-target support cross-positive gradient control

Stable `m95-sample-context-support`; same frozen 256-expression M95 TRAIN
capture and the four preselected fragmented limited rows. The all-target
feature-gradient coherence might conceal conflicting updates on target
superpoints omitted by the best native-positive query. Select that query
by frozen native-positive mask IoU with lowest-index tie break, solely for
retrospective diagnosis. Define its false-negative target superpoints on
the unchanged same-forward mask, without changing predictions.

For each row with >=2 native positive queries and >=1 such missed
superpoint, separately differentiate every positive query's original
BCE+Dice mask loss into final features on those missed superpoints. The
primary readout is norm(mean individual gradient)/mean(norm individual
gradient) on that restricted region. Compare the four fragmented rows to
the other 12 limited, with denominators and two-positive-only control.
Hypothesis: substantially lower missed-support coherence in fragmented
rows despite available corrective final-logit signs. No defined
missed support or only one matched positive is undefined, not zero.

Reconstruct the original aggregate mask loss and all-target feature-gradient
norm before reporting. This is a retrospective oracle-localized gradient
diagnostic only; it does not admit a new loss or deployable inference route.
