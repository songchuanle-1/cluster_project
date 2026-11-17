# Motivation Review: Target Mention Role, Validated Prototype

## 1. Goal
ScanRefer target0.5100, champion M95=0.5020, baseline0.4894. Phase1 unmet.
All18 goal constraints and11 bans remain unchanged; USER-SCOPE-B explicitly
allows a new referent positive-set definition. Only server-6 GPU7/two slots.
Original seed1999, epochs50/max_iters70, weights, matching and data unchanged.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Exact shared-reference phrase joins identify an instance | realization rejected | 28 multiple-target joins in216 mentions | other identity mechanisms unknown |
| Parsed target root always names the annotated target | disproved by one native case | scene0631_00/ann1: root window, target trash can | population identity error rate unknown |
| Joint target/other-role correction changes optimization | native diagnostic support | identity control0; literal-only and wrong-reference gradients separate | trained effect unknown |
| Candidate is executable under frozen gates | reviewed below | isolated source, native backward/repeats, predict controls/resources | no efficacy claim |

## 3. Experiment Assessment
M198-PDC best0.4977434277534485 and M199-BEI best0.4741974174976349 remain
failed trained branches, not automatically restarted. TMR contains neither
PointDetailField nor directed boundary loss. Its initial complete native
forward repeat FAILED; archived v1 sources/results remain authoritative.
V2 copies only nonlearned ordered mean and scoped implicit-GEMM direct_table=False
utilities into its own package. This is a numerical reproducibility repair,
not the proposed scientific mechanism, not a new PDC successor or extra module.

V2 native batch1/2, four passes: forward logits/masks/loss repeat delta0;
full native gradient maxdelta2.1606683731079102e-7/0, within original1e-6.
506 original tensors have finite nonzero gradients, zero new trainable tensors.
Same-forward original-role loss provides the matched numerical-repair control:
only role maps change while forward, matching, weights and parameters stay fixed.
No optimizer steps were taken in these tests.

## 4. Gap Analysis
Corrected taxonomy V2 is authoritative: frozen128 has109 literal-root overlaps,
18 missing literal matches, one outside-root clear case. Full TRAIN has2115
literal-outside-root observations, NOT2115 certified errors. Unique executable
catalog has1332 entries; eligibility is not a proof of description/identity quality.
The initial counter/desk/curtain index adapter was wrong; previous conclusions
using those named category indices require targeted reaudit before reuse.
Initial native CPU/CUDA and resource-module adapter failures are archived.

## 5. Design Rationale And Gates
Use the original semantic-alignment loss with a TRAIN-only new positive set
and explicit old-target-to-other-role transfer. Identity maps give zero loss/
gradient change. Wrong-reference maps are distinct. Literal-only anchoring
versus full role transfer gives lossdelta0.9599117636680603 and token/query
gradient deltas0.34244564175605774/0.09919046610593796 on the fixed native case.
These are causal diagnostics, NOT effect sizes or novelty certificates.

Primary BUTD-DETR joint_det_dataset.py was fetched from the official repository
and content-hashed: _get_token_positive_map already anchors annotation labels.
That primitive and generic semantic alignment are prior art, not contributions.
The scoped whole-mechanism increment is disjoint-root eligibility plus coupled
reassignment of the old parsed target distribution into existing other-entity
supervision; the inspected primary file does not implement that graph-role map.
This is not an exhaustive literature search, and independent novelty is unknown.
Source commit could not be verified due API rate limiting; no "latest" claim.

Six scientific execution gates:
- Diagnosis: actual native annotation/graph contradiction, corrected taxonomy,
  explicit unknowns and frozen denominators; not overall-mIoU speculation.
- Controls: identity, wrong reference, literal-only increment, wrong-object bypass;
  v2 predict with full/empty TRAIN catalog has zero calls to rebind and delta0
  across28 returned tensor fields. Only one fixed native predict batch certified.
- Native backward: v2 batch1/2 full native total-loss gradients finite/nonzero;
  unchanged1e-6 loss/forward/gradient repeats pass, v1 failures preserved.
- Resources: uniform actual VAL predict bs1/warmup20/repeat100, matched
  checkpoint/sample/seed/protocol. FLOPs9.762532428G, parameters157484090,
  memory1008.8515625MiB, median71.3496971875429/P9074.098639562726ms.
  Versus champion0G/0parameters,+6.1249732971191ms,+3.362526% memory.
  Versus baseline+0.061656064G,-37.5180729ms,+2.887745% memory.
  Timing is a measurement, not a trained speedup. Uniform fvcore unsupported
  operators are retained for all models; no unilateral supplementary counting.
- Independence: physical nine-file package/new matching config basename;
  no cross-variant imports, no learned PDC/BEI component; candidate-local
  numerical repair copied physically. Whole-source/config hashes verified.
- Goal constraints: no N-squared attention, new layer/scalar/routing/residual,
  changed seed/schedule/weights/datasets or evaluation tuning. TRAIN labels
  supervise loss only; startup constructs a catalog but predict does not use it.
  Frozen validation/convergence/branch-stop/memory rules preserved.

Scientific execution gates support one structural screening experiment,
not a paper contribution or efficacy certificate. No queue slot is filled
solely because hashes validate. Admission also requires the exact tested
commit, decision, receipt and canonical safe-sync/launch-progress chain.

## 6. Next Batch
One TMR screening trial, original seed/schedule, no tuning or sibling variant.
Before training: hash-bound resource comparison and source review, tested-only
commit and admission receipt. Native increasing training steps, not PID alone,
must establish launch. Overall/subgroup scene-clustered evaluation stays pending.
