# 自主实验设计与闭环 — songcl_research_pipeline

启用 `pipeline/closure_policy.json` 的项目必须执行 `references/closure.md`。
未完成候选以稳定 ID 保存到 research_work.json；event 续做具体阶段，
不要因新增 review/design 就将仍缺原生验证的工作判作闭环。
新入队任务必须具有机器可校验的准入 receipt；训练闭环必须观察步数增长。

cron tick 会话的行为准则。触发条件：**running + claiming + waiting < 可用容量槽位数 + design_buffer** 时，Codex 按缺口自主完成实验设计 → 实现变体 → 补充队列。全部文档格式见 `references/formats.md`。

> **可用卡数定义**（不要搞混）: = 该项目 SERVERS.yaml 中 `dispatch_enabled != false` 的 gpu_server **容量槽位总和** = Σ(白名单卡数 × `max_tasks_per_gpu`)（**容量，固定值**），≠ 当前空闲卡。当前 cluster server-6 [7]（max=2）→ 2；server-4 已从本项目白名单移除，容量0。multiview server-6 [4]（max=2）→ 2。不配 `max_tasks_per_gpu` 时每卡按 1 槽位算。"空闲卡"(util<10%且显存<1GB；单卡多任务模式下=槽位未满且显存余量满足项目 `task_memory_mb`) 只决定**推送时机**，不进深度公式。所有数值始终以项目 `SERVERS.yaml` 为准。

> **候选预算定义**：`active_count = running + claiming + waiting`；`target_active = capacity + design_buffer`；`candidate_budget = min(max_candidates_per_design_tick, max(0, target_active - active_count))`。设计模式以 `candidate_budget` 为本轮目标数量。只有通过诊断、匹配对照、原生前后向、资源、独立性和目标约束这些硬门槛，并完成独立实现和测试的候选才能入队。完整理论推导和文献新颖性检索是建议项，不得单独阻塞实验；未完成时必须记录局限，且不得宣称已证明新颖。合格候选少于预算时允许留空，必须记录每个未入队候选的淘汰原因。

> **储备与训练分离**：启用闭环且已授权缺口研究的项目，默认保留2个待续候选，
> 即使训练满载也可进入 `reserve_only` 准备模式。储备预算不增加 `candidate_budget`，
> 不允许新增队列项或启动训练；旧候选、阻塞项和等待任务计入储备，避免无限扩池。
> 阶段冻结和项目禁令不变。按 `closure.md` 的 Research Reserve 执行。
> 储备已满、准备预算为0且所有待续项仅有未到期的已证实外部阻塞时，不新建
> bootstrap 候选；首次或变化后的等待走 event 校验，无变化才走 steady。
> 到期、真实授权/资源/证据变化仍须唤醒；未知阻塞或可执行候选不能被掩盖。

> **候选优先启动（硬性）**：当 `mode=design`、`candidate_budget>0` 且
> `research_work.due_ids` 为空时，本轮必须在任何大范围路线审查或 abort
> 之前，先建立至少一个稳定的 `diagnosis` 候选。候选即使尚未完成完整
> 理论推导也必须进入账本；`id`、`hypothesis`、`matched_control`、
> `next_action` 和至少一个 hashed evidence 是启动字段，六项准入 receipt
> 仍是入队前门槛。概念上与旧路线相近不等于重复；若怀疑重复，必须在本轮
> 执行最低成本的区分性测试并留下反证，之后才能 reject、推进或建立下一个
> 独立候选。没有 tested candidate progress 的“路线已穷尽/没有新机制”
> 不是可完成 disposition，不能用来结束 design tick。

**未准入时继续做实事**：`candidate_budget` 是本轮目标准入数，不是只允许尝试一次设计。对可执行的证据缺口，立即建立稳定候选 ID 并在 `pipeline/research_work.json` 写入阶段、证据哈希和下一项具体测试；本 tick 资源/时间允许时继续执行原生对照、资源测量及实现测试。失败有反证则记录并筛选另一个独立假设；单纯缺测试不能判作路线失败。tick 因时间结束时允许留空，但必须留下已执行的测试结果和可续做任务，下一轮 event 先续做，直到准入成功或有明确的反证/不可用资源。不得绕过硬门槛、制造假 PASS 或承诺必然成功。

**同轮准入循环**：有容量缺口且进入 design 时，先续做 `research_work.due_ids`，然后在本 tick 内反复执行“下一项可执行诊断/对照/原生及资源测试 → 逐门槛审查 → 准入或带证据淘汰 → 下一个结构独立假设”。`candidate_budget` 只限制本轮最多新增多少合格任务，不限制诊断/筛选尝试。一个候选未通过、一次测试完成或一次阶段转换都不是本轮结束条件。只有达到准入目标、可区分且有依据的路线已穷尽、必需资源确实不可用、目标阶段明确禁止设计或接近 tick 时间上限，才可停止；在报告中逐项写明已做的测试、失败证据、未完工作的稳定 ID 与明确恢复条件。不得重复同一失败路线、无限试错、制造占位变体或为填满 GPU 降低硬门槛。

