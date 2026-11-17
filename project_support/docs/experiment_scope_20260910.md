# Subsequent Experiment Scope

Effective: 2026-09-10. User-directed revision of future experiment coverage.
Authority: pipeline/goal.json description and constraints. This document supplies
the operational detail; it does not override goal.json or create a new phase.
Supersedes the old assumption that queue depth justifies expanding a mechanism
family. The anchor proposal in research_rethink_20260910.md remains provisional.

## 1. Coverage Matrix

| Area | Concrete question | First experiment or artifact | Necessary comparison | Exit condition |
|---|---|---|---|---|
| Error diagnosis | Is the failure candidate coverage, mask quality, or choosing among candidates? | Fixed checkpoint prediction audit; sample IDs, scene IDs, masks, scores, GT used only for diagnosis | Baseline and champion on the same scenes, inputs and protocol | Cannot rank mechanisms without predictions or a quantified error breakdown |
| Core mechanism | Which observed error can a structural change address? | One evidence-selected hypothesis; full derivation and computation graph | Same platform with the hypothesized dependency removed | Do not train if assumptions do not match the observed error or differentiable implementation is unspecified |
| Novelty | Does prior work or a failed local variant already implement the same idea? | Verified primary-source comparison of variables, equations, supervision and computation | Closest method, simplest equivalent operator, and relevant local failures | No new-contribution claim or mechanism admission while material prior-art checks are missing |
| Mechanism verification | Does the proposed dependency explain the change? | Matched structural control, negative control and invariant/counterexample tests | Same inputs, proposals, capacity and schedule where possible; document unavoidable differences | Reject the explanatory claim if controls do not support it, even when aggregate mIoU rises |
| Generalization and robustness | Is the change specific to one subset or representation artifact? | Prespecified scene/category/distractor/relation slices and label-preserving perturbation checks | Non-target error subsets; ordinary descriptions; identical evaluation data | Report regressions and uncertainty; do not extrapolate to untested datasets or seeds |
| Efficiency | Is the complete model eligible and practically useful? | Full-model FLOPs, latency median/P90, memory and unsupported-op record | Matched M95 hardware/input/protocol; bs1, warmup20, repeat100 | Existing <=10G and memory criteria apply; theoretical complexity is not admission evidence |

These are six coverage obligations, NOT six parallel mechanism families or six
mandatory full-training runs. Diagnostics, literature audits, unit tests, and
evaluation-only controls may require no new training.

## 2. Diagnose Before Choosing A Research Direction

The first deliverable is an error inventory from fixed available checkpoints,
not another model package. Record availability before claiming any measurement.
Use a reproducible scene-stratified sample and freeze its IDs before comparing
mechanisms. Preserve a separate evaluation subset not used to select a mechanism.
Repeatedly mined validation results are exploratory, not independent confirmation.
Use test data only for final evaluation, never for design selection.

Let P_x be a fixed nonempty predicted mask bank for example x, y_x its GT mask,
and p_hat_x the selected member of that SAME bank. Define:

    o_x = max_{p in P_x} IoU(p, y_x)
    a_x = IoU(p_hat_x, y_x)
    1 - a_x = (1 - o_x) + (o_x - a_x).

The first term measures the bank's mask-quality limitation. The second is an
oracle selection gap, not proof of any particular language or relation failure.
The identity holds only when the selected mask belongs to the audited bank.
Empty banks, postprocessed masks, and different candidate sets need explicit
handling; do not silently substitute values or compare incompatible oracles.
This decomposition does not itself separate missed objects from rough boundaries.

Audit within these groups:

- Candidate coverage and boundary quality: inspect best-overlap masks and target
  sizes. Separate absent candidates from present but inaccurate masks.
- Same-category ambiguity: inspect target identity, number of distractors and
  noun/attribute evidence. Do not assume every selection gap is relational.
- Relation binding: distinguish relation recognition, coordinate-frame errors,
  missing anchors, and whether predicates genuinely share one referent.
- Multi-scale evidence: test duplication/subdivision with object identity and
  features held fixed before attributing changes to double counting.

Report counts, denominators, annotation rules/disagreements, unavailable outputs,
overall mIoU, and slice metrics. Error labels may overlap; do not sum their
percentages as mutually exclusive causes. Oracle improvements are upper bounds,
not deployable gains. No arbitrary error-frequency cutoff selected after results.

