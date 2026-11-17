# M95 Target-Blind Geometry Screen

2026-09-26 16:00 Asia/Shanghai. Frozen 256-expression TRAIN capture;
server-6 CPU only, no GPU execution, training or model mutation.
The unaugmented scene coordinate file was bound exactly to the native
superpoint axis for all 256 expressions in 220 scenes; three support
binding tests and three graph-screen tests passed. The screen and negative
control were fixed in
`pipeline/reports/m95_geometry_screen_prereg_20260926-1553.md` before
the full screen was run.

The deployed selected mask's 6-nearest-centroid graph boundary fraction
was compared to a size-matched successful selection. All 56 deployed
failures had a match, but only 14 had a same-scene match. Mean
failure-minus-success difference was -0.00154 (27 positive, 29
negative); the rotated-superpoint negative control was -0.00264.
Within the 14 same-scene pairs the original mean was -0.00750 and
the rotated control -0.01021. These are descriptive paired values,
not scene-clustered efficacy estimates.

Restricting to the 16 *no-acceptable-mask* expressions, only 5 had a
same-scene match. The original boundary difference was -0.00528
(6 positive/10 negative); the rotated control was -0.00745. The
same-scene five had original -0.01062 and rotated -0.01835.
An unpaired component summary is likewise not enriched: 7/16
limited masks have >1 graph component versus 65/240 other masks.
The primary target-blind geometry signal does not separate failures
in the expected direction, and same-scene power is inadequate.

Close this specific centroid-graph boundary/connected-component
realization. Do not flip the sign, search thresholds, rename it as
coverage/BCCA, or produce an admission receipt. This does not rule
out every geometric representation or learned boundary mechanism.
Any genuinely distinct route needs a newly preregistered information
source and matched native control; the historical strict 26/65
cross-capture issue remains open.

Evidence:
- `pipeline/reports/m95_geometry_support_binding_20260926-1546.json`
  SHA256 `bde38848d2036d3d2c5b71640a12190106214a0437b28931a9109eaaf238c085`
- `pipeline/reports/m95_geometry_screen_20260926-1602.json`
  SHA256 `45d333fc08a6f35b9b7f7741910977e3b8f3fbace2cde44cdd68e7869880c2f5`
- Screen script SHA256
  `a78dbb2c9460de1e9ab225503847807911264133ce98c5d0246ba120b66c4676`
  and focused tests SHA256
  `d58f6fb7e0639010d9167681486603f6377a58e01602595359d6c1127e5f9a0c`
