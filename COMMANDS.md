# Cluster 项目远程操作命令手册

> Server-4: `192.168.1.137` | 2× RTX 5090 | Conda: `project_cluster` | 项目路径: `/home/songcl/project`

---

## 目录

- [快速参考](#快速参考)
- [1. sync.sh — 代码同步](#1-syncsh--代码同步)
- [2. remote_train.sh — 远程训练](#2-remote_trainsh--远程训练)
- [3. remote_status.sh — 状态查看](#3-remote_statussh--状态查看)
- [4. remote_log.sh — 日志查看](#4-remote_logsh--日志查看)
- [5. remote_kill.sh — 终止训练](#5-remote_killsh--终止训练)
- [6. remote_pull.sh — 拉回产物](#6-remote_pullsh--拉回产物)
- [Claude Code 对话速查](#claude-code-对话速查)

---

## 快速参考

```bash
cd /home/songcl/3dres/project/Cluster

bash scripts/sync.sh server-4                                          # 推送代码
bash scripts/remote_status.sh server-4                                 # 查看状态
bash scripts/remote_train.sh server-4 <config> <gpu_ids> [num_gpus]    # 启动训练
bash scripts/remote_log.sh server-4                                    # 查看日志
bash scripts/remote_log.sh server-4 0 -f                               # 实时跟踪日志
bash scripts/remote_kill.sh server-4                                   # 终止训练
bash scripts/remote_pull.sh server-4                                   # 拉回 checkpoints
```

---

## 1. sync.sh — 代码同步

通过 `git push` 将本地代码推送到远程，远程自动更新工作区。

```bash
bash scripts/sync.sh server-4
```

**内部流程：**

1. 检查远程是否存在 git 仓库，不存在则自动 `git init`
2. 远程有未提交修改时自动 `git stash`
3. `git push --force-with-lease` 推送到远程
4. 远程 `git reset --hard` 更新工作区
5. 恢复 git stash（如有）

**提示：** `remote_train.sh` 会自动调用此脚本，通常无需手动执行。

---

## 2. remote_train.sh — 远程训练

全自动完成 同步 → 环境检查 → 路径适配 → 后台启动训练。

```bash
# 单 GPU
bash scripts/remote_train.sh server-4 <config> <gpu_id>

# 多 GPU
bash scripts/remote_train.sh server-4 <config> <gpu_ids> <num_gpus>
```

**参数：**

| 参数 | 必填 | 说明 | 示例 |
|------|:--:|------|------|
| `server` | ✓ | 服务器名（SERVERS.yaml 中的 key） | `server-4` |
| `config` | ✓ | 训练配置 YAML（相对于项目根目录） | `configs/Quard/model_base1_quard2_c2f_enc_lite.yaml` |
| `gpu_ids` | | GPU 编号，逗号分隔 | `0` / `0,1` |
| `num_gpus` | | GPU 数量 | `1` / `2` |

**示例：**

```bash
# GPU 0 单卡训练
bash scripts/remote_train.sh server-4 configs/Quard/model_base1_quard2_c2f_enc_lite.yaml 0

# GPU 0,1 双卡训练
bash scripts/remote_train.sh server-4 configs/Quard/model_base1_quard2_c2f_enc_lite.yaml 0,1 2

# modelbase2 配置
bash scripts/remote_train.sh server-4 configs/modelbase2/model_base2.yaml 0
```

**内部流程：**

1. 检查本地未提交修改 → 自动 commit
2. 调用 `sync.sh` 推送代码
3. SSH 检查远程 conda 环境 / GPU / 数据集
4. **路径适配**：将 YAML 中的 `work_dir` 替换为远程路径
5. `nohup` 后台启动训练，记录 PID

**路径映射（自动处理）：**

| 配置项 | 本地路径 | 远程路径 |
|--------|----------|----------|
| data_root | `/home/songcl/data/data/` | `/home/songcl/data/data/` *(无需替换)* |
| work_dir | `/data/songcl/3dres/Cluster_project2/Cluster_checkpoints` | `/data/songcl/Cluster_project/Cluster_checkpoints` |

---

## 3. remote_status.sh — 状态查看

查看远程服务器的 GPU 占用、训练进程、最新日志。

```bash
bash scripts/remote_status.sh server-4
```

**输出内容：**

- **GPU 状态**：`nvidia-smi` 查询温度/利用率/显存
- **训练进程**：`ps aux | grep train.py` 列出运行中的训练
- **PID 文件**：检查记录的进程是否仍在运行
- **最新日志**：最近 30 行训练日志
- **磁盘使用**：`/data` 分区剩余空间
- **Checkpoints**：最近的 checkpoint 目录

---

## 4. remote_log.sh — 日志查看

查看远程训练日志。

```bash
# 查看最后 50 行
bash scripts/remote_log.sh server-4

# 查看最后 N 行
bash scripts/remote_log.sh server-4 100

# 实时跟踪日志 (tail -f)
bash scripts/remote_log.sh server-4 0 -f
```

> 脚本会自动找到最新的 `logs/train_*.log` 文件。

---

## 5. remote_kill.sh — 终止训练

终止远程服务器上的训练进程。

```bash
bash scripts/remote_kill.sh server-4
```

**终止策略：**

1. 优先通过 PID 文件精确终止（先 SIGTERM，2 秒后 SIGKILL）
2. 回退：终止所有本项目目录下的 `train.py` / `test.py` 进程
3. **不会影响其他项目**的训练进程

---

## 6. remote_pull.sh — 拉回产物

通过 `rsync` 从远程拉取 checkpoints 到本地。

```bash
# 拉取默认 work_dir
bash scripts/remote_pull.sh server-4

# 指定远程路径
bash scripts/remote_pull.sh server-4 /data/songcl/Cluster_project/Cluster_checkpoints
```

**本地存放位置：** `Cluster/Checkpoints/server_4/`

---

## 环境信息

### Server-4 (192.168.1.137)

| 项目 | 值 |
|------|-----|
| Hostname | `dl04-MS-7E06` |
| GPU | 2× NVIDIA GeForce RTX 5090 (32 GB each) |
| Conda | `/home/dl04/anaconda3/etc/profile.d/conda.sh` |
| Conda Env | `project_cluster` (Python 3.10.20, PyTorch 2.8.0+cu128) |
| 项目路径 | `/home/songcl/project/` |
| 数据路径 | `/home/songcl/data/data/` |
| Checkpoints | `/data/songcl/Cluster_project/Cluster_checkpoints/` |
| 存储 | `/data` 7.3T (可用 3.3T) |

### 可用的训练配置

**Quard 系列** (`configs/Quard/`)：36 个配置
- `model_base1_quard2_c2f_enc_lite*.yaml` — 轻量级粗到细编码（多位置编码/路由变体）
- `model_base1_gbcr_*.yaml` — 基于图的跨关系变体
- `model_base1_hca_*.yaml` — 层次化跨注意力
- `model_base1_topk_*.yaml` — TopK 粗到细

**ModelBase2 系列** (`configs/modelbase2/`)：30 个配置
- `model_base1_cluster_*.yaml` — 聚类注意力变体（fixed/hier/light/c2f）
- `model_base2_quard*.yaml` — Quad 变体

---

## Claude Code 对话速查

在 Claude Code 对话中直接说：

| 你说的话 | 执行的操作 |
|---------|-----------|
| "查看服务器状态" | `bash scripts/remote_status.sh server-4` |
| "在 server-4 上跑 model_base2.yaml，GPU 0" | `bash scripts/remote_train.sh server-4 configs/modelbase2/model_base2.yaml 0` |
| "看看训练日志" | `bash scripts/remote_log.sh server-4` |
| "实时跟踪日志" | `bash scripts/remote_log.sh server-4 0 -f` |
| "停掉训练" | `bash scripts/remote_kill.sh server-4` |
| "推送代码到远程" | `bash scripts/sync.sh server-4` |
| "把 checkpoints 拉回来" | `bash scripts/remote_pull.sh server-4` |
