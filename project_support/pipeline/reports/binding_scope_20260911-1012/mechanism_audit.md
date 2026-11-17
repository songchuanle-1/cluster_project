# Shared-Witness Applicability And Prior-Art Audit

2026-09-11. Status: NOT ADMITTED for model training. This is a bounded audit,
not an exhaustive literature review, a negative efficacy trial, or a new method.

## 1. Observed Problem And Applicability

The frozen diagnostic sample has 90/284 baseline and111/284 M95 recoverable
selection errors. The separate12-case M95 casebook has9 verified wrong-instance
outputs with equal annotation labels. Neither fact identifies relation binding
as the cause. These outcomes motivated this audit but were already visible to
the author; these are not blinded or independently annotated text readings.

scope_audit.json records21descriptionIDs:12errors,9controls;3missing controls
remain missing. Every quoted span is checked against the original description.
Under the prespecified narrow rule, none is confirmed to express two explicit
target-to-anchor predicates bound to the same anchor mention. This is an
applicability limitation on these readings, NOT proof of zero such cases in
ScanRefer, zero implicit relations, or absence of binding errors.

Important counterexamples to premature mechanism selection:
- scene0621 chair22: at(chair,table), closest(table,door) is a nested chain.
  It shares a table variable across edges but is not two predicates of (chair,table).
- scene0426 pillow22: on(bed) and behind(blankets) have distinct anchor mentions;
  behind attachment is unresolved. Merging bed and blankets would be wrong.
- scene0578 chair5: around(table) is explicit; right/front lack a definite
  reference frame or attachment. Do not upgrade this to confirmed shared binding.
- scene0591 pillow14: one on(couch) relation and an orange attribute.
  Same-label distractor and valid target candidate do not isolate relational failure.
- scene0328 microwave17 control: two cabinets are explicitly distinct; forcing
  them to one witness destroys the stated between relation.

Empty exact-label domains for stove, box, entry way, toliet, pile of blankets,
room, cabinets or monitors are lexical missingness, not measured proposal misses.
No synonyms, plural normalization, spelling repair, appearance annotations, new
datasets, external annotation API or additional inference were used.

## 2. Hard Witness Derivation

Let i index a target candidate, a a finite nonempty physical-anchor domain,
and r=1..R predicates explicitly sharing that anchor. Let ell_r(i,a) be finite
energies, larger better. These are hypothetical variables, not extracted from M95.

Independent witness assignment:

    U_i = max_(a_1,...,a_R) sum_r ell_r(i,a_r)
        = sum_r max_a ell_r(i,a).

Adding equality constraints a_1=...=a_R yields:

    C_i = max_a sum_r ell_r(i,a) <= U_i.

For any a, each summand is bounded by its row maximum; summing proves the
inequality. Equality requires a common maximizer of all rows. Hard gap U-C>=0
is valid only for this exact relaxation with the same feasible domain.

Synthetic wrong:[[0,-4],[-4,0]], right:[[-1,-3],[-1,-3]]:
U_wrong=0>U_right=-2, but C_wrong=-4<C_right=-2. This proves possible
rank reversal, not that the current decoder implements U or makes this error.
For R=1, U=C. If the sentence names distinct anchors, independent witnesses
are legitimate and the equality constraint is unjustified.

## 3. Soft Form And Its Limits

Choose an explicitly defined prior pi over physical anchors with total mass1.
For positive-mass anchors define E_i(a)=sum_r ell_r(i,a) and:

    J_i = log sum_a pi_a exp(E_i(a)).
    q*_a = pi_a exp(E_i(a)-J_i).

For any q supported on positive pi:

    sum_a q_a E_i(a) - KL(q||pi)
      = J_i - KL(q||q*) <= J_i.

Thus J is the variational optimum and its derivative wrt every
ell_r(i,a) equals q*_a. No probability calibration or data independence follows
from defining these energies. Positive prior support must be distinguished from
the unrestricted hard domain; zero-mass anchors are excluded from the soft form.

The tempting soft counterpart of U is:

    V_i = sum_r log sum_a pi_a exp(ell_r(i,a)).

There is NO universal sign for V-J. The tests show V-J>0 for incompatible
maximizers and V-J<0 for the common-maximizer example above. A single common
anchor draw and independent draws are different probability models, not nested
normalized relaxations. Therefore V-J is not a nonnegative inconsistency loss.
Do not transfer the hard inequality to soft scores or use that gap as a loss.

For duplicate anchor copies with identical E and conserved total mass,
sum_j pi_(a,j) exp(E_a)=pi_a exp(E_a), so J is unchanged. Uniform reweighting
over all resulting tokens changes the prior and generally changes J. This is
an algebraic property, not robustness to changed geometry or a new contribution.
Distinct objects must remain distinct even when their features look alike.

