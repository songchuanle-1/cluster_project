# M234 worker source audit

Scope: local static audit of the real clean detached checkout `D:/project/cluster_project/pipeline/isolated_versions/rvec_r1_558ef1ee`, admitted source `d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e`.

The accepted read-only resolver (`b8656342280f6d857f89c153c50a6e50c963a649ae51bfca4bcf85b6bc1f634c`) verified detached HEAD/clean status/exact nine source hashes and preserved main HEAD0747, real index,28 user files and r0 nine files. No Torch import, data/model execution, SSH, GPU work, configuration change or shared-ledger mutation occurred.

## Actual source path

- Native YAML lines16–20: train batch size2, four workers, persistent workers. Lines30–48 enable ScanRefer train augmentation and elastic transforms. Dataset factory `framework/dataset/__init__.py:22–36` selects custom collation, shuffle, drop-last and pin-memory. It does not explicitly set multiprocessing context, worker-init function or prefetch factor. Their effective runtime values were not captured.
- `tools/train.py:460–464` builds train/validation datasets and loaders. `train.py:103–109` obtains a batch and then calls the model in the parent process.
- `framework/dataset/scannetv2.py:178–195,352–378`: select a grouped scene/annotation input; locate `scannetv2/train/*_refer.pth`; deserialize via the compatibility torch loader; transform coordinates/features/labels; deserialize `clip_feat/<scan_id>.pth` and index selected superpoints.
- `scannetv2.py:202–257,295–324`: NumPy RNG, matrix multiplication, indexing/unique and SciPy ndimage convolution/RegularGridInterpolator are reachable native CPU boundaries in training augmentation.
- `scannetv2.py:333–347,441–442`: torch-scatter mean reductions produce instance/reference masks. Tensor casts, indexing and NumPy-to-Torch conversion also execute native CPU code.
- `scannetv2.py:109` constructs RobertaTokenizerFast from the local roberta-base assets. Its native tokenizer is called per annotation at627 and through char-to-token mapping at686, and during collation at492. Actual tokenizers version, start method and inherited thread state remain unknown.
- `scannetv2.py:455–511`: custom collation constructs long CPU coordinates and batch IDs, then calls `pointgroup_ops.voxelization_idx`. The actual Python route is `framework/lib/pointgroup_ops/pointgroup_ops.py:6,9–30` to `pointgroup_ops_ext.voxelize_idx`, bound by `src/pointgroup_ops_api.cpp:7`.
- `framework/lib/pointgroup_ops/src/voxelize/voxelize.cpp:11–30` uses tensor data pointers and a native voxel rulebook; line30 dereferences the first entry of the rulebook. This is a concrete data-dependent native boundary. It is not evidence that this operator failed: the failed worker's input shapes, stage and native instruction are unavailable. Normal collation creates the expected long tensor/batch columns.
- DGL and SciPy sparse are imported at dataset14–15 without direct calls in these worker methods. `sng_parser.parse` is in scene-graph cache construction (`111–143,781`), rather than the normal cached per-item path. Actual cache hit/miss metadata has not been audited.
- There is no direct OpenCV/cv2 import or call in this admitted dataset worker path. No evidence yet shows an OpenCV operation in the failed worker; a transitive library import would require installed-module/mapping evidence.
- PointNet2 FurthestPointSampling is imported/called in the parent model (`hier_postprocess.py:13,81`; `network.py:17`). The dataset/collate path does not call FPS. Library inheritance/loading and executing a particular native operator are different facts.

## What the traceback establishes

Authenticated terminal observation: `pipeline/diagnostic_bundles/tick_342a6a92/reconcile.actual.json`, SHA256 `a2c1b89d1d60bbd25175900d41984d374ea21fc2e486ae5e56229f11bdbe6bad`.

Its parent traceback goes through `hier_postprocess.py:87` (`cid[idx.long()] = k`), then installed `torch/utils/data/_utils/signal_handling.py:73`, where `handler` calls `_error_if_any_worker_fails`. The resulting RuntimeError explicitly identifies **worker3815203**, while the registered parent was **PID3813109**.

Thus the model indexing frame is the parent's interrupted notification locus, not a native fault backtrace from the worker. It does not establish that RVE, FPS or that indexing instruction caused the worker failure. The handler/function names in the installed traceback support asynchronous worker-failure reporting; the exact remote installed signal-handler registration, C++ child-status implementation and package version have not yet been copied into this local audit. Collect those source bytes to complete the SIGCHLD implementation chain rather than treating an upstream version as the installed artifact.

## Missing evidence and next safe step

- Worker native instruction/shared object/core or worker Python/native backtrace.
- Worker ID, in-flight scene/annotation indices and the failed load/augmentation/tokenization/collation stage. Four workers can prefetch: parent step4297 does not uniquely identify the failed sample.
- Relevant sample/feature file hashes; stage-specific array/tensor shape, dtype, device, contiguity and batch-ID bounds; actual worker RNG/augmentation state.
- Installed module origins, versions, binary build IDs/dependencies and multiprocessing/tokenizer thread settings.
- No OOM marker appears in the authenticated sampled traceback. That does not identify the segmentation-fault cause.

Next: read the installed `signal_handling.py`, `worker.py` and `fetch.py` as text; package METADATA; exact extension ELF headers/NEEDED/build IDs and hashes; existing permitted user-space crash metadata if available. This is CPU/static evidence collection. Do not import the dataset/model, unpickle data/checkpoints, repeat the passed two-step test or128-scene traversal, change worker/start-method/augmentation/YAML settings, or relaunch training.

Root cause remains **UNKNOWN**. No cause-specific fix is supported yet.
