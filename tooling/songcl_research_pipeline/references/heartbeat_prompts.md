# 前台定时任务提示词

本文件保存四个研究任务的简短入口；执行细节维护在 `foreground.md`、
`experiment_first.md` 和 `closure.md`。
普通 tick 不读取其他项目提示词，不把历史结果、哈希清单或整套执行规程塞回提示词。

## 维护规则

- 代码块逐字对应已保存任务的 `prompt`；修改时同步调用 `automation_update`，不手写 automation.toml。
- 默认保留频率、绑定会话、启停和通知偏好；仅按用户明确要求改变频率，暂停任务不自动恢复。
- 更新后读取实际配置核对文本和元数据；项目归属同时以 execution_mode.json 核验。

## cluster-tick

```text
仅处理 cluster_project。PROJECT_ROOT=D:/project，PYTHONDONTWRITEBYTECODE=1，使用 python -B。读取 C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/SKILL.md 的前台规则及 references/experiment_first.md；核验实际会话归属并接续 pipeline/codex_memory.md。
每轮先查进展、派发已有任务；按本轮快照在待跑不足时实现变体，以原生 YAML 做真实最小检查，通过后当轮入队，有授权空闲资源就启动。复用项目内操作授权，挂起候选不阻断其他工作；不跨项目、不改资源边界、禁用项或调度，不动既有运行。
按 foreground.md 收尾。仅实质进展、完成、失败或需用户处理时，用“运行、完成、新准备、需处理”简报；无变化且无可行动事项时静默。
```

## lighttext-tick

```text
仅处理 lighttext_project。PROJECT_ROOT=D:/project，PYTHONDONTWRITEBYTECODE=1，使用 python -B。读取 C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/SKILL.md 的前台规则及 references/experiment_first.md，接续 pipeline/codex_memory.md 和 pipeline/research_direction.md；核验实际会话归属。
每轮先查进展、派发已有合格任务；现有运行、队列和已准备储备按原契约接续，不因路线变更删除、改序或重启。新设计按2026-10-30用户授权聚焦“固定四层文本下的候选对条件描述回读”，不再为补数量泛换注意力核或仅堆排序损失。
按研究方向文件先补已有纯四层checkpoint的同协议逐样本对照、再做预先固定的TRAIN诊断，按可区分假设推进一个初版原型；不重跑相同旧诊断、不以草案为已验证创新、不重开已拒绝路线。遵守本轮创建/储备/准入预算，预算为零不另建候选。
以原生 YAML/main 做真实至少两步TRAIN有限loss/backward、路径更新及资源/独立性检查，通过后当轮保存测试版本、准入入队并尝试既有派发，有授权真实空槽才启动并核验增长。复用项目内操作授权，挂起候选不阻断其他合法工作；不跨项目，不改目标、资源边界、数据/seed/schedule、禁用项、Phase2限制或调度，不动既有运行。
按 foreground.md 收尾。仅实质进展、完成、失败或需用户处理时，用“运行、完成、新准备、需处理”简报；健康运行/排队无变化且无可行动事项时静默。
```

## adares-tick

```text
仅处理 AdaRES_project，不是 AdaQ3D_project。PROJECT_ROOT=D:/project，PYTHONDONTWRITEBYTECODE=1，使用 python -B。读取 C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/SKILL.md 的前台规则及 references/experiment_first.md；核验实际会话归属。
每轮先查进展、派发已有任务；按本轮快照在待跑不足时实现变体，以原生 YAML 做真实最小检查，通过后当轮入队，有授权空闲资源就启动。依据本会话2026-11-15最新指令，暂停 AdaRES 对 server-1 的全部GPU实验，包括原生检查、派发、训练和冻结后评/成本；恢复须用户明确重新授权，覆盖2026-10-25的server-1资源授权。server-2 GPU1继续按2026-11-04指令暂停全部使用，恢复也须单独明确重新授权。当前仅可用 server-2 GPU0，保持280W，每卡一个独立实验；保留server-1既有350W设置，不改功耗或硬件。保留现有原进程、原产物及原运行收据；已自然结束的实验仅做只读精确终态核验和归档，不重启、不把日志结束当作完整checkpoint校验。原要求server-1或GPU1的冻结后评/成本继续挂起，不擅自迁移或替换资源；Y57实验本身继续单独用户暂停，恢复须单独明确授权；禁止server-6。复用项目内操作授权，挂起候选不阻断其他获准工作；保留原数据协议、禁用项、现有运行及专用恢复要求，不跨项目，不改变调度频率。使用已验证的项目独立运行环境、精确原数据和部署路径映射。当前资源以最新AGENTS、SERVERS.yaml、pipeline/authorizations/server1_pause_20261115_ce356360782a431ab9adc3e015f7d5aa.json及pipeline/authorizations/server2_gpu1_pause_20261104.json为准，保留科学goal字节和原运行收据。
按 foreground.md 收尾。仅实质进展、完成、失败或需用户处理时，用“运行、完成、新准备、需处理”简报；无变化且无可行动事项时静默。
```

## multiview-tick

```text
仅处理原 multiview_project，不操作论文项目。PROJECT_ROOT=D:/project，使用 python -B；先读 C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/SKILL.md 的前台规则及 references/foreground.md。
按最新目标、资源、授权及紧凑快照推进合法到期工作；保留阶段冻结，D99已完成不重开或追加训练，M92不恢复，D98真人审查不代签。不跨项目或改调度。
按契约保存完整六段报告并收尾；通知时按 references/visible_reporting.md 输出中文简报：结论、实验进展、本轮成果、下一步或需确认事项。仅实质发现、准入、完成/失败或需用户决定时通知，健康无变化保持静默。
```
