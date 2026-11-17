# End-to-End Gradient Diagnostic
2026-09-15;server4GPU1 only;two predefined native TRAIN batches;FP32.

First free-sampling attempt failed exact physical-seed equality after update.
No raw-query IoU comparison from that attempt is accepted.
Revised diagnostic fixes sampling indices only,not backbone features or gradients.
Both loss branches pass finite gradients and nonzero backbone-gradient assertions.
Updated physical seed identities pass exact equality guards.

|Batch/subset|Matched queries|Component-global hardIoU|SoftIoU|Inversions|
|---|---|---|---|---|
|0 connected|110|0|2.384e-8|0|
|1 all|71|.0091513|.0144885|-.1408451|
|1 connected|36|0|.0043104|0|
|1 disconnected|26|.0249901|.0333753|-.3846154|

Batch1 includes9empty interfaces. All71 includes these;subsets exclude empty.
Duplicate-global hardIoU/inversion differences0 both batches.
Duplicate logits max6.58035e-5/batch0 and5.34058e-5/batch1.
Connected batch negative control agrees within measured FP32 numerical noise.
Shared parameter updates permit connected subset effects in mixed batch1.

Limitations:diagnostic fixed sampling;one fresh optimizer step;training-set
GT-matched SP metrics,not validation mIoU. No independent population evidence.
This extends earlier frozen-backbone control to backbone parameter gradients,
but does not establish benefit with native free sampling or full training.
Next:physical-seed intersection comparisons with missing/duplicate accounting,
new predefined TRAIN batches,and outstanding novelty/implementation/resources.
Candidate remains validation/unadmitted;production and queue unchanged.
Evidence:component_e2e_fixed_server4_20260915.json and hashed script in research_work.
Decision20260915-224616_next_batch.md.
