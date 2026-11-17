# BPS Native Frozen-Checkpoint Adapter V3 Preregistration

- Tick: 16d02ebf70a846bdad7f1c4f4d30b0c9; immutable deadline:
  2026-10-14T06:09:28.279988+00:00.
- Continue the prior BPS diagnostic and all49 eligible TRAIN expressions/
  all40 scenes with original ordinary companion groups. No new model,
  configuration, admission, optimizer or training launch.
- Preserve immutable V1/V2 scripts and raw failures. Reuse V1 SHA
  f29e5f8dd8dd70a8cb7428f8facd7f8e37401ced27e01cdf1e0ef2db19c175e9.
- Reuse the ORIGINAL prior frozen checkpoint, not a later best.pth:
  /data3/songcl/Project/Cluster_project/pipeline/diagnostics/bps_population_f8bdf4cb21774bf2af11f959fa12d89a/checkpoint_snapshot.pth.
  Copy to a fresh V3 output folder and record/compare its SHA.
- In diagnostic memory only, alias the native checkpoint model mapping to
  state_dict, preserving checkpoint bytes and all tensor values.
- Filter ONLY text_encoder.embeddings.position_ids and
  text_encoder.embeddings.token_type_ids, and ONLY when:
  both are native named buffers, both are absent from native state_dict,
  the entire unexpected-key set equals these two keys, and their shape,
  dtype and every tensor element exactly equal the constructed native buffer.
  Record both value hashes. Any missing/mismatched/extra key fails.
- Negative control: perturb one frozen buffer value in an independent
  diagnostic mapping; require the same equality checker to reject it.
  Never load that control into the model.
- Every other model weight/buffer must still load strict=True. Restore the
  original load hooks in finally. No broad strict=False or numerical repair.
- After adapter checks, execute the immutable original same-forward runner:
  native TRAIN, original checkpoint, actual matcher/mask logits, original
  support component returned unchanged to loss, diagnostic GT-pair oracle only.
  Restore model state and seed1999 for both forwards per group; input identity,
  native mask/full-loss repeats and per-query decomposition remain absolute1e-6.
- Failure is pending diagnostic evidence, not scientific rejection/PASS.
  GT-minimum pairs are not verified witnesses or deployed benefits.
- Live server-6 das/GPU7 UUID/free>=32768MiB/project slots<2 and all three
  existing lock guards remain mandatory. Allocator fraction.25, twoCPUthreads,
  timeout600seconds, no foreign-job eviction. Allow120seconds for reporting.
