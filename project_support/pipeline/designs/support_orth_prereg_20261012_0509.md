# Support-Faithful Cross-Scale Orthogonality Diagnosis

## Hypothesis
Replacing the native CSORT nearest-center inverse correspondence with the
actual partition support might produce a distinct, nondegenerate training
signal between fine and coarse evidence. This candidate tests that
prerequisite before implementing a production "correspondence repair".
It is independent of target/distractor context alias: the unit is a native
fine/coarse support relation and its objective derivative, not instance
identity or selector/mask ranking.

## Frozen Test
Use original M95, seed1999, existing 32-scene/128-expression TRAIN manifest,
unchanged model/config/dataset files. Capture original cluster-bank raw
features, original cluster_ids_list and child_cluster_maps. Compare the
nearest-center mapping with the exact fine-to-parent partition relation:
coverage, wrong-parent incidence and parent child multiplicity.
Compute existing CSORT with its original mapping, exact support mapping,
and a deterministic parent-label rotation as a matched association control.
No weight, temperature, norm epsilon, feature dimension or schedule search.

## Derivative Controls
On detached native fine features F, reconstruct P(F), the exact mean of the
fine features assigned to each parent, with differentiable float64 indexing.
Evaluate the existing absolute-cosine objective on (P(F), F) with the exact
same support relation. Compare with a cyclically rotated parent relation
and the native sparse correspondence on the same F and P(F).
Measure loss and all finite gradients with respect to F; this is an operator
diagnostic, NOT full-new-model native backward certification.
Where nonzero parent vectors are present, cos(P(F), P(F))=1 algebraically;
actual native float32 coarse values are checked separately to reveal
accumulation artifacts rather than silently substituting reconstructed values.

## Disposition
A structurally constant support-faithful objective with zero derivative
rejects only a bare map replacement as a new trainable core. Do not reject
all cross-scale mechanisms, alter the existing champion, or claim that its
original nonzero regularizer is ineffective. If the objective is genuinely
nondegenerate, persist the actual causal next test before further design.
Missing/zero-norm tensors are reported, not hidden behind a PASS.

## Scientific Boundaries
Keep absolute1e-6 repeat checks for the operator, and distinguish them from
known whole-native-forward repeat failures. No training efficacy, resource,
independence, novelty, admission or full backward PASS is inferred here.
Native data and operator execution occur only on authorized server-6 GPU7
under an exclusive diagnostic lock; no optimizer or production-source edits.
