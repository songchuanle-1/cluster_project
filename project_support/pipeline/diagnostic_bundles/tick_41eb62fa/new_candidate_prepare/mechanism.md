# M212-BCR — exclusive bidirectional complement recurrence

Status: **PREPARED_STATIC_ONLY_UNEXECUTED**, `code_commit=null`. Stable ID:
`hierarchy-parent-bidirectional-complement-recurrence`. This is a structural
fork close to PSBR/BTC, not a claim of independent literature novelty or a
reopening/repair of an old held or rejected experiment.

Only the M95 middle operator changes. Original `cf + FFN1(LN1(cf))` becomes
`cf + BCR(LN1(cf))`. The original raw-cf skip, LN1, fine/coarse FFNs, raw banks,
FPS/IDs, CSORT, HCG and single final inst_feats injection stay. FFN1 is replaced
by Identity in the registered ModuleList; no unused525568 parameters remain.
No new gate, attention/QKV, language route, residual, scale or learned index is
introduced. The original zero dropout and three hierarchy levels are checked.

For one batch and original coarse parent, use only true point-supported middle
tokens, determined by `bincount(ids1[ids0])>0`, and their original `ids2` parents.
Sort by detached original middle centroid xyz then original ID. These centers
are the original partitioner's `per_layer_coords[2]`, with unchanged means/FPS.
The work plan never renumbers original IDs or changes CSORT child maps.

For ordered normalized inputs X=(x0,...,x(n-1)), define a shared map
`G(x,h)=GELU(Ws[x,h]+bs)`. GELU is the original middle-FFN activation.

* `L0=0`; `Li=G(x(i-1),L(i-1))`, i=1,...,n-1.
* `R(n-1)=0`; `Ri=G(x(i+1),R(i+1))`, i=n-2,...,0.
* `delta_i=Wf[xi,Li,Ri]+bf`; refined token is the original `cf_i+delta_i`.

Both directions share the same Ws. Only the consumed2(n-1) states are computed;
there is no unused inclusive terminal state. Each direction resets per parent
and batch. Prefix/suffix exclude xi, are disjoint, and together cover precisely
its other supported siblings. A singleton computes Wf[x,0,0] with zero scans;
an empty parent has no plan. Unsupported internal IDs and batch padding enter
no chain, get zero delta, and retain original cf through the original skip.
Outputs scatter to original IDs. Geometry/support are detached; feature states
and readout remain on the graph. No buffers or parameters store the work plan.
Original raw-bank/CSORT empty-slot semantics are preserved. This does not claim
native empty/padding boundary coverage from a scalar topology check.

The closest existing PSBR actually computes inclusive h_i from xi and its prior
state, then Wo[h_i_forward,h_i_backward]; its contexts already include xi. BCR
reads the two pre-own transitions and routes own only to Wf's own columns.
For a fixed plan, the BCR delta Jacobian with respect to normalized xi is Wf's
own block, independent of its siblings. PSBR's inclusive terminal nonlinearity
generically mixes own/sibling effects. This is a graph distinction even without
using activation choice as the justification. It is not a proof that no weight
choice or degenerate/linear setting can make outputs agree. BCR also restores
the original M95 skip absent in the PSBR source, uses original GELU rather than
PSBR tanh, and has different readout capacity; a result cannot isolate one of
these factors or claim a single-factor causal explanation of PSBR's result.

BTC uses a balanced binary inside/outside tree and separate composition maps.
BCR uses two exclusive chains sharing one scan map and separate left/right
readout blocks, with sequential depth n-1 rather than a balanced tree. They
share a complement-information hypothesis but are different factorizations.
HRC refined cross-scale means, PSNC DCT conjugation, MDC one-hop convolution,
RSTR reversible transport and PCE leaf contact are not this scan graph. Limited
current-record keyword and nearby-source checks found PSBR as the nearest
record; this is not an exhaustive history search. All old holds remain intact.

Two maps at C256 have `(2C*C+C)+(3C*C+C)=328192` parameters, replacing525568
(static delta -197376). Actual registered inventory is NOT_RUN. Per n>=1
parent, dense multiplication count is proportional to `(7n-4)C²`; two serial
scans and CPU geometry transfer/sorting can still be slow. The at-most64 middle
slots bound comes from the unchanged native hierarchy, not a new tuned number.
There is no new point-N-squared matrix. Latency/memory/FLOPs remain unmeasured;
fewer parameters do not establish the original10G resource gate.

After the original constructor has consumed its original RNG, only new module
construction uses `torch.random.fork_rng(devices=[])`. No manual seed/default
initializer change or search occurs. It intends to preserve later common CPU
initialization and loader RNG position, but actual paired parameters/batches
are NOT_RUN. Reused random-number subsequences can correlate new/common weights.

The matched control is actual M95 with byte-identical native YAML, seed1999,
epochs50, scheduler max_iters70 and original data/optimizer/resources. Hypothesis:
exclusive sibling contexts may preserve complement evidence from own-token
re-encoding. This is unproven; weaker own/context joint nonlinearity, long-chain
attenuation/explosion, orientation/tie sensitivity and extra synchronization may
hurt performance. Ordering is not claimed rotation invariant or tie-ID invariant.

Future native protocol is recorded in native_protocol.md. It must run original
TRAIN2/loss/backward/optimizer, observe actual tree-free scan path and separately
measure Ws recurrent-state columns and Wf left/right columns on real n>=3 groups.
Pure plan support does not prove a nonzero numerical gradient or task benefit.
No seed/batch/readout selection or threshold change is authorized by preparation.
Accuracy, all native tensor behavior and all original resource checks are UNKNOWN.
