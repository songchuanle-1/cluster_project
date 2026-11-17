# Native Dataset Frame Capture

- Continue the same BPS robustness question without modifying M201-BPS.
- Earlier probes used raw geometry and exact native methods, not full native
  dataset outputs. Close that boundary before attributing drift to training.
- Frozen selection remains the same 12 scenes/48 expressions. Resolve each
  exact four-expression group in original scene_inputs; no substitution on
  missing groups. Use the deployed candidate dataset config, seed1999 once,
  native __getitem__, and its ordinary augmentation/sampling.
- Wrap only the diagnostic dataset instance's data_aug: retain RNG state,
  obtain the matrix with the exact method on an identity basis, then restore
  the RNG state after the original call. Return the original output untouched.
  Verify the original output equals input @ matrix before float32 conversion.
- Check original input supports/instance IDs/GT masks and coords_float
  against captured matrices, native BPS prepare, and event eligibility.
  Missing raw-point alignment after sampling is unknown, not a fabricated PASS.
- This capture is CPU-only. No model forward, native predictor logits,
  parameter gradient, optimizer or trained task-harm conclusion. It validates
  the data transport boundary, not an independent mechanism.
- Two threads, CUDA hidden in the diagnostic process, offline cached tokenizer,
  timeout600. Do not change the running package/config or acquire extra GPU slots.
