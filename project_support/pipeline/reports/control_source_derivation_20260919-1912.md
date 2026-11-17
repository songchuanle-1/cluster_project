# Frozen Control-Source Derivation

Scope: continuation of referent-causality-audit, not a new mechanism, design,
admission receipt, native result or novelty claim.

## Source Audit

M95 network.py:121-128 computes superpoint coordinates before language encoding,
expands them and passes coordinates as criterion input 8; labels are input 4,
FPS input 7 and offsets input 9. dec.py:469 obtains sample_inds from language
and seed features. sample_model.py:64-75 computes language cross-attention before
top-k. dec.py:293-300 computes both prediction heads after language attention.
loss.py:152-175 supervises the score head with matched-target IoU.
native_support_capture_v2_20260916.py computes ious against held gt explicitly.
None of those learned outputs is a verified target-independent objectness axis.
These are local source observations; no external paper claim is made.

## Rejected Sources

- Target-mask IoU and the learned quality head: target-dependent; no substitution.
- Sampling score: language-conditioned; not an independent control.
- Max IoU against all annotated objects: oracle mask quality and still depends
  on language-conditioned predicted masks; not an objectness probability.
- Seed-inside-ANY-instance: for Q_o={q: label(seed_q)=o}, every q in Q_o
  has indicator 1 for each nonnegative object o. Therefore max over Q_o is 1
  for every covered object, and the corresponding minimum cost is always 0.
  The implemented builder reproduces this degeneracy. It does NOT invalidate
  the older any-instance intervention over the unrestricted query set.
- Arbitrary index/hash noise: a synthetic null, not a native objectness source.

## Geometry Nuisance Control

Use the exact native transformed superpoint coordinate x_i and full instance
partition l_i. For every object o, let I_o={i:l_i=o},
mu_o=mean_{i in I_o} x_i and r_o^2=mean ||x_i-mu_o||^2.
Define h_i=||x_i-mu_o||^2/r_o^2 and c_q=h_{FPS[sample_inds[q]]}.
The diagnostic object cost is min_{q in Q_o} c_q, lower is better.
This is annotation-assisted radial seed geometry, NOT objectness, mask quality,
a probability, a model change or deployable inference. It only tests a geometric
nuisance explanation. A null effect cannot establish referent specificity.

The support field h depends on neither designated target nor text. Changing
the target label while freezing coordinates, full partition and query axis
leaves h, c and physical object costs identical. Costs are invariant to
translation, orthogonal transformations, uniform nonzero scaling and instance
ID renaming. Computation is O(N+Q) with grouped reduction in a native vectorized
implementation; the static reference's per-object query scan is O(KQ+N).
There are no learned parameters, gradients, new labels or tuned constants.

Important boundary: sample_inds is language-conditioned. Thus gathered scores
are target-blind only CONDITIONAL on the frozen query axis. Re-running with a
different expression need not preserve selected seeds or object minima. Tests
demonstrate this distinction. This does not satisfy an unconditional
language-independent proposal control and does not repair the old objectness
contract by renaming a field.

## Rejection And Missingness

Reject malformed/nonfinite coordinates, lossy identity coercion, wrong support
axes or uncomposed/out-of-range seeds. Background, zero-radius and singleton
objects yield explicit missing values, never an epsilon or zero replacement.
No covered seed means a missing object, not an imputed cost. Exact ties in any
predeclared target/candidate contrast are ineligible. Symmetric objects can
therefore be systematically excluded: report all denominators, rejected IDs,
radius values, ties and near-tie margins; do not claim population validity.
Count/support-size balancing, outcome-independent selection and scene-level
uncertainty remain mandatory. Native prevalence of degeneracy is unknown.

## Executable Status And Next Action

The separate CPU reference and metamorphic tests implement this derivation.
The existing seven-file native producer and two-axis objectness evaluator are
unchanged and still NOT ready for paired rank/control evaluation.
Next implement a separately versioned geometry capture/evaluation contract,
exporting criterion input 8 on the exact expression support and binding all
source/input/FPS/partition hashes. Test native coordinate slicing and compare
paired target swaps on frozen support before any scientific use. Do not populate
objectness_scores with geometry. Retain referent-only/membership diagnostics as
separate estimands; do not claim an independent objectness control is solved.
GPU execution remains gated by allocation, live capacity and admission policy.
