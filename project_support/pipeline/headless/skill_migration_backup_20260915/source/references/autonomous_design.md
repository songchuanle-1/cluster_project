# 自主实验设计与闭环 — songcl_research_pipeline

启用 `pipeline/closure_policy.json` 的项目必须执行 `references/closure.md`。
未完成候选以稳定 ID 保存到 research_work.json；event 续做具体阶段，
不要因新增 review/design 就将仍缺原生验证的工作判作闭环。
新入队任务必须具有机器可校验的准入 receipt；训练闭环必须观察步数增长。

cron tick 会话的行为准则。触发条件：**running + claiming + waiting < 可用容量槽位数 + design_buffer** 时，Codex 按缺口自主完成实验设计 → 实现变体 → 补充队列。全部文档格式见 `references/formats.md`。

> **可用卡数定义**（不要搞混）: = 该项目 SERVERS.yaml 各 gpu_server 的**容量槽位总和** = Σ(白名单卡数 × `max_tasks_per_gpu`)（**容量，固定值**），≠ 当前空闲卡。当前 cluster server-4 [0,1]（max=1）→ 2，server-6 [7]（max=2）→ 2，合计=4；multiview server-6 [1,2]（max=1）→ 2。不配 `max_tasks_per_gpu` 时每卡按 1 槽位算。"空闲卡"(util<10%且显存<1GB；单卡多任务模式下=槽位未满且显存余量>20GB) 只决定**推送时机**，不进深度公式。所有数值始终以项目 `SERVERS.yaml` 为准。

> **候选预算定义**：`active_count = running + claiming + waiting`；`target_active = capacity + design_buffer`；`candidate_budget = min(max_candidates_per_design_tick, max(0, target_active - active_count))`。设计模式以 `candidate_budget` 为本轮目标数量。只有通过全部科学准入、独立实现和测试的候选才能入队；合格候选少于预算时允许留空，必须记录每个未入队候选的淘汰原因。

核心原则：
1. **不等用户** — 不做交互提问，不弹确认，不等待审批。
2. **直接自主执行** — 基于实验指标、goal.json、已完成分析和决策轨迹做研究决策。
3. **全量落文档** — 每个动作可追溯，用户事后读文件即可了解发生了什么。

## Phase 0: 目标检查（进入自主设计前必须执行）

```
0. 检查 pipeline/goal.json:
   → 不存在: 自由探索模式，正常进入 Phase 1 设计
   → 存在: 运行 check_goal.py 判定:
      ├─ PHASE1_REACHED (champion ≥ target): 停止自主设计，生成消融方案 → 与用户讨论
      ├─ Phase 2 消融已确认: 正常入队运行消融实验，继续闭环
      └─ 未达标: 继续 Phase 1，自主设计服务指标提升
0.5 检查活跃保留（硬性，双源）:
    ① goal.json constraints[] 中含"活跃保留"字样的条款（主源，设计必读且不受截断影响）
    ② decisions/_index.md 最近 10 条中的 route_change/question —— **必须打开原文文件读全文**
      （索引表的决策列会截断，"缺口保留/不自动补位/待用户拍板"关键词可能被切掉——
       20260718 三次越权入队均因此漏检）
    任一源存在未解除的保留 → **跳过自主设计**，tick 报告注明保留依据；
    只有用户明示解除（并同步移除 goal.json 中的保留条款）后才恢复设计。
```

**Phase 1 期间，自主实验设计不强制消融、不强制特定模块。** 唯一目标是让 champion 超过 target。

## Phase 1: 分析

```
0. 读 pipeline/goal.json → 提取 description/motivation ← 始终以动机为出发点
1. 先读 `.tick_context.json` 的 bounded manifest、`codex_memory.md` 和
   `experiments.csv` 最近终态记录。默认只打开 manifest 列出的最近分析；
   更早分析必须按明确实验 ID 或文档引用定向读取，禁止整目录 dump。
   → 对与当前假设相关的已完成实验，带上 motivation 视角:
     "这个实验结果证明了动机的哪一部分？还缺什么证据？"
2. 汇总: 先用 `codex_memory.md` 的关闭方向和 manifest 最近决策；只有发现
   证据缺口时才按 ID 定向读取 `_index.md` 的小段或单个决策原文。
3. 提取每个实验的 Best mIoU/Acc/spmIOU 完整指标
4. 按 motivation 对齐度判断方向:
   ├─ 有效 + 与动机一致 → 扩展该方向
   ├─ 有效 + 偏离动机 → 记录但不优先 (可能是未来的另一条故事线)
   └─ 失败 → 分析原因，考虑是否与动机的某个假设冲突
5. goal.json 的 constraints[] / banned[] 即硬约束与禁区（单文件契约，无独立 roadmap 层）
   —— 候选变体必须逐条对照校验；docs/ 原始计划文档仅作背景，与 goal.json 冲突时以 goal.json 为准
```

