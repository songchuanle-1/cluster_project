# Native FPS Identity And Supervision Stability

## Hypothesis And Independent Axis
The new fixed-input coverage capture shows FPS index drift in scene0124_00.
Hypothesis: this drift changes physical query identity and native referent
positive assignments, creating contradictory supervision on otherwise equal
inputs. This is numerical/physical binding stability, not absence of target
anchors and not the previously observed exact-caption/different-target labels.

## Frozen Population And Controls
Use only scene0124_00's original native group from the frozen32/128 manifest,
M95 checkpoint, original config256->128, native TRAIN seed1999. Keep the same
collated input batch for all controlled forwards.
Capture pre-FPS superpoint coordinates, original FPS and selected identities,
physical labels, native positive assignments and final logits/masks.
Run four original forwards, then four forwards with only the pre-FPS coordinate
tensor restored to the first native capture. No source file or parameter edits.
Replay the original FPS primitive twice on exactly held coordinates, and the
native matcher with one existing non-target instance label as a negative
association control. Held coordinates/labels are diagnostic only, not deployed.

## Readouts And Reject Conditions
Separate FPS integer drift, physical instance changes, positive-query changes,
and float output drift. Record all changes and retain strict absolute1e-6.
If no physical-positive supervision changes are seen, reject this specific
observed-drift-to-label-conflict realization, not all initialization mechanisms.
If fixed coordinates preserve FPS but full outputs still fail1e-6, they do not
repair the complete native forward. No reclassification of earlier failures.
If a causal conflict appears, retain diagnosis and execute the next distinct
binding control before considering a model. No tuning, admission or efficacy.
