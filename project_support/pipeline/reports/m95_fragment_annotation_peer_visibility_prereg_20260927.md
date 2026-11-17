# Annotation peer visibility and native support, frozen M95 TRAIN

Stable candidate `m95-sample-context-support` (diagnosis only). The previous
semantic-superpoint census found zero *uncovered* valid same-category peer
superpoints in two fragmented rows (manifest 64 and 104) that miss target
superpoints. Before viewing this test, separate three non-equivalent causes:
the annotated same-class peers are absent from the sampled scene; present but
semantically unknown/mismapped; or present but already covered by native
queries. Do not infer physical absence from an empty uncovered-peer set.

Freeze the 256-row full TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`,
its 256 artifact hashes, and the annotation-only manifest SHA256
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`.
For each of the 256 manifest rows, crosswalk the *declared* same-class
non-target physical object IDs to the sampled superpoint physical label axis.
For the two preselected fragmented missed-target rows report each peer ID's
present superpoint count, known semantic-label agreement with the modal
valid target category, fraction covered by the OR of all 128 native binary
query masks, and uncovered count. Report the same aggregate for all rows with
valid target category and missed target superpoints, split by original frozen
limited/covered/remainder cohorts and by independently annotated peers present
versus absent. Preserve scene and manifest denominators and unknown labels;
do not drop a peer for class disagreement.

Outcome interpretations: annotation peer present but covered means the
earlier zero-uncovered control is a visibility artifact, not a peer-absence
finding. Missing/unknown physical labels means semantic matching is
unresolved. A present-and-uncovered peer still needs prediction-blind
mechanism-only and placebo intervention; this observational audit cannot
admit a model, tune a geometry threshold, alter an inference selector,
queue, sync or train.
