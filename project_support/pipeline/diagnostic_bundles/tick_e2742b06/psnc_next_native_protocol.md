# PSNC: pending native checks and source-version boundary

This is a plan, not execution evidence. HRC currently occupies the only
authorized GPU0. PSBR is already admitted at source commit
74fcd21df0af9a971792038ffe251af1ffea2604 and waits in FIFO order.

The proposed realization is fixed before native execution:
f = original middle FFN composed with its original LayerNorm, b = f(0).
For each occupied original coarse-parent group, sort middle rows by detached
original centroid (x,y,z,originalID), use fixed orthonormal DCT-II Q, and compute
the middle increment Q^T (f(QX) - b) + b. The original outer X+ increment remains.
Fine/coarse FFNs and original raw banks, IDs, CSORT, HCG and final inst_feats
readback remain. The zero-response work row must retain parameter autograd,
and must never enter a cluster ID bank or readback. No new learned parameters.

## Promote only when existing admitted work is safe

Keep this source and native YAML outside the Cluster repository now. The
preparation's base commit is provenance; it does not contain this new source.
No tested new code_commit, admission receipt or training task exists yet.

Before a later scoped source promotion, first verify PSBR has successfully
launched, or otherwise reconcile all outstanding admitted74f tasks so a new
HEAD cannot invalidate their canonical fresh-dispatch equality check. Preserve
the existing28dirty files and empty index. Only the new nine files may enter a
new project-authorized commit. Never sync or modify a checkout in active use.
The same future committed realization/config must be the one actually tested,
receipted and dispatched; never attach new evidence to the old74f version.

## Future real checks

Use fresh owning thread/token/context/pending/original deadline and the current
GPU whitelist, physical UUID, live idleness, exclusive locks and exact source,
data/pretrain/native-entry hashes. Only then import torch or use GPU0.

Run original M95 and candidate with the original native YAML/seed1999,
backbone pretrain, original TRAIN loader, optimizer/scheduler and two real
TRAIN batches. Record the actual input fingerprints, parameter initialization
scope, finite losses/backward, optimizer steps and updated original FFNs.
Observe that the fixed analysis, original middle nonlinear FFN and inverse
synthesis actually reach the unchanged HCG/inst_feats/mask path. Do not infer
training efficacy from these two steps.

Inspect group support ids1[ids0], original ids2/coordinates/ID order, disjoint
parent and batch boundaries, inverse scatter and the absence of sentinel IDs.
Original nonparticipating empty/padded work rows retain their original FFN
handling. Record whether nontrivial empty/padding/singleton cases actually
occurred; a vacuous assertion is not empirical coverage.

Separate the mathematical properties from tensor tests. Orthogonality and the
zero/singleton/affine identities are real-number properties of deterministic f.
The original dropout is0.0 and must not be changed to make a check pass. Test
the actual dtype/shape transform and direct singleton/zero behavior as scoped
operator diagnostics; do not claim bitwise FP32 equality from algebra.
If an identity-Q control is used, distinguish the full candidate K+1 work
layout from a direct original-layout M95 control. Batched GEMM layout effects
must be measured and disclosed; preserve pre-registered tolerances rather than
changing precision, thresholds, initialization or dropout after observing them.

Cross-sibling derivatives may diagnose the new nonlinear dependence; affine
or specially degenerate f can cancel it. Pure mode-row permutations commute
with shared f and can be equivalent controls; generic sign changes do not
commute with GELU/LayerNorm/bias. Do not mistake an equivalent relabeling for a
geometry intervention or add an unperformed ablation as an admission gate.

Run a separate original-resource M95/candidate pair on the same measured input
and original handlers: bs1/lang1/warm20/repeat100/median/P90, all unsupported
operators and prediction peaks. Count the sentinel FFN row and fixed mixing.
Default10G and the existing relative-memory rule remain. Smoke observers or
probes are not pure TRAIN peak measurements; pure TRAIN may remain UNKNOWN.

Only real reviewed native/resource results and unchanged constraints/config
independence can become standard experiment-first summaries, a receipt and a
canonical queued task. Local AST/stdlib reference tests are supporting evidence
only. No source promotion, native check, GPU experiment, resource PASS,
receipt, queue entry, source sync or launch is claimed by this document.
