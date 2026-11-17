# cluster_project：源码、实验记录与迁移交接

这是 2026-11-17 的私有交接仓库。训练代码以 **M236-CSO 集成提交
`5413102c57b526035f3920b5e7a81f3b58ad764d`** 为基准，补充项目外层支持代码、实验统计与迁移资料。
本次仅做归档和上传，没有迁移服务器、恢复暂停实验或启动训练。

- **[迁移与接班文档](docs/migration/HANDOVER.md)**：环境、数据、checkpoint、原生协议、已知故障和下一步。
- **[实验统计](experiments/EXPERIMENT_SUMMARY.md)**、[逐项 CSV](experiments/experiments_inventory.csv)：完整 ID 去重、局部结果及来源冲突。
- **[数据和权重清单](docs/migration/migration_assets.json)**：原路径、历史哈希、大小和证据时间；文件需另行传输。
- **[导出来源清单](provenance/export_manifest.prepare.json)**、[文件 SHA-256](provenance/files.sha256.json)：支持代码、归档分支和排除项。

## 目录与源码版本

| 位置 | 内容 |
|---|---|
| 仓库根的 `framework/`、`configs/`、`tools/`、`scripts/` 等 | 原 `cluster_project/Cluster/`，以 M236 集成5413为基准 |
| `project_support/` | 原项目根外的 `scripts/`、`framework/`、`configs/`、`pipeline/`、服务器登记和历史实验 YAML |
| `experiments/` | 本次统计、冲突说明、输入哈希及可复算 producer |
| `docs/migration/` | 交接文档、资产清单、源机四份 YAML 的实际差异与原字节 |
| `tooling/` | canonical pipeline/remote-train skill 快照及本次导出工具，仅归档 |
| `provenance/` | 完整性、来源、安全审计和导出范围 |
| `docs/upstream/README.md` | 原训练仓库 README，部分命令和路径已过时 |

`main` 适合检查当前待运行的 M236 代码；原实验提交和未提交代码分别保存：

- `archive/isolated/<原worktree名>`：26 个原始独立版本，引用原提交，无重命名或重写历史。
- `archive/local-main-committed-20261117`：原本地主树提交 `0747f6acec1c61018ec99acf2efa5329c9b3523c`。
- `archive/local-working-20261117`：该主树的 9 项 modified 与 28 项 untracked 文件快照。

本地 working 的 RVEC 等内容可能与新版不同，必须在其归档分支查看，不能直接覆盖 M236。
原 `framework/DEST3D` 仅记录 gitlink 且缺少 `.gitmodules`；当前 main 另将现场已有源码及 LICENSE 展开为普通文件，
见 [嵌套源码清单](provenance/nested_sources.json)。现存文件与原 gitlink 提交的对应关系未知，归档分支保留原指针。
当前 main 移除了历史构建产物和论文二进制；原 Git 历史仍保留原来已跟踪的文件。
没有上传训练权重、数据、原始训练日志、凭据或缓存。大于 2 MiB 的支持层历史记录一般单独列入排除清单；
`research_work.json` 明确保留。原生证据中所有权租约、启动意图和一次性入口均是历史材料，不能重放。

## 实验概况

| 去重账本状态 | 数量 |
|---|---:|
| `done_complete` | 41 |
| `done_earlystop` | 157 |
| `stopped_unknown` | 45 |
| `crashed` | 13 |
| 人工暂停 | 2 |
| 等待正式训练 | 1 |
| 撤回 | 7 |
| **合计** | **266** |

198 个 ID 被账本标为结束，其中 M174/M195/M196 存在已知完成性问题，其余也未逐项重审全部原生日志。
这个数字不能等同于严格确认完成的训练次数。候选工作流另有 162 条，也不能并入训练完成数。

历史 champion 为 **M95-CSORT，账本 mIoU 0.5020**；frozen 参考值 **0.5024607181549072**
与历史 champion 权重的身份对应仍未核实，目标为 **0.5100**。
**M236-CSO 已通过原生两步及资源技术准入，但完整训练尚未开始，效力和新颖性仍未知。**
M206、M227 保持人工暂停；M235 的长程 Adam 故障根因未知。

## 在新机器接手

```bash
git clone -c core.autocrlf=false https://github.com/songchuanle-1/cluster_project.git
cd cluster_project
python -B tooling/export/verify_export.py
```

先阅读交接文档，再选择目标机器并迁移数据与权重、重建环境、重编译 CUDA 扩展及验证协议。
源机器的服务器登记、旧 owner、旧 shim 和 GPU 授权不能直接继承为新机器的启动许可。
独立 `tools/test.py` 还存在模型导入入口问题，详见交接文档。
不要直接执行旧 README 或历史 `SERVERS.yaml` 中的命令。

训练代码可以直接以克隆目录为根使用。若需重建原 `Cluster/` 与外层支持目录的布局，
可用 `tooling/export/materialize_project.py` 在一个**全新目录**生成副本；它不会安装依赖或执行训练。