## 3. Mechanism Selection And Derivation

Select ONE main mechanism using measured headroom, failure prevalence, feasibility
and verified prior art. Do not lock the project to shared-anchor verification.
If the proposal bank dominates error, a ranking-only mechanism is not justified.

Each mechanism record must contain:

1. A concrete failure example and an aggregate evidence artifact.
2. Symbols with dimensions, data sources and test-time availability.
3. Assumptions, objective/constraint and intermediate derivation steps.
4. The resulting forward/loss graph and mapping to the existing implementation.
5. Gradients or optimization procedure, degeneracies and failure cases.
6. Complexity including proposal extraction, not only the new operator.
7. A primary-paper comparison and historical local-variant comparison.
8. A minimal matched control and a preregistered reason to reject the hypothesis.

A restated attention formula, standard marginalization identity, or renamed
counterfactual subtraction does not establish novelty. An unverified primary
source remains a missing prerequisite; do not replace it with a fabricated quote.
All existing Phase1 tuning bans remain active. Expanding coverage does not
authorize forbidden gates, language routing, repeated injection or residuals.

## 4. Minimal Experiment Sequence

| Stage | Work | Training permission | Output |
|---|---|---|---|
| D0 | Verify checkpoint/prediction/data access and freeze diagnostic sampling | No new full training needed | Artifact inventory and split/sample manifest |
| D1 | Quantify errors and oracle selection headroom | Evaluation only under existing resource limits | Error table, examples, missing-data record and measured priority |
| N1 | Derive one candidate and verify closest original papers/local failures | No mechanism admission yet | Derivation and novelty comparison |
| T0 | Check counterexamples, gradients, padding, identity and invariances | Synthetic/offline checks; bounded profiling only when safe | Reproducible correctness tests |
| E1 | Review the minimal main mechanism and necessary matched controls | Only after motivation review, design, scientific and resource admission | Independent packages/configs; same seed1999 and schedule |
| V1 | Evaluate intended error subsets, negative controls, robustness and resources | Reuse trained models when possible | Overall/slice metrics, scene-level uncertainty and limitations |
| P2 | Stability/expanded validation if justified by results | Existing Phase2 confirmation rules; no automatic multi-seed or new-dataset training | Confirmed ablation/validation plan |

No scientific prerequisite is bypassed because waiting depth is low.
Continue productive D0/D1/N1/T0 work and report the exact missing prerequisites.
No automatic new-dataset downloads, external API labeling, paid services or
additional full-training campaigns are implied by this document.

## 5. Existing Batch Disposition

Authoritative queue read on 2026-09-10 around22:00:

| Experiments | Existing status | Disposition |
|---|---|---|
| M184/M185/M186/M187 | running in local registry; last remote snapshot21:10 | Preserve runs and existing completion/early-stop rules |
| M188/M189/M190/M191/M193 | waiting | Preserve original FIFO and admission; analyze as legacy terminal-readout structural controls |
| M192 | resource-rejected before training | Keep rejected; no invented accuracy result |

This request changes subsequent research coverage, not an explicit cancellation
of the previously admitted batch. No queue state, registry, trainer, allocation
or scheduler is modified. Do not retroactively call old experiments invalid or
rewrite their original design rationale.

Legacy results may inform D1/N1, but do not automatically justify successor
selector/pooling/readback variants. A necessary control for a supported NEW
hypothesis is allowed after normal design review; it is not an independent
novel contribution.

## 6. Reporting And Decision Rules

Keep the existing seven pipeline document formats. In future motivation reviews,
place the error evidence in Story Status/Gap Analysis and explicitly distinguish
facts from hypotheses. In experiment designs, include the derivation/novelty
comparison in Analysis & Direction or linked appendices, matched controls in
Experiment Plan, and degeneracies/rejection rules in Risk Assessment.

Every new design must map all six coverage areas to artifacts or an explicit
planned stage; incomplete scientific admission blocks that mechanism's enqueue.
Primary mechanisms require the problem/derivation/novelty checks BEFORE training.
Tests of efficacy and generalization naturally remain planned until after it.

Do not demand novelty from a diagnostic, replication or matched control. Instead
require a named parent question and the evidence that this work can resolve.
Do not report aggregate improvement as proof of a causal mechanism, deployment
quality, multi-seed robustness or cross-dataset generalization.

