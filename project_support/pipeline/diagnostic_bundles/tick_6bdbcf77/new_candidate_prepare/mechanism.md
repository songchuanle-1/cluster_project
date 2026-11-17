# M215-BEC: cross-level bipartite edge composition

This is one whole-forward structural hypothesis, not proven attention, independent algorithmic novelty, a single-factor causal effect, or a repair/resume of a stopped route. Original M95 uses independent per-level FFNs. BEC tests whether joint child/parent nonlinear edge analysis followed by coarse-conditioned two-level synthesis provides useful hierarchy information in the original final inst_feats path. Efficacy and the alleged task deficit are UNKNOWN.

Let original raw banks be X0 fine, X1 middle, X2 coarse; original memberships p1:fine→middle and p2:middle→coarse are unchanged. True supported fine IDs are unique ids0 from real points; supported middle/coarse IDs are their exact composed ancestors. All shared maps act on actual edges, not CSORT child_maps or invented point routing.

F0=LN0(X0), F1=LN1(X1).
[U0_i,V0_i]=GELU(A0 concat(F0_i,F1_p1(i))).
B1_j=equal mean of V0_i over true-supported fine children i of j.
[U1_j,V1_j]=GELU(A1 concat(B1_j,X2_p2(j))).
B2_k=equal mean of V1_j over true-supported middle children j of k.
Delta2=original FFN2(original LN2(B2)), zero-masked outside true-supported coarse slots.
H2=X2+Delta2 (the original coarse cf skip).
Delta1_j=GELU(S1 concat(U1_j,H2_p2(j))).
Delta0_i=GELU(S0 concat(U0_i,Delta1_p1(i))).
Refined=[X0+Delta0,X1+Delta1,H2] → original HCG → original single inst_feats update.

A0/A1 are distinct shared 2C→2C Linear maps; S1/S0 are distinct shared 2C→C Linear maps. The two output branches of each A have separate parameter rows. U is a retained child representation for later synthesis; V is the upward evidence collected for its parent. Fine generates edge evidence and consumes synthesized parent information; middle collects fine evidence, analyzes it with raw coarse context and synthesizes its own delta; coarse applies the original coarse LN/FFN once to collected evidence and supplies its original-skip-refined state downward. Thus fine and coarse are no longer merely unchanged independent FFNs around a new middle-only operator.

Only the three baseline cf additions remain. U/V are private split-message branches, not extra residual or inst injection. Original raw mean construction, FPS, original IDs, CSORT inputs/body, HCG class, original decoder and final delivery stay unchanged. There are no learned pooling scores, selectors, attention/QKV, language route, new gate/scale, pointN² interaction, new loss, data or schedule change.

Private equal means count true-supported child-token rows once, not child point populations. Original raw mean may have different fixed-empty-row semantics and is preserved. Unsupported internal slots and batch padding do not create private edges or biased upward/downward contributions. Their deltas are zero; original cf remains. The coarse FFN is still called once on its full padded bank; its unsupported output bias is explicitly masked before both skip and downward use. One-child groups still use the same four operators and equal means; empty groups never invent a child or divide by zero. No feature-value threshold infers support. Plan construction scans original-ID support and appends each edge once, with deterministic original-ID restoration and O(NpointIDs+Kfine+Kmiddle+Kcoarse) metadata work.

The original constructor creates its three FFNs and three LNs in original order; replaced FFN0/1 then become Identity (no unused weights). Four new Linear modules use default initialization inside CPU-only fork_rng(devices=[]), without manual_seed or init search. Original LN0/1 apply to raw fine/middle exactly once; original LN2 applies to collected B2 and original FFN2 runs exactly once. Actual common initialized parameter equality/loader pairing remains unmeasured. Reusing an isolated random stream can correlate new weights with later original initialization draws; no benefit is claimed.

At C256 new four maps have 787968 parameters, replacing 1051136 in two old FFNs; original coarse525568 remains. Token-refinement total=1313536 vs1576704, delta=-263168, source inference only. Dense-map MACs per batch item change from8C²(Kf+Km+Kc) to6C²(Fsupport+Msupport)+8C²Kc, plus linear-size concatenation/means/gathers. Parent-context duplication, activation storage, CPU-ID conversion and small group kernels can still hurt latency/memory; whole-model fvcore/unsupported/latency/memory remain UNKNOWN and must use the original paired protocol.

Nearest checked routes: CCP is additive child+parent broadcast; REAG_CASC updates points twice and rebuilds raw banks; HRC pools refined children before each next independent FFN; lite_agg changes rawbank pooling with learned weights. BEC instead performs joint child-parent nonlinearity before new-message pooling and preserves a second output branch for a separate two-level synthesis, followed by one original HCG. It is related to generic bipartite message passing/encoder-decoder graphs, not a literature-novelty claim. HAP geometry affine prolongation, M206 coarse Gram channel mixing and all held/failed routes stay unchanged; this is not their new revision. A capacity-reduced multi-part wholegraph comparison cannot isolate any one direction/map as the cause of a future score change.

Local evidence uses actual production plan, mean and full forward AST with stdlib numeric/set tensor-interface carriers. Set cells audit possible dependency provenance, not numeric Linear/GELU values or autograd; numerical equal-mean checks are separate. No Torch/CUDA, real input/gradient/optimizer/resource/accuracy result exists. Source commit and future parent remain null; this packet neither modifies nor versions primary/runtime or creates a sibling branch.
