# Same-physical-instance context-label toggle

Stable candidate `m95-sample-context-support`, diagnosis. Prior native
32-scene final-FPS study lacked same-physical-instance zero-target controls.
The 64-scene all-annotation source cohort may contain pairs where the same
non-target physical instance receives weak context support in one expression
and zero in another. Freeze the first 64 lexicographically sorted TRAIN
scenes and all original annotation/graph records; recover native first-point
semantic class from physical instance labels and the exact class keys in
the graph utterance.

For each scene/physical instance with >=5 points, valid native semantic
class other than `others`, and at least two annotations in which it is not
the target, count distinct context-on and context-off expressions. Report
the number of eligible instances, toggles, scenes, and examples with the
annotation IDs and exact class-key sets. This is a *control-availability*
test; language and target differ across annotations, so toggles do not
establish identical model inputs, native FPS presence, causal loss conflict
or benefit. Negative control: instances with no exact eligible class key
must have no context-on expression. No GPU, model edits or admission.
