# M95 native component-counterfactual implementation

Time: 2026-09-24 22:13 Asia/Shanghai.

The existing native manifest capture already persists boolean query masks,
raw mask logits, query scores, physical instance labels, native-positive flags,
and native matcher causes. The missing post-capture step was an exact replay
that separates repeated-GT mask effects from hard-IoU score-target effects.

Added `scripts/native_component_counterfactual_20260924.py`. It validates the
frozen 256-row capture, checkpoint, manifest and artifact hashes, reconstructs
GT masks from physical instance labels, and replays four matched arms:

- original: native mask targets plus native score targets and eligibility;
- mask-only: corrected BCE/Dice masks, native score targets and eligibility;
- label-only: native BCE/Dice masks, corrected hard-IoU score targets and
  eligibility;
- coupled: corrected mask and score-target paths.

Each arm retains the same matched query/GT pairs and frozen query scores. The
indicator CE is computed from those scores and is reported separately; it is
not treated as evidence for or against mask-binding repair.

Verification: five new tests passed. Together with the dependent score,
mask-counterfactual and manifest-capture suites, 26 focused tests passed.
The new tests cover component separation, all four replay arms, exact
indicator invariance, scene-balanced summary, and fail-closed score/logit/mask
axis mismatches. Python compilation also passed.

At 22:09 Asia/Shanghai, a read-only server-6 query still found external PID
3694608 using 41,996 MiB on authorized GPU7; total use was 42,023 MiB of
81,559 MiB, with 39,057 MiB free and 83% utilization. No native capture,
model execution, backward, resource measurement, sync, admission or queue
mutation was performed.

The next executable action remains the ordered 256-row native TRAIN capture
after GPU7 clears and provenance checks pass. Immediately afterward, run this
analyzer on the capture and evaluate mask-only, label-only and coupled effects
before any admission claim.
