# Native query origin of covered annotated same-class peers

Stable `m95-sample-context-support`, diagnosis only. The frozen 256-row
annotation-peer crosswalk established that two fragmented rows with missed
target superpoints have 49 present valid same-class peer superpoints, all
covered by some native query. It remains unknown whether the *same
target-matched positive query* also covers those peers or whether the
coverage comes only from different matcher-negative queries. These imply
different failure sources; neither licenses a selection/ranking replacement.

Before reading query-specific results, freeze rows 64 and 104, the original
capture/checkpoint/manifest hashes and 128-query native-positive flags.
For each peer object and each superpoint, count support by (a) union of
all native positives, (b) union of all matcher negatives, (c) the best
positive query under the frozen target-IoU criterion, and (d) the
deployed selected query. Report counts for peer and missed-target support
on exact identical axes. Repeat aggregate for all 256 expressions with
valid target semantic class, at least one missed target superpoint and a
present annotated same-class peer; stratify frozen limited, covered and
remaining groups. Include scene counts and unknown/null query controls;
never treat `-100` as a class.

If peer support is confined to matcher-negative queries while the positive
mask misses target, the peer union is not evidence of cross-instance
confusion in the trained positive-mask loss. If positive queries cover peers,
ordinary BCE/Dice already supervises their removal, so a proposed new loss
must show an independent gradient/mechanism deficit before admission.
This is observational TRAIN diagnosis, not a native new-model intervention
or efficacy estimate. No threshold, selector, union, queue or training change.
