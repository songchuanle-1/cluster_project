M217-CRE: supported coarse-root directed exchange, then original-ancestor synthesis

For each original raw bank X_l, use its original LayerNorm z_l=LN_l(X_l).
Real point support follows ids0, ids1[ids0], ids2[ids1[ids0]]. Let R be the
sorted original supported coarse IDs. For p,q in R with p!=q:

e_pq = GELU(U concat(z2_p,z2_q)); m_p = equalmean_{q!=p}(e_pq).
delta2_p=m_p; delta0_i=GELU(D0 concat(z0_i,m_ids2[ids1[i]])).
delta1_j=GELU(D1 concat(z1_j,m_ids2[j])). Refined_l=X_l+delta_l.

U,D0,D1 are three independent shared Linear(2C,C) maps; the original GELU
activation family and three original outer skips/LNs are preserved. No new
residual path, gate, scalar, learned pooling score, QKV, language routing or
point reassignment is introduced. No upstream refined-child pooling is used.
All root edge messages use the same original normalized coarse states. D0/D1
read m itself, not rawcoarse+m. The graph's new hierarchy-branch edges cross
original coarse subtrees and then reach supported fine/middle original IDs.
This does not claim that the entire original decoder lacked global interaction.

With one supported root use the same U concat(z_p,private_zero); this private
slot has no original ID. No supported root means no map work and three zero
deltas. Unsupported fine/middle/coarse slots and batch padding have zero delta,
preserving their original raw cf skip. This intentionally replaces the original
empty-slot FFN-bias updates; raw aggregation/IDs/FPS/CSORT are unchanged. Original
HCG, its existing level gate, final single inst_feats update and mask/loss path
are unchanged. No extra point/decoder-layer injection occurs.

Constructor first builds all original FFNs/LNs in the original order. New maps
are constructed only inside torch.random.fork_rng(devices=[]), without manual
seed or initialization search. Then all three removed FFNs become Identity,
leaving no unused original FFN parameters. This preserves intended common RNG
progression but is not actual paired-initialization evidence; sequence reuse
correlations and FP32/GEMM-layout differences remain possible.

Native K2=8 gives at most56 real directed root edges per scene. At C256, new
maps have 3*(2C²+C)=393,984 parameters versus original3*(8C²+5C)=1,576,704,
delta -1,182,720 (source arithmetic, not measured full-model inventory/FLOPs).
Pair generation is O(K2²), original ID traversal/recipient construction linear
in its metadata size. Fixed mean is private edge-message reduction, not a raw
bank learned pooling replacement. Removing fine/middle wide FFNs suggests a
cost advantage, while coarse dense edges, CPU tolist/grouping, launch shape and
new graph can still increase latency or memory. Original native resources must
decide actual <=10G/unsupported/memory; no measured claim is made here.

Near neighbors: BEC composes membership-tree upward split/mean/down messages;
CRE has no upward branch and explicitly exchanges different coarse roots first.
CPA uses point-query/coarse attention, CGCA uses coarse Gram fine-channel mixing,
CCP adds original ancestor features, MDC uses directional geometric middle
stencils, and parent-chain/tree/butterfly/triadic/edge-flux candidates act through
different graphs. Fixed vector-message averaging alone is not evidence of
novelty. This is a whole-graph matched-M95 alternative, not a single-factor causal
ablation, a repair of held routes, a new-coverage or an efficacy claim.

Only private frozen source preparation is produced. Source/code commits are
null;026c is the current source/future-parent reference. A separately recorded
isolated source version may use that actual parent. If main later changes (for
example AEF56 sibling promotion), require compatible packaging and native tests
of that exact version; never assume sibling fast-forward or relabel old results.
