# M95 bag-control mixing amendment

The first two-batch diagnostic used a one-position rotation of flattened
instance bags. This changed membership in ten expressions but swaps only
boundary seeds and is an insufficient negative control. Before inspecting
the stronger result, replace the shuffle with column-wise round-robin
interleaving of sorted physical-instance bags, then repartition into the
same ordered bag sizes. Preserve all eligible seeds, bag count, sizes,
targets and normalization. Report the fraction of seeds assigned to
non-original bags and gradient delta versus the physical grouping. The
initial weak-control result remains recorded, not overwritten. No
admission or efficacy inference from either backward-only diagnostic.
