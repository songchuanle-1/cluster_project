# Research Rethink: Problem, Mechanism, and Derivation

Date: 2026-09-10. Status: research proposal, NOT an admitted experiment.
User request: rethink subsequent research around core novelty, a specific
problem, and explicit mathematical derivation.
No model, queue, schedule, deployment, or goal changes are authorized by this memo.

Follow-up: the user's subsequent request to change experiment coverage is
implemented in pipeline/goal.json and docs/experiment_scope_20260910.md.
That later policy broadens diagnosis and validation; it does not select this
memo's anchor hypothesis as the final mechanism or cancel the existing batch.

## 1. What The Existing Evidence Actually Supports

- M95 reaches 0.5020 versus baseline 0.4894, but replication is seed-fragile.
- A1 context-only 0.5012 supports context usefulness in the observed comparison;
  it does not establish the unique reason for improvement.
- Active routing A3 0.4468 versus shuffled A4 0.4941 argues against the routing claim.
- Aligned M161 0.4920 is below shuffled M162 0.4980. This weakens alignment as the
  explanation; it does not by itself prove that generic scene context causes gain.
- M170 already tried aligned-minus-shuffled context and reached 0.4970 with
  compromised patience. Feature subtraction is not a new causal intervention.
- M183 ancestor initialization ended normally at 0.49154922. M192 exceeded 10G
  and was never trained; its rejection says nothing about accuracy.
- M184-M193 are primarily bounded structural ablations, not established novelty.

Sources: pipeline/goal.json; pipeline/codex_memory.md;
pipeline/analyses/M161-CTF-HCG-CSORT-MQF_done_earlystop_20260903-1109.md;
pipeline/analyses/M162-CTF-HCG-CSORT-MQF-SH_done_earlystop_20260903-2012.md;
pipeline/analyses/M170-CTF-HCG-CSORT-MQR_done_earlystop_20260905-2309.md;
pipeline/designs/exp_design_20260903-2013.md.

Code inspection: the champion has instance/language interaction, query-instance
attention, query-language attention, and query self-attention. It can encode
relations implicitly. Do not say it has no relational reasoning, or that its
actual score is mathematically identical to the relaxed model below.

## 2. A Specific, Currently Unverified Failure Hypothesis

Question: among same-category candidate objects, can different constraints be
satisfied by DIFFERENT physical reference objects, producing a false match?

Example: "the chair left of and close to the table." A false chair can be left
of table A and close to table B, with neither table satisfying both constraints.
The intended reading binds both predicates to one table. Sentences explicitly
referring to two different tables must NOT be forced to share a reference.

Hypothesis: evidence aggregated without preserving reference identity may rank
this false chair too highly. The multi-scale cluster representation adds a
second risk: parts and ancestors of one object may be counted as independent
evidence. Both are hypotheses, not measured failure frequencies.

Candidate contribution to investigate: reference-identity-consistent relation
verification whose score is invariant to purely representational subdivision.
This is a sharper target than adding more context or another pooling operator.

## 3. Derive The Identity Constraint Before Choosing A Module

Let i denote a target candidate; a a physical anchor identity; and r=1,...,R
predicates that refer to the SAME anchor mention. Let l_r(i,a) be a finite
compatibility energy, with larger values meaning better compatibility.

Independently choosing witnesses solves the relaxed problem:

    U(i) = sum_r max_a l_r(i,a).

Sharing an anchor identity solves:

    C(i) = max_a sum_r l_r(i,a).
    C(i) <= U(i).

Proof: for every a, each l_r(i,a) <= max_b l_r(i,b); sum and maximize.
Equality holds iff the predicates have a common maximizer (finite nonempty
anchor set). The gap U-C measures incompatible BEST witnesses in this idealized
model. It is not a measured property of the existing decoder.

Two predicates and two anchors give a minimal counterexample:

    wrong candidate: l = [[0, -4], [-4, 0]]; U=0, C=-4
    right candidate: l = [[-1, -3], [-1, -3]]; U=-2, C=-2

Independent maximization prefers the wrong candidate. Shared identity reverses
the ranking. These numbers illustrate the proof; they are NOT hyperparameters.

## 4. A Differentiable, Multiplicity-Aware Form

Use anchor masses pi_a >= 0, sum_a pi_a = 1, identical across competing targets
for the same anchor mention. Define E_i(a) = sum_r l_r(i,a), and:

    J(i) = log sum_a pi_a exp(E_i(a)).

