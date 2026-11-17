# Quality Coverage: Native Path Discriminating Follow-Up

Created 2026-10-09 after the first frozen capture, before this follow-up.
Stable ID remains m95-quality-supervision-coverage; do not hide the earlier
observation: quality censorship exists (9/341 matched pairs, 5/31 expressions).
This follow-up is conditional on that observation, not an independent
pre-registration of the original capture or a new population-effect test.

Test the specific absent-error-information realization: censored low-IoU
matched candidates have no corrective target-bearing native gradient.
Use the unmodified champion Criterion.loss_masks on server-6 CPU with two
fixed matched masks against one physical target: IoU 1/4 and 3/4; equal
quality predictions 1/2; original normalizer 2. No arbitrary loss reweighting.
Differentiate the actual native BCE+Dice and score outputs separately.
Control: high-IoU candidate on the same call; check the intended score
filter separates them, while checking whether mask supervision covers both.
The low-IoU realization is falsified if its native mask gradient is finite
and nonzero despite zero score gradient. Missing quality-head coverage then
does not establish absent physical target information in the shared model.

Also audit the exact active source: whether deployment reads scores, and
whether auxiliary loss functions recompute assignments. Retain hashes.
Do not reinterpret this unit control as trained benefit, population efficacy
or rejection of every possible quality-based mechanism.

Candidate disposition concerns this generic missing-target/threshold-removal
realization only. A distinct structural information path would need its own
pre-registered matched intervention; do not rename the old decision-aligned
ranking family. Existing freezes, bans and strict repeat tolerances stay.
