# Conditioned Hierarchical Nonlocal Channel Rank: Diagnosis Only

Stable new ID: hierarchical-nonlocal-channel-rank-audit.
Hypothesis ID: conditioned_cluster_message_nonlocal_rank.
This is not a proposed gate/normalization/attention variant or admission. It does
not reopen the closed superpoint ceiling, centroid-graph boundary/BCCA, FLE or
hierarchical-detail routes. Motivation follows the authorized point-feature
mainline: characterize the actual information interaction BEFORE selecting a
new structural mechanism. Rank is not an efficacy threshold or whole-network claim.

## Frozen Causal Scope And Derivation
M95 CTF applies an independent FFN to each cluster token; HCG gathers only the
point's assigned fine/middle/coarse tokens. For a source outside the readout's
coarsest cluster, conditioning on the native prefix/assignments/query, its only
gather-time channel path is global_mean -> three softmax scale weights.
For readout i, z_i = LN(W_o S_i softmax(A[p_i,mu]+b)+b_o), with S_i three
gathered scale messages. The Jacobian with respect to mu has rank at most2,
because the three-way softmax Jacobian has rank at most2. The final LN/projection
cannot increase it. This is a CONDITIONAL module-level rank bound; previous
encoder/decoder paths and learned parameters can carry other information.
Do not call it a full-network bottleneck or proof of trained harm.

## Actual Test And Controls
One ORIGINAL native M95 train forward/loss.backward/clip0.1; same epoch16 weights,
first two TRAIN groups, seed1999/batch2/native flags. Capture actual gather prefix,
normalized point message and nonzero native loss cotangent. Replay the exact
full-shaped original gather+message_norm with original parameter flags and no
parameter-gradient accumulation: existing native1e-6 control must pass. No seed,
optimizer, schedule, precision/backend change, new VAL or production patch.

Select valid point indices first/middle/last for each of8 expressions, BEFORE
looking at gradients. In float64 CPU mathematical reference using frozen actual
weights and prefix, compute mean-context and own-coarse-token Jacobians. Report
singular spectra/rank using eps*max(shape)*largest_sv as numerical rank
definition, not a relaxed native tolerance. Matched remote coarse-token control
must have exactly zero dependence for the readout; own-coarse must be active.
Check these two controls with 24 actual original full-prefix native token VJPs,
one selected readout per fixed first/middle/last point; report them separately
from full-model training backwards. Parameter gradients must not accumulate.
Report native loss-gradient squared projection onto each Jacobian's output
column space, with zero-gradient readouts marked UNKNOWN rather than0.

Record expression/scene/readout denominators, all cases and failures. Only two
independent scenes: no population confidence interval, seedvariance or trained
benefit. A low accessible fraction is a risk signal, not evidence the mechanism
is universally inadequate. A future mechanism needs a new matched task-relevant
intervention plus full admission; no automatic attention variant or training.

Use only pinned server4GPU0 with fresh current lease/liveidleness/three locks.
Float64 reference is diagnostic CPU math, never production dtype change. Keep all
1e-6 native/1e-12 exact reference controls and historical failures.
