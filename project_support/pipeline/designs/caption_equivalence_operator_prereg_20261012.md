# Caption-Equivalent Allowed-Set Operator Check

## Derivation
Given the same observable scene/caption with alternative physical instance labels,
let A be the union of native positive query indices for those labels.
Let s_q = indication[q,1] - indication[q,0].
A natural new-supervision-unit proposal is
L_alias = logsumexp(s) - logsumexp(s[A]).
It marginalizes the unknown referent query instead of demanding mutually
exclusive labels for identical input. No temperature, weight or numeric search.
For a singleton A this is ordinary categorical cross entropy; for all queries
it is zero. It does not recover unavailable intent or authorize multi-target
inference/annotation changes.

## Prior-Art Check
Verified original: Zombori et al., Towards Unbiased Exploration in Partial Label
Learning, JMLR25 (2024), original PDF p4 and Eq(2), repeated in section6.1.1 p25.
The NLL baseline is -log(sum_{q in A} p_q), p=softmax(s).
Primary source: https://jmlr.org/papers/volume25/23-0868/23-0868.pdf
This paper discusses NLL as a baseline, not as its new Libra contribution.
The query-label specialization above is our comparison, not the paper's
ScanRefer result. No novelty claim follows from a domain-specific name.

## Frozen Test
Execute independently coded logsumexp proposal and direct probability-sum NLL,
and independently evaluate the Eq(2) gradient p - p*y/(p dot y).
Use both saved native capture trials, each of the two expressions, float64
detached operator arithmetic. Match allowed-set, query-permutation,
same-target control and a rotated-set placebo. Preserve the full native
forward strict1e-6 failure separately; this cannot repair or replace it.
Equal loss and gradient within1e-6 plus algebraic identity rejects the claimed
independent new core, NOT the real input-identifiability diagnosis or every
possible future supervision mechanism. No full model implementation/admission.
