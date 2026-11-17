# cluster_project 迁移与接班说明

整理日期：2026-11-17（Asia/Shanghai）。本文是源码、历史实验和运行边界的交接，**没有执行新机器迁移、环境重建或训练**。最后一份完整研究 tick 为 `c1fe217800894083b65baac45f79aa83`，实际观测发生在 **2026-11-14**；不能把其显存、进程或锁状态当作 11 月 17 日的实时状态。本次另于 11 月 17 日对源机身份、HEAD 和四份 YAML 做了只读导出，范围见 `server4_overrides/summary.actual.json`。

本文中的 `Cluster/…`、`pipeline/…`、`scripts/…` 均为**源项目相对路径**，用于查找原始证据；交接包内的实际位置以仓库根目录的源码映射和文件清单为准。命令中的 `M236_CODE_ROOT`、`MIGRATION_DATA_ROOT`、`CFG`、`CKPT` 是接班人按目标机器填写的路径变量，不是已安装位置。原始机器绝对路径仅作资产定位，不应原样执行。

交接仓库采用训练代码在根目录的布局：主代码以集成541为基准；原项目根外支持材料映射到 `project_support/{pipeline,scripts,configs,framework,docs,Checkpoints}/`，仅保留配置、记录和源码；本文及资产清单位于 `docs/migration/`；实验统计位于 `experiments/`；canonical 编排源码快照归档到 `tooling/songcl_research_pipeline/`。数据、训练权重和原始训练日志不在此 Git 源码交付内。本地 working 和历史独立版本通过归档分支/提交保存。源项目相对证据引用需按这张映射及对应版本定位，不能误把本地 main0747当作集成541。

## 首要下一步

接班后优先推进 **M236-CSO 的第一次正式训练**。它已完成真实原生 TRAIN 两步、资源检查、独立复核、技术准入和代码集成；**尚无正式训练、完整验证、精度收益或新颖性结论**。应先确定并获得目标机器、GPU 和允许操作范围，核验源码与资产，再建立属于新执行者的新租约与生产入口。当前没有指定或授权迁移目标，本文不授权启动。

2026-11-14 的最后一次启动在生产前置检查中被 `memory.free=10848 MiB < 20000 MiB` 拒绝。没有写 dispatch intent，没有消费新生产 marker，也没有启动训练。这是资源拒绝，不能改写成模型测试失败。有效的原生/资源结果可保留复用；目标机器的环境兼容性和资源条件仍须实际验证。

技术准入依据：`pipeline/admissions/M236-CSO.json`，SHA-256：

```text
07b56b16948f7f7e1a4a0682fd6abc81d3eda586e05ae4424f89d16005d8be09
```

最近状态及详情见 `pipeline/codex_memory.md`、`pipeline/reports/summary_c1fe217800894083b65baac45f79aa83.md`、`pipeline/diagnostic_bundles/tick_c1fe2178/`。完整实验统计见本交接包的实验统计文档；本文只列影响迁移和恢复的状态。

## 必须保留的版本关系

| 角色 | 原提交 | 含义 |
|---|---|---|
| 本地 main | `0747f6acec1c61018ec99acf2efa5329c9b3523c` | 本地研究主树；最近 tick 保留其 37 项 dirty，不能当作最新生产树 |
| M236 原始实现 | `af45707d7b6089f764843337c5f88af285383f88` | 实际原生/资源执行使用的候选源码，父提交 `d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e` |
| 当时底层 runtime | `b1e639b3ceb14bb5c65d9f81a084d41c834b951c` | 原生测量时的运行树；候选通过私有加载路径执行 |
| M236 集成版本 | `5413102c57b526035f3920b5e7a81f3b58ad764d` | 父提交为上述 `b1e639…`；已与原始实现的八个模型文件和一个 YAML 逐字节关联 |
| 最后观测到的远端 runtime | `5413102c57b526035f3920b5e7a81f3b58ad764d` | 2026-11-14 已实际 safe-sync；不是新机部署证明 |

九个文件的 SHA-256 见 `migration_assets.json` 的 `m236_exact_files`。版本关联证明为：

```text
pipeline/diagnostic_bundles/tick_c1fe2178/cso_version_binding/version_bound_evidence.json
SHA256 4c44c69c847fb597cf275e5eeb115d2efe3320c3e0498d0214878127a95907a9
```

