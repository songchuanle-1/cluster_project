# M95 Native IoU Capture Integrity

2026-09-24 14:08 Asia/Shanghai. Event continuation of the three stable
diagnosis IDs. A read-only server-6 GPU7 observation found external PID
3694608 using 41,996 MiB; GPU7 reported 42,023 MiB used, 39,057 MiB free
and 100% instantaneous utilization. No native capture or sync was run.

The 256-row post-capture checker now rejects nonfinite and out-of-range
IoU values before comparing the frozen outcome counts. In particular, a
nonfocus row's zero IoU can become NaN or negative while all thresholded
counts remain unchanged; both cases now fail closed. The native producer's
hard-mask IoU remains unchanged. 35 focused synthetic checker, source-count
and producer tests pass; AST syntax checks pass. This is capture-integrity
readiness, not native incidence, causal attribution, efficacy or admission.

Once authorized GPU7 is clear, verify SSH, occupancy, code root, runtime,
data and checkpoint/producer provenance; run one ordered 256-row native
TRAIN matcher/query-state capture. Audit all-row outcomes and GT-mask
binding, six-row exclusion causes and four-scene identity controls.
