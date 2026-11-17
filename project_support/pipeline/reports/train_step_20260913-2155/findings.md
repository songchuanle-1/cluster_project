# Fixed TRAIN One-Step Experiment
2026-09-13 22:02 Asia/Shanghai.

## Design And Execution
Executed designs/exp_design_20260913-2110.md, with21:56 pre-forward addendum.
Original M95, batch2, four native expressions per scene, seed1999, original
augmentation/full loss/clip.1/restored AdamW, no scheduler step.
Scenes scene0000_00 and scene0001_00; all8 IDs and raw/tokenizer/source hashes
are in manifest.json. Current builder maps648 parameter positions/642 optimizer
states in5 groups by name/order, not shape matching. Historical parameter names
are unavailable: results are conditional on the current builder/environment.
No full training run, queue entry, model/config edit or checkpoint persistence.
Input/RNG capture fixed_batch.pth resides in the isolated remote output directory.

## Controls
- C0/C1:identical restored parameters/buffers/RNG, no step; max replay logit
  error4.7684e-6 below frozen1e-4 tolerance.
- Full differentiable source weighted loss reconstructed; gradient error0.
  This checks gradient of the summed reconstructed objective, not a saved
  separate gradient for every individual term.
- D2:actual full-loss gradient, source clipping and package AdamW step.
- C2:explicit zero gradients on the same active parameters with restored
  moments/decay; not a null and not additive decomposition of nonlinear Adam.
- Post-result ID alignment and fixed-original-seed forward preregistered in
  identity_followup_protocol.md before execution on the SAME saved input.
- Peak CUDA allocation4021.67MiB, below26GiB bound;600s timeout not reached.
- Both runs completed first attempt. No production repair or resampling.

## Outcomes
8 expressions:4 selected-mask successes,2 candidate-limited,2 recoverable
failures. Both informative failures are in ONE scene; no population inference.
Margin = selected minus highest-scored usable positive; negative change corrects.

| Scene/object/annotation | Head CE velocity | Full SGD velocity | Actual Adam linear change | Seed-aligned actual change | Fixed-seed actual change | Zero-gradient Adam aligned change |
|-------------------------|------------------|-------------------|---------------------------|----------------------------|--------------------------|-----------------------------------|
| scene0001_00/6/28 | -.078419 | -60.4248 | -.006630 | -.006553 | -.006554 | +.007932 |
| scene0001_00/0/29 | -.571527 | -11974.78 | -2.647617 | -2.149680 | -2.149677 | +.127258 |
Unscaled SGD velocity is not comparable in magnitude with finite Adam change.
Full-gradient norm19.3363 clipped to.1. Largest parameter delta9.105e-5.
The second finite-step remainder is.49794, so linearization is quantitatively
imperfect despite agreeing on direction. No inferred accuracy gain.

Both informative pairs retained all128 candidate seed IDs. Their50/53 changed
array positions were permutations, not membership turnover. Aligned and
fixed-seed changes agree within2.4e-6. The initial unaligned apparent changes
(-7.92795,-3.69148) compare different candidates and are INVALID endpoints.
Other expressions replace1/1/0/3/0/0/0/1 seeds; all retained in denominator.
Do not infer that candidate membership never changes.

## Decisions
- No head-correcting informative pair reversed under full loss or actual Adam:
  0/2 on this fixed batch. Reject the specific batch-local reversal explanation;
  insufficient evidence for a population-level conclusion.
- Momentum/decay-only control worsens both margins, but ACTUAL updates correct
  them. This does not justify a momentum reset, optimizer tuning or new method.
- Candidate reordering explains the initial finite-difference anomaly for both
  failures. Do not design a sampling-stability successor from it.
- No scientifically admitted new full-training variant. This experiment is a
  completed causal diagnostic control, not an innovation or training efficacy claim.

## Remaining Gaps
Historical optimizer mapping, historical batch/augmentation trajectory and
environment identity unproved. Forward replay is numerical, not bitwise.
No independent broader training population or temporal recurrence evidence.
No prospective new structural mechanism, primary-source novelty clearance,
mechanism-matched training controls, robustness or new efficiency profile.
The observed negative result closes this particular optimization explanation;
it does not justify an endless chain of similar gradient audits.
Return to the documented same-category/relationship error and derive a concrete
forward hypothesis only where a specific missing information path is established.
Do not infer missing relation information merely from overall low mIoU.

## Reproducibility
Manifest SHA:c67dfb6cb8e4cf3393ba7ffef8a010b22f5214ad45747e030a304f7956251626.
Acceptance SHA:a36c17d2ff7da005df953fe8b1b2b450b51d259007cbe48a7c87e82c35ddab45.
Fixed batch SHA:29438a33f049d3cffaeeeeb7874065e954d795c6fee920df8e8c1d4554518ff7.
Original and follow-up result JSONs retained separately with worker hashes.
Follow-up source extends the original worker; original execution log and worker
hash preserve provenance, not a claim that current worker bytes equal original.
28 pipeline tests passed; code repository status clean.
