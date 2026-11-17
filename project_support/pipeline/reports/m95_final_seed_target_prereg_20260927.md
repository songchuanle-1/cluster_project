# M95 final seed-target diagnostic preregistration

Stable ID: `m95-sample-context-support`. Use unchanged M95 checkpoint and
TRAIN loss path on authorized server-6 GPU7, two native batches at seed 1999.
Capture focal inputs after native matching and the criterion's overwrite.
Prediction-blind quantity: number of unmatched, non-target FPS seeds with
native `sp_ref_masks==0.5` and their *final* focal targets. Record top-k and
matched indices and detect any write outside that protected set. This passive
test is a prerequisite, not a causal control; it does not justify admission.
If final target is unchanged at 0.25, prepare a separate matched label
intervention and native gradient control on frozen batch tensors. If those
seeds are overwritten or absent, reject this realization. No model training,
queue mutation, or alteration of foreign processes.
