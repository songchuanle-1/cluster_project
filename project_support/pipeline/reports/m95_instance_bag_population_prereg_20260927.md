# M95 bag identity specificity population test

Extend the first-two-batch physical-instance bag diagnostic to the
unchanged 16-batch TRAIN population from the frozen 32-key manifest
(transform seed 1999, unchanged M95 checkpoint, server-6 GPU7).
The group construction, hard-zero arm, and column-interleaved shuffled
bags are fixed by the prior preregistration/amendment. Each batch
preserves the matcher, masks, indicator, group count, bag sizes and
eligible seed membership. Report per-batch fraction moved,
`L1(physical_gradient - shuffled_gradient)` versus
`L1(physical_gradient - hard_zero_gradient)`, and the number of batches
with ratio below 0.1. Treat ratios near zero across substantially
mixed bags as evidence against an identity-specific group mechanism;
do not interpret the absolute gradient size as efficacy. This
extension does not authorize a model/config or queue admission.
