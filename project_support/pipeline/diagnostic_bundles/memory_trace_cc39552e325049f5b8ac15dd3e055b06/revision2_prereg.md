# Revision2: Pure-Prefix Rematerialization

Stable candidate m95-hierarchical-mask-feature-path-audit; second and final
default implementation revision, not another mechanism or training variant.
Prior revision1 numerical PASS and all original failures remain immutable.

Evidence: matched allocation traces show the core is reached in BOTH branches.
Immediately before readout both retain about5.81GB. Original M95 exits readout
but OOMs later; canonical OOMs at its output projection. Thus shared prefix
retention limits this25%diagnostic; do not blame foreign use or24GBcapacity.

One causal change: non-reentrant activation checkpointing, preserve_rng_state
True, for every encoder layer whose existing use_cluster is false AND its
paired decoder. This selects the original first5pairs structurally, not a
tuned layer count. Never checkpoint the last cluster-bearing encoder, final
decoder, mutable cluster bank or CSORT accumulator. No arithmetic, parameter,
dtype, loss, data, seed, batch, schedule, gate or25%cap change. The same runtime
adaptation is applied to baseline and canonical for matched resource tests.

Freeze before testing: capture actual first5pair arguments/RNG states from
native TRAIN groups0,60 and101,124,4scenes/16expressions; replay all20modules
plain vs rematerialized. Original float32 maximum absolute output, input-gradient
and parameter-gradient difference must be<=1e-6, including matching None masks.
Use finite deterministic linear readouts for this module equivalence test;
it is NOT a native whole-model loss/backward admission result.

Then separately execute actual unchanged native full loss and backward for
baseline and canonical in fresh processes under the SAME25%cap and NVML guard,
first matched pair0,60, followed by the frozen second pair only if time/resources
permit. Report full forward/backward completion explicitly and all failures.
All reached point-path gradients must be finite/nonzero; final cluster/CSORT
must execute once, not be replayed during backward. No optimizer steps.

Prediction: retained prefix activation memory falls enough to permit full native
backward without changing numerical results. Failures falsify this realization
or remain inconclusive; they do not automatically reject the support mechanism.
Resources remain unpassed until paired whole-model standard FLOPs/latency/memory
are actually measured. Independent package/native validation and all remaining
scientific gates still apply before any admission, commit/safe sync or training.