这份关联只证明相应九个文件相同，**不表示实际测量时 checkout 了 5413102，也不证明两个整棵源码树相同**。原始执行 source、owner、失败记录及原 NULL 字段保留。不要补签旧记录，或把关联证明改成一次新执行。

源项目中的独立树为：

```text
pipeline/isolated_versions/m236_cso_1aa2d994/
pipeline/isolated_versions/m236_cso_integrated_7caf419d/
```

其他历史独立源码、主树 dirty 和 staged/unstaged 状态必须通过归档清单分别保留。仅复制本地 `Cluster/` 会漏掉 M236 和部分历史版本。若交接包采用导出的源码目录，不能把其目录位置或新归档提交误当作原始实验提交。

2026-11-17 源机只读导出再次确认 hostname `dl04-MS-7E06`、uid1001 和 HEAD541。Git status 仅四份 NDE / NSD / RVEC / SINC YAML 修改；保存了工作树原字节、对应 HEAD blob 和完整 patch。YAML 语义解析核验表明唯一字段变化为 `work_dir` 从 `/home/songcl/3dres/project/cluster_project/Checkpoints` 适配为 `/data/songcl/Project/Cluster_project/Cluster_checkpoints`，另有序列/布尔/空行等文本格式差异，不能只存四行路径替换而漏掉原字节。详情在 `server4_overrides/`；这四份历史配置适配不改写 CSO 原生配置的哈希。

原仓库另有嵌套源码与链接类型边界：`framework/DEST3D` 的历史 gitlink 为 `9512afa38fd58114555c5e42a86056c20135e522`，但源目录没有 `.git` 或 `.gitmodules`，**现存 payload 是否对应该提交身份仍 UNKNOWN**。导出修复方案是在当前 main 将现存的49个代码、LICENSE和README文件展平为普通文件，7份 figures 非代码资产排除；`provenance/nested_sources.json` 逐文件记录 SHA 与原 gitlink，历史 archive 的指针保持原样。这是额外 payload 归档，不得声称已恢复或核验该 submodule 提交。

三个历史模型目录别名 cosine / poly50 / step 原为 Git mode120000链接，目标均为同级 `model_base1_quard2_c2f_enc_lite_posA_l1`。清单与便携工具需区分 `kind`、`git_mode`、`link_target`，不能把 Windows 文本占位当成 Linux 普通文件。上述修复的最终文件类型与工具验收以根目录来源清单及后续验收记录为准；本交接没有运行 Linux clone/还原工具，不能提前宣称 Linux 执行通过。问题发现与待验证状态见 `PATH_REVIEW.md`。

## M236 已有证据及边界

两自然 TRAIN loss 为 `9.573954582214355`、`13.908418655395508`；实际原生 `tools.train.train(...)` 完成两次 optimizer step，common 841 参数初始化完全相等，九个 CSO 核心张量均有有限、非零梯度并逐步更新；HCG、inst、ILA 和 mask 路径有实际观测。没有保存正式训练 checkpoint。旧 CPU21 结果不能替代这些原生执行，也没有必要重放它。

| 指标 | 已有观测 |
|---|---|
| 参数总数 | 156,999,866 |
| 同口径 FLOPs | 9.645764684 G |
| 输入 | 固定 `scene0011_00` / ann 0；bs=1、lang_num_max=1 |
| 输入 SHA-256 | `526079d667505fce5957a69797f328cf23fe42c34e1e9ddeca5a5deedbbccf90` |
| 计时 | warmup 20、repeat 100；median 35.407514544 ms，P90 36.583361775 ms |
| 峰值 allocated / reserved | 934,827,520 / 1,189,085,184 bytes |
| 测量范围 | 允许共享、可能受竞争影响；不是独占性能声明 |

资源结果来自独立资源进程，没有 optimizer/scheduler step；完整 optimizer 训练峰值仍未知。带 hook 的两步 smoke 峰值不是纯训练峰值。历史 M95 测量并非同时测量，不能据此声称结构加速；no-cluster 相对增量尚未测量。验证精度未用于本次选择。

原始实际执行、派生关联和独立复核须一起保留：

