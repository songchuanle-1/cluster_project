# Native configured four-worker transport probe

- Additional execution-contract check for the SAME unchanged FLE candidate and M95 reference, not another model/revision. Existing controls/backward used diagnostic workers0; actual training requires batch2/workers4/persistent workers.
- Before any optimizer/training, execute the SAME fixed groups0,60,101,124 through the native build_dataloader with cfg train batch2/workers4/persistent_workers=True. Use native file_system tensor-sharing policy imported from tools.train, existing augmentations and seed1999.
- Record actual collated fingerprints and verify unchanged batches, four scenes/sixteen expressions, finite native full loss/backward and point-message gradients. No optimizer steps, workers override in candidate YAML, validation selection or recovery workaround.
- Candidate and M95 execute separately under fresh live resource checks/three locks. Fingerprints must match across arms before comparing memory; unequal inputs mean noncomparability, not guessed equality. Original workers0 memory comparison remains separately valid and is not overwritten.
- Explicitly shut down the iterator's configured persistent workers after collecting its two fixed batches and before forward/backward. This tests native worker transport, not full-dataset iteration, long-training memory, or absence of rare runtime errors.
