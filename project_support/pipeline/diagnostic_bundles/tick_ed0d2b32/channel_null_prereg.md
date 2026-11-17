# Native Conditional Channel Nullspace Control

Follow-up for hierarchical-nonlocal-channel-rank-audit, not a model revision.
Use the exact saved rank_prefix and original frozen M95 weights/flags. Exactly
one guarded source-interface process; no new fullmodel/data/seed/optimizer/VAL.
The baseline full-shaped original gather+message_norm must reconstruct the saved
native message under1e-6. Do not change this gate or retry until matching.

For each previously fixed24 readouts, select the first valid remote point whose
coarsest ID differs. Let d be remote point minus readout feature, prediction-
and-gradient-blind. Project d into the rowspace/nullspace of centered global
level_gate weights, H=(I-11T/3)W_global. Normalize both to the original remote
feature norm, not a swept step size. Report degenerate/missing cases UNKNOWN.
The float64 H-null residual must satisfy original1e-12 reference control.

Run exactly three matched source-interface conditions/readout: perturb only the
remote point by null direction; remote point by rowspace direction; the readout's
own coarse token by that same null direction. Hold every other prefix argument
and parameter fixed, do not recompute upstream context or claim whole-network
causality. The readout's own gathered tokens remain the conditioning variables.
Report message changes and contraction with the saved actual native cotangent.
This contraction is a local linear surrogate, NEVER a measured new native loss
or trained benefit. Source baseline/null tolerance1e-6 is retained; no fixed
task-effect admission gate. All original parameter.grad must stay unaccumulated.

This checks the module's available information directions, not a deployable
intervention, a gate proposal, whole-network restriction, population inference
or evidence for a specific new attention architecture.
