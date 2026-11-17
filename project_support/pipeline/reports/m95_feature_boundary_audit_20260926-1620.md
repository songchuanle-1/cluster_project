# M95 Frozen Feature-Boundary Screen

2026-09-26 16:20 Asia/Shanghai. Read-only server-6 CPU screen on the
same frozen 256 TRAIN expressions / 220 scenes. Source capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
All feature-artifact and scene-file hashes, superpoint/point bindings,
expression identities and selected IoUs were verified. Three focused
feature-edge tests passed. The hypothesis and controls were frozen before
execution in `m95_feature_boundary_prereg_20260926-1613.md`.

At the **deployed selected-mask** crossing edges, compare mean cosine
distance of different-instance versus same-instance edges. The contrast
uses GT instance labels only to score the retrospective diagnostic, never
to choose a mask, feature or inference-time threshold. Eligible 15/16
no-acceptable-mask rows contain both edge types. Their original minus
rotated-feature control contrasts are 0.00857 raw 2D (9/15 positive),
-0.00263 raw 3D (8/15 positive), 0.03810 fused (9/15 positive) and
0.00859 final (9/15 positive). For the corresponding eligible covered
rows, the contrasts are 0.02292, 0.02981, 0.10570 and 0.01640.
Counts differ by feature validity: 176 covered raw-2D rows and 179
covered rows for the remaining modalities.

Only four limited rows have an eligible same-scene covered comparison
for all modalities. Limited-minus-covered original contrasts are
+0.03031 raw 2D (2/4 positive), -0.04635 raw 3D (1/4),
-0.08125 fused (1/4), -0.00270 final (1/4). No population
effect can be estimated reliably from four same-scene pairs.

The source feature banks encode some physical boundary information,
especially on covered examples. That does not demonstrate a distinct
missing task information path on the limited group or a control-separated
repair. Adding a generic feature-contrast/mask-edge loss would collide
with earlier boundary, identity/fusion and mask-supervision routes.
Do not train, label this as a six-gate PASS, or choose a coefficient
from the retrospective results. A genuinely independent mechanism
needs a new causal hypothesis and a native matched intervention.
Historical strict cross-capture comparator remains fail 26/65.

Evidence: `pipeline/reports/m95_feature_boundary_screen_20260926-1614.json`
SHA256 `f321f6928cddf95f5499eeea87d727e3bc687bf831c4fb3a25e7ab55eb79dfa0`;
script SHA256 `486216b446bf8493a95cd9bd8346a76b7ebacd883dd4f151d3c8a8222b9a8a4e`;
tests SHA256 `e0b31b2fd84a1f0397228908c1fd5d628b313fba715e3cac7cfff9b1eed2ce1a`.
