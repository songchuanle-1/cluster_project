# Native repeated-GT mask indexing prerequisite

Stable ID `m95-multigt-mask-index`. Source-bound synthetic evidence in
`m95_repeated_gt_mask_contract_20260924-0309.json` shows that expanded
masks can be addressed by unexpanded GT indices. The fault can affect
an expression only when at least two GT object IDs are matched and the
per-GT repetition order creates a displaced index.

Before examining failures, read the hash-bound 256-expression M95 native
capture (SHA256 `9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd`).
For each row, use native `native_match_cause.object_ids` and
`matched_query_gt_pairs`, assert their GT axes and recorded positive map,
reconstruct the repeated-mask indexing and count actual mismatched pairs.
Report every identity, all and ambiguous/class-unique denominators, deployed
failures and same-scene discordant controls. If zero affected rows, reject
as a ScanRefer research route; the source bug may still matter elsewhere,
but it does not support a new candidate here. Affected rows alone would
require native loss-path and matched intervention before admission.