## Phase 1.5: 从动机推导设计（硬性规则，决定 Phase 2 设计什么）

```
基于 motivation 和已有实验结果，问三个问题:
  Q1: 我们的故事现在缺什么？
      例: cluster 的动机是 "聚类矩阵与点云特征相关 → cluster_attn 更新特征"
      → 已有的实验证明了 cluster 路由有效 (γ=+0.0118 vs baseline)
      → 缺: refine 机制消融 / 不同路由策略对比 / 多 seed 稳定性
  Q2: 下一步实验如何填补缺口？
      → 每个候选变体必须直接回答故事线的一个未验证假设
      → 如果某个变体 "做了也不错"但跟动机无关 → 搁置
  Q3: 这批实验跑完后，故事线会推进到哪一步？
      → 预期: 某假设被证实/证伪 → 故事线更完整

对每个候选变体校验:
  ├─ 这个变体验证了动机中的哪个假设？
  ├─ 如果结果 > baseline: 对故事线有什么贡献？
  ├─ 如果结果 < baseline: 说明了什么（排除一个方向也是推进）？
  ├─ 与 goal.json 的 constraints[] / banned[] 是否冲突？
  │   （冲突 → 搁置或记 question。前车之鉴: E1-cosine 与"禁单变体改 schedule"条款冲突被撤回）
  └─ 偏题的变体 → 搁置

在 exp_design 文档的 §1 Motivation 中:
  - 直接引用 goal.json 的 description
  - 写清这批变体在故事线中的角色（验证假设X / 排除方向Y / 消融确认Z）
```

**Phase 1 产出（硬性）**：分析过程必须存档为 `pipeline/reviews/motivation_review_<ts>.md`（6 段格式见 `formats.md#4-动机审查`），供后续决策追溯。该文档是 exp_design 的上游分析，每次自主设计实验前必须生成。

## Phase 1.6: 调参气味检测（硬性，每个候选变体入队前必须通过）

黑名单永远无法穷举。模型会找 banned[] 里没写到的漏洞（"我没调 orth_weight，我调的是 orth_temperature"）。所以 Phase 1 的禁区必须是**原则而非列表**。

### 判定标准：单一追问

> 这个变体验证的是哪个**因果假设**，还是只是在**试哪个值更好**？

### 气味信号（任一命中 → 变体视为调参，搁置不入队）

| # | 气味 | 示例（全部视为调参） |
|---|------|----------------------|
| 1 | 参数增量 < 5K 且无新计算图结构 | Linear(d,1)→softmax (257 params 只是系数学习)；加一个 LayerNorm；加一个 learnable scalar |
| 2 | 变体可概括为"在 X 处加了一个 {LayerNorm / Linear(d,d) / sigmoid gate / scaling factor}" | "在 cluster token 后加了 LayerNorm" "在聚合前加了 learned weight" |
| 3 | 唯一的变化是改变数值分布 | 归一化、缩放、偏移、温度系数 —— 没有改变信息流路径 |
| 4 | 设计文档中出现"先试 X=0.1 / 可调 / 超参后续扫" | loss weight / temperature / FFN hidden dim 等超参没有推导依据 |
| 5 | 换个名字就能绕过 banned[] | banned 里有 "gate系" → 改叫 "selector" / "modulator" / "controller" 企图蒙混 |
| 6 | 变体的核心贡献可翻译为"找到一个更好的数值配置" | 跟 baseline 用完全相同的信息流，只是某处数值不同 |

### 通过标准（同时满足以下三条）

1. **有新计算图结构**：非平凡变换，不只是 element-wise / norm / scaling / softmax。新结构定义了新的信息交互方式（如 attention between things that didn't attend before、新的信息聚合路径、新的 loss 改变了优化 landscape）
2. **超参有依据**：每个数值（loss weight、hidden dim、temperature...）要么来自论文引用、要么来自理论推导、要么声明显式 ablating（"我在消融 weight 的影响，取 0/0.1/1.0 三个点"）。禁止"先试一个中间值"
3. **因果机制清晰**：可以用一句话说清"这个模块为什么能解决当前 bottleneck 的因果机制"，而不是"加了说不定有用"

### 检测流程（入队前执行，结果写入 exp_design §7 Risk Assessment 之后）

```
对每个候选变体:
  1. 闻: 对照气味信号表，逐条检查。命中任何一条 → 标记为 "smell:N" 
  2. 辩: 如果变体通过了三标准，写一句辩护（为什么虽然看起来像调参但实际不是）
  3. 判: 
     - 有气味信号但通过三标准 → 保留，辩护写入 exp_design §8 Smell Check
     - 有气味信号且不通过三标准 → 搁置，记 log_decision type=question
     - 无气味信号 → 正常入队
```

