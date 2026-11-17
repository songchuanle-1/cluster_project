# M230-HVD private source preparation

Stable ID: `hierarchy-native-variance-decomposition-composition`.

The core starts from the same valid current `point_feats` used by the original
cluster bank. For each true-supported fine node f, compute a private mean μ_f
and componentwise central variance v_f over its actual points. At each higher
node p, take equal true-child means:

μ_p = mean_child μ_child
w_p = mean_child v_child
b_p = mean_child (μ_child - μ_p)^2
v_p = w_p + b_p.

These private moments use the original membership arrays and exclude nodes not
reached by any valid point. Each higher node weights each supported child equally,
not by its number of native points. Thus the root's distribution is the nested
equal-child law. Raw M95 banks and CSORT retain their original semantics; private
centers are independently computed and are not replaced by raw upper banks.

The original three LN outputs supply semantic inputs z. The core concatenates:

- fine: [z_f, v_f, b_middle(parent f), b_coarse(ancestor f)]
- middle: [z_m, w_m, b_m, b_coarse(parent m)]
- coarse: [z_c, w_c, b_c, 0].

Pack all supported rows once through one shared 4C→C→C Linear/GELU/Linear map,
then restore original node IDs, leaving unsupported private deltas zero. Retain
original raw token skips and untouched HCG, raw CSORT, decoder ILA and one
inst_feats injection. Do not alter data, partitions, query, loss or native YAML.
Original constructor FFN/LN initialization consumes the original RNG prefix;
new core construction is inside CPU fork_rng, and unused original FFNs become
Identity. No new gate, learned aggregation, softmax, QKVO, N² point operation,
new residual writeback, repeated injection or numeric configuration change.

The statistic path is O((N + K0 + K1 + K2) C) in work/storage. The new learned
maps cost 5 C² per supported hierarchy row, versus 8 C² per original FFN row.
At C256 the new learned core has 328,192 parameters (original three FFNs:
1,576,704), without a parameter-count admission gate. This is a source expression,
not measured whole-model resource evidence or a 10G PASS.

The squared deviations and GELU are differentiable. Constant features give zero
moments; singleton groups give zero between-child dispersion. Neither case
invalidates the core or demands a per-channel/per-module nonzero gradient.
Nonfinite native loss/backward is an implementation failure to preserve; trained
efficacy, novelty and whether this statistic helps ScanRefer remain UNKNOWN.

Only standard-library source/topology/statistic checks have run. The tensor shim
executes the actual production statistic and packing functions; it does not run
the full forward, Torch, native data, AMP, autograd, resources or training.
