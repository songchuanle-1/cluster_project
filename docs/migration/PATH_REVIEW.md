# 最终布局只读复核记录

复核对象：`D:/project/cluster_github_export_20261117`。初始复核发生于文档 finalize 期间；未修改 stage、未运行 materialize、未安装环境或训练。下文保留当时发现，并附 root 已接收的修复方案；**本文尚未验收修复后的 clone/还原执行，也未在 Linux 执行**。

## 已通过的关键引用

- `migration_assets.json` 的 39 份 `source_evidence` 均存在且 SHA-256 匹配。源 `Cluster/` 路径映射到训练根，根外支持记录映射到 `project_support/`，本次交接证据映射到 `docs/migration/`。
- `pipeline/isolated_versions/<name>/…` 对应 `archive/isolated/<name>` 分支中的原文件；已按 Git blob 读取并匹配相关哈希。
- M236 的八个模型文件及一个 YAML 在 stage 根目录全部匹配既有九项 SHA-256。
- HANDOVER 中抽取的 24 个直接路径/目录引用均找到正确映射；数据和 checkpoint 原路径属于明确排除的外部资产，不记为缺文件。
- canonical pipeline 快照为 52 份文件，关键文件哈希匹配；remote_train 快照为 1 份 SKILL.md。stage 的 HANDOVER、migration_assets 与源交接文件逐字节相同。
- 统计文档已改为 `experiments/build_experiment_inventory.py --project-root project_support --verify`，原来的归档布局复算路径问题已在文档中修正。

## 已发现的问题与修复待验证状态

### 1. 校验器把目录符号链接当成普通文件

当前 Git index 中三条历史模型别名是 `120000`：

```text
framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_cosine
framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_poly50
framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_step
```

其 Git blob 内容为相对目标 `model_base1_quard2_c2f_enc_lite_posA_l1`。本次 Windows 工作树中表现为普通文本占位文件，`files.sha256.json` 也按占位字节生成哈希。Linux 的正常 Git clone 会把它们还原为指向目录的符号链接。

`verify_export.py` 对所有条目使用 `path.is_file()` 和 `path.read_bytes()`；因此在正常 Linux clone 中会把这三条合法链接判为 mismatch。应记录并区分 Git mode/文件类型，对符号链接校验链接目标字节，不能把占位文件字节校验直接用于 Linux 链接。

修复状态：root 已安排清单区分 `kind` / `git_mode` / `link_target`，便携校验与还原 helper 由另一 agent 修复。待核验最终 manifest 与三个 Git链接类型一致，并确认 helper 对真实链接和 Windows占位两种情形均采用正确语义。本文未运行修复后的 helper，Linux执行结果未建立。

### 2. 还原工具不能处理 gitlink 和目录链接

`materialize_project.py` 对 `git ls-files` 的每条记录直接 `shutil.copy2(source, target)`。Git index 包含 mode `160000` 的 `framework/DEST3D`；stage 中该路径是空目录，`copy2` 会对目录报错。Linux 的上述三个目录符号链接也会被 `copy2` 默认跟随后当作目录，从而报错。

应先分类 Git mode/文件类型：普通文件复制；符号链接明确保留或按受控规则物化；gitlink 需要已归档的对应源码或明确记录缺失并采取不会半途失败的策略。新目标目录限制本身正确，路径映射模拟未发现目标冲突；本次没有实际生成副本。

修复状态：root 的方案是将现有 DEST3D payload 展平为当前 main 的普通文件，解除该目录对未初始化 gitlink 的依赖，并由便携 helper 处理模型目录链接。待验收最终 tracked mode、普通文件清单、缺失源文件处理和全新目录生成行为；不能由修复计划推断 `copy2` 问题已实际通过测试。

### 3. DEST3D 源码内容未进入当前交付树

源 `cluster_project/Cluster/framework/DEST3D/` 实际有 `issm_triton/`、`models/`、`pointnet2/`、`utils/` 等源码与 LICENSE/README；stage 的 `framework/DEST3D/` 是空目录，`project_support/framework/DEST3D/` 也不存在。Git 仅保留 gitlink 提交 `9512afa38fd58114555c5e42a86056c20135e522`，没有 `.gitmodules`，SHA 清单不包含其内部源码，prepare 的删除/排除说明也未解释这一项。

这不影响 M236 九个核心文件的一致性，但与“当前全部代码”交付范围有关；只保留 gitlink 不能等同于包含内部代码。

root 已接收缺项并确定修复方案：

- 当前 main 将现存49个代码、LICENSE和README文件展平为普通文件；7份 figures 非代码资产排除。
- `provenance/nested_sources.json` 记录每文件 SHA、来源与原 gitlink `9512afa38fd58114555c5e42a86056c20135e522`。
- 源 payload 无 `.git` 或 `.gitmodules`，现有文件与原 gitlink 提交的身份关系保持 **UNKNOWN**；不得因展平而标记成已验证的原提交内容。
- 原始 archive 分支保留 gitlink 指针，不重写历史。

待核验该 provenance 文件和49份归档实际文件逐项匹配、7份 figures 的排除记录存在，以及当前 main 不再将 DEST3D作为gitlink交给普通文件复制逻辑。本文未自行重读或验收修复后的 stage，不能把上述计划写成已经通过的最终验收。

## finalize 后的检查范围

初始复核时 Git index 仍包含待删除的历史构建产物，新增支持文件也尚未全部入 index；这是 finalize 中间态，不作为文件丢失结论。最终应在 add/commit 完成后重新核对 tracked 文件与完整性清单，并对文件类型适配后的校验器做只读验证。还原工具需在显式指定的全新目录单独验收；Linux clone若未实际执行则继续标记未验证。本文不是最终整个仓库的全量哈希或跨平台执行验收。

## 后续修复与本地验证

上述三个缺项已处理：main 将现场的49份 DEST3D 源码、配置、README 和 LICENSE 展开为普通文件；
`provenance/nested_sources.json` 保留原 gitlink、逐文件 SHA 与排除的七张 figures，现存源码与原 gitlink 的身份对应仍为 UNKNOWN。
清单对三个目录别名标记 `git_mode=120000`、`kind=symlink` 和 `link_target`，新校验器按链接目标字节核验。
还原工具解析 Git mode，预先拒绝未物化的 gitlink，并保留目录链接。

两个 helper 的14项小型 fixture 检查通过，包括目标已存在时不覆盖、gitlink提前拒绝和链接目标校验。
当前 Windows 用户无创建 symlink 的权限（1314）；readlink分支采用模拟验证，未提权，
**没有宣称实际完成 Linux 克隆或新服务器运行**。验证记录随包保存于
`provenance/migration_helper_verification.actual.json`。最终复制和全文件清单验收以根目录 provenance 的最终记录为准。
