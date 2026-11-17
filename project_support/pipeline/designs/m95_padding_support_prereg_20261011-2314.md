# Native Text Padding Support Preregistration

- Created: 2026-10-11 Asia/Shanghai; owning tick b395a8b5064a4b6a810cc2285c82c890.
- Stable ID: m95-native-text-padding-isolation; hypothesis ID: phantom-text-loss-support.
- Hypothesis: native semantic alignment includes padding positions in its object-to-token partition function, so identical real-token representations and native annotations receive different loss/gradient solely from padding content or count.
- Evidence basis: champion loss.py loss_sem_align uses unmasked negative_logits.logsumexp(2); native collator supplies lang_masks. Forward sampling and attention already mask padding.
- Matched control: one frozen native TRAIN forward, same projected tokens/queries, masks, assignments and annotations; change ONLY invalid token representations. Repeat the original arm and use a real-token perturbation as a positive control.
- First diagnostic: import the exact champion criterion remotely; reproduce native semantic loss on fixed TRAIN groups. Compare original, exact repeat, invalid-token-zero, invalid-token-permutation and invalid-token-perturbation arms. Report valid/padding counts, input manifests, finite gradients and query-gradient differences.
- Non-GPU operator contract may use fixed tensors to verify masking sensitivity, but cannot stand in for native-data evidence.
- Predicted direction: padding perturbations may affect the current loss; a valid-support event likelihood should have exactly zero invalid-token gradient and be invariant to appended padding.
- Falsifier: no padding in the native cohort, or loss/query-gradient invariant to all invalid-token interventions within the existing 1e-6 repeat protocol. Failed repeat remains failed, not an effect.
- No tuning, no inference routing, no new dataset/annotation, no schedule/seed change. A single masking repair alone is not claimed as core novelty or sufficient Phase1 structural admission.
- If this is a real deficit, next test is a supervision-unit derivation with an independent new interaction, not renaming padding masking as a new module.
- Native data and behavioral execution remain remote only; GPU7 live occupancy and diagnostic lease must be verified. No training admission before all six gates.
- Post-training efficacy, scene uncertainty and novelty are unknown. Official target remains 0.5100.