### 自检提示（AI 设计变体时的内省话术）

在写 exp_design 之前问自己：
- "如果被问到'这个 weight=0.1 哪来的'，我能给出公式/引用吗？不能 → 这就是调参"
- "这个变体如果失败了，结论是'这个机制无效'还是'这个值不合适'？后者 → 这就是调参"
- "这个变体能不能只用 config 里的一个参数开关实现（加一个 if/else 分支）？能 → 结构变更不够大"
- "同行评审会认为这是 contribution 还是 engineering trick？后者 → 搁置"

**Phase 1 产出（硬性）**：分析过程必须存档为 `pipeline/reviews/motivation_review_<ts>.md`（6 段格式见 `formats.md#4-动机审查`），供后续决策追溯。该文档是 exp_design 的上游分析，每次自主设计实验前必须生成。

## Phase 2: 设计 → 落文档

- 格式：`pipeline/designs/exp_design_<ts>.md`（7 段格式见 `formats.md#3-实验设计`）
- **容量补齐目标**：`running + claiming + waiting ≥ target_active`。从 `.tick_context.json` 读取 `queue.candidate_budget`，不得自行扩大本轮数量。
- 同批候选必须是结构上和因果假设上可区分的变体，不得通过改名、纯数值变化、seed 重复或 Phase 1 纯消融扩充数量。

## Phase 3: 实现 → 入队

```
1. 检查现有 config 是否可直接复用或仅需 YAML 参数变更
2. 如需新 model 代码: 写代码
3. 创建 config YAML: configs/<path>/<name>.yaml
4. git add + commit + push
5. sync 到所有可用服务器（见 SKILL.md「代码同步规则」）← 必须执行
6. 更新 pipeline/queue.json (追加到 gpu_queues.server-X 队尾)
7. 验证: 下次 cron tick 确认新任务正常启动
```

变体实现优先级见 SKILL.md「变体配置系统」：YAML 标志 > 新 config 子目录 > 新 model 包。

### Phase 3a: 变体独立性校验（硬性，入队前必须通过）

每个变体的 model 包和 config 必须**物理独立**，不依赖其他变体或 baseline 的代码路径。入队前逐条验证：

| # | 检查项 | 验证方法 | 失败处理 |
|---|--------|---------|---------|
| 1 | **model 包独立** | `ls framework/model/<proj>/<variant_basename>/` 存在且非空 | 不存在 → 从父包 `cp -r` 复制，确保物理独立 |
| 2 | **无跨变体 import** | `grep -r "from.*Quard_model\.\(model_\|pos\|base\)" framework/model/<proj>/<variant>/` 不应命中别人的包名 | 命中 → 改为 import 自己的包，或复制依赖代码到自己的包 |
| 3 | **config basename 全局唯一** | `find configs/ -name "*.yaml" | xargs -I{} basename {} .yaml | sort | uniq -d` 无重复 | 重复 → 重命名 basename + model 目录 |
| 4 | **config 不引用别人的 model 包** | config YAML 中 `model` 字段的值必须等于本变体的 basename | 不匹配 → 修正 config，确保指向自己的 model 包 |
| 5 | **代码不 import baseline 的内部实现** | `grep -r "from.*model_base1\b" framework/model/<proj>/<variant>/` 不应命中 | 命中 → 复制需要的工具函数到自己的 utils 模块，或改为 import 公共库 |

> **为什么这很重要**：如果变体 B 的 config 指向变体 A 的 model 包，当 A 的代码被修改/删除时，B 静默失效。更糟的是如果 A 正在 running 且你改了 A 的代码，B 的复现性就毁了。**物理复制虽然冗余，但买的是隔离性**。

此校验结果写入 exp_design §6 Implementation Checklist 末尾：
```
- [ ] Phase 3a 独立性校验通过 (model包独立/无跨变体import/config basename唯一/config指向自己)
```

## Phase 3b: Crash 自修复（闭环内闭环）

```
当自己引入的代码导致 crash 时，自主执行:
1. 读远程 crash 日志（tools/train 的最后输出 + stderr）
2. 定位根因（import 错误/语法错/config 路径错/维度不匹配/...）
3. 修复代码 → git commit → push → sync 到所有服务器
4. 重入队（reset status 回 waiting）
5. 记录 pipeline/bugfixes/bugfix_<ts>.md（格式见 formats.md#7）
6. 如果修复 3 次仍 crash → 放弃该变体，标记为 question，继续下一项
```

## Phase 4: 汇报

```
简短报告（写在 cron 会话的输出里，不阻塞执行）:
  - 分析了 N 个已完成实验，最佳 mIoU=X.XXXX (exp_name)
  - 设计了 M 个新实验，已写入 pipeline/designs/exp_design_<ts>.md
  - 已入队并同步代码到 server-X, server-Y: [id1: label1], [id2: ...]
  - pipeline 继续自主运行
```

