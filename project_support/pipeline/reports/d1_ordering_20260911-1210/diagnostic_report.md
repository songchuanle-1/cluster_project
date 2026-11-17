# D1 Score Ordering And Semantic Alignment

Protocol frozen2026-09-11 12:10:32 Asia/Shanghai, before CPU execution.
Upstream six-sectionreview and seven-sectiondesign20260911-121000.
No model/config/training/queue change. No new inference or annotation API.

## Sample And Provenance
568 immutable banks:284 descriptions/model,71 physical scenes,128 candidates
per bank. Same frozen diagnostic manifest as previous audits, no reserved
scenes. Labels use previous assignment replay, not historical training labels.
All bank, summary, assignment, source and protocol hashes checked.
No missing IDs; no rank/selected-index discrepancy between saved float32
softmax and double-precision logit-difference ordering across568records.

OutputSHA bdc2eb6cf03cea4381124baae303acf7544f4bafb845605e0dba7cecaaa4bf23.
ProtocolSHA5f300b5fac61d0aa8529e53c7c919a1f07645008466e2e5269b05e93f9918b02.
WorkerSHA1cfa09eb6059f6e8dc28520a0e8a47cb6985992b71ee5d93f11606cf8da8812c.
Semantic functions AST-extracted from actual baseline/M95loss.py; package
source hashes match prior checkpoint identity audits. No active imports/mutations.

## Rank Definition
Let d_q=z_q1-z_q0; exact-arithmetic p_q=sigmoid(d_q) is monotonic.
Let G={q:pointmaskIoU>.5}, P=replayed seed-positive set, H=G intersect P.
For a nonempty set E in {G,H}, choose q_E=argmax_E d.
Report rank(E)=1+sum_q I(d_q>d_q_E) and margin(E)=d_selected-d_q_E.
Ties are recorded separately; no arbitrary confidence/margin threshold.
If E is empty, rank is missing, not zero or128. This is GT-based diagnosis,
not a deployable reranking algorithm or an improvement in measured accuracy.

## Ranking Results
| Model and stratum | Descriptions | Eligible E | Rank median [Q25,Q75] | Margin median [Q25,Q75] |
|---|---:|---|---|---|
|baseline success|171|G:171|1 [1,1]|0 [0,0]|
|M95 success|158|G:158|1 [1,1]|0 [0,0]|
|baseline recoverable|90|G:90|9 [5,18.75]|1.560078 [.734130,4.005056]|
|M95 recoverable|111|G:111|10 [5,22]|1.789623 [.691214,5.093583]|
|baseline recoverable|90|H:84|8 [5,16.25]|1.397878 [.719641,3.514381]|
|M95 recoverable|111|H:99|9 [5,16]|1.722511 [.650715,4.536512]|
|baseline bankfailure|23|G/H:0|missing|missing|
|M95 bankfailure|15|G/H:0|missing|missing|

Different G/H rows have different eligible description sets. Their aggregate
medians cannot be used to claim restricting to positives improves rank.
For a given description with H nonempty, rank(H)>=rank(G).
Success controls have rank(G)=1 by construction, not an independent discovery.
Usable-positive ranks in successes may exceed1 when selected usable seed was
labelled negative. Priorassignment audit counted6 such successes/model.

Common bank-usable intersection:256 descriptions/71scenes,28 descriptions
excluded for missing usable masks in one/bothbanks. First average eligible
description ranks within each scene, then average scenes equally.
Baseline meanrank6.698356808;M956.920187793;difference+.221830986.
Paired physical-scene bootstrap10000resamples/seed1999:
95% descriptive interval[-1.757071596,+2.097505869].
This conditional statistic does not establish generally worse M95ranking.
Per-model recoverable strata are outcome-selected and not identical pairs.
No calibrated probability, causal mechanism or population prevalence claim.

## Semantic Source Derivation
The decoder projects and L2-normalizes queries/tokens, S=V T^T/tau.
Saved config leaves tau atsource default.07. Innetwork.loss the original
valid-token mask is passed to criterion; decoder uses its own inverted mask
for attention. In loss_sem_align, lang_masks locates final valid-token indices,
but query->token logsumexp sums over the complete padded tensor dimension.
Attention key masking elsewhere does not itself remove these denominator terms.