This is a chosen latent-energy model, not a calibrated physical likelihood.
No independence of observed predicates is being asserted. Additivity assumes
the selected predicate factors adequately represent the sentence.

Variational derivation, for q supported on positive pi:

    J(i) = max_q { sum_a q_a E_i(a) - KL(q || pi) }
    q*_a = pi_a exp(E_i(a)) / sum_b pi_b exp(E_i(b)).

Proof: substituting q* gives the objective = J(i) - KL(q || q*).
The objective is maximized at q*. Thus all predicates share ONE posterior q*,
instead of retrieving separate anchors and averaging their context vectors.

Gradient:

    dJ(i) / dl_r(i,a) = q*_a.

Jointly compatible witnesses receive the learning signal. A wrong confident
anchor or bad language binding can still dominate; this is not an accuracy
guarantee. With one predicate, the distinctive identity constraint disappears.

Subdivision property: replace anchor a by copies a1,...,am, with unchanged
energies E_i(aj)=E_i(a) and conserved mass sum_j pi_aj=pi_a. Then:

    sum_j pi_aj exp(E_i(aj)) = pi_a exp(E_i(a)).

J is exactly unchanged. Unweighted token log-sum-exp generally lacks this
property. This only covers equivalent subdivision, NOT actual changes to
geometry/features or two physically distinct objects.

Multi-scale implication: use one non-overlapping identity/support measure.
Parent and child clusters must not become additional independent witnesses.
Mapping overlapping clusters to physical identities is an UNSOLVED part of
the proposal. Assigning uniform weights to all hierarchical tokens does not
solve it, and merely inserting weights would not satisfy the research goal.

## 5. What An Implementable Model Would Still Need

- Target masks and language-independent anchor proposals with adequate recall.
  The current text-conditioned target proposals may omit anchors entirely.
- A reproducible language binding mechanism grouping predicates by referent.
  Handwritten parsing is suitable only for a bounded diagnostic, not a claimed
  general solution. No oracle parse or ground-truth anchor at test time.
- Relative geometry with defined coordinates. "Left" needs an appropriate
  reference frame; "near" is scale-dependent. No arbitrary thresholds disguised
  as derivation. Unary noun/attribute compatibility belongs in the energy model.
- A non-overlapping anchor identity measure pi, with invalid/self anchors
  excluded and a specified empty-anchor fallback. Point mass alone is not a
  justified prior over objects because it can favor large objects.
- A candidate score s_i = u_i + J(i), only after jointly defining/training u and
  relation energies. Directly adding J to a frozen, uncalibrated M95 score is
  NOT derived. Candidate cross-entropy is one possible training objective:

      L = -s_y + log sum_i exp(s_i).

  Existing mask assignment/loss compatibility and score supervision require
  inspection before choosing this objective. No extra loss-weight sweep.
- Complexity with Q targets, A anchors, R predicates, feature dimension d:
  O(Q*A*R*d), plus proposal generation. No pointwise N-by-N attention.
  A full proposal pair matrix can still be expensive; report it explicitly.
  Current M95 9.762532428G leaves only 0.237467572G under the nominal 10G limit.
  Actual full-model FLOPs, memory, median/P90 timing determine eligibility.

## 6. Novelty Audit: Explicitly Incomplete

Max-sum inference, latent-variable marginalization, KL variational identities,
and mass-conserving mixtures are NOT themselves new contributions.
Neither "relation reasoning" nor "anchor reasoning" is a novelty claim.
Even their combination may already exist.

Required primary-paper comparisons: relational 3D grounding, anchor/coreference
grounding, factor-graph/neural-symbolic inference, and hierarchical evidence
aggregation. For each, compare identity variables, exact aggregation equation,
hierarchy handling, supervision, and complexity.

Web search/open returned no usable content this turn; a CVF retrieval attempt
also failed to connect. No papers were verified and no priority claim is made.
The specific combined problem and implementation remain provisional. If prior
work already has this structure, do not rename it and present it as new.

## 7. Evidence Gates Before Any Training Admission

1. Diagnose a fixed, scene-stratified validation sample; annotate whether
   failures arise from proposal recall, mask boundaries, target semantics,
   relation recognition, or same-anchor binding. Record denominators, shared
   scenes, annotation disagreement, and same-class distractor counts.
2. Measure whether a good target proposal exists but is ranked incorrectly.
   If missing proposals/boundaries dominate, this ranking mechanism is the
   wrong priority. Do not invent a numerical prevalence cutoff after results.
