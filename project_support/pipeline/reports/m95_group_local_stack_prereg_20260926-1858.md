# Local-Stack Physical Control

Stable ID: `m95-explicit-group-topology`. Frozen physical geometry artifact
SHA256 `1eb77f4ff466877e872bc084a3e52aa2afaf31ede2d0a88e45ab5dbc48a88766`
and group screen SHA256
`3b249386d9526296fa89df4c9b0e250a89eab388c880bcc338b0f611af2c3136`.
For all seven exposed rows, choose the nearest same-class peer by horizontal
(x,y) centroid distance, with object ID as deterministic tie-breaker.
This is an outcome-blind choice of a potential local stack, not a
target-blind inference feature. For explicit `bottom`/`lower` cues only,
compare target z against this peer. Report the reversed-z negative, the
horizontal distance, and all missing/unresolved rows. `under` is not
interpreted as same-class order; `middle column` additionally needs
a physical column-membership rule and is unresolved here.

No threshold is fitted, no validation/test data is used, and no model
intervention or admission is implied. This follow-up is motivated after
viewing the seven scene geometries, so its support is exploratory. A
separate predeclared cohort and true versus shuffled local-stack
native control would be required to advance the hypothesis.
