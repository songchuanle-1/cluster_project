# M95 Explicit Size-Language Diagnostic Preregistration

Stable ID `m95-explicit-size-comparison`. Independently test whether
comparative size language identifies a physical same-class distinction
missed by M95. Freeze the 256-expression manifest SHA256
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`
and deployed selected-outcome screen SHA256
`44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a`.
Descriptions are from native ScanRefer TRAIN only. No target masks or IoUs
enter feature computation.

Predefine two standalone token sets: larger `{larger,bigger,largest,biggest}`
and smaller `{smaller,tinier,smallest,tiniest}`. Exclude generic `big`,
`small`, `large`, `tiny` because they do not identify a comparison.
Mark both-direction descriptions as ambiguous and report them separately.
Primary stratum: the 128 same-class-ambiguous expressions. Report
exposed/non-exposed failure counts, class-unique negative control, and
same-scene discordant-exposure pairs. If comparative phrases are absent
among failures or have no within-stratum enrichment, reject this route.
If enriched, validate physical instance-size ordering among native
same-class peers under a deterministic scene-label binding, with a
within-scene shuffled-peer control, before any mechanism design.
An association is not a causal mechanism or admission.
