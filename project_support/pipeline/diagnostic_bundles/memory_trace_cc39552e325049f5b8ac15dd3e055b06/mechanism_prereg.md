# Current Independent Mechanism Controls

Same independent revision2 package and frozen TRAIN groups0,60,101,124;
4scenes/16expressions,2repeats. Reuse the already validated exact last-encoder,
last-decoder, raw token bank and native Criterion frozen-prefix replay. No
extra backward here: full independent native backwards were tested separately.

Freeze three diagnostic conditions, not three training variants:
canonical=current physical full-bank-axis disjoint-support readout;
uniform=identical disjoint supports, fusion and full bank axis, zero attention
scores so only content selection is removed;
ancestor=the original singleton fine/middle/coarse ancestors, same fusion,
projection/loss/prefix, separating support coverage from attention selection.

Verify native/current-canonical replay identity and within-condition repeated
masks/loss under original1e-6 bound. Require control-separated readout/final-mask
responses above the measured paired repeat differences; no fixed pretraining
task gain, significance or VAL threshold. Report both signed loss directions
and query-selection changes. Untrained fixed-weight loss increases are risk
signals, not trained efficacy; do not conceal or declare them improvements.

Measure branch-scoped support deficit on the actual stored hierarchy: point-
weighted fraction of valid leaves missed or multiply covered by original
three ancestor sets, versus disjoint cut coverage. Denominator is existing
valid fine tokens per expression, not raw scene points or all-model information.
Other network paths can already communicate scene context; do not claim the
whole model cannot see other objects. Geometric clusters are not semantic labels.

No source/config/loss/schedule/precision/batch/cap changes, optimizer steps or
validation-based selection. Keep prior12/4strictFAILs and all scope holds.
