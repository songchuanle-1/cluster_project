# Frozen Native BPS Mask-Direction Diagnostic

- Continue BPS stable ID with the same48 ordinary TRAIN groups/192 expression
  appearances/40 scenes and epoch4 frozen checkpoint. No new training candidate.
- Reuse immutable V1 native runner and V3 strict named-buffer adapter, original
  config, seed1999 and source manifest. Preserve prior scalar/ranking evidence.
- During unchanged same-forward support loss, clone actual unpadded mask
  logits as isolated differentiable diagnostic inputs. Keep original matched
  query/GT indices, GT masks, native support geometry and normalization.
- Original native mask task reference is loss_weight[0]*BCE +
  loss_weight[1]*Dice from unchanged Criterion.loss_masks on those SAME masks,
  original scores and matches. Do not include indication as a mask derivative.
- Compare original support_excess, exact identity and GT-minimum-pair oracle.
  The oracle subset uses exact teacher-cost minima, including all ties.
  Return ONLY the original support component to the actual native criterion.
- Compute each direction's gradient with respect to cloned MASK LOGITS only,
  dot with the native mask-task gradient, and per-matched-query dot/IoU/norm.
  Positive dot means local first-order mask-task descent; negative means
  opposition. This does not imply optimizer-level or model-level task harm.
- For finite-difference control use original epsilon.001 and the normalized
  whole-mask direction, paired descent/ascent and zero-direction control.
  Report analytic versus central derivative errors at unchanged1e-6 without
  dropping near-zero/nonsmooth cases or treating finite-difference failure as
  zero/no effect. Original and identity losses/gradients must match exactly.
- Two restored native forwards per group. Record full native mask/loss repeats,
  isolated-gradient/readout repeats, component identity and finite values.
  No optimizer, parameter .grad or model-parameter backward; retain failures.
- Report group/expr/matched-query denominators and inactive paths separately.
  GT-pair oracle is not a verified witness, independent mechanism, deployed
  repair or measured training/VAL efficacy.
- Live GPU7 guards and all3existing locks/.25 allocator/twoCPUthreads/
  timeout600 unchanged. Preserve external jobs and M201 training.
