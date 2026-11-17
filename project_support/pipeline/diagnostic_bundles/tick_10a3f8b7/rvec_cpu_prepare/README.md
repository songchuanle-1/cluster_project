This is a new, isolated CPU implementation-test packet for provisional M234-RVE, candidate `fine-leaf-receiver-conditioned-vector-exchange`. It does not admit the candidate, deploy its nine files, or reuse an old admission receipt. The runtime HEAD remains 0747f6acec1c61018ec99acf2efa5329c9b3523c.

The packet executes only the hash-bound actual receiver_vector_exchange.py and the frozen FLE fine_exchange.py graph reference in memory. It does not import the native model, load data/checkpoints, run the native task loss or two native training steps, measure resources, use CUDA/NVML, change packages/environment files, or write remote files.

The fixed cases use the actual C256/H8/D32/K32 operator: singleton, small padded two-batch input, leaf sizes K-1/K/K+1, coincident K+1 cutoff ties with another leaf, all-valid multiple leaves, and one float32 K+1 case. Optimized/reference outputs and every differentiable feature/parameter gradient are compared at preregistered tolerances. All support fields must equal the inherited FLE builder and pass independent leaf/nearest-support checks. Cutoff ties retain the actual raw whole-leaf mean and permutation symmetry. Padding outputs and gradients must be zero.

The matched own-only diagnostic uses the actual forward_own_only method with identical geometry, IDs and parameters. Ordinary rows keep W2 GELU(Wr xi+b1)+b2; fallback rows return raw xi. Both paths must have exactly zero off-diagonal feature derivatives. The actual path must have a nonzero same-leaf off-diagonal derivative and zero cross-leaf derivatives in ordinary and fallback fixtures. Activity is not evidence of neighbor benefit.

One fixed toy CPU update checks finite gradients for every parameter of the complete isolated operator and finite outputs after a manual step of size 0.001. This is not native task training or an efficacy test. Source/model settings are never chosen from control results. Geometry and integer/bool membership inputs retain the original detached, nondifferentiable support semantics.

Both scripts default to NOP without Torch import, SSH or file mutation. Root execution requires GIT_OPTIONAL_LOCKS=0, Python -B, the exact foreground root thread/owner/context/pending hashes, unchanged source/test/FROZEN hashes, more than 180 seconds of lease, and a genuine independent source/test/transport review bound to the final bytes. The independent reviewer must not be root or this packet's author.

Root-only command after genuine review:

    python -B run_cpu_probe_once.py --execute-root --review ABSOLUTE_PEER_REVIEW_JSON --review-sha256 ACTUAL_REVIEW_SHA256

The transport uses the direct original conda Python -I -B, cwd /, CUDA_VISIBLE_DEVICES='', strict existing SSH host-key checking, and pinned hostname/uid verification before Torch. Owner, runtime HEAD, GPU UUID (provenance only), full source hashes, producer and request bytes are verified. No old shim or intent is sourced. Exclusive-create request/intent/result prevent replay; timeout is uncertain and receives no explicit signal or retry.

Python, Torch CPU and NumPy RNG states are restored exactly, and CUDA must remain uninitialized. Actual CPU tests, SSH, native tests and resources are NOT_RUN by the author; scientific admission is not granted and efficacy/novelty remain UNKNOWN.
