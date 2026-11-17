# Caption Equivalence Supervision Diagnosis

## Frozen Question
Candidate: m95-native-caption-equivalence-supervision.
Hypothesis: repeated native scene/caption inputs with mutually exclusive physical
target labels impose contradictory referent gradients even when all image,
language and query inputs are identical.
This differs from cross-expression consistency for descriptions of one object:
it tests one observable input associated with different objects.

## First Discriminating Test
Audit native TRAIN36665 annotations and parsed utterances, without checkpoint
outcome selection. Group by (scene_id, exact native normalized utterance), retain
original annotation IDs and target sets. Separate repeated same-target labels
from disjoint target sets. Report all denominators, do not alter annotations.
Intersect only with the already frozen32-scene128-expression manifest.

## Matched Controls
Same scene/caption/same target is a negative control.
Distinct text with the same target is not evidence of this hypothesis.
For disjoint labels, capture actual native same-forward indication/masks,
query seed identities and criterion positive indices; compare identical-input
outputs and native indication gradients, not a synthetic data-benefit claim.
Record any stochastic query differences or ambiguous graph equality.

## Predeclared Dispositions
No repeated-input/disjoint-target groups: reject this concrete explanation.
If native tensors differ, diagnose which input differs before claiming
contradiction. Actual conflict permits a supervision-unit derivation, but
generic partial-label marginalization or union relabeling alone is not a new
core contribution. Test exact equivalence to verified existing objectives.
No optimizer step, relabeling, extra annotations, new split, new seed or tuning.
Native backward/resource/independence/efficacy remain unverified until executed.
