# Native Target-Distractor Multiscale Evidence Alias

## Frozen Hypothesis
For a target and its closest same-category distractor, the native composed
cluster supports may coincide at every context scale, making their context
evidence identical despite distinct instance identities. This is a
target-specific information gap, not a claim that all scale tokens duplicate
one another or that generic pooling/gate changes are a new mechanism.

## Population
Use the existing prediction-blind TRAIN manifest of 32 scenes and 128
expressions, M95 checkpoint, seed1999 and original native configuration.
Pair each single target with the nearest distinct physical instance having
the same native semantic class, using surviving superpoint centroids.
Enumerate all eligible expressions and missing semantic/instance geometry.
Multi-target expressions are reported separately and not forced into pairs.
The denominator must not depend on model success or selected query.

## Readout And Controls
Capture the original cluster bank IDs at a native forward. Compose each
superpoint's IDs through the original hierarchy, without changing partitions.
For each pair report exact overlap of fine/coarse support sets, identity of
normalized per-instance membership distributions, and original pooled
context representations. Record full/native repeat failures separately from
integer membership reproducibility; retain the existing absolute 1e-6 check.
Same-instance identity is the equality control. A geometrically distant
same-category instance, when present, is the negative association control.
Semantic class comes from native data, not from a model-predicted category.

## Disposition Rules
Exact aliases support only a scoped diagnosis; they do not establish harm,
trained gain or a new independent operator. No aliases disconfirm this
exact-support realization only, not approximate redundancy or all multiscale
mechanisms. Missing native class/support is unknown, not a negative result.
If support alias exists, next test must establish a control-separated,
task-relevant intervention distinct from historical residual/detail/routing.
If support alias is absent, do not manufacture an equivalent variant.

## Limits
No production edit, optimizer, training, resource PASS, novelty claim,
admission or dispatch follows from this capture alone. The local machine
performs orchestration and static checks only; native data runs on authorized
server-6 GPU7 after fresh occupation/UUID/lease checks.
