# cluster_project 实验统计与迁移事实表

统计日期：2026-11-17（Asia/Shanghai）。本表读取本地已保存记录；没有连接服务器、运行训练、派发候选或改变研究状态。原账本最后记录的时间和统计日期不是同一概念。源文件集合 SHA256：`4ee342ce3d8b604f1955ccf13ddc66da5885007490f7f1a87ef93241d7344620`。

## 应怎样理解“做了多少实验”

当前源材料合计 **266 个去重完整实验 ID**，其中 M 系列 **218 个完整 ID、217 个不同 M 编号**，另有 48 个早期非 M ID。最大编号 M236 不代表做完了 236 次训练；19 个中间编号不在本次读到的账本中，M81-CONS 与 M81-CTF-HCG 又共用数字 81，明细保留二者。

实验 CSV 有 **274 行、250 个完整 ID**。21 个 ID 多次入账，共有 24 行超出去重数量；其中只有 1 行属于全字段完全重复，其余包含等待、崩溃、修正或恢复后的历史。不能把每一行算作独立、完成的训练。

`pipeline/experiments/` 有 **217 份 JSON**，其中原始 `running` 有 32 份，多数是旧快照。`queue.json` 有 37 条跨状态记录，包含已结束和已撤回历史，不能把队列条数理解成待训练数量。当前不存在单体 `pipeline/experiments.json`。

## 按完整 ID 去重后的状态

| 归一状态 | ID 数 |
|---|---:|
| `done_complete` | 41 |
| `done_earlystop` | 157 |
| `stopped_unknown` | 45 |
| `crashed` | 13 |
| `paused_by_user` | 2 |
| `waiting` | 1 |
| `withdrawn` | 7 |

账本标为 `done_complete` 或 `done_earlystop` 的合计 **198 个 ID**。其中 **M174、M195、M196 共 3 个**有明确的 partial-patience / 停止归因问题。余下 **195 个只是“账本报告已结束，且不含这 3 个已知例外”**，本导出没有逐条审计所有原生训练日志，不能将此数宣称为严格验证过的完整训练总数。`done_complete`/早停完成也不等于都跑满 50 个 epoch。

45 个 `stopped_unknown` 的完成性未知；13 个 `crashed` 保留不完整训练的局部指标；2 个人工暂停保留 checkpoint；1 个 waiting 尚未开始完整训练；7 个 withdrawn 没有完成训练证据。这里没有把旧快照 `running` 当成当前仍在运行的进程，也没有通过本地记录宣称服务器当前无训练。

M 系列独立口径：`done_earlystop`=154，`stopped_unknown`=41，`crashed`=13，人工暂停=2，waiting=1，withdrawn=7。41 个 `done_complete` 全属于早期非 M ID。

## 实验路线覆盖

下面按原始 ID 和 config 名称整理路线，数量是完整 ID 数，包含中断、撤回及准备状态，不能再次当作已完成训练数量。逐项状态和配置均在 CSV 中。

| 记录范围 | 去重完整 ID 数 | 代表性实验与路线 |
|---|---:|---|
| 早期非 M | 48 | model_base1/base2、quard2/c2f/encoder lite、posA/B/C、layerscale、GBCR、detail/2layer 等基础与组件比较 |
| M1–M64 | 45 | QGC/QSF、ORT、XCA、CTF、CSF、DCA、FILM 等 query/context 与跨尺度组件 |
| M65–M95 | 32 | HCG、ITER/REAG、CCP、CTF×HCG、DET、MLAY、CSORT；含历史 champion M95 |
| M96–M138 | 43 | 多 seed 对照、MEMBANK、SRL、LCC、MFP、MLAY、DCA/DCM、DUAL 等组合 |
| M139–M196 | 58 | CL*、object/query/support 系列、MQ* 与 MQ*-TR、CPS、BCA 等候选 |
| M197–M236 | 40 | PIRS/PDC/BEI/TMR/BPS、HDS/CPA/MDC、层次点特征与组合结构、各候选技术准入及原生运行 |

## 候选与技术准入另算

`research_work.json` 有 **162 条去重候选记录**，stage 分布为 complete=54、rejected=94、blocked=13、deployment=1。只有 **40 条**带 experiment_id；另 122 条没有实验 ID，包含诊断、否决与准备工作。stage=`complete` 是候选工作流结束，不等同于完整训练。

