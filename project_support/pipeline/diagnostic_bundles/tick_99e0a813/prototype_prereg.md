# Isolated Operator Test, Before Native Integration

- Same fine-leaf-local-point-exchange candidate. Candidate-only operator stays in the diagnostic bundle; no existing model/config is modified.
- Six frozen controls: bounded within-leaf adjacency, recipient-specific off-diagonal influence without cross-leaf leakage, singleton identity, node permutation equivariance, isolated CPU autograd gradcheck, equivalence to ordinary scalar attention restricted to the same edges.
- Use existing K32 and8heads, no numerical scan. SciPy cKDTree builds exact nearest neighbors inside each original fine leaf; incomplete degrees are masked, not counted as repeated neighbors. No global NxN attention matrix. Feature gradients flow through gather/softmax/value sums; coordinates/neighbor selection are intentionally nondifferentiable.
- CPU float64 controls use1e-12 for algebra/equivariance and torch.autograd.gradcheck defaults. They do not change native model precision/tolerance and are not full-model native backward, efficacy, efficiency or admission.
- The standard-attention equivalence control is intentionally a novelty limitation: no original-contribution claim from this operator alone. The full task-specific hierarchy/point path still needs a material prior-art comparison and matched native controls.
- Verify pinned server4GPU0/no contexts/3locks and frozen source/best checkpoint after all diagnostics. Run this isolated CPU test in the existing remote environment only, no new dependencies installed. A passing toy does not clear a single unmeasured training gate.
