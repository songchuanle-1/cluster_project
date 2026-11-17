# Independent Hierarchical Fusion Padding-Invariance Diagnosis

Stable ID: hierarchical-padding-context-invariance-audit.
This is a finite source/native error diagnosis, not a model variant or
permission to modify the shared baseline, its mean operator or training.

Concrete source observation: actual inherited _cluster_to_points constructs
global_mean=point_feats.mean(dim=1) BEFORE masked_fill on its output. Thus
appending masked positions can change the context used by level_gate even
when all valid points, hierarchy IDs, scale messages and trained weights
are unchanged. This hypothesis is independent of norm-matched neighbor
permutation and must NOT call that helper or silently repair it.

Use the SAME unique terminalbest13 and the FIRST TWO scenes of the already
frozen32TRAINcohort in their unchanged order/seed1999. Capture actual native
cluster gather arguments/output, cluster message, final ILA prefix and
last decoder prefix. Require exact gather->message reconstruction and
unmodified suffix replay <=1e-6. No training, backward, VAL or selection.

At the gather interface ONLY append masked positions; leave valid tensors,
cluster tokens and ALL composed IDs fixed. Prespecified cases:7maskedzero
positions,Nmaskedzero positions,Nmaskedone feature positions. Extend fine
message with zeros, mark ALL appended positions masked. Compare valid
gather outputs/gate logits, then actual message_norm and same-prefix mask
readouts after cropping back to original N. Original fixed query INDEX.
The invariant expectation is valid outputs unchanged within1e-6. A larger
change disproves padding invariance of this exact interface; it is NOT a
task gain or proof of real training harm. Nonzero masked features are a
separate sentinel control, not a claim that native padding takes value1.

Negative control: ALL scale messages zero, same actual gather/projection;
masked padding must not alter valid output within1e-6. Preserve identity
controls, sample list, failures and uncertainty. Only2scenes/8expressions:
no confidence claim, generalization, improvement or novel contribution.

If padding sensitivity is present, shared legacy source provenance and
native batch2 incidence remain further questions. Do not unilaterally use
a single masked-mean replacement as a Phase1 structural innovation; the
project explicitly bans normalization-only tuning. A uniform bug fix is a
separate reviewed decision, not automatic admission or a baseline handicap.
Require fresh server4physicalGPU0/no foreign contexts/3lifetime locks and
the original local current-tick lease before native CUDA execution.
