# Diagnostic GT-Conditioned Pair Compatibility

- Same 49 expressions/40 scenes/all237 physical masks; full population result
  e930143cfd9476c6336ba4f0a89278a86280d6d15d70450c1de30c7bb73a01c5.
  No selection by loss direction, no new model/config/queue entry.
- Question: among zero-loss alternatives, can contrast minimization choose a
  pair with higher GT expected cost than every GT-minimum-energy pair, hiding
  a positive readout when the teacher's own compatibility is held fixed?
- Matched control fixes the native GT masks/counts/fields and masks. For each
  event, retain every exact minimizer of the GT expected pair cost (float64,
  exact ties, no tunable tolerance), then call the unchanged native
  support_excess on these columns. This is an explicitly GT-conditioned oracle.
- Unrestricted losses must exactly reproduce the prior population arm.
  GT-self must be measured in both arms. No assumed universal inequality for
  mixed events, no task-benefit or admission threshold.
- Report all exact zeros/nonzeros, numeric differences at inherited1e-6,
  zero-unrestricted/positive-oracle cases, expression/scene denominators and
  retained pair counts. A GT-minimum pair is not a verified true witness.
- This is a causal reduction/selection diagnostic on ideal physical masks,
  not model logits, native model backward, deployable supervision, label
  correction, trained harm, efficacy or independent contribution. Do not
  launch a GT-pair selection variant merely from this result.
- CPU-only server-6, two threads, CUDA hidden for diagnostic, timeout600;
  M201-BPS and all prior controls/gates/failures remain unchanged.
