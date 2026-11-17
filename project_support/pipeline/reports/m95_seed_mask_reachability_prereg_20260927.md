# M95 selected seed-to-mask reachability

Stable ID `m95-sample-context-support`. On the same 32-key
prediction-blind cohort (16 native batches, transform seed 1999,
unchanged M95 checkpoint), record whether the selected binary mask
contains its selected FPS seed superpoint. For all selected expressions,
also compare the selected mask with the selected seed's physical
instance mask. Report exposed versus non-exposed denominators and
the full 128-expression context-exposed numerator. Preserve the
original matcher, indicator and mask logits. If selected context
seeds are systematically outside the selected masks, a seed-local
role-label mechanism has no demonstrated direct mask-binding path;
do not infer training efficacy from seed-logit gradients. This is a
falsification screen, not a matched training intervention.
