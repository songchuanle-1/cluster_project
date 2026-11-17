# Native Instance Sentinel Collision

Tick: 63db8202cf55406f8f29e19f14229f70.
Stable ID: m95-native-instance-sentinel-collision.
Hypothesis ID: unassigned-support-sentinel-collides-with-real-target.

Original dataset get_sp_label initializes unassigned supports to199.
Original criterion compares sp_ins_labels to physical target IDs.
If a real annotated referent is199, unassigned supports may become false
positives for that referent without any actual point membership.
This asks about instance identity, not target-majority disappearance,
sampling anchors, boundary refinement or a learned routing successor.

First prediction-blind test: read exact unchanged TRAIN annotation IDs and
frozen32/128 IDs, verify original dataset/criterion source hashes and native
sentinel initialization, and count actual target199 incidence.
If incidence is positive, test its real scene supports with original native
get_sp_label and criterion equality before considering a repair.
If all native target IDs differ from199, reject this target-collision premise
for the unchanged native TRAIN annotations. Other sentinel paths remain
unverified, not automatically rejected.

Controls: constructed target199 equality must include unassigned199 supports;
wrong-ID and shifted-sentinel controls must not. These demonstrate code-path
sensitivity only, never native data incidence or an admitted model.
Do not mutate original code, sentinel, IDs, thresholds or training state.
Bind annotation, manifest, local/remote native source and diagnostic script.