The policy lives in goal.json so later foreground sessions and autonomous ticks
read it even after this conversation or decision-index entry ages out.

## 7. Selection-First Revision - 2026-09-11

The fixed diagnostic now measures the dominant unresolved failure inside
candidate selection rather than candidate coverage:

- M95 has 111 recoverable failures; 105 select a different physical instance
  and 97 still have a candidate assigned nearest to the target.
- On recoverable banks, the saved `indis` score has Spearman 0.1723 with
  candidate IoU and only 14/111 oracles in the top five.
- On successful banks, the same score has Spearman 0.5143 and 59/158 oracles in
  the top five.
- Simple mask-area and equal-rank fusion probes do not recover the oracle.

Therefore subsequent mechanism work must address candidate competition or
selection evidence, not add another context, pooling, selector, or readback
variant. Relation-binding and shared-anchor proposals remain closed until a
fixed diagnostic demonstrates applicable cases; the existing 21-case audit did
not.

The current N1 candidate is language-mask evidence calibration (LMEC):

    m_qn = sigmoid(mask_logits[q,n])
    v_q^+ = sum_n m_qn f_n / (sum_n m_qn + eps)
    v_q^- = sum_n (1-m_qn) f_n / (sum_n (1-m_qn) + eps)
    e_q = g(v_q^+, l) - g(v_q^-, l)
    s_q = u_q + lambda e_q

This is a proposal, not an admitted mechanism. The log-odds addition,
support-versus-complement operator, supervision, gradients, degeneracies, and
primary-source distinction are unverified. No model code, config, queue entry,
or training run may be created until full-text novelty comparison and synthetic
gradient/degeneracy checks pass.

The next diagnostic scope is therefore:

1. Full-text comparison against Fine-Grained Spatial and Verbal Losses
   (arXiv 2411.03405), UniSpace-3D (arXiv 2506.14238), PC-CrossDiff
   (arXiv 2603.17753), and CoT3DRef (arXiv 2310.06214).
2. CPU autograd and finite-difference checks for whole-scene, tiny-mask,
   saturation, permutation, and language-shuffle degeneracies.
3. A matched structural control with equal capacity and a preregistered
   rejection threshold before any E1 training request.

Existing FIFO entries remain valid legacy controls. Queue depth still does not
override scientific admission.

## 8. Selection-First Closure Update - 2026-09-12

Section 7's LMEC candidate is now closed. The corrected 284-bank reranking
study found no language-specific evidence: the deployed selection head scored
Acc@50 0.5070 in the original analyzer row, while support/language and
exclusive-support variants scored at or below 0.3204, with 11-20 recoverable
rescues outweighed by 27-66 success harms. Shuffled-language controls were
statistically indistinguishable or better. The quality head was also closed
(0.4683 Acc@50, 17 rescues, 29 harms). Those are diagnostic results, not
training-time causal tests.

The trained semantic-alignment projection was then captured read-only for all
284 banks and tested with `docs`-level matched controls. Real-language
`sem_max_cos` reached 0.5070 Acc@50 (3 rescues, 4 harms), while
shuffled-language and same-category shuffled controls reached 0.5141 and
0.5249 on their respective protocols. The deployed `indis` softmax reached
0.5106 overall. Therefore language/support/projection rerankers are not a
current mechanism route. The full record is in
`pipeline/reports/d1_semantic_projection_20260912-0007/diagnostic_report.md`
and `full_analysis.json`.

The surviving measured problem is narrower than generic relation binding:

- A usable candidate mask exists in the bank on the recoverable failures.
- The selected wrong candidate is usually a different physical instance, with
  empty mask intersection on 80.2% of the audited recoverable cases.
- The wrong candidate wins by a large score margin; per-bank monotone
  normalization cannot change its rank.
- Simple mask-area, overlap, quality-head, language-support, and semantic
  projection readouts do not recover it.

The next admissible work is therefore a code-level audit of how M95's
training-time query-to-instance supervision and mask-score coupling behave on
the frozen recoverable banks. The question is whether the correct mask's query
is positively supervised and whether its score path contains enough
candidate-specific evidence to distinguish physically disjoint same-category
instances. This audit is read-only and must record:

1. the matched/positive query indices and ground-truth instance assignment;
2. whether the oracle candidate receives positive `indis` supervision;
3. whether the score head sees mask-conditioned evidence or only query state;
4. masked controls for assignment identity, padding, and gradient paths;
5. the exact discrepancy, if any, between mask quality and score formation.