```text
pipeline/diagnostic_bundles/tick_c1fe2178/cso_native_execution/run_smoke_candidate_actual.json
pipeline/diagnostic_bundles/tick_c1fe2178/cso_native_execution/run_resources_candidate_actual.json
pipeline/diagnostic_bundles/tick_c1fe2178/cso_version_binding/native_smoke.version_bound.json
pipeline/diagnostic_bundles/tick_c1fe2178/cso_version_binding/resources.version_bound.summary.json
pipeline/diagnostic_bundles/tick_c1fe2178/peer_review/
```

## 调度、机器与一次性入口

最后保留的授权配置是 server-4 物理 GPU0，UUID `GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c`，主机身份 `dl04-MS-7E06`，固定地址 `192.168.1.115`。这只是源机器身份和原授权范围，不能继承成任意目标机器的权限。连接 server-4 前先核验身份，不能使用其旧 IP；SSH 优先使用密钥，不假定账户具备 sudo/root。

原有边界为：本项目每卡最多一项任务；启动直接读取实际 `memory.free >= 20000 MiB`；保留 training / diagnostic / exclusive 三类协作锁。允许与外部任务共享，不要求空卡、零 context 或低利用率；外部任务不得驱逐、发信号或重启。原阈值不得为启动而降低。GPU1 和其他机器不在最新可派发范围。

`Pipeline-cluster_project` 在最近记忆中为 Disabled；正式控制器位于项目外的 canonical skill。归档旧调度文件或脚本不等于启用调度，也不授权建立新自动化。

**旧 lease、owner、stage、intent、shim 均不可重放。** 最近 tick 的 owner 有效窗口为 `2026-11-14 09:52:47.538159–10:52:47.538159 +08:00`，现已过期。最近安装的 `cso_path_prod_c1fe2178_v2` 虽未消费，也绑定旧 owner；不得把“marker 不存在”当作现在可执行。主 `SERVERS.yaml` 的 `conda_source` 仍指向旧的、已消费的 `rvec_path_prod_21ebd237` 入口，不能直接 source 后启动。

后续执行需复用已审 v2 逻辑，另存新 scoped server-copy/source resolver、owner/stage/lease、源码/运行树/UUID/producer 绑定并复核。v1 collect 因文本模式 CRLF 归一化而失败，v2 使用 raw git blob 修正；旧失败和 FROZEN 原样保留。已同步到 5413102 的源机无需为了重放流程再同步 b1→541。

## 数据与预训练资产

源码上传不能代替数据、预训练权重和关键 checkpoint 的迁移。可机读清单为 `migration_assets.json`，包含每项原路径、SHA-256、字节数、证据来源和观测时间。资产文件没有因这份清单而被复制或重新哈希。

源数据逻辑根目录为 `/home/songcl/data/data/`；部分路径实际解析到 `/data/songcl/3dres/data/`。迁移时保留相对结构和 Linux 文件名大小写；`scanrefer/` 与历史文档中的 `ScanRefer/` 不能随意互换。

| 资产 | 迁移要求 |
|---|---|
| `scanrefer/ScanRefer_{train,val}_new.json` | 固定训练/验证标注，不能重新下载另一版本替换 |
| `scanrefer/scene_graphs_new_{train,val}.json` | 保留原解析结果；缺失会触发数据集构造器重新解析并写文件 |
| `scannetv2/train/*.pth`、`scannetv2/val/*.pth` | 已预处理的点云、超点和标签；保留清单逐文件哈希 |
| `scannetv2-labels.combined.tsv` | 语义标签映射 |
| `roberta-base/` | 本地语言模型及 tokenizer；数据集 tokenizer 使用 `local_files_only=True` |
| `clip_feat/` | 保留已有特征供历史复现；是否进入当前模型以实际代码路径为准 |
| `sp_unet_backbone.pth` | 正式冷启动的 backbone 预训练权重；不是 M95 checkpoint |
| Multi3DRefer、额外数据集 | 不属于当前 ScanRefer 首筛授权；原配置存在不代表允许新增训练 |

历史全量数据清单 `pipeline/diagnostic_bundles/m201_server4_8eea3f8d47eb4034a4ea148c066192f6/data_target.json` 于 **2026-10-14**记录 2,226 个文件、17,894,540,419 bytes：ScanNet train 1,201、val 312、CLIP 703，其余为标注、词表和语言模型。它是历史基准，未证明今日远端全部文件未变化；11 月 14 日新检查只覆盖其中明确列出的关键资产。完整逐项条目已收入机读清单，不能把一份清单的文件哈希当作整个数据目录的哈希。

