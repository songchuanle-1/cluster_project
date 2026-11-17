# Shower-curtain phrase graph-role audit

Freeze the 11 physical phrase-exposed expressions in the SHA-bound
`m95_multiword_context_20260928.json`. For each original TRAIN scene graph,
locate every adjacent exact `shower curtain` occurrence in the original
utterance. Classify each occurrence by overlap with validated
`graph_node[].target_char_span`: target node 0, other Object node, both
(ambiguous), or unbound. Include all phrase occurrences and graph nodes;
do not choose the one that best fits a route. Bind graph SHA to the physical
report. Report unique expressions/scenes, mention-level denominator, and
expression-level other-only versus target/unbound incidence.

This is only a linguistic-role check. Graph nodes are not physical instance
IDs; no outcome is captured for these scenes. Other-only mentions are a
necessary descriptive observation for an anchor-context hypothesis, not a
causal loss-path test or a structural admission. Fail closed if spans or
physical report source hashes differ.
