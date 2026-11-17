# Group-Topology Physical Diagnostic

On the seven frozen explicit-group rows, bind the ScanNet TRAIN `_refer.pth`
physical-instance labels to the manifest target and same-class peers. For
each instance compute point count, centroid, and 10/90% z bounds, with a
SHA256 scene identity. The vertical control applies only to expressions
explicitly saying `bottom`, `lower`, `under`, or `middle`: check whether the
target centroid is lower than every same-class peer (`bottom/lower`) or
strictly between the min/max peer heights (`middle`), without choosing an axis
after outcomes. `under` is reference-bound and not a same-class peer ordering
without a resolved anchor; mixed `middle` and `under` is unresolved. Report
all rows including missing peers. No world-x/y
direction is inferred for `right`, `column`, or observer-frame words.

Compare target position with all same-class peers and an outcome-blind
negative formed by reversing z-rank. This is GT-bound oracle diagnosis,
not an inference-time feature or matched model intervention. A target
identity absent from physical labels, no peers, ambiguous stack membership,
or a contrary vertical relation fails this realization. Even a positive
result requires independently identified group membership and true/shuffled
native model controls plus remaining gates before admission.
