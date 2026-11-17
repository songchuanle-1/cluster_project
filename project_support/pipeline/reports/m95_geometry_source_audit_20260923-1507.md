# Frozen M95 Geometry Source Audit

2026-09-23 15:07 Asia/Shanghai. Event-mode bounded follow-up for the three
existing diagnosis IDs. Read-only source/schema inspection; no model execution.

## Evidence

- `pipeline/reports/m95_nearest_provenance_20260923-1211.json` (saved
  capture SHA256 `f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025`)
  established that the criterion's `sampled_pos`, `obj_pos` and cause tags were
  not saved.
- A targeted read of the completed native capture on server-6 found
  `hierarchical_fps_positions` for all four same-physical-seed-ID discordant
  classes (manifest indices 11, 23, 79, 253). Each row has three levels of
  256, 64 and 8 positions and 128 `sampled_seed_indices`.
- The capture producer's hook records `fps_pos` passed to
  `partitioner.partition_points` as `hierarchy_positions`.
  `hier_postprocess.py` computes this FPS from cluster-layer input `pos`,
  then aggregates cluster centers before subsequent levels.
- The native criterion instead computes `seed_pos =
  sp_coords_float[fps_seed_sp]`, `sampled_pos =
  seed_pos[sample_inds]`, and `obj_pos` from masked native
  `sp_coords_float` and instance masks. Its nearest-GT branch uses
  `torch.cdist(sampled_pos, obj_pos)`; instance-membership matches are
  added separately.

## Resolution

The hierarchy positions are real coordinates, but they do not provide a
query-index binding to the criterion's sampled seed coordinates or native GT
centroids. They cannot serve as a silent substitute for either input to exact
nearest-GT replay. The four matched seed-instance groups have zero exact
seed-index pairs; equal physical IDs do not imply equal query state. No
nearest-GT cause, representation collapse, or new supervision unit is inferred.

The three tracks remain in diagnosis. A native, separately bound coordinate
and matcher-cause capture is still required for discrimination; independent
query-state controls are still required for identity. Supervision needs a
distinct expression-level unit and matched native-positive/objectness/listwise
controls. GPU7 was occupied at observation (42,025 MiB used, 100% utilization,
one 41,996 MiB compute process); no GPU execution, launch, enqueue, sync,
resource measurement or admission occurred.

This is a source-contract audit of a failure-selected TRAIN subset, not a
population result or efficacy measurement.