关键哈希：

```text
ScanRefer_train_new.json
018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d
ScanRefer_val_new.json
4455b8857ade37aaafa32581537a961a77bcc756b22d8143ed4021bc88b7931f
sp_unet_backbone.pth
a6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f
roberta-base/pytorch_model.bin
278b7a95739c4392fae9b818bb5343dde20be1b89318f37a6d939e1e1b9e461b
```

## 必须保留的 checkpoint 与恢复状态

关键恢复/复现权重清单见 `migration_assets.json` 的 `checkpoints`。这里的 checksum 来自已存实际证据，并非本次读取远端大文件所得。原目录必须保留到目标校验完成；不要用日志里“最后看到的 epoch”推测 checkpoint 已保存。

| 项目 | 已保存状态与接班限制 |
|---|---|
| M95 frozen reference | 源远端项目下 `pipeline/hds_server4_3c22e34d/frozen_m95.pth`，936,269,892 bytes，SHA `fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`；用于对照/血缘，不是 M236 冷启动权重；其与历史 champion 权重的身份关系尚未核实 |
| M206-CGCA | 人工暂停；冻结 `last.pth` 为完整 epoch24，best `0.4952535927295685`，no-improve 7；SHA `e9b42b2632762dae5ca49d80b3272889809b1ffe3ec30dd377690af8cb2e8e9d` |
| M227-LFT | 人工暂停；`last.pth` 完整 epoch22，best `0.4977978467941284`，no-improve 5；SHA `38033f488e7b0b2d6fba7bc3da9ff757d2f22c939ecd3c829f3d84aca5fd6199`；best 权重也单独保留 |
| WFC / NEC / MIC | 已完整完成各自最后一轮验证并早停，分别到 epoch30 / 23 / 26；不自动重启。早停发生在保存块之前，NEC 的 last 保存到22、MIC到25，不与终态验证 epoch 混淆 |
| M235-SINC | partial epoch2 / 1870 of 4686；仅 saved complete epoch1 的 metadata 可用；原 Adam `list.grad` 故障根因 UNKNOWN，未修复 |
| M232-NSD | partial epoch1 / 1961 of 4686；完整验证0、无 `.pth`，不能恢复“epoch1已完成” |
| M230-HVD / M231-PSC | 分别 partial epoch5 / 1449、partial epoch2 / 984；完整保存仅4 / 1；不把失败轮次计成完整结果 |

M206、M227 的队列字段虽然是 `waiting`，同时明确 `dispatch_phase=user_paused`、`resume_authorized=false`；它们不是真正就绪任务。不得因迁移、空槽或新机器可用而恢复、冷启动、替换或借用其他实验授权。BFC 也有独立恢复人工授权 hold，不借用其他候选许可。

原生恢复使用 `gorilla.resume`，应保留 **model、optimizer、scheduler、meta.epoch、meta.best_miou、meta.epochs_no_improve**，并核对实际加载和开始 epoch。只有 model state 的权重加载不是完整 resume；不能清零 patience、把 partial epoch 当作已保存进度，或自动换到另一份初始化/数据/模型源码。M206 的已存 CPU 检查确认这些状态存在；M227 的 CPU 检查也确认完整 model/optimizer/scheduler。新机仍需在副本上验证文件哈希与状态。

旧短测、CPU import 修正或两步 PASS 不能宣称已修复历史长期 Adam/张量故障；它们目前的根因保持未知，也不能据此把科学机制记成已证伪。

## 环境重建与扩展验证

已有实际环境绑定记录 Python 3.10、PyTorch `2.8.0+cu128`、`CUDA_HOME=/usr/local/cuda-12.8`，但不是完整可复现 lockfile。`Cluster/requirements.txt` 中有历史 `dgl-cu111==0.6.1`；`Cluster/docs/cluster_env_setup.md` 又记录 dgl1.1.3、torchdata0.8.0、spconv-cu126 等兼容经验。两者不能不加核验地拼成“已验证新机环境”，也不要沿用旧文档的 `pip install ... || true` 忽略失败。

目标机器在获得执行授权后按以下顺序建立新证据：