3. Use oracle anchors/bindings ONLY to measure an upper bound. A deployable
   result must use predicted anchors/bindings with the same data access.
4. Hold proposals, geometry encoders, capacity, and schedule fixed; compare
   independent-witness vs shared-witness scoring. Also test anchor-identity
   permutation without changing marginal feature distributions.
5. Unit-test the counterexample, R=1 behavior, gradients, masks, and equivalent
   anchor subdivision. Distinct physical anchors must not be merged by this
   invariance. Test sentences referring to separate anchors as negative controls.
6. Check error reduction specifically on binding failures, plus overall mIoU
   and non-relational cases. Bootstrap by scene, not independent utterances.
   An mIoU increase alone does not validate the mechanism.
7. Respect seed1999, unchanged epochs50/max_iters70, <=10G, and existing bans.
   This is not language-conditioned routing back into instance features.
   Any later such injection would re-enter the banned family.
8. Reject the proposal if the failure is rare, oracle potential is negligible,
   predicted bindings erase the benefit, matched controls do not support shared
   identity, prior work subsumes it, or the resource budget is exceeded.

The new research standard is: observed error -> formal assumption -> derived
structure -> distinction from prior art -> falsifiable tests -> resource audit.
Queue depth is a scheduling concern, not evidence for a scientific contribution.
Existing runs and FIFO are preserved; this memo does not impose a global hold.

## 8. 2026-09-12 Addendum: The Anchor Proposal Is Not Admitted

The shared-witness hypothesis in Sections 2-7 remains a valid derivation of a
possible failure mode, but it is not the current selected mechanism. The fixed
21-description audit found no confirmed narrow two-predicate/same-anchor case,
and NS3D plus CSVG already cover broad joint-anchor or constraint-satisfaction
reasoning. Rebranding that structure would not establish the requested core
novelty.

The measured priority has moved to selection among disjoint same-category
instances. The correct mask is already present on the recoverable banks; the
wrong physical instance wins by a large score margin. Quality-head, language
support, and trained semantic-projection rerankers have now been measured and
closed. The next work must therefore derive a new score-formation mechanism
from M95's training-time query-to-instance supervision and mask-score coupling,
not add another readout to the frozen score.

The admission standard is unchanged: observed error -> formal variables and
assumptions -> an implementable forward/loss derivation with gradients and
degeneracies -> verified primary-source distinction -> matched control and
preregistered rejection -> resource audit. Until that sequence is complete,
no model or queue mutation is authorized.

## 9. 2026-09-12 Addendum: Selection Is Query-Only

The M95 score-coupling audit now shows why the measured mask-quality and
selection evidence can diverge. The deployed candidate score is

    z_q = indis_embedding(u_q)

while the candidate mask is computed by a separate path:

    m_{q,n} = u_q dot f_n

The auxiliary quality score is also `out_score(u_q)`, and inference selects
with `argmax softmax(indis)[:,1]`, not with mask-derived or quality-derived
evidence. Training assigns `indis` positives from seed position/instance
labels. Mask and quality losses supervise matched queries only, so selection
and mask evidence meet only through shared query features.

This is a concrete implementation discrepancy, but it is not yet a novel
mechanism. Standard mask-conditioned reranking would be the null explanation.
The next admissible step is either a bounded capture of real query/head/mask
tensors for a parameter and Jacobian coupling audit, or an N1 derivation whose
score field uses candidate-specific mask evidence in a structure that survives
primary-source comparison and matched controls. No queue refill follows from
queue depth alone.

### 9.1 Local Query-State Coupling Audit - 2026-09-12 03:15

The preserved 284-bank capture already contained the final decoder queries and
mask logits. The frozen checkpoint's final selection and mask heads have
disjoint trainable parameters; only the decoder query is shared locally. On
the 109 recoverable banks, the selected wrong candidate has mean score margin
3.081 versus -1.911 for the oracle. The oracle-supervised selection gradient
and oracle-mask improvement direction are near-orthogonal at the shared query
state: mean cosine 0.0148, with selected-to-selected 0.0443 and success
controls near zero.

This closes the local head-level Jacobian check without authorizing a
mask-conditioned selector. A full upstream parameter-Jacobian study remains a
separate bounded protocol, or the project continues with a
primary-source-distinct N1 derivation. See
`pipeline/reports/d1_parameter_coupling_20260912-0307/diagnostic_report.md`.

### 9.2 Legacy Terminal-Readout Result - 2026-09-12 04:08

