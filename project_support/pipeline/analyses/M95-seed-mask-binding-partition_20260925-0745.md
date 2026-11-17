# M95 Query-Seed / Mask Binding Partition

## Question

Are the remaining deployed native-negative selections explained by
query-seed/mask binding failures, separate from the closed selector and
referent-ranking families?

## Method

- Source: the completed 256-expression full-train capture with SHA256
  `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
- For every one of the `32,768` query slots, map `sampled_seed_indices` through
  `sample_inverse`, read the seed's physical-instance label, and test whether
  the query's own predicted mask contains that sampled seed.
- Partition the `49` deployed native-negative selections by whether their seed
  lies on the target, the selected wrong instance, background, or another
  instance.
- This is a read-only CPU diagnostic. It does not establish a deployable
  selector, mechanism, native backward, resources, novelty, or admission.

## Results

Only `354/32,768` queries (`1.08%`) contain their own sampled seed in the
predicted mask. Among the `49` deployed native-negative selections,
`48/49` exclude their own seed, but this is not an enrichment over the
all-query prevalence (`2.04%` versus `1.08%`).

For those 49 selected negatives:

| Selected-query seed location | Rows |
|---|---:|
| Selected wrong instance | `1` |
| Different, non-target instance | `36` |
| Background | `12` |
| Target | `0` |

Only one selected query contains its seed and places that seed on the selected
wrong instance. The query seed is therefore not a reliable causal anchor for
the predicted mask: the model usually predicts masks that exclude the seed.

## Conclusion

Seed/mask membership is not an admissible repair target. A new supervision
term forcing masks to contain their sampled seeds would contradict the
dominant measured behavior and has no supporting association with the 49
selection failures. The result instead reinforces the closed ranking
diagnosis: target-seeded positive queries exist, while deployed native-negative
queries are scored above them.

No independent candidate is admitted. Keep both queue slots empty and do not
train or launch a seed-consistency successor.

## Evidence

- `pipeline/reports/m95_seed_mask_binding_partition_20260925-0745.json`
  `sha256=30ffe0954a05daec3787633cbf9a64f54d4526220e7ba8f65b4ee92c0a5d2e61`
- `scripts/m95_seed_mask_binding_partition_20260925.py`
  `sha256=c7610e72ae21dd5300df6804d90ad9bf8fc5290d9eb4c054817261939dc30699`
- `scripts/test_m95_seed_mask_binding_partition_20260925.py`
  `sha256=9ea80a138bd14722a3fae9f8271718e4f3741e5224626970282c7d066334054c`
- Local tests: `7/7` passed.
- Server-6 CPU tests: `7/7` passed.
