# M95 frozen native-31 outcome and support incidence

Candidate: `m95-sample-context-support`, diagnosis only. Server-6 GPU7 was
vacant for the guarded native runs; each run held the existing exclusive
diagnostic flock, checked fixed source/data/checkpoint/script hashes and
stopped without modifying model weights. The first adapter attempt exposed
a missing `collate_fn`; the second completed 31/31 frozen TRAIN expressions
in two scenes. A later native source-boundary run completed 11/11 phrase
expressions with original `sp_ref_mask` parity. Neither was a training run.

Outcome capture: `m95_native31_capture_20260928-1018.json`, SHA256
`9952b3b8bcc2aa21442a70aae26c703ba1f39acbb76aaf97f1183e3511b3758c`.
Preregistered scene-target aggregation:
`m95_native31_grouped_20260928-1019.json`, SHA256
`05e1a233369cf9548c8e3681772d0b16f6b0e48fe5b5b70d4210d8744ba85c7d`.
The five scene0029_00 units average +0.1267 exposed-minus-control
selected-mask IoU, while the two scene0065_00 units average -0.01275.
These are text-confounded descriptions and only two scenes, not an effect
estimate or confidence interval.

Physical support: `m95_native31_incidence_20260928-1029.json`, SHA256
`a7b5b39f5cb2474e2d93bdb464c7c2f70b35cdddc796ed492f3f531830b596d3`.
All eleven exposed rows have physical support on native FPS seeds (55 per
expression in scene0029_00 and 21 in scene0065_00). Refined source matcher
audit: `m95_native31_incidence_v2_20260928-1036.json`, SHA256
`a081481280def0d3a57376142ccc6096089d2cabd26422963c46856db7ff799c`.
After excluding native matched/top-k protected seeds, all eleven rows retain
55 or 21 eligible treatment seeds respectively and at least 150 or 208
eligible zero-support placebo seeds. These counts are reused scene geometry,
not independent trials.

At 10:40 Beijing time foreign PID 2184092 temporarily occupied GPU7
(~19.9 GiB), so no diagnostic was launched then. After it cleared, the
guarded same-forward replay completed on 11/11 exposed descriptions at
10:53. Result `m95_native31_same_forward_20260928-1053.json`, SHA256
`0aff088bad85425c11a351e5f7c0d060020b219a71c5799db02cf45b10d89a17`.
Baseline repeated within tolerance; treatment and placebo each changed
the same 55 or 21 unprotected final FPS focal targets by 0.25, leaving
protected targets and non-sample losses invariant. All treated and placebo
`ref_scores` gradients were finite and nonzero relative to baseline.
Treatment sample loss was lower than matched placebo in 10/11 rows,
and all seven scene-target unit means were lower (scene mean unit contrasts
-0.000960 and -0.001239). The comparison is still a frozen TRAIN
loss-path perturbation, not inference improvement or trained efficacy.
The repeated descriptions share scene geometry, and the single adverse
description is retained.

The first replay failed exact-equality verification despite differences
below 1e-6, and the unchanged contract tolerance was applied on rerun;
the prior failure was not interpreted as a scientific result. Sampler
parameter backward, resource measurements, independence, and all six
admission gates remain pending. No candidate was admitted or dispatched.
At 11:02 Beijing time another foreign GPU7 PID 2275671 appeared; the
prepared sampler-parameter backward was not run while it occupied the card.
