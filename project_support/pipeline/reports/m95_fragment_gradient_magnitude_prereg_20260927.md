# Fragmented mask support and native source-gradient magnitude

Stable diagnosis `m95-sample-context-support`. Frozen 256-expression M95 TRAIN
capture. Join the four limited rows with positive extra target recall in the
all-query union to the existing native final-mask BCE+Dice gradient capture;
compare with the other 12 limited rows and the 16 preselected target-size-matched
covered controls. Bind both inputs by SHA256 and manifest index/scene.

Primary readout: median target-superpoint feature-gradient norm and selected
positive query-gradient norm. Also report median native loss and denominators.
If the four fragmented rows have gradients of comparable or greater magnitude,
simple gradient attenuation is not supported. If lower, treat it as a diagnostic
only: target size, mask error and matcher count may confound magnitude, and a
larger gradient is not evidence of useful parameter updates. Do not select
inference-time queries using GT, alter model weights, or grant admission from
this retrospective readout.