M188 terminal-only MQB stopped early at epoch 23 with best mIoU 0.4916@13,
which is +0.0022 over baseline and -0.0108 below M95. The legacy
terminal-readout branch therefore remains validation evidence, not a route to
the target. No successor is generated; M189 continues and M190/M191/M193 stay
in FIFO. See
`pipeline/analyses/M188-CTF-HCG-CSORT-MQB-TR_done_earlystop_20260912-0408.md`.

### 9.3 One-Layer Upstream Coupling Closure - 2026-09-12 06:14

The bounded CPU-only audit reconstructed final decoder layer 5 from the frozen
checkpoint and compared parameter gradients for oracle-selection CE and
oracle-mask BCE+Dice on all 284 banks. Recoverable banks had mean parameter
cosine 0.00796 (median 0.00668, 40.4% negative); success controls had mean
0.01294. The weak/conflicting alignment is present one layer upstream, but the
audit does not measure earlier encoder layers and does not admit a
mask-conditioned mechanism. See
`pipeline/reports/d1_upstream_layer_coupling_20260912-0607/diagnostic_report.md`.

### 9.4 Layerwise Candidate-Selection Closure - 2026-09-12 07:17

All 284 frozen M95 banks were replayed through decoder layers 0-5. The layer
Acc@50 values were 0.4648/0.5141/0.5106/0.5246/0.5141/0.5106. Layer 3 led
each individual layer with 149 valid selections versus 145 at layer 5, but
the net gain was only +4: six final-recoverable banks were rescued and two
final-success banks became failures. Oracle layer choice among layers 0-4
covers 18/109 final-recoverable banks (16.51%), but the oracle union is
non-deployable because it has no available choice rule.

Simple early-layer selection and early-layer ensembling are therefore closed
at the scientific admission gate. They are readout variants rather than a
primary-source-distinct forward/loss mechanism. No new mechanism is admitted,
FIFO is preserved, and no queue mutation follows. See
`pipeline/reports/d1_layerwise_selection_20260912-0718/diagnostic_report.md`.

### 9.5 Multilayer Decoder Coupling Closure - 2026-09-12 08:17

The frozen M95 model was run with gradients on all 284 diagnostic banks. For
each decoder layer, oracle-selection CE and oracle-mask BCE+Dice were compared
in that layer's own parameter directions. On the 109 recoverable banks, mean
cosines for layers 0-5 were
0.019247/0.029284/0.011262/0.011056/0.008010/0.007961. The 145 success
controls were also weak and mixed: layer 0 mean -0.010086 and layers 1-5
0.016549/0.010974/0.019529/0.016993/0.012937. Layer 5 reproduces the earlier
one-layer measurement.

This removes the earlier-decoder conflict hypothesis for a simple
selection-mask alignment mechanism. No mechanism is admitted, FIFO is
preserved, and no queue mutation follows. Encoder and backbone parameters are
outside this audit, so the result is not a full-model causal estimate. See
`pipeline/reports/d1_multilayer_coupling_20260912-0826/diagnostic_report.md`.

### 9.6 Upstream Parameter-Group Coupling Closure - 2026-09-12 09:14

All 284 frozen M95 banks were replayed with gradients enabled to compare
oracle-selection CE and oracle-mask BCE+Dice in top-level parameter groups.
Recoverable-bank mean cosines were `dec_shared .09340`,
`decoder_layers .02061`, `output_layer .09135`, and `unet .09198`; success
controls were `-.02275`, `-.00079`, `-.00043`, and `-.00531`. `input_conv`
had zero gradient in this inference path.

A paired physical-scene bootstrap over the 50 scenes containing both subsets
gave 95% descriptive intervals crossing zero for every group. The largest
recoverable-specific shift, `dec_shared`, had interval `[-.00037,+.23328]`
and a 40.4% negative fraction among recoverable banks. The upstream groups
therefore do not provide a robust existing joint selection-mask direction.

This closes the upstream parameter-locus hypothesis without admitting a
mechanism. A future mechanism still requires its own forward/loss derivation,
primary-source distinction, matched controls, robustness, and efficiency
evidence. Worker SHA-256
`3b37801434e7a5ecfcf084be2011623bc82fd92dc38c1276b0d3556a2aae22c1`; result
JSON SHA-256
`b175f796124ca36cdf092f8be04e593556430bfc988bf23c3e40cf95a4f8d015`.
Full result:
`pipeline/reports/d1_upstream_group_coupling_20260912-0914/diagnostic_report.md`.
