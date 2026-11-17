# M95 shared-FPS role gradient diagnostic

Frozen M95 checkpoint, seed 1999, 16 native TRAIN batches, 128 expressions
in 32 scenes. The preregistered physical-role screen gave 38 ordered triples
in 13 scenes. The native sample focal loss was exactly reconstructed; all
128 expression input fingerprints and selected seed positions matched the
previous frozen capture. For each triple, the three sampler input feature
vectors and FPS superpoint/physical instance were identical.

There are 266 paired comparisons at 133 unique physical FPS positions.
All 266 target-expression labels were positive (32 exactly 1.0); all three
gradient norms were nonzero. Negative target/context dot products occurred
in 36/266 comparisons, versus 171/266 target/zero. Each of the 13 scenes
had more negative target/zero than target/context products. Mean cosines
were +0.520 for target/context and -0.131 for target/zero. Repeated
positions are not independent samples; no population significance or
performance gain follows from these descriptive counts.

The preregistered context-specific gradient-conflict direction is reversed.
Reject that realization under `m95-sample-context-support`; do not change
its focal target or scale, or relabel ordinary object-text contrast/PCGrad
as an independent mechanism. A role-shuffle control is unnecessary for
claiming this realization because the primary directional gate failed,
but would be required for any future identity-specific positive claim.
No training model, resource gate, admission receipt, sync, queue push or
efficacy result is present.

Sources: `pipeline/reports/m95_role_gradient_prereg_20260927.md`,
`pipeline/reports/m95_role_gradient_native_20260927.json`,
`pipeline/reports/m95_role_gradient_summary_20260927.json`.
