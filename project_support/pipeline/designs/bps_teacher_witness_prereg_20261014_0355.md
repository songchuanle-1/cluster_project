# Teacher-Witness Slack Diagnostic

- No production edit/admission: original independent BPS source stays frozen.
  Same eight original groups plus both input-ranked stress groups; all native
  companion expressions. Original checkpoint, seed1999, native criterion
  matching, actual cost fields and GT masks.
- Question: min_p relu(Eq_p-EGT_p) may select a pair whose GT cost is worse
  than the smallest available GT cost. Does original zero occur while ALL
  best-GT proxy pairs yield positive excess on actual native queries?
- Readouts per actual matched query/event: minGT cost, original min excess,
  original minimizing pair's GT cost, best-GT-set restricted excess, pair
  counts, and exact versus >1e-6 numerical-noise readout counts. Neither
  best-GT pairs nor class matches are asserted to be true physical witnesses.
- Diagnostic coupled contrast:
  J=relu(min_p(Eq_p+EGT_p)-2min_p EGT_p).
  The coefficient2 is the repeated-GT self baseline, not a searched weight.
  It jointly assigns one latent pair to teacher and prediction before the
  teacher-self subtraction. GT-self J is exactly0 algebraically.
- Constructed physically realizable two-slabs/two-point fixture demonstrates
  old zero despite switched best-GT witness; this is operator evidence only.
  Actual native data decides whether the slack is present; absence is not a
  claim that witness identity is known.
- Frozen operators, no clipping/temperature/routing/optimizer or fresh variant.
  Compare matched gradients/GT-self/identity twice on the SAME native graph.
  A component-only coupled contrast is NOT independent candidate/full-backward
  admission. If active, a future production change needs its own regression and
  behavior/resource/independence tests under the same stable ID.
