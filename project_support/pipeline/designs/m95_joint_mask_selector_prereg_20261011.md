# Joint Mask-Selector Diagnostic

Stable ID: m95-native-joint-mask-selector
Hypothesis ID: joint-query-mask-likelihood
Scientific stage: diagnosis, not admitted.

The unchanged M95 selector can choose a poor mask even when another native
query predicts the referred instance correctly. Independent per-query indi
labels do not transmit the selected mask's likelihood to selector logits.

Freeze the existing 31-expression, two-scene TRAIN manifest before capture.
Use native M95 checkpoint SHA fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e,
seed1999, original loader/annotations and unchanged native matching.
No validation/test-based design selection and no extra labels or seeds.

For every expression, capture all native query masks and indi logits at the
final native criterion call. Record selected thresholded-mask IoU, oracle
native-query IoU, the best Bernoulli-likelihood query and latent responsibilities.
The proposed diagnostic operator is the negative log marginal likelihood of
the original referred superpoint mask, marginalizing the native query identity:
log_softmax(indication class difference) plus summed Bernoulli log likelihood
over original valid superpoints, then logsumexp over the unchanged query set.
Normalize by original superpoint count, without a tunable temperature/weight.

Matched controls on the SAME detached forward tensors:
1. Native indication loss and its original matched-query labels.
2. PIRS's exact existing detached soft-IoU target/operator.
3. Joint operator with detached mask likelihood (selector-only ablation).
4. Joint operator with detached selector (mask-only ablation).
5. Repeat, query permutation and equal-mask neutral control.

Qualification is diagnosis only: actual selected-IoU<0.5 and oracle-IoU>=0.5
cases must exist; numeric outputs/gradients must be finite and repeatable.
Preserve all cases, including whether likelihood favors a mask worse than
the selected mask and whether responsibilities collapse onto one query.
Different gradients alone do not justify admission or establish improvement.
If no recoverable failure exists, reject this selection-deficit realization.
If the joint gradient is identically the detached PIRS gradient, reject its
claimed independent supervision mechanism. Other adverse evidence remains
pending for a native broader population test, not silently ignored.

Distinction under test: PIRS changes per-query detached soft labels; this
operator jointly models original mask evidence and query identity. CPS links
expressions sharing physical seeds; this operator has no cross-expression
sharing. Ordinary categorical seed ownership is not reintroduced.

Next action: native frozen cohort capture and exact matched operator backward.
No production graph edit, admission, resource PASS or training efficacy claim
is authorized by this diagnosis. A genuine positive diagnostic still needs
full-native backward, population/negative controls, goal review, independent
mechanism assessment, resource protocol, tested commit and gated dispatch.
