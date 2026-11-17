# Native Superpoint Target Erasure Diagnosis

Tick: 544cb1c4187542cd9ebe69d68351bd98.
Candidate: m95-native-majority-target-erasure.
Hypothesis ID: majority-quantization-erases-present-referent.

Independent of target cardinality, an existing singleton target might retain
point-level positives yet have no positive superpoint after the native >0.5
majority operation. Such an expression would have no native positive mask unit.
This asks about complete target disappearance, not partial boundary error,
missing sampled anchors, selector ranking or pooling successors.

Use unchanged native get_ref_mask and original TRAIN dataset/transforms, seed
1999, fixed 32-scene/128-expression manifest, two seed-reset CPU passes.
Keep augmentation/crop behavior and loss thresholds unchanged. Record raw
scene masks before augmentation separately from augmented native output.
Separate point-target absence, majority erasure, and represented targets.
Do not count an absent physical target as majority erasure.

Controls run the exact native method: known present singleton identity,
absent-ID zero output, 50/50 synthetic tie erased and 2/3 majority retained.
Synthetic controls establish sensitivity only, not native prevalence.
Bind sources, config, manifest, inputs and script hashes; verify both repeats.
Reject the total-erasure premise on this frozen cohort only if every expression
with native positive points retains at least one positive superpoint.
Zero incidence is not a universal population claim or a rejection of all
boundary/quantization mechanisms. Positive incidence requires native loss
participation and causal controls before any new mechanism or admission.
