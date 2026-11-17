# NDE isolated software reserve

Candidate: `hierarchy-native-distribution-embedding-composition` / `M233-NDE`.
Parent source: `f6257de79148581334ee495e6e2d60ccb525457c`.

The hypothesis is that a learned vector embedding of the empirical native
point-feature distribution, conditioned on its original fine token, can supply
useful hierarchy context that fixed means and fixed low-order descriptors do
not represent. A native task bottleneck, trained efficacy and novelty are
UNKNOWN.

For each original fine leaf, apply the shared two-input value map
`phi = Linear(2C,C), GELU, Linear(C,C)` to each
`[native point value, original normalized fine token]` before the first private
group mean. At the middle and coarse scales apply the same map to
`[child state, original normalized parent token]`, then take the equal mean of
the original true-supported children. Apply a second shared map with the same
shape top-down: coarse uses `[own state, zero]`, middle/fine use
`[own state, parent synthesized state]`. These three outputs replace the
original refinement deltas before the existing raw skips and HCG.

The original SharedClusterBank, partitioner, memberships, raw token banks,
normalization, CSORT, HCG, decoder/network and single inst_feats delivery remain
unchanged. Six model files and the native YAML are byte-exact parent copies.
Only the private refinement integration and new private core differ.

## Difference from protected history

Historical `..._lite_agg` replaces the original lvl0 bank using a scalar
`2C -> C/2 -> 1` point-weight MLP, scatter softmax and weighted raw values.
NDE keeps the original bank mean and adds a separate C-dimensional transformed
value graph with no scalar weights, softmax or query conditioning. It does not
restart or repair the historical aggregation variant.

HRC starts from already-averaged tokens; NDE's first nonlinearity receives every
valid native point before its private mean. HVD/PSC/NSD add fixed variance,
coordinate cross-scatter or chain-energy summaries. NDE represents a learned
conditional distribution embedding rather than adding another hand-selected
moment. This is not a novelty claim. FLE point-neighbor exchange and CGCA
coarse-conditioned channel attention are not used or reopened.

## Constructed information check

At fixed positions `0,1,2,3`, feature values `[1,-2,1,0]` and their negatives
have the same mean, variance, position-feature cross moment and adjacent squared
chain energy. A possible value function `GELU(x+1)` has different mean outputs.
This only establishes constructed function expressivity. The illustrative
offset is not installed as a model bias, initialization or hyperparameter;
the actual model uses the original default learned Linear initialization.
The example does not diagnose a native population error or prove benefit.

## Actual software checks and limits

`static_check.py` performs 33 bounded checks: all eight Python files parse and
compile without execution; exact nine-file hashes; seven byte-exact parent
copies; unchanged original bank/partitioner/CSORT/HCG ASTs; sparse/gapped true
ancestry, input permutation, empty/single supports and invalid IDs; private
graph integration; fixed YAML; and the constructed mathematical example.
Only the pure support-plan function is extracted and executed. No Torch import,
model forward, native data, autograd, optimizer update, GPU or resource
measurement is executed.

Preparation failures are preserved. Attempt 1 refused because the producer
child thread was not the root lease thread; the corrected builder verifies the
actual root owner and separately records the producer identity. Attempt 2
refused a line-ending-sensitive literal after copying three byte-exact files.
The final attempt reconciled those files by byte equality, copied only missing
files and used line-ending-neutral exact token replacements without rewriting
old sources.

Native forward/backward, original two natural TRAIN batches/common
initialization, whole-core finite gradients and real weight/module updates,
complete matched resources and independent actual review remain NOT_RUN.
Current repeated runtime failures remain inconclusive implementation/runtime
evidence; this reserve is not an NSD recovery or a bypass.

No commit, main/index change, deployment, queue addition, execution binding or
training is performed by this preparation.
