# Native Target And Other-Entity Token Collision

Tick3d7b538083db43b2932216472dedaa8c; original deadline
2026-10-13T04:09:28.488289+08:00. Original TRAIN only, seed1999.

Hypothesis: the same native token position receives both main target positive
and other-entity supervision in original dense maps, despite distinct parsed
entities; this creates a conflicting role label for one referent decision.
This is not caption canonicalization, postfix drift, wrong parsed root,
TMR target-span rebinding, or literal multiword category recognition.

Freeze all36665 TRAIN annotations and original stored graph/fast-tokenizer/
seven-role mapping method. Audit positive_map row0 versus other_entity_map
native columns, excluding padding and reporting sentinel separately. Count
actual intersecting nonzero token indices, not shared word strings.
Record graph root and other-node spans for any actual collisions.
Controls: original native mapper on a constructed distinct-span two-entity
graph must separate; deliberately overlapping spans must be detected. These
constructed controls do not establish real parser correctness.

Reject only actual target/other token collision if all native TRAIN maps have
zero active-token intersection. If positive, freeze first collision per scene,
max8groups, prediction blind, and test native loss transport with matched
role-disjoint intervention; do not rename TMR or declare whole-method novelty.
Missing loss/backward/resources/independent package remain pending, not PASS.
