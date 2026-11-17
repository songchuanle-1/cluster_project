# Fixed-target physical context toggle

Continue stable `m95-sample-context-support`. Freeze the same 64 TRAIN
scenes and all ScanRefer annotations, using the same physical and exact
class-word contract as the preceding toggle availability audit. Tighten
the control: find two descriptions of the *same target instance set* in
the same scene where the same other physical instance has weak context
support in one description and none in the other. Target masks and scene
geometry then coincide. Record unique (scene, target, other-instance)
units, scene counts, exact annotation IDs, and whether the on/off pair
shares identical normalized graph utterances (negative lexical control).
No selection by checkpoint outcomes.

This remains a source-level control feasibility test. Different sentences
may intentionally change which context is useful. It does not prove an
incorrect loss, altered native FPS seeds, trained efficacy or scientific
admission. If no fixed-target toggles exist, do not claim the prior 679
cross-expression toggles form a matched supervision control.
