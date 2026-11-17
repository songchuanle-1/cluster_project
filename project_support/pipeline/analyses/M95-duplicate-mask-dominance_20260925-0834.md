# M95 Duplicate-Mask Dominance

## Question

Are the deployed low-IoU selections caused by a high-score wrong-instance
duplicate cluster that outvotes a less redundant target mask, rather than by
the already-closed score-ranking deficiency?

## Method

- Source: the completed 256-expression M95 exact capture with SHA256
  `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
- For every expression, select the deployed score-argmax query.
- Count other query masks with IoU above `0.5` against the selected mask as
  duplicate hypotheses.
- Count query masks with IoU above `0.5` against the target union as
  native-mask-positive target candidates.
- Compare the deployed query with the highest-score target candidate and
  report the same statistics on successful and low-IoU selections.
- This is read-only CPU diagnostic evidence. It does not establish a
  selector, model change, native backward, resources, novelty, or admission.

## Results

The capture contains `200` successful and `56` low-IoU deployed selections.
All expressions in both groups have at least one duplicate query mask.

| Group | Rows | Duplicate-query mean | Target-query mean |
|---|---:|---:|---:|
| Successful | `200` | `40.885` | `39.295` |
| Low-IoU | `56` | `17.786` | `8.696` |
| Low-IoU with target candidate | `40` | `17.925` | `12.175` |

Wrong-instance selections therefore do not show duplicate dominance. They
contain fewer mutually overlapping masks than successful selections, so
duplicate suppression is not supported as an error cause.

Among the `40` low-IoU rows with a target candidate, the best target query is
always below the deployed wrong query. On `29` rows, at least one duplicate of
the selected wrong mask also ranks above the best target query. This is still
the same target-versus-wrong-instance score-ordering failure. Seven selected
wrong masks also overlap the target above `0.5`, which is already covered by
the closed mask-co-support/positive-assignment route.

## Conclusion

The set-level duplicate-dominance hypothesis is rejected. A duplicate-aware
training loss, set decorrelation objective, or cluster-level suppression
mechanism has no supporting enrichment: successful selections have more than
twice the mean duplicate count. The remaining target-bearing failures require
the already-closed selector/ranking or identity path, and no new information
path is exposed.

No candidate is admitted and both queue slots remain empty. Do not implement a
duplicate-suppression, mask-diversity, or set-decorrelation successor from
this result.

## Evidence

- `pipeline/reports/m95_duplicate_mask_dominance_20260925-0834.json`
  `sha256=cc65914d4370e8016df4f58521cdfa140f2f4bb9f202765092475e667d608a6f`
- `scripts/m95_duplicate_mask_dominance_20260925.py`
  `sha256=8d146418a9055d8c8210ff482053e56219e819f847375b4a99a14a56c0110770`
- `scripts/test_m95_duplicate_mask_dominance_20260925.py`
  `sha256=59ed529ab65096255d4ce58ba9122f44822b434aa8a1e16eda725333211854a6`
- Local tests: `7/7` passed.
- Server-6 CPU tests: `7/7` passed.