1. 记录 OS、编译器、驱动、GPU型号/UUID和实际 compute capability；核对 `torch.__version__`、`torch.version.cuda`、`torch.cuda.get_device_capability()`、`torch.cuda.get_arch_list()`、`nvcc --version` 与 C++ ABI。**不能从旧技能示例或旧环境代码推断新 GPU 架构，不套用“RTX5090=9.0”。**
2. 建立干净 Python 环境，安装与目标驱动/工具链兼容的 torch、spconv、torch_scatter、DGL、gorilla-core、transformers4.31.0、fvcore 及数据集实际导入依赖；保存成功安装的精确版本/来源和 `pip check`。历史版本只是重建起点。额外 mamba/其他变体依赖按其实际导入路径验证。
3. 从当前源码重编译 `framework/lib/setup.py` 的 `pointgroup_ops.pointgroup_ops_ext` 和 `pointnet2/setup.py` 的 `pointnet2._ext`。核对编译器、CUDA ABI、架构覆盖和实际 `.so` 导入路径，不能把源机 `.so` 原样当作新机可运行保证。`pointgroup_ops` 的 setup 依赖 `torch.cuda.is_available()`，无 CUDA 环境构建并不等于扩展可用。
4. M236 使用 `pointgroup_ops`、`pointnet2`、spconv、torch_scatter 及 PyTorch 结构；它没有新增独立 CSO CUDA 扩展。历史 `ClusterAttention` 扩展按实际模型导入需要单独编译；不必因为归档了所有变体就盲目编译每个旧目录。
5. 实际导入并记录 `pointnet2._ext.__file__`、`pointgroup_ops` 和其他关键库路径，然后运行最小合法 tensor 调用/反向及固定 TRAIN 数据加载；最后完成目标环境的原生两步和资源兼容性检查。

源机曾出现 **激活相同 conda 环境但 isolated arm 导入了不兼容 conda-site egg、普通 native arm 导入 user-site 的兼容 pointnet2** 的差异。最近实际兼容扩展位置为：

```text
/home/songcl/.local/lib/python3.10/site-packages/pointnet2/_ext.cpython-310-x86_64-linux-gnu.so
SHA256 ef0daa5ccf7fe471a5d73528762f209ba6d2dd89a6c3b50c6371eb9e0edebcfe
```

此哈希用于源机溯源，不能代替新机编译/执行验证。不要靠 `PYTHONPATH`、隐藏 shim 或复制 user-site 来掩盖新环境导入冲突。完整环境相关源证据为 `pipeline/diagnostic_bundles/tick_c1fe2178/cso_native_bound/environment_binding.json`。

## 保持原生协议

当前 M236 唯一 YAML basename 与模型包名均为：

```text
model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso
```

配置：`configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml`；原文件 SHA `908bc08a4d78dcc2723588abb7a6e3adeb169a79e788ce74ee5afbd78c991081`。

| 固定项 | 原生值 |
|---|---|
| 数据/随机性 | ScanRefer train/val；train/test seed1999；不新增数据或多 seed 扫描 |
| Schedule | epochs50、interval1；PolyLR max_iters70 / power4.0 / constant_ending0.0；已知50/70不一致暂保持 |
| 训练 loader | bs2、workers4、lang_num_max4、原生 augmentation/elastic |
| 验证 loader | bs1、workers2、lang_num_max32；资源 profiling 另外固定 lang1 |
| Optimizer | AdamW lr0.0001、weight_decay0.0005；text_encoder multiplier0.001，input_conv/unet/output_layer0.01，dec1.0 |
| 梯度 | grad_clip0.1；原冻结 text_encoder |
| 原 loss | focal；loss_weight `[1,1,0.5,5,0.1,0.1,0.1,1]`；cost_weight `[1,1,0.1]`；match_last_layer / layer_differ_weight=True |
| 资源预算 | 统一口径总 FLOPs≤10.0G；报告相对 baseline/champion 增量；峰值显存增加15%需至少+0.003 mIoU才保留 |
| 效率协议 | 固定输入、bs1、lang1、warmup20、repeat100、median/P90；同时报告测量范围和竞争状态 |

不要为迁移单独改变 seed、epoch、max_iters、原 loss/optimizer 或模型值。只能在单独保存并哈希的新 YAML 中适配 `work_dir`、数据根路径和预训练路径，并保留原 YAML 与明确 diff；包名/basename保持一致。Phase1 不允许把超参扫描、纯数值修改、改名副本计作新机制；目标、bans、历史失败和人工暂停不因搬机器而失效。

