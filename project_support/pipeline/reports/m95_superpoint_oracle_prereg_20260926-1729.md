# M95 Superpoint Representational Ceiling Diagnostic

This is a read-only extension of the already rejected stable route
`cluster-instance-purity`, not a new model candidate. Freeze the 256-row
TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and the manifest SHA256
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`.
Bind each row's original unaugmented `scene*_refer.pth` point-to-superpoint
inverse and instance labels to the frozen capture. Use target object ID only
for a retrospective oracle; no label participates in deployable inference.

## Post-execution metric correction (17:34 Asia/Shanghai)

The first run failed closed because its guard compared point-level oracle
IoU to native IoU computed against binarized *superpoint* GT. Native
`target_union` has one entry per superpoint, not per original point.
These numerical IoUs are not comparable. Preserve that failure; the
revised output below is only a point-level representational diagnostic.
The original native-limited 16-row stratum is retained for descriptive
counts, not a claim that this ceiling explains their native failures.

For each superpoint, count target and non-target points. Sort all
superpoints by target purity descending, breaking ties by native
superpoint index. Compute IoU for every nonempty prefix and take its
maximum, including the empty-set IoU of zero. This exactly maximizes
the ratio of target points selected to union points selected because
for any fixed optimum IoU the inclusion condition is a threshold on
target purity. Report the point-level oracle IoU for all 256 expressions
and separately the 16 with no acceptable native superpoint-GT query.
Report full denominators without subtracting the incompatible IoUs.

If all 16 limited rows have point-level superpoint-oracle IoU > 0.5,
the original superpoint partition can in principle represent their
point-level target above that threshold. This does not explain their
superpoint-GT query failure. If any do not, that is a point-level
representation bound, not admission for a re-partitioner; no
model or training may follow without an independent structural
mechanism and six gates. Check hashes and point axis exactly and fail
closed on any disagreement. No threshold fitting.
