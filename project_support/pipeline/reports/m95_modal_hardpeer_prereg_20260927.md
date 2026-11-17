# Hard-peer control for modality disagreement

Follow-up to frozen `m95_modal_disagreement_v1` under stable ID
`m95-sample-context-support`. A pre-fusion 2D/3D discrepancy is larger at
missed target support in both fragmented scenes, but the same sign occurs in
both covered controls. Test whether it merely tracks the native positive
query's low logits rather than referent-specific information.

Freeze exactly the 26 annotated same-class physical-peer rows and the
unchanged M95 final query logits. For each missed target superpoint in each
row, select the still-unselected same-class physical-peer superpoint with
nearest *best native-positive query logit*, breaking ties by support index.
Use at most min(target, peer) pairs without reuse, iterating targets in
support order. The 2D/3D discrepancy score is unchanged from the previous
preregistration. Evaluate paired target-minus-hard-peer discrepancies and
compare the already frozen fragmented, other-limited, covered and remainder
groups. No score threshold, tuning, GT for proposal generation, or new
training. A specificity claim requires both fragmented rows to retain a
positive mean beyond this matched hard-peer control and a pattern distinct
from covered controls; otherwise continue diagnosis only. Matching uses GT
only for retrospective controls, never as a proposed inference operation.
