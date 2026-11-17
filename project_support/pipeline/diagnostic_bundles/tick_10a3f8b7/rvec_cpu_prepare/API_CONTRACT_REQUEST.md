CPU packet author: /root/fresh_ops. No Torch or SSH execution is authorized for this worker.

The collaboration messaging tool is not exposed in this worker. The actual API is now available under ../rvec_prepare/source/ and is used directly.

Required callable coverage: the actual optimized operator and direct reference, with the same parameters and features, through fixed ordinary, singleton, K-boundary, cutoff-tie, padding, and all-valid supports. The actual source exposes forward_own_only: ordinary rows retain W2 GELU(Wr xi+b1)+b2, while rows selected by the original cutoff-tie fallback return raw xi. This keeps each receiver's self transform and removes every off-diagonal donor, including on fallback rows. It is diagnostic only, never a selectable model variant.

All differentiable feature and parameter gradients must agree. Support/leaf isolation, off-diagonal donor gradients, own-only zero off-diagonal gradients, finite complete operator gradients and one fixed CPU-only update are included. Native model/data, task loss, native two-step training, resources, benefit, admission and novelty stay NOT_RUN/UNKNOWN.
