# M95 instance-bag operating-regime check

Stable ID `m95-sample-context-support`; unchanged M95 native TRAIN
population from the frozen 32-key manifest, transform seed 1999.
The prior noisy-OR physical-instance bags use focal target 0.25.
Before treating the changed parameter gradient as constructive
supervision, record each bag's size, probability
`1-product(1-sigmoid(seed_logit))`, focal derivative sign with respect
to the bag logit, and mean derivative sign with respect to member
seed logits. Report the fraction of bags whose probability is above
0.25 and whose gradient descent suppresses member scores.

Reject this formulation as an evidence-support mechanism if a
majority of eligible bags are already above the target and its
member gradients primarily suppress scores. Do not silently change
the bag target, focal alpha, temperature or scale to rescue it;
any alternative requires a separate derivation and controls.
