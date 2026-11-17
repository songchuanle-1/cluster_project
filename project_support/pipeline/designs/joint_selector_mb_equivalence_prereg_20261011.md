# Conditional Multi-Bernoulli Equivalence Test

Stable candidate: m95-native-joint-mask-selector.
Scientific question: does the proposed joint operator have a whole-mechanism
increment over an existing probabilistic set-prediction likelihood, rather than
merely differing from detached PIRS labels?

Primary source verified 2026-10-11:
Georg Hess, Christoffer Petersson, Lennart Svensson,
Object Detection as Probabilistic Set Prediction, arXiv2203.07980v3,
2022-07-13, sections3.1/3.2 equations2,3,6.
https://arxiv.org/html/2203.07980v3
The authors model object existence with Bernoulli components and marginalize
object/component assignments in a multi-Bernoulli set likelihood.
The paper's object attributes are class/bounding box, not ScanRefer masks;
the following specialization is OUR derivation, not a reported paper result.

Let s_q=z_q,1-z_q,0, r_q=sigmoid(s_q). Let ell_q be the original mask's
summed Bernoulli log density using native valid superpoints.
Exactly-one-present assignment weight is
a_q=log(r_q)+sum_{j!=q}log(1-r_j).
The single-object conditional MB loss is
-[logsumexp_q(a_q+ell_q)-logsumexp_q(a_q)]/N.
Since a_q=s_q+sum_j log(1-r_j), this equals the proposed
-logsumexp_q(log_softmax(s)_q+ell_q)/N.

On all frozen128/32 native tensors, evaluate the UNSIMPLIFIED MB expression
independently of the proposed operator and compare value, selector gradient
and mask gradient. Use the already-declared diagnostic float64 arithmetic
and fixed absolute1e-6 tolerance; not a full native float32 repeat claim.
No change to cohort, model, target definition, normalization or seed.

If equivalent on value and both gradient paths, reject THIS claimed new-core
realization: it is a direct conditional-MB specialization with mask density,
without a demonstrated independent mechanism beyond existing set likelihood.
Do not reject the observed selector deficit, all supervision mechanisms, or
claim literature-wide exhaustion. Do not rename or tune the same objective.
If non-equivalent, preserve the counterexample and examine the derivation.
