# Motivation Review - Alignment Padding Contract
2026-09-16 06:09 Asia/Shanghai.

## 1. Goal
Authoritative pipeline/goal.json unchanged:Phase1 .51, exactM95 .5024607181549072.
Scientific admission precedes capacity; no bugfix renamed as core innovation.

## 2. Story Status
Existing source passes valid language masks into semantic alignment but does not
mask its object-to-token logsumexp. Dataset uses padding="longest".
Question:can incidental padding affect the native optimization objective?

## 3. Experiment Assessment
Server6GPU7 native checkpoint embeddings,4TRAIN batches31expressions.
182existing padding positions. Original criterion invoked on original embeddings
and on1/8zero extra tokens or8copies of an existing padding vector.
Ground truth maps and false language mask extended consistently;12controls.
No optimizer step;no full-forward batch-composition intervention.
Original padding gradient L1 perbatch .000879/.000813/.001460/.000924.
Existing-pad extensions lossdelta1.025e-5 to1.752e-5.
This proves loss-level leakage,not major error causation or training impact.

## 4. Gap Analysis
AST diagnostic changes only object-to-token denominator support:
logsumexp(logits + other_term over valid tokens).
Original-value equality checked before interventions. All12corrected controls
lossdelta<=2.3841858e-7,querygradientdelta<=3.818423e-8.
Existing and appended padding gradients exactly0.
Workerexit0;first versionzero-paddingonly alsoexit0,not a crash-repair.

## 5. Design Rationale
Mask correction is a correctness finding,not novel mechanism.
It must not be used to bypass the eight scientific gates or the prohibition
on trivial/operator-only variants. Production baseline/champion/M196 untouched.
Native effect small at checkpoint;do not reinterpret as dominant bottleneck.
Retain as protocol issue for a separately approved consistent correction,
not a filler training experiment.

## 6. Next Batch
Resume complete instance-conditioned mechanism derivation. No further padding
capture needed for this contract. Need novel whole computation and actual native
backward/resources before any independent model/config/admission.
Evidence padding_alignment_20260916.json and sourcehash;decision060842.
