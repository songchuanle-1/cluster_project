# Paired Native Training-Path Resources

- Primary calibrated inference measurements are already complete and retained:
  baseline9.700876364G, champion/candidate9.762532428G. Do not replace that
  standard or unilaterally count extra operators against only the candidate.
- Supplemental real TRAIN benchmark: same two INPUT-selected stress groups
  5743/7787, original native augmented data/collate, seed1999, batch2/eight
  expressions, common native backbone checkpoint, clean process per target.
- Baseline/champion/candidate use their own physically verified original
  configurations and identical dataset batch fingerprint. Warmup20/repeat100
  whole forward loss/backward passes; no optimizer or parameter update.
- Report synchronized wall median/P90 (includes CPU geometry; excludes
  optimizer), allocated/reserved GPU peaks, all finite checks, parameters and
  actual candidate support-pair counts. Training mode may update BN buffers;
  this is a benchmark, not a trained checkpoint or task-benefit measurement.
- Same shared GPU7, free>=32768MiB, allocator fraction.25, both diagnostic
  locks, preserved foreign PID262355. Shared timing is not exclusive speed.
- +15% training memory would require the original +.003 trained-gain retention
  condition, not fabricated pretraining efficacy. No admission from this test.
