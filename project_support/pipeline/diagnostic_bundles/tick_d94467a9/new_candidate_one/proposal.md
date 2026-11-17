# M228-NEC: coupled node-edge state composition

Stable ID: `hierarchy-coupled-node-edge-state-composition`. This is one new source-only point-feature hypothesis, not a renamed SFC/ELC/PES or reopened held/rejected route. Code/source/actual-parent remain NULL; current WFC94 is only a compatibility reference.

On the unchanged point-supported original fine-middle-coarse forest, retain BOTH one C-vector `h_v` per true node and one C-vector `e_uv` per true undirected original membership edge. Initialize `h0=original3LN(raw)` and `e0=0`. For each component's genuine tree diameter D (2 or4), use shared maps `E,N:2C→C` with the original GELU:

`e_uv^t = GELU(E[ e_uv^(t-1), (h_u^(t-1)+h_v^(t-1))/2 ])`

`h_v^t = GELU(N[ h_v^(t-1), mean_{uv incident v}( e_uv^t ) ])`.

Each round synchronously replaces all active edge states using the SAME OLD node/edge states, then synchronously replaces node states using OLD own nodes and newly updated incident edges. Components stop after their actual D; no fake padded/finished-component updates. Final `hD` is the three delta banks, not `hD-h0`; scatter to original IDs, then the original three raw skips/HCG/CSORT/singleinst/ILA/mask path. Raw means/FPS/IDs, three LN calls and all training/YAML values stay unchanged. Empty/pad/unsupported delta0.

The closest actual graphs differ: SFC has only node states and applies T after OLD neighbor-node mean; ELC has only undirected edge states and applies line-graph OTHER-edge recurrence then final node means; PES asynchronously changes only a receiver node. NEC persistently feeds nonlinear node and edge states back into each other, with node updates every round. It is an ordinary coupled node-edge message-passing family, not a novelty claim or diagnosed task bottleneck. Original ancestor raw features already contain descendants/global context; this introduces no new raw information or physical self-exclusion.

At C256, two new2C→C maps use262656 parameters versus original3FFN1576704; source delta−1314048. For maximum original N328/E320 with D4, learned linear MACs339738624 versus original171966464. Applying only that linear delta to historical M95 9.762532428G gives a SOURCE proxy9.930304588G, not a profile or10G PASS. No width/round/degree/sampling cap or handler change is permitted to force acceptance. Metadata and tensor gather/mean/copy costs, memory and serial latency remain unmeasured.

Risks include endpoint-mean loss of child/parent difference, backtracking self-information, oversmoothing, repeated-state loss/amplification, edge-state redundancy and extra state memory/kernel cost. Some parameters or individual maps/rows may have zero gradients; both initial edge states and first-round own-edge columns may be zero legitimately. Task benefit, novelty, native FP32/autograd and resources are UNKNOWN/NOT_RUN. No failure of another candidate is repaired or explained by this proposal.
