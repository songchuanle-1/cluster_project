# Wrong-instance query seed context support

Continue stable ID `m95-sample-context-support`, but test a distinct
physical label axis absent from its previous lexical screen. Freeze native
M95 256-row capture SHA256 `9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd`,
TRAIN graph SHA256 `e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08`,
dataset source SHA256 `2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d`,
and TSV SHA256 `9c17c0da2061beea889edc9f49ff14e8218f4cd040ab241fc70186e03b32a744`.

Native `point_context_mask` marks all physical instances in the exact
utterance class-key set, target instance is overwritten to 1, then
`sample_loss` halves this value and overwrites matched/top-k seed scores.
This diagnostic maps each frozen query's `sampled_seed_indices` through
`fps_superpoints` to the captured physical/semantic superpoint labels,
checks the native matcher positive vector, and counts unmatched non-target
seeds whose semantic class is in the exact class-key set. A query with a
mixed or unknown class, out-of-range seed, or mismatched native matcher
axis is unresolved, never silently treated as negative. Matched queries
are not an exposure. The top-k overwrite is not captured, so this is
only an upper bound on final non-target class-context support.

Report all 256 rows, 128/128 strata, deployed failures, selected-query
exposure and same-scene discordant pairs. The negative control is
matched positive seeds and non-context non-target seeds in the same
expression; describe their denominators separately. If selected failure
enrichment is absent or the upper bound is sparse, reject this extension.
If it survives, capture actual native final `ref_padding_seed` and matched
controls before mechanism design. Do not admit or train from this screen.
