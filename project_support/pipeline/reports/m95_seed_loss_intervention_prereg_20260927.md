# M95 sample-loss intervention preregistration

Stable ID `m95-sample-context-support`, checkpoint
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`.
Repeat the first two native TRAIN batches, seed 1999, unchanged model and
criterion. On frozen `ref_scores` and *final* focal targets from the native
criterion, replay its exact normalized-weight focal loss and record gradients
with respect to each seed logit. Intervention sets only unmatched non-target
class-context seed targets 0.25 -> 0. Placebo sets the same number of
unprotected zero-target, non-target seeds 0 -> 0.25, chosen by closest
baseline logit, within expression. All positive/matched/top-k supervision
is unchanged. Both arms perturb equal seed counts; class and physical
instance are not matched and remain an explicit limitation. Report coverage,
loss differences, gradients on treated and untouched seeds, and original
unchanged referent argmax. Repeatability is assessed against the passive
capture's scene/ann/final-target values. No optimizer step or inference
retraining; no immediate task-effect claim and no admission from a gradient.

Follow-up: on the same first native TRAIN batch, retain the full model
computation graph and replay baseline/treated/placebo sample loss without
detaching `ref_scores`. Differentiate each with respect to the existing
sampling-module trainable parameters (no optimizer step). Record finite,
nonzero gradients and L1 branch differences. This checks propagation beyond
the focal logits; it does not establish a new variant's native-backward gate.
