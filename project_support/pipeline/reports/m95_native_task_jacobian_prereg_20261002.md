# Native Multi-Task Jacobian Preregistration

Registered 2026-10-02 before inspecting new gradient outcomes.
Stable work: `m95-sample-context-support`. Diagnosis only; no admission.

## Hypothesis
The actual native multi-positive referent, mask and semantic losses can
produce antagonistic updates on the final shared query representation and
its generating decoder parameters. This is distinct from the September 12
oracle-only head audit and the September 27 cross-expression sampler audit.
The test does not propose PCGrad, scalar reweighting or a renamed selector.

## Frozen Inputs And Sampling Unit
Use the original M95 checkpoint SHA256
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`
and the existing prediction-blind 31-expression/two-scene TRAIN manifest
SHA256 `85e108e8c86d65bcdbdc25061987e0a973fa45b35b00030d0721d359da720040`.
The manifest constant is imported from the frozen adapter and checked.
Include all original loader companion expressions, label them explicitly,
and do not substitute a new outcome-selected subset. Seed 1999, native
collate, single scene per batch, no dropped tail, checkpoint eval mode.
This is a bounded TRAIN diagnostic, not a population/generalization claim.

## Mechanism Readout And Controls
Capture the final query before the existing out_norm, without modifying
the prediction or loss. On one native forward extract actual loss_indi,
mask BCE+Dice, semantic alignment and quality-score gradients. Use existing
loss weights. Verify their sum equals the gradient of the complete native
loss on that query. Also measure each component at the final decoder FFN
parameters using native autograd; report finite/nonzero/missing denominators.

For each expression report paired cosine/dot and the directional derivative
of each loss under the summed native update. Negative cosine alone is not
proof of harmful optimization; positive dot(component,total) predicts its
loss decreases under an infinitesimal SGD step. Compare same-query gradients
to a cyclic query-index rotation with all norms and task weights preserved.
Repeat the full capture with identical seed and verify fingerprints,
native loss and gradient readouts agree within floating-point tolerance.

Expected diagnosis: reproducible native-specific antagonism separated from
the rotated ownership control, with a directly adversely affected objective.
Exact no-op, nonfinite or disconnected gradients invalidate that readout.
If objectives remain jointly descending, do not claim task antagonism as
the explanation. No trained effect size or tiny-sample significance gate.

## Bounds And Next Action
Only server-6 GPU7, exclusive flock, live idle/foreign-process checks and
bounded timeout before this tick's actual deadline. No optimizer step,
checkpoint write, queue entry or training.
Any follow-up needs a deployable structural causal mechanism, matched
native control, independent model/config, new-path backward, standard
resources and goal constraints. Generic gradient surgery is prior art.
