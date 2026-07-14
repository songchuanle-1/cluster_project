## Cluster 环境配置文档

**项目**: BQNet — 3D Referring Expression Segmentation  
**目标**: 基于 `model_base2_quard_bottleneck` 模型，使用 PyTorch 2.8 + CUDA 12.8，不依赖 PYTHONPATH hack

---

### 1. 硬件与基础环境

| 项 | 值 |
|---|---|
| GPU | 2× NVIDIA RTX 5090 (32.6 GB) |
| OS | Linux (CentOS 7) |
| Python | 3.10 |
| CUDA | 12.8 |
| PyTorch | 2.8.0 |

### 2. 创建 conda 环境

```bash
conda create -n cluster python=3.10
conda activate cluster
```

### 3. 安装 PyTorch

```bash
pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \
    --index-url https://download.pytorch.org/whl/cu128
```

### 4. 安装核心依赖

```bash
# 稀疏卷积
pip install spconv-cu126

# 图神经网络（⚠ 必须 1.1.3，2.x 与 PyTorch 2.8 不兼容）
pip install dgl==1.1.3

# torch_scatter（点云散射操作）
pip install torch_scatter

# torchdata（⚠ 必须 0.8.0，太高版本缺少 datapipes 模块）
pip install torchdata==0.8.0
```

### 5. 安装 Python 依赖

```bash
# 安装 requirements.txt（跳过冲突项）
pip install -r requirements.txt 2>&1 || true

# 补充安装
pip install easydict matplotlib h5py opencv-python open3d \
    plyfile scipy pypng open-clip-torch gorilla-core \
    transformers==4.31.0

# 场景图解析器 + 语言模型
pip install sng_parser spacy==3.7.5 pydantic==2.10.6
python -m spacy download en_core_web_sm
```

### 6. 编译项目 C++ 扩展

```bash
cd /data/songcl/3dres/Cluster_project2/Cluster

# 编译 pointgroup_ops
cd framework/lib/
pip install -e .
cd ../../

# 编译 pointnet2
cd pointnet2
python setup.py install
cd ..

# 以 editable 模式安装项目
pip install -e .

# 编译 ClusterAttention CUDA 扩展（对每个模型目录都要执行）
cd framework/model/Quard_model/model_base2_quard_bottleneck/ClusterAttention
python setup.py build_ext --inplace
cd ../../../../../
```

### 7. 修复兼容性问题

```bash
# 激活环境后执行
conda activate cluster

# sng_parser 缺少 audio.py 模块 → 创建 dummy
cat > $(python -c "import sng_parser; print(sng_parser.__path__[0])")/audio.py << 'PYEOF'
"""Dummy audio module for sng_parser - not needed for text-only usage."""
def parllel_transcode_opus(*args, **kwargs):
    raise NotImplementedError("Audio encoding not available")
def eval_audio_futures(*args, **kwargs):
    raise NotImplementedError("Audio encoding not available")
PYEOF
```

> **说明**: `sng_parser` 的 audio 子模块在 PyPI 发行版中缺失，训练只使用 text 功能，因此用 dummy 模块绕过。

### 8. 版本冲突总结

| 依赖 | 问题 | 解决 |
|---|---|---|
| `dgl 2.1.0` | 需要 graphbolt `.so` for PyTorch 2.8，不存在 | 降级到 `dgl==1.1.3` |
| `torchdata 0.11.0` | 移除了 `datapipes` 子模块 | 降级到 `torchdata==0.8.0` |
| `sng_parser` | 缺少 `audio.py` | 创建 dummy 模块 |
| `spacy 3.7.5` | 降级了 numpy 到 1.26（不影响训练） | 忽略警告 |

### 9. 数据准备

```bash
# 数据根目录
/home/songcl/data/data/

# 目录结构
├── roberta-base/          # 语言模型
├── sp_unet_backbone.pth   # 预训练 backbone
├── ScanRefer/             # ScanRefer 数据集标注
├── Multi3DRefer/          # Multi3DRefer 数据集标注
├── scannetv2/             # ScanNet v2 点云数据
├── clip_feat/             # CLIP 特征
└── scanrefer/             # ScanRefer 标注
```

### 10. 训练命令

```bash
conda activate cluster
cd /data/songcl/3dres/Cluster_project2/Cluster

# 模型通过 YAML 文件名自动索引（framework/__init__.py 的 resolve_network）
# YAML 文件名 → 模型模块：configs/Quard/model_base2_quard_bottleneck.yaml
#   → framework.model.Quard_model.model_base2_quard_bottleneck.Network

# 训练（GPU 1，跳过验证以快速测试）
python tools/train.py \
    configs/Quard/model_base2_quard_bottleneck.yaml \
    --skip_validate \
    --gpu_ids 1

# 使用 GPU 0
python tools/train.py \
    configs/Quard/model_base2_quard_bottleneck.yaml \
    --skip_validate \
    --gpu_ids 0
```

> **注意**: 使用 `--gpu_ids` 显式指定 GPU，避免和他人占用的卡冲突。`CUDA_VISIBLE_DEVICES` 和 `--gpu_ids` 不要混用。

### 11. 验证结果

| 指标 | 值 |
|---|---|
| 模型参数量 | ~153.5 M |
| 训练速度 | ~1.2 it/s (~0.8 s/batch) |
| 显存占用 | ~6 GB (batch_size=2) |
| 损失 | 正常下降，无 NaN |

### 12. 快速启动检查清单

```bash
# 1. 确认环境
conda activate cluster
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"

# 2. 确认模型可导入
python -c "
from framework import resolve_network
Network = resolve_network('configs/Quard/model_base2_quard_bottleneck.yaml')
print('Model OK')
"

# 3. 启动训练
python tools/train.py configs/Quard/model_base2_quard_bottleneck.yaml --skip_validate --gpu_ids 1
```

