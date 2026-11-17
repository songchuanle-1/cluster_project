# Distinct-Referent Ownership Preregistration

2026-10-02; stable ID `m95-distinct-referent-ownership`, diagnosis only.

## Hypothesis And Information Unit
Different TRAIN expressions in the same native scene group can supervise
different physical instances on the same superpoint axis. Independent
binary losses do not enforce joint ownership of those shared superpoints.
Test whether this is a task-relevant deficit before implementing a method.
Do not use validation/test data, change grouping, select new expressions by
outcomes, or equate this with the rejected same-target description family.

## Frozen Cohort And Readouts
Same frozen M95 checkpoint and 31-expression/two-scene TRAIN manifest as
the task-Jacobian test. Retain all native companion expressions in its 21
groups. Only compare same-forward pairs with distinct, nonoverlapping GT
object-ID sets and disjoint GT masks. Reject identity/support mismatch.
Same physical targets are explicitly excluded, not treated as independent.

Report deployed selected-mask intersection, overlap on either GT target,
target union size and whether either deployed expression failed IoU 0.5.
Also compare the first native-matched query for each expression in fixed
query-index order. These matched queries are selected from native TRAIN
seed matching, not prediction quality, highest score or oracle IoU.
List all eligible pairs and denominators, including pairs with no failure.

## Matched Intervention And Controls
Use two mask-logit rows and a background-zero logit on the shared axis:
`L_joint = mean_s(logsumexp(0,z_a,z_b)-z_owner)`.
Owner is 0/background, 1/a or 2/b from disjoint TRAIN masks.
Independent control is per-row native BCE, with the same logits/targets.
Compare infinitesimal negative-gradient changes to each expression's
target-versus-the-other-target mask margin. Repeat with b's superpoint
order cyclically shifted to break physical correspondence while preserving
logit distribution and GT support sizes. Do not call a generic softmax
loss novel, or admit it from this head-only gradient experiment.

Expected result: coassignment on target-bearing shared support plus a
native-ownership-specific corrective direction not explained by independent
BCE or the shifted-axis control. If BCE already corrects the same error and
joint ownership creates no distinct correction, the proposed categorical
realization does not supply a new causal information path. Preserve results
instead of changing thresholds or names. Only two scenes: no efficacy claim.

## Remaining Gates And Literature
A positive screen still needs an independent deployable model/config,
full candidate-native backward, standard resources and all goal constraints.
SetCon (arXiv:2605.20110), MDETR (ICCV2021) and RefMask3D are relevant original
comparators; this diagnostic does not establish an original whole mechanism.