带 experiment_id 的候选阶段与实际实验账本交叉表如下：

| 候选 stage | 对应训练状态 |
|---|---|
| `blocked` | `crashed`=3、`paused_by_user`=2、`stopped_unknown`=1 |
| `complete` | `crashed`=6、`done_earlystop`=23、`stopped_unknown`=3 |
| `deployment` | `waiting`=1 |
| `rejected` | `stopped_unknown`=1 |

native TRAIN2 / backward / resources PASS 及 `technical_admission=true` 仅证明相应技术门槛，不证明原生长程稳定性、完成训练、达到目标或科学新颖性。候选中的原始 `scientific_admission` 语义有历史差异，导出保留原值，不据此计训练数。

## 当前参考与最近实验

历史 champion ID 仍为 **M95-CTF-HCG-CSORT**，历史账本值 **0.5020**。已保存的 frozen M95 epoch16 full-VAL 参考为 **0.5024607181549072**，baseline 精确参考引用为 **0.4894491136074066**，目标为 **0.5100**。M202 的原分析明确说 frozen M95 权重与历史 champion 权重的身份尚未核实，因此两个 M95 数值分列保留，不用精确参考回写历史 ledger。

| 实验 | 状态 | 进度记载 | mIoU 与证据范围 |
|---|---|---|---|
| M226-WFC | `done_earlystop` | 30/50 | 0.49711745977401733（complete_experiment_restored_history_exact_best） |
| M227-LFT | `paused_by_user` | saved epoch22 | 0.4977978467941284（saved_checkpoint_metadata_paused_not_final） |
| M228-NEC | `done_earlystop` | 23/50 | 0.49454113841056824（账本） |
| M229-MIC | `done_earlystop` | 26/50 | 0.49881425499916077（complete_native_terminal_result） |
| M230-HVD | `crashed` | 5/50 (partial1449/4686) | 0.4264346659183502（saved_checkpoint_metadata_crashed_not_final） |
| M231-PSC | `crashed` | 2/50 (partial984/4686) | 0.3036（账本） |
| M232-NSD | `crashed` | 1 | UNKNOWN |
| M233-NDE | `crashed` | 0 complete; partial1/50 step932/4686 | UNKNOWN |
| M234-RVE | `crashed` | partial Train[2/50] batch4297/4686; precise completed-epoch count UNKNOWN | 0.3192218840122223（saved_checkpoint_metadata_crashed_not_canonical_archive_best） |
| M235-SINC | `crashed` | 2/50 | 0.2787637412548065（saved_checkpoint_metadata_partial_training） |
| M236-CSO | `waiting` | — | 完整训练未启动 |

M226 完整实验 best 为恢复历史的 0.49711745977401733，不能以恢复段最后验证值代替。M229 有 26 次完整验证、epoch26 原生 patience10 早停，best 0.49881425499916077@16；尚未超过 M95。

M206-CGCA checkpoint epoch24/best 0.4952535927295685，M227-LFT checkpoint epoch22/best 0.4977978467941284，二者都是**人工暂停中的局部结果**，没有自动恢复授权。

M230-HVD 保存完整 epoch4，崩溃于 partial epoch5/1449；M231-PSC 保存 epoch1、partial epoch2/984；M232-NSD 只有 partial epoch1/1961、完整验证0；M233-NDE 只有 partial epoch1/932、完整验证0。M234-RVE canonical best UNKNOWN，另有 epoch1 checkpoint 元数据 0.3192218840122223，二者不互相替换。M235-SINC 仅有完整 saved epoch1（元数据 best 0.2787637412548065）和 partial epoch2/1870；账本 2/50 并不表示完成两轮。

**M236-CSO：native=PASSED、resources=PASSED、technical_admission=true、已入队，full_training_started=false，完整训练尚未启动，efficacy/novelty UNKNOWN。** 本地队列保留 GPU0 启动资源不足及新 owner 重新绑定执行阶段的约束；不得从技术准入或候选编号推断已训练。

## 已知冲突与取值优先级

本次发现 **39 个完整 ID 的来源状态不一致**；另有 2 个来源数值差异大于 0.0001 的 ID，完整列表在 `ledger_conflicts.json`。状态修正只发生在导出视图：

