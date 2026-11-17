# Native matcher contract in four mask-limited rows

Under stable diagnosis `m95-sample-context-support`, freeze the
256-expression full TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and the four-row residual JSON SHA256
`915e1d7e9385392a4f30da35a50b2698b54e005394caeb1d6d6a5ed2d3ca6bd5`.
Check the exact manifest IDs, native match-cause records, and query axes.
Partition the four selected physically target-seeded but mask-limited rows
by whether native `native_positive[selected_query]` is true; count same
physical target-seeded queries that are matcher-positive, and compare the
selected query's best IoU to the matcher-positive maximum. Report rows,
scene denominator and whether the selected query is nearest-GT or member.

This tests a supervision-contract ambiguity: physical target-seed identity
is not identical to native matcher membership. If a selected physical
target seed is matcher-negative, do not infer it received referent-positive
training or claim a new mask loss. If all relevant queries already receive
native positive supervision yet fail, ordinary native mask quality and
coverage remain explanations. No retargeting, selector, or novel model is
admitted from this oracle audit.