No new model, config, queue entry, schedule, checkpoint, or training run is
authorized by this audit. If the audit finds a mismatch, the resulting
mechanism must still pass the full admission sequence in Section 3 and must
state a non-trivial distinction from standard detection matching, query
classification, grounding rerankers, and the already closed local families.
If it finds no mismatch, the correct next deliverable is another measured
diagnostic or literature boundary, not a renamed selector.

## 9. Score-Coupling Audit Closure - 2026-09-12

The Section 8 audit is complete. The assignment replay found that 84/90
baseline and 99/111 M95 recoverable failures already contain a usable positive
candidate. The margin audit found that, for 97/111 M95 recoverables, the
selected negative and an available usable positive already have opposing
score-level corrective signals under the current `indis` objective.

The source-level score-coupling audit closes the remaining static question:
the deployed selection score is query-only. The implementation has

    u_q      = decoder query state for candidate q
    z_q      = indis_embedding(u_q)
    p_q      = softmax(z_q)[1]
    m_{q,n}  = u_q dot f_n
    q_hat    = argmax_q p_q

`prediction_head(query, mask_feats, batch_mask)` returns
`pred_scores = out_score(query)` and does not use `mask_feats` for the score.
The selection head `indi_embedding(query)` is separate again. The auxiliary
quality head is therefore also query-only, and `predict_by_feat` selects from
`indis`, not from the quality score.

`match_sampled_ins` assigns positive `indis` supervision from seed geometry:
one nearest query per target plus queries whose seed superpoint label equals
the target. Mask BCE/Dice supervise matched queries, and the quality score is
trained only on matched masks with IoU > 0.5. Selection and mask supervision
therefore meet only through shared query/network features; the selection score
does not directly read the candidate mask.

This establishes the discrepancy, not a mechanism. A simple mask-conditioned
score head is still a standard detection/mask-scoring-style reranker until a
verified primary-source comparison says otherwise. The frozen banks do not
contain decoder query embeddings or head inputs, so a real-data parameter
Jacobian audit requires a new bounded read-only capture protocol. No training,
config, checkpoint, queue, or scheduler mutation is authorized.

### 9.1 Local Query-State Coupling Audit - 2026-09-12 03:15

The existing 284-bank capture did contain final decoder queries and mask
logits, so the bounded local check was completed without another GPU capture.
The final selection and mask heads have disjoint trainable parameters; their
only local shared state is the decoder query. On the 109 recoverable banks,
the wrong selected candidate has mean selection margin 3.081 versus -1.911 for
the oracle. An oracle-supervised selection objective and the oracle-mask
improvement direction are effectively orthogonal on the shared query state:
mean cosine 0.0148 for selected-to-oracle and 0.0443 for
selected-to-selected, with success controls near zero as well.

This closes the local head-Jacobian question only. It does not propagate
through the upstream decoder and is not a full parameter-level causal result.
It also does not authorize a simple mask-conditioned selector. See
`pipeline/reports/d1_parameter_coupling_20260912-0307/diagnostic_report.md`.

### 9.2 Legacy Terminal-Readout Result - 2026-09-12 04:08

M188-CTF-HCG-CSORT-MQB-TR completed the preserved terminal-only branch
ablation with best mIoU 0.4916 at epoch 13 and early stop at epoch 23. It is
+0.0022 over the baseline but -0.0108 below champion M95, so it does not
preserve the M95 gain and does not justify a successor in the legacy
terminal-readout family. M189 remains running; M190/M191/M193 remain in the
original FIFO with no automatic successor generation. See
`pipeline/analyses/M188-CTF-HCG-CSORT-MQB-TR_done_earlystop_20260912-0408.md`.

### 9.3 One-Layer Upstream Coupling Closure - 2026-09-12 06:14

The bounded CPU-only audit reconstructed the final decoder layer from the
frozen M95 checkpoint and measured parameter-gradient alignment between
oracle-selection CE and oracle-mask BCE+Dice on all 284 frozen banks. On the
109 recoverable banks the mean shared-parameter cosine was 0.00796, median
0.00668, with 40.4% negative alignment; the 145 success controls were similar
at mean 0.01294. The conflict is therefore already present in the final
decoder layer, not resolved by moving one layer upstream.