`tools/train.py` 内置的快速 profile 是 warmup3/repeat10，且使用第一条验证样本；它不能代替上面的正式 warm20/repeat100 口径，更不能单边换口径来否决新候选。

## CLI 与已知入口问题

以下是源代码参数说明和未来操作模板，本次没有执行。所有训练、验证、GPU import/编译均须在目标范围明确并完成上述检查后进行；已有前台闭环项目继续遵循新收据、safe-sync、锁和启动后进度证明。

```bash
cd "$M236_CODE_ROOT"
CFG="configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml"

# 原生训练参数；实际调用由新 scoped 入口执行。
python -B tools/train.py "$CFG" --gpu_ids 0 --num_gpus 1 --patience 10

# 仅在该实验获得恢复授权且完整状态验证后，使用其自己的 CKPT。
python -B tools/train.py "$CFG" --resume "$CKPT" --gpu_ids 0 --num_gpus 1 --patience 10

# 沿用训练端模型解析的验证入口；写入新时间戳 work_dir。
python -B tools/train.py "$CFG" --resume "$CKPT" --skip_training --gpu_ids 0 --num_gpus 1

# 独立 test 脚本的参数形状；见下述未解决问题，不能直接当作已验证评测命令。
python -B tools/test.py "$CFG" --checkpoint "$CKPT" --gpu_ids 0 --num_gpus 1 --out "$TEST_OUTPUT"
```

源码静态核验发现：集成541的 `tools/test.py` 使用 `from framework import Network`，而当前 `framework/__init__.py` 提供 `resolve_network(config)`，并未导出 `Network`。独立 test 入口须先在单独修复中改用与训练一致的模型解析，并对指定 basename 做实际验证；不能宣称该命令已可用。训练解析器还会在 ImportError/AttributeError 时退回默认模型，因此接班必须检查解析类的 `__module__` 确实包含目标 CSO 包，避免“能导入”却跑了默认模型。

`--skip_training` 路径恢复完整 checkpoint 后执行一次 native validation，但默认保存逻辑可能继续在新时间戳输出目录写 checkpoint；结果 epoch标签来自 `saved_epoch+1`，不能将其当作训练增加一轮。`--save_ckpt`、`--par_and_flops` 是 `type=bool` 参数，不能假定传字符串 `False` 会关闭功能。训练脚本有 PyTorch2.6+ checkpoint兼容加载补丁，独立 test 未自动继承这一补丁；新机应核验原 `.pth` 的实际读取兼容性。旧 README 中的 `--checkpoint` 训练示例及 `--gpu_id` 拼写不是当前训练 CLI。

## 迁移验收与继续研究

1. 确定目标机器、GPU、允许的读写/编译/训练范围和数据位置；未指定时停止于归档与文档交付。
2. 对照源码包清单检查文件数和 SHA，核对 main、原始af457、集成541及历史独立源码的映射；九个候选文件逐项匹配。不要重置源主树或覆盖原运行目录。
3. 在源资产稳定时生成新的迁移前文件清单；与 `migration_assets.json` 的历史基准比较并解释差异。复制后在目标逐文件比较 `relative_path + bytes + sha256`，保存缺失、多余和不匹配清单。检查 symlink 实际目标、大小写、train/val分界和 tokenizer完整性；不重新生成 scene graph 替代原资产。
4. 在目标独立输出目录重建并记录环境、扩展导入与实际计算兼容性；核对固定数据样本。对于 checkpoint，用可信资产副本做 CPU读取，确认完整状态与 metadata，记录当前 CUDA是否初始化。
5. 依原授权约束完成本机兼容性 native TRAIN2 与统一资源记录；旧模型证据和新环境证据分别留存，不改写旧 owner。验证测试入口问题并保存独立修复记录。
6. 仅在目标启动明确获授权、资源满足、收据和新 owner绑定通过后启动 M236。通过 PID、实际进程源码/配置与至少两次递增步数确认启动；stdout一句“成功”不够。之后按完整训练/验证台账报告精度，保持效力、新颖性和机制对照结论的未知项。

