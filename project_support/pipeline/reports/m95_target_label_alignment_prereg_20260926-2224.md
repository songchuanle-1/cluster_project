# Frozen target-label alignment audit

Stable ID: `m95-target-label-alignment`. This is a TRAIN-only input/supervision
contract audit, not a model variant or a new selector. Freeze the 256-row
changed-producer cohort from the 2026-09-26 shape screen and the same native
ScanRefer source and parsed scene graphs, with their recorded SHA256 hashes.
The changed producer is not the strict historical full-scan comparator.

Before inspecting outcomes, normalize only case, spaces, underscores and
terminal plural `s` in the annotation `object_name` and graph node-0
`lemma_head`. An exact normalized match is aligned; a mismatch is an
**unresolved lexical mismatch**, not proof of incorrect identity. Report
empty/non-object target nodes separately. As a parser-noise control, count
expressions with at least one non-target object node whose lemma differs from
the annotated target category; this is not a ground-truth reference label.
Do not use this noisy control as a causal comparison. Stratify by frozen
ambiguous/class-unique status and selected native IoU <=0.5, list all row
identities, and count same-scene exposure-discordant pairs. Inspect exact
strings in mismatched failure rows before claiming semantic conflict.

Disconfirm this realization if strict mismatches are sparse, reflect synonyms
or annotation granularity, or are not enriched in failures. Favorable
incidence is only a diagnosis lead: a matched native intervention, distinct
mechanism, backward, resources, independence, constraints, and prior-work
audit are still required. No queue or training mutation from this audit.
