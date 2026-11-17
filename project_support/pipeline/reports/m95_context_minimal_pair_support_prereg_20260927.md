# Physical support in the only strict fixed-target minimal pair

Continue stable `m95-sample-context-support`. The frozen 64-scene audit
identified only one fixed-target, one-class-token insertion pair:
`scene0035_00`, target instance 9, other instance 3, annotations 21/31,
token `desk`. Before reading the support values, reconstruct native
per-point context target using the first semantic label of each instance,
the exact class-token map, and target overwrite. Aggregate both
expressions to the same original superpoint IDs. Compare the other
instance's support values on/off, its physical point and superpoint
coverage, and the target instance's unchanged support. Record source
hashes and full denominators. The paired negative control is non-target
superpoints not overlapping physical instance 3, which should be
unchanged unless the token also maps to other desk instances.

This is a one-scene source-level feasibility check, not a native
forward/backward or failure-linked intervention. Different language is
still a substantive input change. No result can establish training
benefit or admission.
