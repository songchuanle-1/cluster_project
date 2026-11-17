# 实验优先模式

仅在本轮快照 `experiment_first.enabled=true` 时使用。本模式替代旧的训练前
科学准入、全路线穷尽和逐变体操作授权要求；不是取消安全检查，也不宣称创新或有效。
旧快照没有该字段时仍按旧契约完成，禁止改正在运行的快照。

## 每轮只做四步

1. 按 foreground.md 第 1、2 节核验所属会话，begin --auto-steady；
   它先查询进展、处理终态并尝试派发已有合格队列。steady 已自动完成则停止。
2. 按快照补缺口：优先完成最近可入队的候选；待跑不足时设计、实现独立变体。
   默认准备约 2 个待跑实验，每轮最多新增 2 个候选，可推进候选上限 4；
   项目更小的单轮上限、暂停、阶段限制仍生效。GPU 忙时可先做不占 GPU 的准备，
   需要 GPU 的原生检查等待授权空槽，不挤占运行中或外部任务。
3. 使用原生 YAML 及训练入口检查真实训练数据加载、至少 2 步有限 loss/backward、
   新路径确实被执行、资源预算、独立配置及数据/seed/schedule/禁用项。
   通过就保存经过测试的版本、生成准入收据、入队，并在本轮尝试现有派发入口；
   没有空闲资源就保持 waiting。启动成功仍须原生步数递增，不以 PID 代替。
4. 保存结果，按 foreground.md 第 5 节生成报告、finish 并核验释放锁。
   向用户只说：在跑什么、完成什么、新准备什么、哪些事真的需要用户处理。
   无实质变化且无可行动事项时静默。完整审计表由脚本生成，不手写六段套话。

本模式不执行 foreground.md 第 3、4 节的旧设计穷尽与全候选推进要求；
其他归属、锁、故障、资源、证据和收尾规则照常。

## 配置和一次授权

- **实验任务仍读取 YAML**：保持 queue 中 `config` 指向项目原生 YAML 的契约，
  沿用既有字段、基线、数据路径和启动命令；不把训练配置迁成 JSON，
  不在队列或提示词内复制一份互相冲突的训练参数。检查和实际训练使用同一
  YAML/代码版本，部署只允许现有策略规定的确定性路径适配。
- `closure_policy.json` 中的 `experiment_first.authorization` 引用本项目的
  哈希绑定授权。它允许本项目范围内的实验代码/配置修改、测试、保存相关版本、
  既有安全同步、入队与训练，不再为这些常规操作反复询问用户。
- 当前 goal.json、SERVERS.yaml、数据/验证边界、费用/并发限制、资源白名单、
  主线、硬预算、明确 bans 和暂停仍约束所有操作。仅旧的“论文级诊断/推导/
  原文查重/有效性证明必须先完成才能训练”和“每个变体重复操作授权”被替代。
  训练效果是待测结果，不得要求预先证明上涨，也不得把未测效果写为 PASS。
  文献与机制分析可随结果深入，不作为每次启动的硬前置。
- 不授权扩大服务器/GPU、外部付费、新数据/标注、测试集选机制、调参扫参、
  越过 Phase2 人工确认、重开 rejected/banned 路线、额外历史修订、
  重启/迁移受保护实验、驱逐任务或改调度。真实缺权限只问具体一项。
- 局部实现失败不等于整个假设失败。允许原有修订预算内的有证据修复，
  保留同一 ID 和全部负结果；已明确冻结的历史候选仍不重开。

## 简短记录和准入

候选只需稳定 ID、结构假设、所比较的基线、当前 stage、真实测试证据
`evidence=[{path,sha256}]`、明确 next_action。无需为每个候选重复生成
motivation_review 和 exp_design 长文。格式不全的旧记录不能伪造补齐。

新收据沿用原来的 id/config/code_commit/goal_sha256/decision 字段，并设置：

```json
{
  "profile": "experiment_first",
  "authorization": {"path": "pipeline/authorizations/...", "sha256": "..."},
  "native_smoke": {"path": "pipeline/checks/<id>_smoke.json", "sha256": "..."},
  "gates": {
    "native_backward": {"passed": true, "evidence": [{"path": "...", "sha256": "..."}]},
    "resources": {"passed": true, "evidence": [{"path": "...", "sha256": "..."}]},
    "independence": {"passed": true, "evidence": [{"path": "...", "sha256": "..."}]},
    "constraints": {"passed": true, "evidence": [{"path": "...", "sha256": "..."}]}
  }
}
```

四项可以引用同一份真实检查记录，不需要四份报告。native_smoke 内容包含与
收据一致的 id/config/code_commit/goal_sha256，以及 steps>=2、至少两次实测
losses、native_data_loaded=true、backward_finite=true、
intended_path_observed=true、split="train"、实际 command、data_source、
真实日志/追踪证据 evidence。这些是观察记录，不能用模型推测、合成数据、
静态检查或旧 champion 的结果代签。goal/版本/证据哈希、现有安全同步和
启动核验仍强制执行；旧收据按旧规则验证，不自动把以前的失败门槛改成 PASS。

## 挂起与收尾

挂起候选和受阻队列仍保留、展示、按条件复查，但不占可推进候选名额，
不计入可运行待跑数量。不满足依赖、dispatch_hold 或 admission_error 的
waiting 项不是就绪实验。先做其他独立候选，不靠改名重跑绕过历史结论。

不要求凑满本轮额度、不要求测试两条路线、不要求改动所有旧候选或等到 deadline。
一次真实测试有结果就可收尾；有余力且下一步安全可执行时，应继续做到入队/启动。
没有任何准入时，design 轮在 research_work.json 保存：

```json
{
  "tick_attempt": {
    "tick_started_at": "<本轮 generated_at>",
    "candidate_id": "<本轮确有证据变化的候选>",
    "kind": "native_smoke",
    "result": "failed",
    "command": "<实际运行的命令>",
    "observation": "<实测结论，不是预期>",
    "evidence": [{"path": "<本轮新产出的日志/结果>", "sha256": "..."}]
  }
}
```

kind 也可为 implementation_test 或 resource_check；result 为 passed/failed/blocked。
证据必须同时归入该候选。只改 stage、时间或文字不算进展。未做实验就如实
abort/INCOMPLETE，不伪造 PASS。未碰的可执行候选留待下轮，不需额外 tick_handoff。
单个失败不建立全局研究冷却；下小时按新的队列和资源状态继续。
