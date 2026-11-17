# M95 Feature-Boundary Screen Preregistration

2026-09-26 16:13 Asia/Shanghai. Diagnostic question only; no model variant.
Frozen 256-expression TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
The native artifact has 2D, 3D and fused superpoint features. Original
scene geometry and support were bound exactly in
`m95_geometry_support_binding_20260926-1546.json`.

On each frozen scene's symmetric 6-nearest-centroid graph, compare cosine
distance on edges crossing the **deployed selected query mask** versus
edges internal to that mask. Compute separately for normalized raw 2D,
raw 3D, fused and final features. All features, graph edges and mask are
available at inference; no GT or oracle query may select the boundary.
Use GT only afterward to label same-instance and cross-instance graph
edges, and to stratify 16 no-acceptable-single-mask expressions versus
240 covered expressions. Record zero-edge and undefined groups explicitly.

Primary prediction: among 16 limited expressions, native boundary
features provide directional, repeatable discrimination of same- versus
cross-instance edges not reproduced by rotating the superpoint-to-feature
association within the same scene. Compare the feature separation to the
240 covered expressions and report per-scene values; neither pooled
counts nor oracle-selected thresholds constitute causal evidence.
Control 1: identical recomputation must match exactly. Control 2:
rotate feature rows by one within the scene, retaining feature
distribution, geometry, mask and class labels. Control 3: compare 2D
and 3D separately to avoid attributing generic feature contrast to a
specific modality. No adaptive threshold or tuned numeric coefficient.

Reject this avenue if no directional feature-vs-rotation separation
appears in the limited cases, if too few eligible edges exist, or if the
measured dependency reduces to prior mask-edge segmentation/fusion or
previously rejected identity/ranking without a distinct task mechanism.
Positive offline association alone cannot pass diagnosis/controls or
establish novelty; any later candidate still requires native matched
intervention, backward, resources, independence and constraints.