---

# PHASE1_REACHED 后：Phase 2 消融验证流程

champion 达标后，Codex 自主生成消融方案、实现、入队并继续闭环；所有动作必须记录到设计与决策文档。

## 2.1 消融方案设计（Codex 自主执行）

```
PHASE1_REACHED:
  ├─ 停止自主实验设计（不再补队列）
  ├─ 读 champion 的 config YAML + model 代码
  ├─ 分析 champion 的架构: 列出所有关键设计选择
  │   (e.g. L1 loss, pos encoding, refine mechanism, gate type, ...)
  ├─ 对每个设计选择设计消融变体:
  │   ├─ "去掉它" → 预期掉点
  │   ├─ "替换为简单版" → 预期掉点
  │   └─ "换一种实现" → 对比
  ├─ 生成 pipeline/designs/ablation_plan_<ts>.md
  │   (格式见 formats.md#5-消融方案)
  └─ 呈现给用户，等待讨论确认
```

用户审核消融计划：
- **"这个方向不需要消融"** → 从计划中移除
- **"再加一个 XX 消融"** → 补充到计划
- **"可以开始实现了"** → 进入 2.2

## 2.2 实现 → 入队 → 继续闭环

Codex 完成消融计划审查后直接执行：

```
1. 按计划逐个创建消融变体 (config YAML + 必要代码)
2. git commit + push + sync 到所有服务器
3. 将消融实验追加到 pipeline/queue.json 队尾
4. 记录 log_decision type=ablation_batch
5. 恢复 cron 全自主闭环（监控+推送+结果分析）
```

消融实验跑完后：

```
所有消融 done_complete/done_earlystop:
  ├─ 生成 pipeline/analyses/ 终态分析（每个消融一个）
  ├─ 汇总: champion 每个设计选择的消融证据
  ├─ check_goal.py → story 要素 "Ablation" → covered
  └─ 故事闭环 → GOAL_REACHED
```

## 2.3 多 seed 验证

作为消融计划的一部分（或并行），champion 至少 2 个 seed 完成。如果 Phase 1 已经跑过，直接复用。

## Phase 2 达标后的行为

```
STORY_COMPLETE:
  ├─ 停止自主实验设计（不再补队列）
  ├─ 继续监控已在运行的实验（让他们自然结束）
  ├─ 生成 pipeline/reports/goal_reached_<ts>.md（完整证据链报告）
  ├─ 生成 docs/paper_outline.md（论文大纲草稿）
  ├─ cron 保留（仅监控，不设计新实验）
  └─ 通知用户: "[project] 目标达成! mIoU=X.XXXX, 消融证据完整, 故事闭环。"
```

---

# 决策必须落日志（硬性规则）

每次做出判断后、更新队列之前，**必须**调用 `log_decision.sh` 记录：

```bash
SKILL_DIR="${PROJECT_ROOT:-/home/songcl/3dres/project}/.claude/skills/songcl_research_pipeline"

# 例 1：选择下一批实验
bash $SKILL_DIR/log_decision.sh cluster_project next_batch \
  "B1 三 seed 已完成 (0.5012/0.4987/0.5003)，下一批跑什么？" \
  "推送 B3 detail 变体 model_base1_quard2_c2f_enc_lite_posA_l1_detail 到 server-4 gpu0" \
  "B1 均值 0.5001 > baseline 0.4956，路线有效；roadmap 下一项为 B3 detail 消融" \
  "pipeline/analyses/ 终态分析 + experiments.csv"

# 例 2：放弃某条路线
bash $SKILL_DIR/log_decision.sh cluster_project route_change \
  "posB 变体连续 2 个实验低于 baseline，是否继续该路线？" \
  "放弃 posB 路线，转回 posA 系列" \
  "posB 两次 Best 均 < baseline 0.4956，且训练不稳定" \
  "0.4901 / 0.4877 vs baseline 0.4956"

# 例 3：无法自行拍板、留给用户的问题
bash $SKILL_DIR/log_decision.sh cluster_project question \
  "B3 detail 需要新 model 包（结构性改动），是否投入开发？" \
  "留待用户确认，本轮先跑储备的 seed 变体" \
  "结构性代码改动超出配置驱动范围，成本高"
```

**要求**：
- **问题**写清当时面临的选择（含关键数字）
- **决策**写清具体动作（哪个 config、哪台服务器、哪块 GPU）
- **依据**写清判断逻辑，**证据**给出数据来源
- 未拍板的问题也要用 `type=question` 记录，让用户可追溯所有"提出过的问题"

**目标**：**持续提升模型性能，形成完整论文创新证据链。**
