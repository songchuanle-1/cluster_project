# M213-BFC: parent butterfly token composition

Status: PREPARED_STATIC_ONLY_UNEXECUTED. Stable ID: `hierarchy-parent-butterfly-token-composition`. Source commit is null; parent/base reference is11a811618179ab1ddc0cee299194667413b7fdb9. Files are external preparation only. No installation, primary checkout mutation, commit, sync, lease or GPU/native execution occurred.

Only the original middle FFN delta changes. Original fine/coarse FFNs, all three LayerNorms, raw hierarchical means/FPS/IDs/CSORT, HCG point readback, original middle `cf + delta` skip and single inst_feats writeback remain. Five other model files and native YAML are byte-identical to M95. New operator weights use ordinary nn.Linear default initialization and original GELU; no dropout/numeric schedule change. The original constructor finishes before a fork_rng(devices=[]) creates the new module, without manual_seed or initialization search. Actual common parameter/loader pairing remains NOT_RUN.

## Exact graph

Let x=LN(cf_mid). True middle support is computed from actual points by ids1[ids0], not feature magnitude or fine-slot occupancy. Original middle centers are the existing detached fine-mean then middle-mean coordinates per_layer_coords[2]; original ids2 remains middle-to-coarse membership. For each actual parent, supported original middle IDs are sorted lexicographically by(x,y,z,originalID), giving ranks0..n-1. There is no learned selector, new point partition or new geometry pooling.

For n>=2, m=ceil(log2(n)) and bit sequence is(0,...,m-1,m-2,...,0). At each bit, pair ranks i<j<n with j=i XOR2^bit. With one shared W of shape(2C,2C) and bias b, compute jointly

    [s_i_next, s_j_next] = GELU(W [s_i_old, s_j_old] + b).

Both output halves use the same old stage; all pairs are disjoint. Unpaired real states carry unchanged for that stage. Parent groups at different local bit positions can share a batched round because their domains are disjoint. All n C-dimensional states remain present throughout; this does not imply injectivity, invertibility or no information loss. Original-ID inverse scatter writes final states as the middle delta. The unique baseline outer skip adds original raw cf.

n=1 uses the SAME W/GELU on[x,0] and takes first C outputs; no new C-to-C singleton map. The zero is private boundary input, not a real/padded hierarchy ID or extra bank row. n=0 invokes no map. Unsupported internal IDs and batch padding never participate in any pair and receive delta0, preserving original cf. These scalar/topology cases are tested, but torch tensor boundaries are NOT_RUN.

## Hypothesis and close mechanisms

M95 middle FFN acts independently on each middle token. BFC asks whether multi-stage same-parent interactions that preserve separate token states provide useful point-mask context without compressing a whole subset into one summary. This is a concrete, falsifiable structural branch; efficacy and error-subset improvement are UNKNOWN. Original M95 is the matched native control with identical YAML/data/seed1999/epochs50/max_iters70, original pretrain and real batches.

BTC reduces subtrees to C-dimensional inside summaries and forms outside complements; BFC never reduces token count and has no complement/exclusive-context claim. BCR/PSBR accumulate directional chain states; BFC revises both token states jointly at every matching round. PSNC performs one fixed DCT analysis/row FFN/synthesis; BFC inserts a nonlinear joint map between successive sparse matchings, without a fixed conjugation or zero-response-preservation claim. MDC is one directional neighbor convolution; BFC uses repeated parent-internal rank XOR matchings with no distance kernel. This bounded comparison is not proof of whole-history or literature novelty. No held RSTR/PCE/other hold is reopened.

One shared2C-to2C map has4C^2+2C=262656 parameters at C256 versus original middle525568: inferred delta-262912. This is not a<5K Linear/LN/scale tweak: new cross-token edges, repeated nonlinear stages and two updated token outputs replace per-token processing. No QKV, gate, new residual path, language routing, normalization/scaling change or extra injection is added.

## Cost and risks

For configured original middle K<=64, no group has n>64; at most11 rounds. A coarse upper bound on counted linear MACs is2*C^2*K*(2ceil(log2 K)-1), using at mostK/2 pair rows each round, plus bounded singleton work. Compared with original8*C^2*K, maximum middle-map excess is approximately58.72M MACs for K64/C256. This loose source bound excludes actual handlers, GELU, gathers/scatters, CPU synchronization and allocations; it is not a10G profile or latency claim. Exact fvcore/unsupported/timing/memory remains NOT_RUN.

Repeated GELU/mix may attenuate/amplify features; unpaired truncation gives nonuniform path lengths and fixed left/right roles. Geometry order is axis-dependent; exact coordinate ties use originalID and do not promise relabel invariance. Default-init RNG reuse correlations may remain even though common RNG progression is isolated. Context reachability does not establish tensor Jacobian magnitude, original-loss usefulness or accuracy. Original M95 control changes operator parameterization/depth as well as topology; no single-factor causal attribution is claimed.

## Actual local evidence

static_check.py extracts the REAL build_butterfly_plan AST and runs it with stdlib only. Final result:197963 assertions,152 valid production plan calls and13 invalid-metadata refusals; supported n0..128 exhaustive, actual native cap remains64. It checks disjoint old-state matchings, source IDs/support/parents, complete final same-parent reachability, deterministic ties, non-power-of-two groups, original-ID restoration for uniquely positioned metadata permutations, original byte/AST paths and constructor wiring. These are not197963 experiments or native/autograd runs.

First local harness run requested nonexistent baseline method get_cluster_center and stopped before plan tests. Actual method is cluster_layer. Initial checker snapshot and failure JSON are retained; only checker lookup was corrected. Model source stayed unchanged. No native failure or scientific candidate revision was recorded.
