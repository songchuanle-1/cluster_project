# M211-BTC — parent binary-tree complement composition

Status: **PREPARED_STATIC_ONLY_UNEXECUTED**. Stable candidate ID:
`hierarchy-parent-binary-tree-complement-composition`. No Git commit is bound.

The baseline is the actual M95 package on primary commit
`74fcd21df0af9a971792038ffe251af1ffea2604`. Its original middle update is
`cf + FFN1(LN1(cf))`. BTC changes only that operator to
`cf + BinaryTreeComplement(LN1(cf))`. The original outer skip remains.
The fine/coarse FFNs and every original LayerNorm remain; the removed middle
FFN is replaced by Identity in its ModuleList, so it has no unused parameters.

For one batch item, true middle support comes from `ids1[ids0]`, not token
feature values or the number of fine slots. Original `ids2` assigns each true
middle token to its coarse parent. Within each such parent, a balanced binary
work tree recursively splits the supported tokens at the median of their
detached original middle centroids along the longest spatial extent. Axis ties
use x/y/z; ordering ties use axis coordinate, xyz, then original middle ID.
Centroids are the original partitioner's fine-mean then middle-mean coordinates
`per_layer_coords[2]`; no FPS, ID, raw mean, or child map is recomputed differently.

Let `x_t = LN1(cf_t)`, with concatenation written `[a,b]`:

* Leaf inside: `I_t = x_t`.
* Proper internal node: `I_v = GELU(W_inside [I_left,I_right] + b_inside)`.
* Root outside: `O_root = 0`.
* Left outside: `O_left = GELU(W_outside [O_parent,I_right] + b_outside)`;
  right outside uses its left sibling instead. Both directions share this map.
* Leaf update: `u_t = W_leaf [x_t,O_t] + b_leaf`; refined token is `cf_t + u_t`.

The root inside is unused and is not evaluated. By induction, every inside
depends only on its own subtree, and a leaf's outside depends on exactly the
other supported leaves in the same original parent, excluding itself. This is
a statement about graph support, not proof that numerical derivatives are nonzero.
A singleton uses `W_leaf[x,0]`; no inside/outside map is called for it. Groups
of two call outside but cannot exercise inside weights. A future native check
must record actual groups of at least three to measure all three weight paths.

Internal unsupported middle slots and batch padding never enter a tree. Their
tree update stays zero, preserving original `cf` through the original skip.
Original HCG composed IDs never read unsupported middle slots for a real point.
All outputs scatter back to the same original middle IDs. Parent/batch state
is local and resets on each forward. No tree node is added to raw banks, IDs,
CSORT, HCG, or state_dict. CSORT still uses the original raw banks. HCG, the
existing level gate and the existing single final inst_feats injection remain.

At C=256, three shared Linear(512,256) maps have 393984 parameters, replacing
the original 525568 middle-FFN parameters (static net delta -131584). GELU is
the original M95 activation; dropout remains the original zero and is checked.
Only new module construction is enclosed in `torch.random.fork_rng(devices=[])`,
after constructing the original modules. No manual seed or initializer changes.
This preserves the subsequent CPU RNG position in the intended control, but
actual common initialization and loader fingerprints are **NOT_RUN**. Random
sequence reuse can correlate new weights with later common initialization.

For n>=2 leaves, a parent uses n-2 proper-inside, 2n-2 outside and n leaf linear
calls, with depth at most ceil(log2 n). Total token work is linear in at most
64 original middle slots, not point N squared. The three shared maps have 6C²+3C
parameters in total, not attention Q/K/V. Many small GEMMs and CPU
geometry synchronization may increase latency despite fewer parameters. No
FLOP, GPU-memory, unsupported-op, or latency result has been measured.

This graph differs from HRC's cross-scale refined means, PSBR's two sequential
tanh states, PSNC's fixed DCT analysis/nonlinearity/synthesis, MDC's one-hop
directional convolution, and RSTR's fine-token reversible Markov transport.
It adds neither a gate, language routing, repeated injection, point exchange,
new residual, nor numeric-only change. A limited goal/current-candidate and
near-route check found no explicit same graph; this is not a full-history or
literature novelty claim and does not reopen held routes.

The matched control is unmodified M95 with the byte-identical native YAML:
seed1999, epochs50, scheduler max_iters70, original data, original budget.
Future checks require actual two original TRAIN-loader batches through
tools.train.train/loss/backward/optimizer; finite gradients and actual updates
for inside/outside/leaf (with recorded n>=3 true group); raw-bank/CSORT/HCG and
single-injection observations; matched input fingerprints and common parameter
initialization evidence. Same-forward geometry/support/order/scatter must be
recorded. A frozen-weight outside-zero intervention or offdiagonal derivative
can falsify claimed sibling use, but is an auxiliary diagnostic, not a newly
invented admission threshold. Keep the original resource protocol: bs1/lang1,
fvcore original handlers, warm20/repeat100 and original 10G/memory rules.

Actual offline evidence: static_check.py compiles the eight real source ASTs,
checks unchanged base bytes/AST and original YAML bytes, and executes only the
production pure topology function extracted from middle_tree.py. It checks
boundaries, exact leaf coverage, disjoint subtrees, depth, and complement sets.
These checks do not import torch and do not substitute a mirror model.
Tensor shapes, autograd, actual parameter inventory, numerical behavior,
FP32 controls, real empty/padded examples, accuracy and all resources remain
**NOT_RUN**. Axis-aligned split topology is rotation dependent, and coincident
centers can make original-ID ties relevant. Effects on accuracy are unknown.

Files are external preparation only. Future version retention must be a child
of PSNC43 (`43dce016c1a1713c2a5dab7061810dc2efde8954`) when root authorizes it;
this packet does not change primary HEAD, index, protected files, or PSBR FIFO.
