# M95 Explicit Orientation Diagnostic Preregistration

Stable ID: `m95-explicit-orientation-geometry`. Frozen 256 TRAIN manifest
SHA256 `4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`;
frozen outcome screen SHA256
`44b6833d717401b691236e14f42a3849b6b66ebcf466ab3ee4cfb195b7bc007a`.
The input descriptions and scene graph are native server-6 ScanRefer TRAIN
artifacts. No validation/test outcomes participate.

Freeze case-insensitive standalone tokens: facing, faces, face, oriented,
orientation, angled, slanted, tilted, leaning, upright, vertical, horizontal,
parallel, perpendicular. Report all 256 exposures, then ambiguous and
class-unique strata separately. Match the source by scene, ann_id, object_id
exactly and fail closed on duplicates. Compare failure incidence with
unexposed descriptions and exposure-discordant pairs within a scene.
Use target ID and GT only for the retrospective selected-IoU outcome, never
for an inference-time feature or threshold.

This lexical screen is not a native geometric intervention. Advancement
requires (1) evidence the orientation phrase modifies the target, (2) a
physically grounded reference frame or relative orientation, (3) a matched
native intervention that separates true from shuffled orientations under
the same model/data, and (4) native backward, resources, independence and
goal checks. Sparse exposure, contrary association, ambiguous referent,
or unavailable physical frame rejects this realization under its stable ID.
Do not infer a mechanism or launch training from lexical association alone.
