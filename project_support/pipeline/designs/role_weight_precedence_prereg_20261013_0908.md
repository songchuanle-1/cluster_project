# Role Weight Precedence Diagnosis

- Stable ID: m95-native-main-role-weight-precedence.
- Hypothesis ID: main-role-token-weight-is-overwritten-by-secondary-role.
- Hypothesis: an actual TRAIN token can be marked as a main target and a
  modifier, pronoun or relation simultaneously; the original ordered tmask
  assignments can then replace its main weight 1 with 0.2 or 0.1 in the
  token-to-query semantic loss. Whether this is intentional, harmful or worth
  a new mechanism is unknown.
- Distinction: not relation/OTHER positive-negative conflict, empty target map,
  postfix drift, main/OTHER intersection, padding isolation or span omission.
- Sampling: unchanged full TRAIN annotations and original scene graphs,
  native tokenizer and mapper; no predictions, VAL/test or label edits.
- First test: count actual main/secondary overlaps, altered tmask entries,
  expressions/scenes and role-specific incidence. Preserve exact source/data
  hashes and denominators.
- Matched controls: unchanged maps, deliberately disjoint main/secondary maps,
  deliberately overlapping main/secondary maps; evaluate the original ordered
  assignment versus a diagnostic-only main-preserving assignment. A source
  helper must be extracted from the actual original function, not reimplemented
  and presented as original behavior.
- Expected readout: original main weights decrease only in overlapping
  positions; disjoint positions and identity copies must remain unchanged.
  Repeated original mapper/readout results must be exact.
- Reject only the actual-overlap/override premise if full TRAIN has none and
  positive/negative controls separate. A positive result is a loss-contract
  diagnosis, not proof of wrong labels, adverse whole-model gradients or gain.
- If positive: compare original Criterion same-input gradients on the
  fixed native maps on remote CPU, then preregister whole-native same-forward
  confirmation before any implementation or admission.
- No new model/config, numerical search, optimizer or training. Bare weight
  precedence repair cannot be claimed as an independent contribution.
- All six admission gates remain unpassed until separately evidenced.
