# Native Target Mention Role Diagnosis

Candidate: m95-native-target-mention-role
Hypothesis ID: parsed-root-mismatch-enters-target-supervision

Observation motivating a distinct test: in the shared-reference audit, some
native graph root nouns name a contextual reference rather than the annotated
physical target. This is not a claim about model predictions.

Freeze the existing32-scene/128-expression TRAIN manifest, original M95
checkpoint/config/seed1999 and native dataset/loss sources. Use native raw point
semantic-majority class of the single annotated target, the unchanged parser
root lemma and only unambiguous known native category mappings. Unknown classes,
missing target support and multiple matching non-root mentions are reported
separately, never counted as negative evidence.

First CPU test: count root category mismatch with independently known target
class; record candidate non-root target mentions, category-consistent annotations,
exact IDs and graph spans. Same-root category-consistent records are controls.

If examples exist, capture their original native token maps and full loss.
Compare original target-role maps against a target-identity-matched reassignment
and a wrong-reference reassignment on the SAME forward tensors. Only training
supervision may use native TRAIN target labels. No GT-conditioned inference.
Measure whether the map changes the intended token supervision and whether
native indication/token gradients actually differ. Preserve strict1e-6 repeats,
all graph failures and missing mappings. This does not prove trained benefit.

No numeric sweep, selector/pooling/routing/residual successor or model gate.
The proposed structural axis is target-mention supervision role, not co-reference
labels from lexical equality. Full mechanism, controls, native backward,
resources, independence and constraints remain unverified until tested.
Any existing-literature or old-realization identity must be tested, not assumed.
