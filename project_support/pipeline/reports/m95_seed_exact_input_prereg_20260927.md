# M95 exact-input and instance-role repeat diagnostic

Stable candidate `m95-sample-context-support`. Use the frozen 256-key
manifest SHA256 `4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`
and its prespecified indices 0..15 and 128..143. Run the unchanged M95
checkpoint SHA256 `fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`
on server-6 GPU7, 16 native TRAIN batches per pass, with transform RNG seeds
1999 and 2000. The prior two seed-1999 captures are same-seed replays; this
new comparison must not call them independent augmentations.

Hash the collated native voxel maps, coordinates, features, superpoints,
language tokens and masks, instance labels and referent masks for each batch.
Bind each selected FPS seed to physical instance ID, target instance ID,
pre-context value and final criterion target. Report exact-input hash
agreement, selected-context exposure and IoU by the prespecified 32 keys,
with missing keys and changed outcomes explicit. Hash identity only certifies
the recorded tensors; it cannot establish identical hidden runtime state.

No candidate implementation or training is authorized by this diagnosis.
The next mechanism must change the supervision unit or information path,
preserve matcher/indicator/masks in a matched native same-forward control,
and pass backward, resources, independence and goal constraints. Failure to
find same-class or same-instance non-context placebo seeds is an identified
matching limitation, not license to call count/logit matching causal.
