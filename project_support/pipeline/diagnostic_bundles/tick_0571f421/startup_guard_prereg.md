# Training lifetime guard

- Canonical gated launcher starts original tools/train.py, but does not itself keep the project's three GPU0 flocks. Before admitting this new candidate, bind its package's train.py-only import to a fail-closed lifetime guard. Do not modify canonical skill code, shared train.py, HDS, resource authorization or scheduling.
- Verify pinned server4 hostname/physicalGPU0 UUID, live idle NVML and all three locks before allocating. Reject late CUDA identity binding. Bind CUDA_VISIBLE_DEVICES to the authorized UUID; keep descriptors until the training process exits. Never remove locks, evict jobs or use GPU1.
- Diagnostic imports skip this branch and retain their existing three-lock runtime. The seven mathematical model-source files and YAML tested by native/resource checks remain byte-identical. New __init__/startup_guard add no parameters, forward path, loss, hyperparameter or model revision.
- First run the guard as a standalone zero-allocation check, verify all locks released and package/source independence. Preserve a failed guard test rather than weakening it. Admission and launch remain separate, through existing pipeline_monitor gated dispatch only.
