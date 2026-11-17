# Existing Direction Results: Resolution And Complement Controls

- Secondary analysis after observing primary1e-6 finite-difference failures.
  It does not replace those failures or pretend to be a blind efficacy screen.
- Inputs are exactly this tick's complete25-group native task-head and48-group
  mask-direction records. Check hashes, use every measured condition, retain
  absent/zero directions; no new forward, precision change or step selection.
- Reconstruct native scalar descent/ascent from baseline plus stored deltas.
  Calculate binary32 final-scalar output spacing using adjacent IEEE754 values.
  Estimated derivative rounding budget is
  (0.5*ULP(desc)+0.5*ULP(asc))/(2*epsilon), with fixed epsilon.001.
- Compare recorded central-versus-analytic errors to this budget descriptively.
  It accounts ONLY for final scalar quantization, not intermediate arithmetic,
  nonsmooth heads or gradient-rounding error. Within-budget is NOT a new PASS.
  Above-budget is not proof of task harm or of absence of floating error.
- For each complete semantic condition/role/complement, reconstruct task dot
  as minus analytic unit-descent derivative times native direction norm.
  Check total=role+complement at1e-6 and count group-level combined opposition.
  A partial opposed direction is not the complete original semantic update.
- Preserve all1e-6 failures, scope and paired native input/checkpoint identity.
  No training candidate, PCGrad/weighting/priority/mass successor or gate change.
