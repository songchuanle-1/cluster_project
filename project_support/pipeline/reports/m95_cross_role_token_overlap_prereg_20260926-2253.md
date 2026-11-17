# Cross-role token supervision overlap

Stable ID `m95-cross-role-token-overlap`. Use the immutable native
`m95_token_span_integrity_20260926-2200.json` receipt (actual RoBERTa
token positions, verified source/graph/capture hashes) and its 256 frozen
TRAIN outcomes. The M95 loss makes node-0 target noun tokens positive and
other-object noun tokens an additional negative term. Before outcomes,
define the primary exposure as a token index in both the node-0 target noun
span and any nonzero object-node target noun span. Separately count overlap
of other-object tokens with node-0 modifiers, pronouns and relation spans,
which receive smaller positive terms, and overlap among node-0 roles.
Repeated mentions are not physical identity labels. Report all rows,
ambiguous/class-unique strata, failures <=0.5, and same-scene
exposure-discordant pairs; zero-length or unmapped spans are unresolved.

If primary overlap is absent or not enriched among failures, reject
this realization. If present, inspect exact phrases and verify that the
actual native loss uses both maps on the same token/query before deriving
a distinct mechanism. No training admission from an overlap count alone.
