# M95 full identity-control evidence

Time: 2026-09-24 23:18 Asia/Shanghai.

## Source

The pre-registered 256-row identity capture at
`server-6:/data3/songcl/Project/Cluster_project/pipeline/diagnostic_runs/m95_identity_capture_20260922-1813/capture.json`
was complete (`SHA256
f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025`).
It contains 256 report rows and 256 artifact rows stored in 250 hash-checked
shard files. Its manifest is the frozen hash
`4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023`,
and its checkpoint is M95
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`.

The CPU-only preregistered analyzer was run on server-6 against this capture.
The resulting local evidence is
`pipeline/reports/m95_identity_control_analysis_20260924-231333.json`
(`SHA256
c7b6e78c64e29144d3abfea5007e5ec0843142b3e7aa6294c600e8eb114d4abb`).

## Primary result

On the 65 complete score-matched ambiguous pairs across 65 scenes, selecting
the highest-scoring native target-positive query rather than the deployed query
increases the paired superpoint IoU by `+0.6649` pooled and `+0.6649`
scene-balanced. The scene-bootstrap 95% CI is `[+0.5864,+0.7398]`.

Across all 256 expressions and 220 scenes, target-positive oracle selection
has an `88.28%` expression success rate and `88.64%` scene-balanced success
rate, versus `78.13%` and `77.73%` for the deployed selector. The paired
scene-balanced uplift is `+0.1023` with 95% CI `[+0.0687,+0.1381]`.

## Matched controls

- Selecting the highest-scoring query with any dominant physical instance
  changes zero of 256 choices and therefore has exactly zero paired uplift
  versus the deployed selector.
- Target-positive selection beats the any-instance selector by `+0.0967`
  pooled and `+0.1023` scene-balanced IoU, 95% CI `[+0.0687,+0.1381]`.
- Selecting any query whose dominant instance has the target or a same-class
  peer changes the success rate only from `78.13%` to `78.52%`; the
  scene-balanced paired delta is `+0.0028` with 95% CI
  `[-0.0025,+0.0116]`, so the class-only repair is not supported.
- Restricting selection to same-class non-target instances succeeds on `0/123`
  available expressions.

These controls support a target-specific query-scoring defect. They refute the
interpretation that generic objectness or class membership alone explains the
selection gain. Oracle labels forbid a deployable efficacy or admission claim.

## Remaining blocker

The same capture omitted `native_match_cause`. Running
`scripts/native_component_counterfactual_20260924.py` failed closed with
`KeyError: native_match_cause` and produced no output. The existing capture is
therefore not enough for the repeated-GT mask component counterfactual; a new
full capture with `--capture-match-causes` is required after authorized GPU7
becomes available.

At 23:12 Asia/Shanghai, server-6 GPU7 still had external PID `3694608` using
`41,996 MiB`; total use was `42,023 MiB`, free memory was `39,057 MiB`, and
utilization was `0%`. No project process was launched or interrupted.

No queue mutation, training admission, native backward, resource gate, sync or
deployment occurred.
