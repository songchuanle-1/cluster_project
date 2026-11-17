# M95 Subset Comparator Invalidation

2026-09-25 00:00 Asia/Shanghai. Design-mode closure continuation for the three
stable diagnosis IDs.

## Result

The manifest-only capture is not an exact comparator for the frozen full-scan
capture. Although the subset replay produced 256 expressions from the same
frozen manifest and checkpoint, it changed the native augmentation trajectory.
Compared with the frozen capture it changed the selected query in 170/256
rows, success outcome in 18 rows, 548,759/36,235,264 mask values, and produced
zero rows with exactly equal scores. The maximum score and logit differences
were 0.9994 and 108.83.

The replay result is therefore disconfirming evidence only for the subset
implementation, not evidence about repeated-GT masks, score targets, query
identity, or training efficacy.

## Action

An exact full-scan capture is running on authorized server-6 GPU7:

- output:
  `/data3/songcl/Project/Cluster_project/pipeline/diagnostic_runs/m95_identity_match_capture_full_20260924-2351`
- child PID: `3140840`
- last observation: step `132` of `4663`, `3617284` KiB RSS, 306% CPU
- flags: `--capture-match-causes --capture-identity-query`
- frozen manifest:
  `4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`
- frozen checkpoint:
  `fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`

The exact run must finish before the component counterfactual and identity
query controls can be evaluated. Do not launch a duplicate or substitute the
subset replay.

## Hashes

- subset component replay SHA256:
  `84e3d330bac31999927703a2b902e3e0d8983604ba75f00792f3e4ab731d87ec`
- subset comparator comparison SHA256:
  `5f709fc0a27d9b30ed2d3c9388069458fd15caad5a90ec7c6b239b93b49f3604`

## Limits

No admission, queue mutation, native backward, resource gate, deployable
efficacy, population effect, or novelty claim follows from this evidence.
