# 文档模板汇总 — songcl_research_pipeline

本文件是流水线全部产出文档的**唯一格式源**。生成任何 pipeline 文档前先读对应模板，禁止凭记忆自由发挥。

| # | 模板 | 写入路径 | 生成时机 |
|---|---|---|---|
| 1 | [Tick 报告](#1-tick-报告) | `pipeline/reports/summary_<ts>.md` | 每次 cron tick / 用户前台询问（`_manual` 后缀） |
| 2 | [终态结果分析](#2-终态结果分析) | `pipeline/analyses/<id>_<state>_<ts>.md` | 实验判定为终态后自动生成 |
| 3 | [实验设计](#3-实验设计) | `pipeline/designs/exp_design_<ts>.md` | 自主/手动设计新一批实验时 |
| 4 | [动机审查](#4-动机审查) | `pipeline/reviews/motivation_review_<ts>.md` | 每次自主设计前（exp_design 的上游） |
| 5 | [消融方案](#5-消融方案) | `pipeline/designs/ablation_plan_<ts>.md` | PHASE1_REACHED 后出方案与用户讨论 |
| 6 | [决策记录/索引](#6-决策记录与索引) | `pipeline/decisions/<ts>_<type>.md` + `_index.md` | 每次决策（log_decision.sh 自动写） |
| 7 | [Crash 修复记录](#7-crash-修复记录) | `pipeline/bugfixes/bugfix_<ts>.md` | crash 自修复时 |

---

## 1. Tick 报告

每次 cron tick 的 `pipeline/reports/summary_<YYYYMMDD-HHMMSS>.md` 和**用户前台询问状态**时，使用以下固定格式。**始终使用完整六段格式（0-5），不允许精简、不允许合并为单行**。即使没有任何变化，也要展开完整的表格结构和段落标题。删 24h 前旧 summary。禁止自由发挥。

```
================================================================================
  Research Pipeline Report — <project_name>
  <YYYY-MM-DD HH:MM:SS> (tick #<N>)
================================================================================

## 0. Goal Status
  Target: mIoU ≥ X.XXXX | Champion: <id> X.XXXX | Gap: ±0.00XX | Phase: 1 (NOT YET) / 2 (ABLATION)
  (从 pipeline/goal.json 读取，check_goal.py 结果。无 goal.json 时写 "No goal defined.")


## 1. GPU Overview
┌──────────┬──────┬───────┬─────────────┬──────────────────────────┐
│ Server   │ GPU  │ Util  │ Memory      │ Process                  │
├──────────┼──────┼───────┼─────────────┼──────────────────────────┤
│ server-X │ 0    │ 95%   │ 18.6/24 GB  │ text_unet (pid 108985)   │
│ server-X │ 1    │ 0%    │ 0.0/24 GB   │ — IDLE —                 │
│ server-Y │ 0    │ 0%    │ 0.0/24 GB   │ — IDLE —                 │
│ ...      │      │       │             │                          │
└──────────┴──────┴───────┴─────────────┴──────────────────────────┘
Free GPUs: server-X:1, server-Y:0
(只列出本项目 SERVERS.yaml 中 role=gpu_server 且在 allowed_gpus 白名单内的服务器)

## 2. Running Experiments
| ID       | Config                        | Server   | GPU | Epoch    | Best mIoU | Acc@50 | spmIOU | No-Impr | Status     |
|----------|-------------------------------|----------|-----|----------|-----------|--------|--------|----------|------------|
| dec4     | model_early_exit_4_dec4       | server-2 | 1   | 29/50    | 0.4874    | 0.542  | 0.449  | 4/10     | running    |
| text_unet| model_early_exit_4_text_unet  | server-3 | 0   | 21/50    | 0.4986    | 0.551  | 0.458  | 1/10     | running    |
| ...      |                               |          |     |          |           |        |        |          |            |

## 3. Queue Status
| Position | ID   | Config                           | Status  | Depends On    | Server     |
|----------|------|----------------------------------|---------|---------------|------------|
| 1        | XXX  | ...                              | waiting | —             | server-X   |
| 2        | YYY  | ...                              | waiting | XXX           | server-X   |
| ...      |      |                                  |         |               |            |
Active capacity: A active (R running, C claiming, W waiting) / N target → capacity OK / NEED MORE；candidate budget = B

## 4. This Tick's Actions
  - [自主早停] <action> — <result>
  - [队列推送] <action> — <result>
  - [代码同步] <action> — <result>
  - [终态判定] <action> — <result>
  - [实验设计] <action> — <result>
  (无动作时写 "No actions taken. All stable.")

## 5. Decisions Made
  - [YYYY-MM-DD HH:MM] <type>: <decision> (见 pipeline/decisions/_index.md)
  (无决策时写 "No decisions this tick.")

================================================================================
  Next tick: <YYYY-MM-DD HH:MM>
================================================================================
```

**格式强制检查**:
- 第 0 段: Goal Status — 每次必写。无 goal.json 写 "No goal defined."，有则显示 target/champion/gap/phase
- 第 1 段: GPU Overview — 只列白名单内的服务器和卡
- 第 2 段: Running Experiments — 必须含 10 列(ID/Config/Server/GPU/Epoch/Best-mIoU/Acc50/spmIOU/No-Impr/Status)
- 第 3 段: Queue Status — 队列顺序 + 深度判定
- 第 4 段: This Tick's Actions — 每次必写，无动作也说"No actions"
- 第 5 段: Decisions Made — 每次必写，无决策也说"No decisions"
- **禁止精简格式**：不允许 `## GPU: server-4 GPU0(...), GPU1(...)` 这类单行合并。即使无变化，每个段落标题必须独立出现，GPU/Running 表格必须完整展开。
- 结尾: Next tick 时间

**用户前台询问**: 用户说"查看 pipeline 状态"/"实验进度"/"pipeline 报告"等:
- 按六段固定格式现场输出
- **必须同步写入** `pipeline/reports/summary_<YYYYMMDD-HHMMSS>_manual.md`。使用 bash `cat > file << 'EOF' ... EOF` 写入，内容即上述六段格式的完整输出。不要跳过这一步。
- `_manual` 后缀区分 cron 触发 vs 手动查询，方便事后追溯

---

## 2. 终态结果分析

每个实验判定为终态后，**cron tick 必须自动生成该文件**。后续实验设计的 Phase 1 分析主要读取这组文件。

```
================================================================================
  Experiment Result Analysis — <project_name>
  Experiment: <experiment_id> | State: <state>
================================================================================

## 1. Basic Info
  - ID: <id>
  - Config: <config_path>
  - Server: <server> | GPU: <gpu_id>
  - Started: <start_time> | Finished: <end_time> | Duration: <Xs/h>
  - State: done_complete | done_earlystop | crashed

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | X.XXXX | N       |
  | Acc@50   | X.XXX  | N       |
  | spmIOU   | X.XXXX | N       |
  (if crashed: last saved mIoU before crash)

## 3. Convergence Summary
  - Best first reached at: epoch <N>
  - Subsequent no_improve epochs: <K> (if early-stopped)
  - Final epoch best: mIoU=X.XXXX vs historical best=X.XXXX
  - (简要描述收敛形态: 快速上升后平台/震荡/一直未收敛)

## 4. Comparison
  - vs baseline (<baseline_id>): γ = +0.00XX (有效) / -0.00XX (失败) / ≈0 (持平)
  - vs current champion (<champion_id>): γ = ±0.00XX
  - (列出所有可对比的前置实验)

## 5. Conclusion
  - 结论: [有效] / [失败] / [持平]
  - 解释: <一句话说清这个实验证明了什么>
  - 对后续实验设计的建议: <复现验证? 扩展该方向? 放弃?>

## 6. Crash Info (if crashed)
  - Error type: <import / CUDA OOM / dimension mismatch / ...>
  - Error message excerpt: <first 5 lines>
  - Auto-fix attempt: <Y/N> — <retries> retries, result: <fixed/abandoned>
================================================================================
```

---

## 3. 实验设计

`pipeline/designs/exp_design_<ts>.md`，7 段格式：

```
================================================================================
  Experiment Design — <project_name>
  <YYYY-MM-DD HH:MM:SS>
================================================================================

## 1. Motivation（为什么设计这批实验）
  - 项目动机（直接引用 goal.json description）: <goal.description>
  - 故事线当前状态: 已验证的假设 / 未验证的假设 / 缺口
  - 触发原因: running+claiming+waiting < target_active，candidate_budget=B / Phase 2 消融计划确认
  - 这批变体在故事线中的角色: 验证假设X / 排除方向Y / 消融确认Z

## 2. Current Best Results（基于什么数据做决策）
| Experiment ID | Config                  | State          | Best mIoU | Acc@50 | spmIOU | Epochs |
|---------------|-------------------------|----------------|-----------|--------|--------|--------|
| ...           | ...                     | done_complete  | 0.5012    | 0.552  | 0.460  | 50     |
| ...           | ...                     | done_earlystop | 0.4874    | 0.542  | 0.449  | 29     |
  (来源: pipeline/analyses/ 下各实验终态分析 + experiments.csv + pipeline/decisions/_index.md)

## 3. Analysis & Direction（方向分析）
  ### 3.1 哪些方向有效（> baseline）
    - <方向A>: best=X.XXXX, γ=+0.00XX vs baseline, 机制分析: ...
  ### 3.2 哪些方向失败（< baseline 或持平）
    - <方向B>: best=X.XXXX, γ=-0.00XX vs baseline, 失败原因推测: ...
  ### 3.3 哪些尚未消融
    - <方向C>: roadmap 计划但未跑, 优先级: high/medium/low
  ### 3.4 结论
    - 下一步选择理由（为什么这批设计比别的方向更值得投入）

## 4. Experiment Plan（具体做什么）
| # | ID            | Config Path            | Purpose / Hypothesis                          | Expected Result            | Priority | Depends On |
|---|---------------|------------------------|-----------------------------------------------|----------------------------|----------|------------|
| 1 | <id>          | configs/.../xxx.yaml   | <这个实验验证什么假设? 为什么预期> 0.50?       | > baseline 0.4956          | P0       | —          |
| 2 | <id>          | configs/.../yyy.yaml   | <假设>                                         | > current best 0.5012      | P1       | <id1>      |
| 3 | <id>          | configs/.../zzz.yaml   | <假设>                                         | complement evidence chain  | P2       | —          |

## 5. GPU Allocation Plan（GPU 分配计划）
| Server   | GPU | Assignment              | Config                       | Justification            |
|----------|-----|-------------------------|------------------------------|--------------------------|
| server-4 | 0   | 当前 running: l1_refine | ...                          | —                        |
| server-4 | 1   | 当前 running: l1_detail | ...                          | —                        |
| server-4 | 0   | Next: <id>              | configs/.../xxx.yaml         | first free card gets P0  |
| server-4 | 1   | Next: <id>              | configs/.../yyy.yaml         | second card gets P1      |
  空闲卡均为 FIFO 队列顺序分配，不绑定卡号(gpu 字段不写或写 None)

## 6. Implementation Checklist（实施清单）
  - [ ] 检查现有 config 是否可直接复用或仅需 YAML 参数变更
  - [ ] 如需新 model 代码: <描述变更内容, 文件路径, 预计行数>
  - [ ] 创建 config YAML: configs/<path>/<name>.yaml
  - [ ] git add + commit + push
  - [ ] **sync 到所有可用服务器**（见 SKILL.md「代码同步规则」）
  - [ ] 更新 pipeline/queue.json (追加到 gpu_queues.server-X 队尾)
  - [ ] 验证: 下次 cron tick 跑 pipeline_monitor 确认新任务正常启动

## 7. Risk Assessment（风险评估）
  - 代码风险: （是否涉及新 model 包 / 结构性改动 / CUDA 扩展?）
  - 资源风险: （是否需要更多 GPU 显存? 是否影响其他项目?）
  - 数据风险: （是否需要新数据集? 现有数据够不够?）
  - 失败回退: （如果 crash 3 次，怎么处理? 跳回哪个方向?）
================================================================================
  Status: DRAFT | APPROVED | IMPLEMENTED
  Designed by: Research Pipeline (autonomous)
  Created: <YYYY-MM-DD HH:MM>
================================================================================
```

---

## 4. 动机审查

`pipeline/reviews/motivation_review_<ts>.md`，6 段格式。是 exp_design 的**上游分析**，每次自主设计实验前必须生成。

```
================================================================================
  Motivation Review — <project_name>
  <YYYY-MM-DD HH:MM:SS>
================================================================================

## 1. Goal
  - 引用 pipeline/goal.json 完整内容
  - 当前 target / champion / gap

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 聚类路由提升特征表达 | confirmed | posA_l1 0.5012 vs base 0.4894 (γ=+0.0118) | 需要消融哪些设计必要 |
  | ... | partial | ... | ... |

## 3. Experiment Assessment（已有实验的动机视角评估）
  对每个已完成实验:
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 | 0.5012 | 直接验证 cluster_attn 路由 | 确认核心假设 ✓ |
  | posB | 0.4953 | 消融位置编码类型 | 排除 posB, posA 最优 |
  | ... | ... | ... | ... |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: ...
  - 未验证: ...
  - 矛盾/疑问: ...

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 每个变体填补哪个缺口
  - 预期结果对故事线的推进

## 6. Next Batch
  → 见 pipeline/designs/exp_design_<ts>.md
================================================================================
```

---

## 5. 消融方案

`pipeline/designs/ablation_plan_<ts>.md`，PHASE1_REACHED 后生成、与用户讨论用：

```
================================================================================
  Ablation Plan — <project_name>
  Champion: <champion_id> (mIoU=X.XXXX, config=<path>)
  <YYYY-MM-DD HH:MM:SS>
================================================================================

## 1. Champion Architecture Analysis
  - Config: configs/.../xxx.yaml
  - Model: <model_package>
  - Key design choices:
    1. <设计选择1>: <描述> (config 字段: xxx)
    2. <设计选择2>: <描述> (config 字段: yyy)
    3. ...

## 2. Proposed Ablations
| # | ID | 消融什么 | 对照实验 | 假设 | 预计 Δ | Priority |
|---|----|---------|---------|------|--------|----------|
| 1 | abl-XX | 去掉 L1 loss | l1_weight=0 | L1 对收敛稳定关键 | -0.005~-0.010 | P0 |
| 2 | abl-YY | pos encoding A→B | pos_enc=B | posA 优于 B | -0.003~-0.008 | P1 |
| 3 | abl-ZZ | 关掉 refine | refine=false | refine 收益 0.003 | -0.003 | P1 |

## 3. Implementation Details
  (每个消融的 config 路径、改动点、是否需要新 model 代码)

## 4. GPU Allocation
  (消融实验的排队计划，与现有队列的优先级协调)

================================================================================
  Status: DRAFT → DISCUSSING → APPROVED → IMPLEMENTING → DONE
  Created: <YYYY-MM-DD HH:MM>
  Approved: (用户确认时间)
================================================================================
```

---

## 6. 决策记录与索引

单次决策 `pipeline/decisions/<YYYYMMDD-HHMMSS>_<type>.md`（由 `log_decision.sh` 写入，无需手写）：

```
# <project> 决策记录

- **时间**: <YYYY-MM-DD HH:MM:SS>
- **类型**: early_stop | queue_push | next_batch | route_change | question | manual | manual_batch | other
- **问题**: <当时面临的选择，含关键数字>
- **决策**: <具体动作，哪个 config、哪台服务器、哪块 GPU>
- **依据**: <判断逻辑>
- **证据**: <数据来源，如 pipeline_monitor 输出、experiments.csv 等>
```

索引 `pipeline/decisions/_index.md`：

```
# <project> 决策索引

| 时间 | 类型 | 问题 | 决策 |
|------|------|------|------|
| 2026-07-17 06:56:46 | route_change | A3 true_route 已 kill... | 推送 B4 refine 变体... |
```

---

## 7. Crash 修复记录

`pipeline/bugfixes/bugfix_<YYYYMMDD-HHMMSS>.md`：

````
# Bugfix: <简短描述>

- **时间**: <YYYY-MM-DD HH:MM:SS>
- **实验**: <experiment_id>
- **错误类型**: <import / CUDA OOM / dimension mismatch / ...>
- **错误日志摘要**:
  ```
  <关键错误行>
  ```
- **根因**: <一句话定位>
- **修复**:
  ```diff
  <修复的 diff>
  ```
- **重试**: 第 <N> 次，结果: <fixed / still failing / abandoned>
````
