# M95 prediction-blind seed target population

Stable ID `m95-sample-context-support`. Select manifest indices 0..15 and
128..143 from frozen preregistered manifest SHA256
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`.
This selection uses no model outcomes and covers 16 ambiguous and 16
class-unique expressions. Map each expression to its native dataset scene
index, draw one fresh native TRAIN transform, and report every expression
returned in these scenes; separately tally only the 32 prespecified keys.
Bind M95 checkpoint/config/loss hashes. Measure final post-overwrite seed
targets, selected-query seed context, and selected mask IoU, with same-scene
non-context comparisons. The new transforms are not exact old-capture
replicates. This is exposure diagnosis, not evidence of a model effect,
novelty, or admission.
