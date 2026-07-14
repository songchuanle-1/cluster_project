# Copilot Instructions for this Workspace

## Big Picture
- **Domain:** 3D Referring Expression Segmentation (3D-RES) and 3D Grounded RES (3D-GRES), plus an embedded DEST3D detection module.
- **Top-level entrypoints:** training and inference are driven via [tools/train.py](tools/train.py) with YAML configs under [configs/](configs/).
- **Model families:** `BQNet_model`, `Agent_model`, `mamba_model`, `Quard_model` under [model/](model/). Many submodules are configured via YAMLs in [configs/](configs/) and orchestrated by the `framework` package.
- **Custom ops:** CUDA/C++ extensions in [framework/lib/](framework/lib) and [pointnet2/](pointnet2/) are required; build them before running.
- **Datasets:** Primarily ScanNet v2 and ScanRefer; preparation scripts referenced in [README.md](README.md).

## Developer Workflow
- **Environment setup:** Follow [README.md](README.md) for Python, PyTorch, CUDA, `spconv`, `torch_scatter`, spaCy model, and `pytorch3d`.
- **Build custom libs:**
  - Run `python setup.py develop` at repo root, then in [framework/lib/](framework/lib).
  - Build PointNet++: `cd pointnet2 && python setup.py install --user`.
- **Train:**
  - 3D-GRES: `python tools/train.py configs/BQNet_gres.yaml --gpu_id 0`
  - 3D-RES: `python tools/train.py configs/BQNet_res.yaml --gpu_id 0`
- **Inference:** Provide `--checkpoint` to `tools/train.py` with the same config.
- **DEST3D tests:** See [framework/DEST3D/test_issm.py](framework/DEST3D/test_issm.py); Triton kernels JIT on first run.

## Project Conventions
- **Configs-first:** All experiments are driven by YAMLs in [configs/](configs/). When adding features, expose knobs in the appropriate YAML and read them in the `framework` model setup.
- **Scene/query points:** Many modules operate on “query points” and “scene points” with masks and attention. Keep tensor shapes explicit; pass masks alongside features.
- **Paths:** Data and pretrained checkpoints are referenced by relative paths in configs; avoid hardcoding absolute paths in code.
- **Logging/checkpoints:** Outputs are under [work_dir/](work_dir/) or as configured. Use existing `utils/logger.py` and `utils/checkpoint.py`.

## Key Files and Patterns
- **Training loop:** [tools/train.py](tools/train.py) reads a YAML, initializes dataset from [framework/dataset/](framework/dataset/), builds model from [model/](model/) via `framework` utilities, and runs epochs.
- **Datasets:** ScanNet v2 loader in [framework/dataset/scannetv2.py](framework/dataset/scannetv2.py). Respect its expected directory layout and precomputed features (see [README.md](README.md)).
- **Utilities:**
  - Checkpointing: [utils/checkpoint.py](utils/checkpoint.py)
  - Distributed: [utils/dist.py](utils/dist.py)
  - Metrics/meters: [utils/meters.py](utils/meters.py)
  - Mask encoding/restoration: [utils/mask_encoder.py](utils/mask_encoder.py), [tools/test_mask_restore.py](tools/test_mask_restore.py)
- **Custom CUDA:** PointGroup ops in [framework/lib/pointgroup_ops/](framework/lib/pointgroup_ops/) and PointNet++ under [pointnet2/](pointnet2/). Kernel code like `score_computation_kernal.cu` exists under model modules; ensure proper compilation flags in setup scripts.
- **DEST3D module:** Lives in [framework/DEST3D/](framework/DEST3D/). Use [framework/DEST3D/models/](framework/DEST3D/models/) and [framework/DEST3D/utils/](framework/DEST3D/utils/). See [framework/DEST3D/README.md](framework/DEST3D/README.md) for ISSM design and runtime notes.

## Integration Notes
- **External libs:** `spconv`, `torch_scatter`, `pytorch3d`, and `spaCy` with `en_core_web_sm` are required. Install exact versions as in [README.md](README.md).
- **Backbones/pretrained:** SPFormer backbone should be placed under `backbones/` as described in [README.md](README.md).
- **Configs by variant:** Additional model variants exist under [configs/mamba/](configs/mamba/) and [configs/Quard/](configs/Quard/). Keep consistency with their expected module paths under [model/](model/).

## How to Contribute Productively
- **Add a new module:**
  - Place code under an existing family in [model/](model/) and wire it through `framework` factory/init paths.
  - Add YAML options under the relevant config (e.g., [configs/Agent/model_base.yaml](configs/Agent/model_base.yaml)) and read them in the constructor.
- **Extend dataset features:** Modify [framework/dataset/scannetv2.py](framework/dataset/scannetv2.py) and document preprocessing in [README.md](README.md). Keep feature token dimensions consistent with CLIP projections.
- **Debug build issues:** Re-run setup steps, verify `spconv`/`torch_scatter` CUDA versions match `torch`, and ensure `CONDA_PREFIX/include` is discoverable when building C++/CUDA.

## Examples
- Train BQNet for 3D-RES with a custom GPU: `python tools/train.py configs/BQNet_res.yaml --gpu_id 1`
- Resume from checkpoint: `python tools/train.py configs/BQNet_res.yaml --checkpoint work_dir/sceneXXXX/best_res.pth --gpu_id 0`
- Test ISSM module alone: `python framework/DEST3D/test_issm.py`

If any part of the workflows or file references is unclear, tell me which tasks you want to run (train, infer, or extend) and I’ll refine these instructions accordingly.