# Semantic Positive Mass Diagnosis And Controlled Follow-Up

## Independent Mass Hypothesis
- Stable ID: m95-native-secondary-positive-mass.
- Hypothesis ID: boolean-positive-numerator-normalized-secondary-denominator.
- Original loss numerator uses boolean role support, whereas nb_pos_obj sums
  raw normalized modifier/pronoun/relation map values. A multi-token span may
  produce unequal numerator/denominator positive mass even without main-role
  overlap, encoding span-length-dependent attraction.
- Distinct from tmask precedence: no main/secondary overlap is necessary;
  leave every original tmask assignment untouched in this diagnosis.
- Audit unchanged full TRAIN/native mapper once. Count active secondary
  entries, raw-vs-boolean denominator disagreements and affected scenes;
  keep role-specific incidence and source/data hashes.
- Freeze the first eight distinct affected scenes sorted by scene/ann_id
  before controlled loss readouts; no prediction or VAL/test selection.
- Controls: original, exact identity, AST-edited boolean-only denominator,
  and a deliberately normalized two-token secondary span versus a
  one-token span. Do not present edits as a new deployable mechanism.
- Controlled embeddings: Q=128, token basis identity, zero queries; probe
  one fixed positive query/token logit at 0, 4 and 8 (dimensionL, NOT native64).
  All original logits/temperature/role maps fixed across each paired condition.
- Original Criterion is executed; the diagnostic comparison changes only
  the denominator expression. Two repeated readouts must be exact and finite.
- Interpret any changed loss/gradient as a loss-contract dependence, not
  adverse native-model behavior, parser error, novelty or training gain.
  Decoder projection bounds remain unknown here; no unbounded-model claim.
- If no actual mass discrepancy and positive controls separate, reject only
  this actual-data premise. Otherwise retain same stable ID for native
  same-forward validation and causal interpretation before admission.

## Precedence Follow-Up
- Continue m95-native-main-role-weight-precedence using the first eight
  affected scenes already frozen by role_weight_audit_20261013_0908.json.
- Compare original Criterion and identity with an AST-edited main-preserving
  tmask assignment, all other original inputs/terms unchanged.
- Use the same explicit synthetic embedding protocol above. Capture complete
  scalar loss and query gradients, identity delta and two-repeat equality.
- Inspect native getter maps for selected groups against original mapper;
  repeat map readouts with seed1999. Getter checks are NOT full-model repeat.
- Any native full-forward/backward, resource or trained efficacy claim still
  requires the fixed authorized GPU7 protocol. CPU derivatives are not PASS
  for the native_backward gate.

## Scope
- No production loss edit, optimizer, model/config variant, seed search,
  admission or launch. Simple weighting/normalization repairs alone cannot
  meet the project's independent-core requirement.
- No numerical acceptance threshold added or weakened.