1. 完整 experiment_id 是去重键；不按 config 相同或 M 数字相同擅自合并。
2. 人工暂停的明确标记覆盖通用 waiting，保留未授权恢复的约束。
3. 同一 ID 的 CSV 取最后追加行；部分补记的时间倒序，所以不能简单取 finished_at 最大者。所有旧行号留在明细表。
4. 没有 CSV 记录时，用已保存 terminal/waiting 队列记录，再用 experiment JSON。
5. C2-posC / F1-2layer 的保存终态分析补足旧 running 快照；分别为早停结束和手动中断。
6. M82 的 CSV/JSON 是 stopped_unknown，而 queue 写 done_earlystop；保留 CSV/JSON 口径并揭示冲突。M17、M22 的最后 CSV 与保存分析相符，旧 JSON stopped_unknown 不覆盖修正；M98/M106–M108 的最后追加 crash 修正保留。
7. candidate.stage、queued 历史布尔值、技术门槛不覆盖训练终态。M226、M235 的 candidate.training_status 仍残留 running，实际分别是 done_earlystop、crashed。
8. 精确参考、checkpoint 元数据、canonical 舍入值分列；partial 和未知值不进入完整训练效果结论。

M174 的 monitor 将 spmIOU 误匹配进早停序列，只有5次真实峰后验证；M195 native 没有早停 footer、只有7次峰后验证；M196 只有5次峰后验证且实际 kill 的执行来源未核实。三者原始 done_earlystop 原样保留，训练范围另列为不完整/未核实。

## 交付与复算

- `experiments_inventory.csv`：266 行，以完整 ID 去重，含状态、范围、报告/精确指标、配置、来源、行号、冲突标记和证据。
- `candidate_status_summary.json`：完整计数、162 条候选的紧凑状态、训练状态交叉表；只引用证据指针，不展开诊断包。
- `ledger_conflicts.json`：重复行、状态/指标冲突、候选残留字段、优先规则。
- `source_manifest.json`：所有实际读取输入的大小、SHA256 及原账本 schema。
- `build_experiment_inventory.py`：仅标准库的 producer；`--verify` 只读校验历史源哈希、去重明细、候选统计和冲突事实，不改原账本或历史导出。

最终交接仓库采用训练代码在根、原项目支持资料在 `project_support/`、统计产物在 `experiments/` 的布局。在**导出仓库根目录**校验：

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B experiments/build_experiment_inventory.py --project-root project_support --verify
```

在**原本地项目根目录**使用原位置的脚本校验：

```powershell
python -B pipeline/handoffs/20261117_github_migration/experiments/build_experiment_inventory.py --project-root . --verify
```

`--project-root` 指原始账本所在的支持资料根，即它下面应有 `pipeline/experiments.csv`；`--output-dir` 默认是脚本所在的 `experiments/`，用于读取已保存产物。`--verify` 不重制统计、不更新 CSV/JSON，也不改写其中的源 SHA；JSON 的 `producer_sha256` 保留最初生成时的版本，兼容校验脚本会另行报告当前脚本 SHA。显式 `--rebuild` 才会重建输出，迁移核验无需使用。

配置路径通常相对于训练代码根目录保存。历史明细在**原项目根与原 `Cluster/`**分别检查：前者命中 19 个 ID，后者命中 221 个 ID，有 45 个 ID 在这两个根未定位。未检查 `isolated_versions`、保留 source commit 或远端 runtime 中的完整代码，此数不能解释为“代码丢失”。交接仓库已把原 `Cluster/` 展平到根，布局变化可能改变这些配置定位辅助值；`--verify` 会报告这些差异，但只对训练/候选事实及原始证据进行严格比较，不据此回写历史事实。配置字符串、状态、metrics、source/evidence、重复记录和源哈希仍须一致。

统计范围只包含 manifest 明列的 CSV、217 份 experiment JSON、research_work、queue 和选定分析文本。没有读取诊断包巨量 JSON、CRlogs、owner.work_before、账号文件或密码。脚本不导入项目控制代码或模型，不发起联网、训练、恢复、派发、前台接管或服务器操作。原日志、checkpoint、未包含账本中的历史启动次数及所有 seed 的科学有效性不由此表新增推断。