13 named tests in formal_tests.json cover hard counterexample/bound,
single-predicate degeneration, both soft-gap signs, subdivision, uniform-copy
counterexample, joint permutation, variational optimum, finite-difference
gradient, zero-mass masking,4invalid domains, separate-anchor control and stable
log-sum-exp shift. Synthetic thresholds are test tolerances, not model parameters.
No automatic differentiation or production neural forward was validated.

## 4. Primary-Source Comparison

[P1] Joy Hsu, Jiayuan Mao, Jiajun Wu. NS3D: Neuro-Symbolic Grounding of 3D
Objects and Relations. arXiv:2303.13483v1, March23,2023; section3.3.
Archived primary HTML and source SHA: NS3D.html, sources.json.
Locator: `https://arxiv.org/html/2303.13483v1`.

NS3D defines object score vectors and compositional neural execution. Its binary
operation uses:

    y_i = min(x_i^t, sum_j softmax(x^r)_j prob^rel_(i,j)).

Its ternary operation sums over j,k with the product of two reference softmax
weights and a learned ternary score. This explicitly addresses viewpoint and
multi-object references. Reusing the same reference score vector in both slots
does not algebraically restrict the sum to j=k; a diagonal joint variable would
be a different operator. That observation is about the displayed equation, not
proof that NS3D fails or lacks other compositional expressive power. Generic
object-centric soft relation reasoning and high-arity reference handling cannot
be claimed as new here. Segmented-object inputs, learned concept modules and
language-to-program parsing differ from this project's mask-decoder setup.

[P2] Qihao Yuan, Kailai Li, Jiaming Zhang. Solving Zero-Shot 3D Visual Grounding
as Constraint Satisfaction Problems. arXiv:2411.14594v2, August11,2025;
sections3.1-3.3. Archived primary HTML and source SHA: CSVG.html, sources.json.
Locator: `https://arxiv.org/html/2411.14594v2`.

CSVG represents mentioned objects by variables with instance domains and spatial
relations by constraints. Backtracking finds joint assignments satisfying all
constraints, grounding both targets and anchors. A reused variable necessarily
keeps one instance assignment across its constraints. Thus globally consistent
target/anchor identity is already prior art, not our broad novelty. The method
uses LLM-generated programs, predefined geometric thresholds, a scene-center
viewpoint for view-dependent relations, and an average-distance heuristic when
multiple solutions remain. Those engineering choices are not independently
validated physical truth for our examples and are not adopted automatically.
Its hard CSP differs from the memo's soft mass-weighted energy model, but merely
softening an established formulation does not establish publishable novelty.

No published performance values are compared to our mask mIoU: inputs, metric,
supervision and task protocols differ. Only the method sections above were
audited; related work, supplements and other newer papers remain to be checked.
Neither paper's lack of a subdivision claim proves that our proposal is novel.
The exact HTML versions and retrieval times are archived, not asserted latest.

## 5. Implementation And Admission Gaps

The prototype calculations have O(Q*A*R) energy operations and O(A) temporary
space when streamed. This excludes building proposals, energies and bindings.
A general multi-variable graph can be much more expensive; a star formula
cannot be substituted for the nested chain identified in scene0621.

Still missing: test-time anchor proposals with recall, coreference/scope and
viewpoint inference, a justified object prior, compatibility training targets,
empty-domain behavior in the real model, integration with existing loss and
gradient paths, production-level padding/identity tests, full-model<=10G and
matched latency/memory evaluation. The current M95 score is not calibrated to J;
adding J to it is not derived. Training admission remains false.

Historical A3routing .4468 and A4shuffle .4941, M161aligned .4920 versus
M162shuffle .4980, and M170 subtraction .4970 with compromised patience remain
negative/limited local evidence. Rebranding routing or feature subtraction as
causal binding would not resolve either the local bans or prior-art overlap.

## 6. Decision And Next Work

Do not adopt the narrow shared-witness proposal as the main mechanism now.
It lacks confirmed applicability to the fixed cases, and its broad joint-anchor
idea is covered by prior art. This is not a permanent ban on future evidence.
Do not expand to a generic graph model just to encompass every example.

Next concrete work: inspect M95's candidate discrimination supervision and
loss-to-score path against the measured recoverable error bank; establish
whether a usable target candidate receives the intended selection signal.
Combine that code-level check with the fixed one-relation-plus-attribute cases,
whose ambiguity could instead be unary discrimination or training assignment.
Record one falsifiable discrepancy before proposing another structure.
No new training entry, queuehold, dataset, multiseed run or unsupported novelty claim.
