# M95 Two-Anchor Resolvability Preregistration

Stable ID `m95-explicit-two-anchor-order`; read-only native TRAIN audit.
Freeze the two-anchor lexical screen SHA256
`69a5ea6de4ab4c72744b2431464858d19679571b79956752b9f44d71ac482725`
and manifest SHA256
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`.
Inspect the five failed `between` expressions only. The parsed scene graph
must contain two distinct edges with standalone `between` in the relation,
both from the same subject that denotes the target class. Each edge's
anchor noun must map to exactly one native ScanRefer scene `object_id`
by lowercase exact object-name match, and the two IDs must be distinct.
Report whether all conditions hold, never choose an anchor using target
IoU or outcome. This strict binding is a lower bound, not a universal
parser assessment. A lone resolvable row cannot support a population
mechanism; a target-versus-peer native spatial test would still be needed
before any design, alongside the other gates.
