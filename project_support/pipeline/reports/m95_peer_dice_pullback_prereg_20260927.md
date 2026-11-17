# Native BCE plus Dice query-state competition check

The prior frozen LayerNorm pullback tested BCE alone. M95's mask loss gives
BCE and Dice both unit weight. On the same 26 frozen TRAIN rows, retain the
reconstructed best-positive query logits, and separately autograd the full
binary target-mask BCE, the project's smoothed Dice loss, and their sum
against the pre-LayerNorm query state. Measure the cosine of each resulting
update against the missed-target BCE and peer-negative BCE component
directions from the prior pre-registered test.

Compare fragmented, covered and other strata without tuning. This can only
resolve whether native mask Dice changes the local query-gradient direction;
it is not a new backward graph, intervention, efficacy result or admission.
