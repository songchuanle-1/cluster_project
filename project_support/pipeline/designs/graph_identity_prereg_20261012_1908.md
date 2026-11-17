# Native Annotation Graph Identity Preregistration

Stable ID: m95-native-annotation-graph-key-collision
Hypothesis ID: native-scene-ann-key-merges-distinct-referents

The original dataset indexes parsed scene graphs by scene_id and ann_id, not
object_id. Test whether actual TRAIN annotations reuse a key for distinct
physical referents or descriptions, producing a wrong graph lookup. This is
distinct from token postfix, character normalization, semantic point order,
and the already diagnosed wrong parsed root.

Use original TRAIN annotations, graphs and native source, hash-bound, on
server-6 CPU only. Report all 36665 rows, missing graphs, repeated keys,
distinct-target collisions and normalized annotation/graph caption mismatch.
Canonicalization follows original comma/whitespace normalization; do not
invent a new tokenizer or replace the source. Controls: a deliberately
duplicate key with distinct targets/captions, identical duplicate identity,
and wrong-graph lookup. Separate benign duplicates from distinct-target
collisions.

Reject only this key/lookup premise if actual keys are unique and all graph
captions match corresponding annotations. A detected collision supports
diagnosis, not a training admission, efficacy or independent novelty claim.
No native model backward/resources/independence gates are certified here.