This closes the one-layer audit only. It does not measure earlier encoder
layers, does not admit a mask-conditioned reranker, and does not justify a
queue change. Full result:
`pipeline/reports/d1_upstream_layer_coupling_20260912-0607/diagnostic_report.md`.

### 9.4 Layerwise Candidate-Selection Closure - 2026-09-12 07:17

A read-only replay of all 284 frozen M95 banks measured Acc@50 at decoder
layers 0-5 as 0.4648/0.5141/0.5106/0.5246/0.5141/0.5106. Layer 3 had the
largest per-layer count at 149 valid selections versus 145 for the final
layer, but the net effect is only +4 selections (6 recoverable rescues, 2
final-success harms). An oracle choice among layers 0-4 covers 18/109
final-recoverable banks (16.51%), but that union is non-deployable because it
requires knowing the valid layer per bank.

This closes simple early-layer selection and early-layer ensembling at the
admission gate: the measured effect is a readout/selector choice, not a
primary-source-distinct forward or loss mechanism, and no reviewable
deployment rule was derived. No new mechanism is admitted, FIFO is preserved,
and no queue mutation follows. Full result:
`pipeline/reports/d1_layerwise_selection_20260912-0718/diagnostic_report.md`;
result JSON SHA-256
`a2b30327a87537bbbc20c8423551c4caeb9e0b818a0f9ad59d202c80c75dbb24`.

### 9.5 Multilayer Decoder Coupling Closure - 2026-09-12 08:17

A read-only audit ran the frozen M95 checkpoint with gradients enabled on all
284 diagnostic banks and compared oracle-selection CE against oracle-mask
BCE+Dice in each decoder layer's own parameter directions. On the 109
recoverable banks, mean cosine values for layers 0-5 were
0.019247/0.029284/0.011262/0.011056/0.008010/0.007961. The 145 success
controls were similarly weak and mixed (layer 0 mean -0.010086; layers 1-5
0.016549/0.010974/0.019529/0.016993/0.012937). Layer 5 reproduces the prior
one-layer result of 0.00796.

There is no strong negative selection-mask conflict at an earlier decoder
layer and no layer-specific target for a simple alignment mechanism. This
closes the bounded decoder-layer coupling audit. It does not audit encoder or
backbone parameters, does not admit a mask-conditioned mechanism, and does
not justify a queue change. Worker SHA-256
`6a1b47bb6243661e74484745c559aefaf686b62056e46735a754b47bff0b7a0d`;
result JSON SHA-256
`fd52f290e66366db7d909dea05cf5ad3945dc0bea3f5db89e3447e1021e2d734`.
Full result:
`pipeline/reports/d1_multilayer_coupling_20260912-0826/diagnostic_report.md`.

### 9.6 Upstream Parameter-Group Coupling Closure - 2026-09-12 09:14

The bounded upstream audit measured oracle-selection versus oracle-mask
parameter-gradient alignment in every top-level parameter group of the frozen
M95 checkpoint on all 284 banks. On the 109 recoverable banks, mean cosines
were `dec_shared .09340`, `decoder_layers .02061`, `output_layer .09135`, and
`unet .09198`. The corresponding success controls were `-.02275`, `-.00079`,
`-.00043`, and `-.00531`. `input_conv` was present but received zero gradient.

The recoverable-specific shift in `dec_shared`, `unet`, and `output_layer`
was weak relative to the bank-level spread. In the 50 scenes containing both
subsets, a paired scene bootstrap (10,000 draws, seed 1999) gave 95% intervals
for recoverable-minus-success mean cosine of `[-.00037,+.23328]` for
`dec_shared`, `[-.03998,+.22374]` for `unet`, `[-.05360,+.22744]` for
`output_layer`, and `[-.00281,+.06496]` for `decoder_layers`. All intervals
include zero.

This closes the shared-upstream parameter-locus audit as an uncertain/negative
result. It does not establish a robust existing joint direction, does not
admit a mechanism, and does not justify a queue mutation. Worker SHA-256
`3b37801434e7a5ecfcf084be2011623bc82fd92dc38c1276b0d3556a2aae22c1`; result
JSON SHA-256
`b175f796124ca36cdf092f8be04e593556430bfc988bf23c3e40cf95a4f8d015`.
Full result:
`pipeline/reports/d1_upstream_group_coupling_20260912-0914/diagnostic_report.md`.
