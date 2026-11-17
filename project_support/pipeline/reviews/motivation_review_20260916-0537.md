# Motivation Review - Negative Existence
2026-09-16 05:37 Asia/Shanghai;continuation,not training admission.

## 1. Goal
goal.json unchanged,target.51;M95 exact.5024607181549072.
Seed1999,schedule,bans,existing-data and resource constraints unchanged.

## 2. Story Status
Existing fixedTRAIN scene0320_00/19 contains no-chair relation and wrong target.
Cue change influences logits,not selectedquery. FullTRAIN419cueexpressions
does not imply419negative-existence predicates;scope remains unverified.

## 3. Experiment Assessment
No new model accuracy. Native probe alreadycomplete;not repeated.
Static check distinguishes normalized anchor attention from absolute existence.
Same normalizedmass for logits[-10,-10] and[10,10];ordered relation score1
in both. Independent sigmoid-presence absence products .999909 versus2.061e-9.

## 4. Gap Analysis
EaSe original arXiv2502.01401v1 Appendix execution Algorithm2 lines17-20:
softmax relation score,if negative then max(f)-f,multiply candidate logits.
Negative relation execution already exists;not new to add a sign/complement.
Uniform relation scores yield zero reversedvector in this operator.
This is an operator property,not a claim the complete published method fails.
Primary HTML read and archived SHA256
ea91a7af0779892b7876a1c5bd1154e35abba7fe387bb3ba5b7c18af0b3b65df.
PowerShell download timed out;curl bounded retry succeeded,content verified.

## 5. Design Rationale
Provisional formula P(no witness)=product_j(1-p_j*r_j).
This standard independent-witness/noisy-OR complement is NOT core novelty.
Over SPs,duplicating a witness withp=.2 changesabsence .8 to.64 to.10737
for1/2/10copies;not invariant to physical sampling.
Negative-only supervision permits p=0 everywhere. Positive observations or
calibration are necessary to rule out that shortcut;not authorization for
additional labels or proof shared supervision can never learn presence.
Thus neither normalized-attention inversion nor naive pointproduct is admitted.
Need a distinct computation with observable existence/calibration and physical
support semantics,without reviving closed shared-witness/dedup variants.

## 6. Next Batch
No candidate/config. Keep the derivation as a limitation,not a new variant.
Do not repeat this formula check or original no-to-a probe.
Next examine whether an actual available instance-specific signal supports a
nonredundant mechanism;do not invent anchor labels or predicate truth.