当前研究主线是不同层级信息交互**真实更新参与 mask 的点云/超点 inst_feats**；监督候选仅保留辅助证据。历史 champion ID 仍是 M95-CTF-HCG-CSORT，历史账本值 `0.5020`；frozen M95 epoch16 full-VAL 的独立精确参考为 `0.5024607181549072`。原 M202 分析明确说两份权重身份尚未核实，因此分列保留，不能用精确 frozen 参考回写 champion ledger。历史 baseline `0.4894`，统计文档另列精确参考 `0.4894491136074066`；目标 `0.5100`。这些口径与 `experiments/EXPERIMENT_SUMMARY.md` 一致。M236 技术准入不代表超越 champion。完整统计按实验统计文档的证据分级解释，不把 partial/crashed、技术检查和完整验证混算。

## 项目外依赖与原始来源

正式编排 skill 的源位置为 `C:/Users/chuanle song/.codex/skills/songcl_research_pipeline`，不是历史 `.claude` 目录。仓库的 `tooling/songcl_research_pipeline/` 保存其脚本与 references 源码快照，排除 cache、`__pycache__`、字节码和 `_task_backup`；具体文件以归档清单为准。**tooling 仅作源码归档，没有安装到新机器、启用调度、续租或授予同步/训练权限。** 源脚本里的绝对路径和历史示例保持来源语义，不能因位于仓库内就直接执行。机读清单记录关键源文件的读取哈希。

`songcl_remote_train` 是相关操作说明，源位置为 `C:/Users/chuanle song/.codex/skills/songcl_remote_train/`；建议一并以 `tooling/songcl_remote_train/` 归档并在包清单中标明。其旧 IP、自动 commit/sync/launch 等说明属于历史工作流，不覆盖本项目当前 identity pin、foreground/closure、用户暂停和资源授权。归档它也不代表安装或执行授权。

归档重排还会影响旧脚本的默认路径：例如 `project_support/scripts/remote_train.sh`、`sync.sh` 默认拼接同级 `Cluster/` 和上级 `SERVERS.yaml`；仅设置 `PROJECT_DIR` 并不能证明所有配置/控制器路径已正确适配。接班者应先完成独立、可审查的路径适配或显式编排解耦，并用新收据核验，再讨论执行；不要直接调用旧 `pl.sh` 或训练脚本。统计 producer 的重算也须明确区分原源项目布局与归档仓库布局，不能把源路径默认值视为归档后仍有效。

原始来源（非目标机位置）：

| 事实 | 源项目相对证据 |
|---|---|
| 最近运行边界/状态 | `pipeline/codex_memory.md`、`SERVERS.yaml`、`pipeline/goal.json`、`pipeline/queue.json` |
| tick结论 | `pipeline/reports/summary_c1fe217800894083b65baac45f79aa83.md` |
| 新鲜资产/环境检查 | `pipeline/diagnostic_bundles/tick_c1fe2178/runtime_readiness.actual.json` |
| 原始执行、版本关联 | `pipeline/diagnostic_bundles/tick_c1fe2178/cso_native_execution/`、`cso_version_binding/` |
| 已同步与未启动 | `pipeline/diagnostic_bundles/tick_c1fe2178/cso_deployment_execution/sync.actual.json`、`cso_resource_refusal.actual.json` |
| M206完整恢复状态 | `pipeline/manual_ops/20261022_gpu1_pause_105409/checkpoint_evidence.json` |
| M227暂停/完整状态 | `pipeline/manual_ops/20261101_dual_user_pause/checkpoint_confirmation.json` |
| M95精确参考身份边界 | `pipeline/analyses/M202-HDS_done_earlystop_20261017_21500d1a.md`；与 `experiments/EXPERIMENT_SUMMARY.md` 分列口径一致 |
| 数据全量历史基准 | `pipeline/diagnostic_bundles/m201_server4_8eea3f8d47eb4034a4ea148c066192f6/data_{source,target}.json` |
| 环境与CLI源码 | `Cluster/requirements.txt`、`Cluster/docs/cluster_env_setup.md`、集成541中的 `setup.py`、`framework/lib/setup.py`、`pointnet2/setup.py`、`tools/{train,test}.py` |

源项目本地位置为 `D:/project/cluster_project`；最后观测的生产源码位置为 `/data/songcl/Project/Cluster_project/Cluster_nsd_20261107`，训练产物根为 `/data/songcl/Project/Cluster_project/Cluster_checkpoints`。凭据、SSH私钥、私人账户参考文件不属于交接包；本次整理没有读取密码文件。
