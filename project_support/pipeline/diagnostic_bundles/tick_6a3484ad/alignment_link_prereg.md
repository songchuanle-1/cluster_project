# Exploratory Same-Cohort Alignment / Point-Readout Link

Use only existing saved32scene attention observations and the separately
valid32scene Q/F replication. No model execution, sample expansion,
threshold selection, VAL or reruns. Retain the initial Q/F norm failure.
This link is exploratory and was specified after seeing aggregate Q/F
readouts, before computing expression/scene associations.

Require identical scene order, expression order/ann IDs and input SHA256.
Primary denominator is the previously defined target-nonself-support set
(119of128expressions,32scenes); the9support-empty expressions are excluded,
not missing labels. Align = uniform_cross-target - attention_cross-target.
Point benefit Piou = L00-L01; point benefit BCE = BCE(L01)-BCE(L00).
Hypothesis: more target-aligned weights predict greater point-path benefit.
Use equal-weight scene means; report Pearson and Spearman relationships
with10000paired-scene bootstrap draws/seed1999/95%percentile intervals.
No bins, chosen subsets, multiple-comparison-confirmed claim or regression
of architecture efficacy. Background alignment is a specificity comparison,
NOT a guaranteed-zero negative control. Record all missing/constant cases.
An association or absent association cannot establish novel structure or
falsify the whole hierarchical point-update mechanism.
