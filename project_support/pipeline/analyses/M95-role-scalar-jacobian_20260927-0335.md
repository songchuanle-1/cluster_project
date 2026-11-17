# M95 focal scalar and sampler Jacobian factorization

The preregistered native same-scene target/context/zero role-gradient test
failed its primary direction gate. A second unchanged-checkpoint server-6
GPU7 replay captured the actual scalar sample-loss derivatives at the same
266 comparisons, 133 physical positions and 13 scenes. All 128 input
fingerprints and selections matched the earlier capture; physical bindings
and positive target labels matched to numerical tolerance.

- The target scalar derivative was negative at 238/266 comparisons and
  positive at 28/266 soft-label comparisons. Context and zero derivatives
  were positive at all 266.
- Negative target/zero feature-gradient dots occurred 171 times; 158/171
  also had opposite scalar signs. The remaining 13 are not explained by
  scalar sign alone.
- Negative target/context feature-gradient dots occurred 36 times; 28/36
  had opposite scalar signs.
- Chain-rule removal of scalar signs yielded positive target/zero sampler
  Jacobian cosine in 173/266 comparisons and positive scene-mean cosine
  in 10/13 scenes. The remainder warrant no automatic causal story.
- Physical-position deduplication of the original vectors retained
  0/13 scenes with more context conflict than zero conflict.

These are descriptive fixed-checkpoint TRAIN diagnostics, not randomized
training interventions, efficacy evidence, or evidence for a novel method.
The focal soft-label derivative and language-conditioned sampler Jacobian
already explain much of the apparent gradient conflict. Do not present
generic contrast, PCGrad, label retargeting or a renamed ranking loss as
an independent core mechanism. An actual new supervision unit would require
independent causal diagnosis and a same-forward matched control before
native backward/resource/independence gates.

Sources: `pipeline/reports/m95_role_gradient_dedup_20260927.json`,
`pipeline/reports/m95_role_scalar_gradient_summary_20260927.json`,
`pipeline/reports/m95_role_jacobian_summary_20260927.json`.
