# M95 Two-Query Union Upper Bound

2026-09-26 14:53 Asia/Shanghai. Read-only CPU diagnostic on the frozen
256-expression TRAIN manifest. The source capture SHA256 is
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`;
every native tensor artifact was checked against its capture hash. The
manifest SHA256 is
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`.
No forward, training, model modification, or GPU use was requested.

For each expression, enumerate the union of two *existing* native predicted
query masks and compare its target IoU to the best single query. This is an
oracle upper bound: target labels select the pair and cannot be used at
inference. The target is the same native superpoint target union used for
the saved query IoUs. All 256 best-single values reproduce the capture
within 1e-6.

| Frozen stratum | Expressions | Oracle pair IoU increased | Crossed IoU > 0.5 |
|---|---:|---:|---:|
| No acceptable single query | 16 | 4 | 2 |
| Acceptable single query exists | 240 | 35 | Not a rescue |

The two rescued no-acceptable cases are manifest row 64
(`scene0186_00`, ann 93; 0.5000 to 0.7778 by queries 86/90)
and row 104 (`scene0463_00`, ann 30; 0.4091 to 0.5217 by
queries 14/45). The remaining 14/16 are not rescued even with
target-aware pair choice. These 16 expressions belong to 16 distinct
scenes. This does not establish that no new mask generation mechanism can
help; it specifically weakens the proposed *existing two-query mask
composition* route. It does not pool the earlier 123-expression coverage
cohort or reverse its sampling result.

The bounded relation cohort overlaps only 29/256 expressions in this
manifest; seven are deployed failures, five of those have zero anchor
candidates. Neither a generic relation route nor a pair-selector has a
separate supported information source from this audit. No mechanism
controls, native backward, resource, independence, or admission receipt
are present. Leave the queue unchanged and preserve the strict 26/65
reproducibility failure.

Evidence: `pipeline/reports/m95_pair_union_bound_20260926-1450.json`
SHA256 `e84871b5c9f7a9007a570792ce349f938cb40f790985ea6a6a87ebde0e6b575e`;
`scripts/m95_pair_union_bound_20260926.py` SHA256
`2bf4c92c382f8671c0b9a279e12b9f1531d71de5ba38a9e9ec19a8ebc18aef7f`;
three focused native-CPU tests pass in
`scripts/test_m95_pair_union_bound_20260926.py` SHA256
`c8feefe796c25bc10b0ec427ca5271a00275b2785fc89bdb5886c6eb6b87b06b`.
