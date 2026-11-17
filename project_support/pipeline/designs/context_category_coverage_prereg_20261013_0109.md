# Native Physical Target Context Coverage

Tick df2a9c7a64ac4f32aaeeb64746369555; original deadline
2026-10-13T02:09:04.233414+08:00. TRAIN only; original protocol unchanged.

Hypothesis: among annotation names left unmapped by the previous diagnostic,
the physical target has a known non-others native class, but the stored graph
utterance has no native lexical license for that class. This is a graph-to-
physical-context coverage test, not a rerun of annotation metadata transport.
The original target override may preserve target labels despite this deficit.

Freeze all36665 original TRAIN expressions /562scenes /7875physical targets.
Use original type2class, sem2nyu, nyu40id2class, TSV raw-category mapping and
unchanged graph utterance plus the native postfix. Do not infer synonyms or
change captions, annotation labels or parser output. Report the previous
unmapped and others subsets separately. Known-class lexical absence is a
diagnosis only, not proof of wrong language or trained harm.

Controls: class-name token present/absent must separate in the original lexical
loop; physical target override must remain intact. Select first eligible
annotation per scene, ordered by scene/ann_id, max8groups, prediction blind.
Run original native getter twice with seed1999 on this diagnostic extension.
Record whether a same-class non-target physical instance exists and its native
context supervision, distinguishing absence of an instance from exclusion.
Keep the original32/128 manifest and prior failures unchanged.

Reject the proposed missing-context premise only if no known-class unlicensed
case exists, or native paired observations disconfirm the claimed exclusion.
Bare lexical coverage repair is not an independent novel mechanism. Native
backward, resources, independence and whole-method novelty remain pending.
