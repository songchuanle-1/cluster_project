# BPS Frozen Native Query Bank Diagnostic

- Continue stable BPS ID, not a new variant. Freeze exactly the48 native
  ordinary groups/192 expression appearances/40 scenes already captured,
  using the same epoch4 checkpoint SHA f17f2ec3b08422f033a6683a4030bff1d69a1112514c6ac96dcb38870be735fd.
- Reuse immutable original runner and V3 exact buffer adapter. Bind both SHAs;
  preserve source/config/schedule and original matched-query capture.
- Extend READOUT ONLY to all native query masks, including unmatched queries.
  Native target support IoU uses unchanged native get_iou sigmoid>=.5 and
  GT>.5 rules. Selection is final TRAIN indication class1 argmax, not a
  claim about full deployed postprocessing or VAL performance.
- For each actual native bank, compute vectorized original support-excess
  and GT-minimum-pair oracle using the original point-count weighting,
  sigmoid probabilities, event mean and GT subtraction. Report per-query
  UNNORMALIZED quantities; verify matched sum/num_boxes reproduces original
  full component at1e-6. Verify original GT-self algebraic control equals0.
- Retain exact-zero versus >1e-6 counts separately. Stratify queries by native
  support IoU<.5 versus>=.5, selected versus bank-best, and original/oracle
  readouts. Low-IoU or zero cost is not itself a proved relation/label error.
  Do not call these wrong same-class objects without physical identity evidence.
- Two checkpoint-restored native forwards per group, input identity,
  mask/full-loss/readout repeats at unchanged1e-6. Missing geometry is
  unavailable, never a zero measurement. No output-dependent sample selection.
- Both conditions use exactly the same query masks and GT/native geometry.
  Return ONLY original support component to criterion. No parameter backward,
  optimizer, train launch, tolerance/precision change or reference relabeling.
- Same live server-6 GPU7/two slots/free>=32768MiB/.25 allocator/twoCPUthreads/
  all three original locks/600seconds timeout. Preserve foreign jobs.
