# Frozen Native BPS Task-Head Direction Diagnostic

- Tick2bbb4e0b9a814185a795b2ea2178483f, immutable deadline15:08:04+08.
- Resume the three existing scalar validation IDs. No new candidate/config,
  optimizer, training launch or scientific gate conversion.
- Exactly the25 deduplicated ordinary native groups/97 expression appearances
  from the prior two source manifests; same native seed1999 and epoch4 BPS
  frozen checkpoint SHA f17f2ec3b08422f033a6683a4030bff1d69a1112514c6ac96dcb38870be735fd.
  Do not use newer best checkpoints or prediction-selected cases.
- Reuse immutable scalar_checkpoint.py SHA
  70055ed9aa157347ca045e536bfef9412dea0447ab1ab0fb6145f9095ee1bc60.
  Versioned AST adapter changes diagnostic capture only:
  enable the native forward graph, capture final decoder query/instance
  features/mask padding, and evaluate the original existing task heads.
- Extract previously executed functions from immutable
  native_role_calibration_20261014_0115.py SHA
  0ad3570f4aaf40a4122f92287b4bb88a69a8d387ed5ea917af3c409231fab67b,
  and native_role_head_20261014_0126.py SHA
  684244f76a8e81abb7679a1af7c958262e376888ba18a00e149a6bca2584af4c.
  Only the known singleton-mask metadata adapter is applied: native repeated
  GT mask rows must align to matched indices and be exact copies.
- Identify final semantic, mask and indication calls by native tensor identity
  or exact final unpadded-mask equality, not last-call/auxiliary assumptions.
- On the SAME forward, compute original semantic role-local query derivatives
  for MAIN-secondary, REL/OTHER, fractional-secondary and their complements.
  Compare dot products with original native mask, indication and combined
  task gradients. Test fixed-head ascent/descent at unchanged epsilon.001,
  with original/identity, head-identity and repeated-readout controls.
- Autograd stops at the final decoder query; all model parameter .grad must
  remain None. No optimizer, model-parameter backward or full-model update.
  Retain strict1e-6 identity/repeat failures, no tolerance or cohort repair.
- Report actual active role/expr/group denominators and absent controls,
  direction disagreement and finite-difference limits. This is local task
  response, not global causal harm, VAL mIoU, convergence or new-core efficacy.
- Same das/GPU7 UUID/free>=32768MiB/two slots/all3locks/.25 allocator/
  twoCPUthreads/600sec limit. Preserve all foreign jobs and original training.
