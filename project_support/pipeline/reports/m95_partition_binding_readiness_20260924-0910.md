# M95 Frozen-Partition Mask-Binding Readiness

2026-09-24 09:10 Asia/Shanghai. Event continuation of the three stable
diagnosis IDs. The read-only server-6 GPU7 observation found external PID
3694608 using 41,996 MiB, 42,023 MiB used, 39,057 MiB free, and 100%
instantaneous utilization. No external process was touched.

The unchanged M95 loss source (SHA256
`c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5`)
expands masks by GT match counts (line 534), then indexes them by unexpanded
GT IDs in mask BCE, Dice, and IoU-filtered score targets (lines 162-172,
560). The native matcher also supplies the indicator and semantic supervision
indices (lines 558-563). This is a conditional source-level concern, not
measured native incidence or a causal claim.

The existing 256-row checker now reports mask-binding counts by the frozen
outcome partition, including multi-GT, all-pair mismatch, target-pair
mismatch, and other-GT-to-target counts. The 256-row total and six exclusion
rows remain separate. These descriptive partition comparisons cannot
identify the effect of correcting the loss. Fourteen checker tests and seven
producer tests passed; both changed Python files compile.

Next: once GPU7 is available, verify runtime, data, checkpoint, and deployed
producer provenance; capture the frozen 256 TRAIN expressions with matcher
pairs and identity-query states. Run the partition checker, six-row
exclusion-cause analysis, and preregistered four-scene identity controls.
Supervision still needs component-isolated/coupled matched controls, native
backward and resources before admission.
