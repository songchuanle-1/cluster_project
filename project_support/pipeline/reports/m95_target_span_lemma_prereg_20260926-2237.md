# Target span versus lemma audit

Stable ID: `m95-target-span-lemma-contract`. Frozen 256 TRAIN expressions,
source/graph/capture SHA256 as in the prior audits. The token-span audit
proved span reachability, not that node-0 `lemma_head` is contained in its
own marked target phrase. Normalize node-0 lemma and each literal
`target_char_span` substring to lowercase alphanumeric tokens with only
terminal plural `s` normalization. Mark exact lemma-token subsequence
presence, and separately mark whether the final lemma token appears in
any target span. Compound descriptions, aliases and parser labels without
literal containment are unresolved, not automatically misbound.

Before reading outcomes, define primary exposure as nonempty valid target
spans with neither exact lemma-token subsequence nor final lemma token in
any marked phrase. Invalid or empty spans form an unresolved denominator.
Report every frozen identity, target span text, 128/128 strata, native
selected-IoU failure <=0.5, and same-scene discordant pairs. Negative
control: lemma-token subsequence present. Inspect exact phrases for
failure-exposed rows. Do not infer physical identity from lexical mismatch.

Reject the realization if exposure is sparse, aliases explain it, or
failure incidence does not distinguish exposure from control. No admission
without matched native intervention and all six gates.