For the controlled subcase with no modifier/pronoun/relation/other maps:
- A_ql=1 for matched query's annotated main token; unmatched queries receive
  positives at the last two valid-token positions.
- w_q=1 for matched queries, eos_coef=.1 otherwise.
- n_q=sum_l A_ql+eps, m_l=sum_q A_ql+eps.
- t_l follows source weights: defaults.1, main-positive tokens1, then
  penultimate-validtoken overwritten to.1.
- e_l=-log(m_l+eps)/m_l, M=matchedquery count.

    L = {sum_q w_q[-sum_l A_ql S_ql/n_q + logsumexp_l S_ql]
       + sum_l t_l I(any_q A_ql)
         [e_l - sum_q A_ql S_ql/m_l + logsumexp_q S_ql]}/(2M)

    dL/dS_ql = {w_q[softmax_l(S)_ql-A_ql/n_q]
      + t_l I(any_q A_ql)[softmax_q(S)_ql-A_ql/m_l]}/(2M)

    dL/dV = (dL/dS)T/tau
    dL/dT = (dL/dS)^T V/tau

These last derivatives are with respect to projected embeddings treated as
inputs to the criterion. They do not include the normalization Jacobian or
the rest of the decoder. Full parameter gradients are unmeasured.

For a padding column j with no annotation, A_qj=0 and I(any A_qj)=0:

    dL/dS_qj = w_q softmax_l(S)_qj/(2M) > 0

for finite logits and positive weights. Thus padded tokens participate in
query->token competition under this subcase. Holding valid logits fixed,
adding padding with log-sum-exp mass B_q increases this component by
sum_q w_q log(1+B_q/Z_q)/(2M), where Z_q is original valid-token mass.
No new tunable coefficient or novel mechanism follows from this identity.

The full source adds modifier/pronoun/relation terms (.2/.2/.1), overwrites
tmask in sequence, and doubles other-entity logits within one denominator.
The simplified formula above does not claim equivalence for arbitrary
overlapping annotation maps. Those cases remain an explicit audit gap.
Neither source fields nor parsing outputs are grounded relation truth.

## Controlled Tests
Three unit query embeddings, four unit valid-token embeddings, one matched
query; fixed maps and validmask. Compare:
1. Base no padding:source loss12.589463904389335.
2. Append two unit padding embeddings, validmask zeros:12.875488352177712,
   delta+.28602444778837643.
3. Same padded length, negate the two padding embeddings:12.589465522381605,
   delta+1.6179922699421923e-6.
4. Permute queries and matching indices:base loss unchanged.

Both actual model criterion sources give these same results. Valid embedding
gradient maximum change .6368021512810031 forcase2vsbase.
Four configurations/source; original autograd agrees with independently
derived criterion embedding gradients (maxerror1.300e-11).
Finite differences maxerror3.032e-10; independent localNumPygradient
readback passes. Tests usefloat64 projectioninputs andfloat32 source maps;
they are mathematical controls, not production precision replay.

This rejects padding invariance for these controlled inputs. It does NOT
establish padded-token exposure on actual training batches, how large the
effect is on trained normalized embeddings, or whether changing the loss
improves grounding. Priorinference grouping invariance tested a different
question and is not contradicted by a criterion-only counterexample.

## Execution And Decision
CPUworker3.5456383051s,peakRSS542.421875MiB,CUDAuninitialized,oneCPUthread.
First execution exit0; no repairs. All568local scalar ranking checks pass.
No mask recomputation or projection capture. Existingbanks do not contain
proj_queries/proj_tokens/lang_masks/densemaps; realsemantic exposure missing.
Helpers/protocol/review/design/assignment synced withhashverification to
bothservers /tmp/cluster_d1_ordering_20260911_1210. Deploymentdiffs preserved.
No active source edits, modelcommit/push,training restart or enqueue.

Next:measure actual token-mask/padding exposure and criterion gradient share
using an explicitly bounded diagnostic capture, before considering correction.
Reconstruct full maps and include matched success controls. If actual padded
mass/gradient is negligible, deprioritize this direction. Ordinary mask
correctness is not the requested core novelty, regardless of later efficacy.
No automatic auxloss/rescore descendant. Novel mechanism/primary comparisons,
causal matched intervention,generalization andfullmodel efficiency remain
incomplete. Validation was historically mined;reservedscenes only prospective.