**训练前门槛校准（硬性）**：六个硬门槛（diagnosis / controls /
native_backward / resources / independence / constraints）验证真实且可证伪的
机制、对照、原生训练路径、资源及目标约束，不要求新变体在训练前达到固定
任务收益（如 +0.05/+0.02）、小样本显著性或验证 mIoU 增益。预先冻结机制
读数、匹配对照、采样单位、重复性和预期方向；真实无效、反向或无法解释的
有害原生结果不能靠删除阈值获得 PASS。一批数据只能证明机制活动，不能证明
泛化收益。启动前冻结训练后比较方案：ScanRefer mIoU、champion/baseline、
评估划分、场景聚类单位、有意义子组的预注册伤害规则及轻量化 Pareto 约束。
噪声底限由独立重复或恰当配对参照估计；无数据则如实标注未量化。场景不足、
区间跨决策边界时标为不确定并补证据，单个场景下降仅触发诊断，不自动否决。
旧冻结/拒绝原样保留；仅因废弃幅度门槛失败的路线可用原稳定 ID 重审其余反证
并预注册补测，绝不自动改 PASS、改名重入队或干扰运行中的训练。详见
`references/closure.md` 的 Gate Calibration。

核心原则：
1. **授权内自主执行** — 已有授权的研究不重复审批；缺少所需权限时，明确候选、
   文件范围和操作，一次性向所属会话交接确认并保留证据等待，绝不自行授权。
   用户在本会话的无歧义确认按项目契约留档，不要求固定口令或用户手写JSON。
   未变阻塞不反复催问；本地提交许可不等于推送、准入或训练许可。
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

### 气味信号（触发审查，不单独证明机制失败）

| # | 气味 | 示例（需结合实际信息流审查） |
|---|------|----------------------|
| 1 | 参数增量 < 5K 且无新计算图结构 | Linear(d,1)→softmax (257 params 只是系数学习)；加一个 LayerNorm；加一个 learnable scalar |
| 2 | 变体可概括为"在 X 处加了一个 {LayerNorm / Linear(d,d) / sigmoid gate / scaling factor}" | "在 cluster token 后加了 LayerNorm" "在聚合前加了 learned weight" |
| 3 | 唯一的变化是改变数值分布 | 归一化、缩放、偏移、温度系数 —— 没有改变信息流路径 |
| 4 | 设计文档中出现"先试 X=0.1 / 可调 / 超参后续扫" | loss weight / temperature / FFN hidden dim 等超参没有推导依据 |
| 5 | 换个名字就能绕过 banned[] | banned 里有 "gate系" → 改叫 "selector" / "modulator" / "controller" 企图蒙混 |
| 6 | 变体的核心贡献可翻译为"找到一个更好的数值配置" | 跟 baseline 用完全相同的信息流，只是某处数值不同 |

### 通过标准（同时满足以下三条）

以下标准用于新机制。已有机制的局部修订无需再发明一个新机制或再次满足
参数规模启发式；应记录原实现缺陷、局部因果改动及预注册对照，依照
`closure.md` 的 Implementation Revisions 在原稳定ID下有界验证。项目
goal.json 的更严格禁令仍优先；不能把纯数值扫描、验证集择优或旧路线改名
包装为修复。一次实现失败不能外推成整个机制无效。

1. **有新计算图结构**：非平凡变换，不只是 element-wise / norm / scaling / softmax。新结构定义了新的信息交互方式（如 attention between things that didn't attend before、新的信息聚合路径、新的 loss 改变了优化 landscape）
2. **超参可解释**：优先使用父配置已有默认值、结构直接决定的值或保守固定值，并明确本轮不做数值搜索。论文引用和完整理论推导是加分项，不是入队硬门槛；仍禁止用任意数值扫描伪装成结构创新。
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
- "反证针对核心假设、当前实现还是证据不足？" 先分类，不以局部失败关闭整个机制。
- "这次改动是否有缺陷证据和可区分的预测，还是只是在试哪个数值更好？" 后者仍是调参。
- "配置开关是否真正改变信息流？" 实现短小或能用开关控制本身不构成否决依据。
- "同行评审会认为这是 contribution 还是 engineering trick？后者 → 搁置"

**Phase 1 产出（硬性）**：分析过程必须存档为 `pipeline/reviews/motivation_review_<ts>.md`（6 段格式见 `formats.md#4-动机审查`），供后续决策追溯。该文档是 exp_design 的上游分析，每次自主设计实验前必须生成。

## Phase 2: 设计 → 落文档

### Phase 2.0: 候选优先启动（硬性）

没有 due stable ID 时，先写候选，再评审路线：

1. 从当前任务缺口与最近证据中选一个**可区分**的深度假设。
2. 立即在 `pipeline/research_work.json` 建立稳定 ID，`stage=diagnosis`，
   写清 `hypothesis`、`matched_control`、`next_action` 和 hashed evidence。
3. 在同一 tick 执行该 `next_action` 的首个可执行测试；优先 CPU/source、
   单位测试或冻结协议，再按证据决定是否进入原生对照/backward/资源测试。
4. 只有测试给出反证才 reject；概念重叠、尚未实现或缺少完整推导都不能作为
   reject 依据。
5. reject 或推进后，继续下一个结构独立候选，直到达到准入目标、真实
   deadline、目标阶段 hold 或有证据的外部阻塞。

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

**信息增益边界**：持续研究不等于重复推理直到 deadline。若本轮已执行的独立测试
证明暂无新增信息，且没有被搁置的可执行候选，使用 closure.md 的有证据提前收尾
格式；finish 校验成功后进入短期冷却。不得把单次失败、未执行测试或改名的重复路线
冒充穷尽证据。冷却期间继续监控，目标/队列/证据变化或 retry 到期即重新评估。
