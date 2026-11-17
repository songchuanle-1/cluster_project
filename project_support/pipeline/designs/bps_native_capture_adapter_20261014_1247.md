# Native Capture Adapter Repair

- First attempt failed before model construction/forward:
  KeyError: state_dict. Preserve original native_capture.py and its execution.
- Read-only schema check of the frozen snapshot returned keys
  meta/model/optimizer/scheduler. model is OrderedDict; metaepoch4,
  best_miou0.4201701879501343. This is the actual project-native format.
- V2 reuses the immutable original runner and aliases only this frozen
  checkpoint's model mapping to state_dict in diagnostic memory. It does
  not rewrite checkpoint bytes, weights, source, model config or training.
- Reuse the first frozen checkpoint, copy into a fresh versioned output
  directory and bind the hash. No replacement from a later best checkpoint.
- All cohort, locks, .25 allocator fraction, free>=32768MiB, native
  input/repeat/decomposition1e-6 and no-optimizer/no-backward rules unchanged.
