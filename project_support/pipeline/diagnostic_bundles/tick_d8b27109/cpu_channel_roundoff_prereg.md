# Single-Readout CPU Arithmetic Reference

Candidate: hierarchical-nonlocal-channel-rank-audit. This is not a model
revision or a substitute for the failed native null gate. The original native
failure and unknown exact amplitude remain unchanged. Both authorized GPUs
were occupied on this tick, so no native forward has run.

Use exactly the original frozen prefix and weights, expression 0, last valid
point 728, and the first point outside its coarse cluster. Keep the original
remote-minus-readout direction, centered-weight SVD, row/null splitting,
remote feature norm, and 1e-12 ideal-null tolerance. No new samples, step-size
selection, retries, or architecture changes.

Evaluate the source-formula full-shaped message four times (baseline,
remote/null, remote/row, own-coarse/null) for each of three CPU references:
float32 arithmetic; float64 arithmetic with the ideal float64 directions;
float64 arithmetic on the ACTUAL float32-perturbed tensors. The last two
references distinguish ideal algebra from rounding at the input assignment.
Record, never relax, the original strict 1e-6 output criterion for each
reference. These are arithmetic reference criteria, not a native gate PASS.

Record point assignment residual, float32 direction cast residual, exact
single-point-change/N, float32 mean shift and its rounding residual, centered
global-logit shifts, baseline difference from saved native message, and all
three message changes. Preserve the full padded shape, source-formula masking,
and native saved weights. Do not change production precision or mask behavior.

Prediction: ideal float64 remote/null preserves the fixed conditional message,
whereas the native failure MAY include float32 assignment, reduction, or later
operator effects. This test can establish CPU arithmetic behavior only. It
cannot attribute the original GPU failure uniquely, measure trained harm,
establish efficacy/novelty, or authorize admission. CUDA must stay uninitialized;
all new training, optimizer, scheduler, full native and VAL counts remain zero.
