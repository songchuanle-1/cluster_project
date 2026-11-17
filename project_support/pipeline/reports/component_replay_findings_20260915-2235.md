# Fixed Backbone Replay Validation
Executed2026-09-15 on server4GPU1;existing processes preserved;memory fraction.28.
Native FP32 TRAIN batch1;71matches(36connected,26disconnected,9empty).

|Subset|Queries|Component-global hardIoU|SoftIoU|Inversions|
|---|---|---|---|---|
|All|71|.0078854|.0133503|-.0422535|
|Connected|36|0|.0039422|0|
|Disconnected|26|.0215332|.0307576|-.1153846|

Duplicate-global hardIoU/inversion differences zero;softIoU max2.98e-7;
logits max4.57763671875e-5. Global/component full loss.44873655/.42151758.
Finite parameter gradients;preclip norms15.43339/15.41591;inherited optimizer/clip.
Connected samples can change via shared downstream parameter gradients from
disconnected samples;this is not failure of connected loss equality.

Important:backbone extract_feat output detached/replayed and sampling fixed.
Thus only downstream parameters update;this is not end-to-end training evidence.
Fresh optimizer,one batch,one step,GT-matched SP metrics;not validation mIoU.
Inherited result.json scope string mentions two batches;actual results contain only
batch1. This document corrects that inherited metadata;do not count two batches.
Native training compute only on server4;no production code or training queue edits.
Next:end-to-end FP32 paired controls and additional predefined native batch;
original-source novelty,independence and resource gates remain incomplete.
Source/results hashed in research_work.json;decision20260915-223507_next_batch.md.
