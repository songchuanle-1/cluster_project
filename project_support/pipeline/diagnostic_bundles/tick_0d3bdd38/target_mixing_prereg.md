# Terminal FLE Native Nonself Target-Mixing Diagnosis - Before Execution

Stable ID:fle-native-nonself-target-mixing-audit. New observational diagnostic,
not a new model/variant/reopening of M203. Motivation:the converged FLE screen
failed efficacy,and a valid early-checkpoint content permutation does not show
established benefit. Test whether terminal fine-feature attention actually
discriminates target-consistent neighbors beyond its geometric edge set.

Freeze unique already-declared M203bestepoch13,original source/config/data;
never select a different checkpoint after seeing this diagnosis. TRAIN only.
Before any forward,choose32unique scenes by SHA256(scene_id),each scene's
first native group with4expressions,from original dataset.scene_inputs.
Persist full group indices/object/annotation identities before prediction.
This may overlap the prior8TRAINscenes;not an independent held-out set.

One unmodified native forward per scene. An observational hook clones the
actual fine inputs/membership and output;GT is read only after that forward.
Reconstruct original attention and assert output error<=1e-6. Preserve K32/H8,
self support,hard cutoff fallback and augmented coordinates. No intervention,
query selection change,optimizer,new train,VAL or TEST. Use exact native
gt_spmasks only when binary and aligned;unknown labels are not fabricated.

For recipient i/head h,exclude self from its actual fine attention. Read out
cross-target normalized nonself mass,using1[y_j!=y_i]. Matched control is
uniform mass over the SAME nonself edge support,not shuffled masks or a
different graph. For exact-cutoff fallback use the actual whole-leaf mean
support,not truncatedK32. Singleton/zero nonself support is unknown and
reported with denominators. Primary statistic per expression is mean
weighted-minus-uniform cross-target fraction for TARGET recipients.
Expected task-alignment direction is negative,but no fixed magnitude is an
admission gate. Background and nonself mass/self mass are secondary summaries.

Controls:reconstructed source,all-equal-label null,global-label-complement
invariance,and synthetic uniform-feature weighted=uniform equality. Labels
must never change the returned features. Test synthetic controls on server4
CPU with CUDA hidden before native use;native runs require fresh pinned
GPU0idleness/threeflocks/current lease and all original asset hashes.

Aggregate expressions within each scene,then equal-scene mean. If at least10
known independent scenes,report5000scene bootstrap draws/seed1999;otherwise
no population interval. Report all denominators/missing labels and scene list.
This observational alignment statistic is not causal mask benefit,not
generalization or an innovation claim. It cannot admit a model by itself.
Any next mechanism still needs a prediction-blind deficit and matched causal
control;no new family or parameter sweep is authorized by this diagnosis.
