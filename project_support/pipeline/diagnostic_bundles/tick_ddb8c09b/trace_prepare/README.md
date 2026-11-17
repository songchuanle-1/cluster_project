# Preparation-only real TRAIN-data trace carrier

**BLOCKED; not frozen, not launchable, no runtime readiness established.**
This directory contains locally authored source and a deliberately blocked
packet template. It does not contain an SSH command, launch supervisor, new
model, training admission or repaired training implementation.

`trace_carrier.py` defaults to NOP. The only local execution performed during
preparation is its default NOP plus stdlib AST parsing; neither imports Torch,
opens remote data nor starts workers. An eventual root-reviewed supervisor
would run the ordinary project Python3.10 interpreter, never the consumed
production entry. No such invocation is supplied here.

The intended observation uses the exact d214 dataset and build_dataloader,
rendered production YAML, seed1999, train split, batch2, four persistent
workers, default prefetch2, augmentation, elastic deformation and mode4 CPU
voxelization. It does not import tools.train, resolve a network, construct a
model, invoke loss/backward, load a model checkpoint or initialize CUDA.
The environment requires empty CUDA_VISIBLE_DEVICES, bytecode disabled,
original TOKENIZERS_PARALLELISM=false, and offline tokenizer/HF behavior.

The finite-work instrumentation wraps the original BatchSampler with an
explicit ten-batch prefix. It calls the original iterator next exactly ten
times and leaves RandomSampler order unchanged for that sequence. The
configured batch size, four workers and prefetch factor stay original, but
this is transparently a finite diagnostic sampler, not a full training epoch.
At most ten batches/twenty dataset groups can be scheduled; ten are consumed,
and an additional next verifies StopIteration. A clean observation therefore
has zero scheduled batches beyond the consumed ten. Original model,
profiling, epoch history and CUDA-parent RNG consumption remain absent, so
seed1999 does not identify the historically failed input.

Instrumentation calls each original stage once with unchanged arguments and
returns the original result unchanged. It adds no RNG draws, seeds or state
restoration inside observers. RNG digests use Python/NumPy/Torch CPU state
getters only. Constructor and original gorilla seed calls retain their
original behavior. Records contain worker PID/start ticks, group/scene/ann
identity, stage enter/exit/exception and small shape/dtype/contiguity metadata.
No features, raw utterances, full samples or pickle dumps are serialized.
Voxel batch endpoints are read as two CPU scalars; they are explicitly not
claimed as a complete min/max validation.

Stages include __getitem__, trusted scene/CLIP torch.load, load, transform,
data_aug, elastic, sample_rdn, get_sp_label/get_ref_mask, positive token maps,
tokenizer, scatter_mean, collate and voxelization_idx. A stage enter without
exit identifies the last observed boundary, not the instruction that caused
a fault. Instrumentation changes timing.

Every worker enables its own faulthandler FD in worker_init_fn, which must be
shown by the exact installed worker source to occur after Torch installs its
critical signal handlers. Original worker seeding precedes this observer and
is preserved. A fault before init may be captured only on the inherited
parent FD and is not automatically attributable without matching PID
evidence.

Outputs require eleven distinct supervisor-owned anonymous memfds:
parent and four worker event FDs, parent and four worker fault FDs, and one
status FD. The project interpreter only uses the inherited FDs; it does not
need os.memfd_create. Event output is capped at8192 records and2MiB per PID.
Faulthandler FDs require a separately reviewed outer collection/bounding
policy: this draft does not claim a Python audit hook bounds native
faulthandler writes.

Before imports, the carrier requires exact current owner/deadline and source
hash, admitted source pins, reviewed runtime/installed/asset pins, true
independent review receipts for every prerequisite, ordinary interpreter,
approved import paths and the two explicit native-write/uncertain-worker
policies. Missing proof blocks before Torch imports. The template supplies
none of those readiness permissions.

The Python audit guard denies persistent writes, model/train imports,
non-Unix networking and process signals. It allows only anonymous output FDs
and a private supervisor-owned transient IPC directory. TMPDIR is for owned
DataLoader/resource-sharing IPC, not a redirected import/model cache.
Required constructor caches and tokenizer assets must already exist; graph
fallback writes are denied, the graph cache is hashed immediately before its
original load, and all annotation graph keys are checked before workers
start. Python audit hooks do not cover all direct native filesystem calls;
native cache/import/sharing paths remain a material review prerequisite.

The Process.start wrapper captures each owned worker's target arguments,
done event, index queue and worker ID before calling the original start once.
It records PID/start as soon as start returns or raises. Exact installed
BaseProcess/Popen source must still show that no partial-launch child can
escape this capture. There is no claimed proof until that review exists.

Cleanup sets the iterator shutdown flag, sets only owned worker done events,
cancels index-queue join finalizers, sends cooperative None sentinels and
performs bounded joins. It does not call _shutdown_workers, terminate, kill,
normal Python exit or multiprocessing atexit. The carrier always uses
os._exit after status to bypass those implicit termination paths. A live or
unknown worker is reported uncertain with identity; it is never signalled or
retried. This does not guarantee a native-hung worker exits within a bound.
That unresolved policy is one reason this packet is blocked.

See MISSING_INPUTS.md for the exact evidence needed. A future freeze requires
fresh genuine peer review of the final source, supervisor, installed lifecycle
and fulfilled prerequisites. A clean short trace can establish observed real
input contracts only; it cannot establish historical root cause, repair,
operator clearance, efficacy, or authorize training restart.
