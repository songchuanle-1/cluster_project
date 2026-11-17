# Full frozen TRAIN query-union intervention

Stable ID `m95-sample-context-support`. Use the unchanged 256-expression
M95 TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and checkpoint SHA256
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`.

Apply the previously frozen `m95_query_union_support_20260927.py`
algorithm to all 256 expressions, not just the 16+16 cohort. Keep the
same full-logit reconstruction tolerance, deployed query, all-query
Boolean support, fused-feature replacement, half-width circular-shift
control and IoU >0.5 threshold. Partition *after* computation by native
maximum query IoU <=0.5 versus >0.5. Report expression/scene counts,
per-expression original and intervention IoUs, target coverage and
matched shifted-control changes. Summarize failure specificity, not
just aggregate improvements. No data-dependent threshold or support
selection, inference-time target labels, new model, or admission claim.
