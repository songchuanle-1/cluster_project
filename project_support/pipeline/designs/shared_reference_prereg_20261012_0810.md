# Scene-Level Shared Reference Diagnosis

Candidate: m95-native-shared-reference-identifiability
Hypothesis ID: scene-caption-shared-reference-identifiable

The native TRAIN annotation and language graphs may provide an independently
identifiable physical reference for a relational utterance through another
utterance in the same scene. Such links could support a scene-level referent
supervision unit, instead of another selector/pooling/routing variant.

First discriminating test: inspect the unchanged native TRAIN graph/annotation
join on server-6, retaining the frozen 32-scene/128-expression manifest and its
IDs. Count explicit reference mentions, independently annotated object-category
instances, unique and ambiguous bindings, missing categories, and self-reference
collisions. Compare the literal mention binding to a deterministic wrong-category
control and a within-category alternative when available. No predicted score,
VAL performance or test-set label may select examples or define the binding.

An object-category match alone is not physical co-reference. Unique category
availability is a proxy, not proof of the described reference's identity.
If the native graphs explicitly identify reference object IDs, verify their
source and controls; otherwise report identity unknown and investigate whether
geometry or independently anchored descriptions can disambiguate it.

No rejection from insufficient cohort size, generic conceptual overlap or
unrun native tests. Rejection requires concrete nonidentifiability or an actual
control-invariant realization, and is limited to that realization. This
diagnosis has no claim of novelty, trained efficacy or admission.

Only server-6 GPU7 is authorized for native work. Local execution is limited to
orchestration, edits and static checks. Original model, checkpoint, seed1999,
TRAIN/VAL boundaries, resource budget, schedule and all bans remain unchanged.
