# 前台定时任务提示词

本文件保存四个研究任务的简短入口；执行细节只维护在 `foreground.md` 和 `closure.md`。
普通 tick 不读取其他项目提示词，不把历史结果、哈希清单或整套执行规程塞回提示词。

## 维护规则

- 代码块逐字对应已保存任务的 `prompt`；修改时同步调用 `automation_update`，不手写 automation.toml。
- 只更新提示词，保留频率、绑定会话、启停和通知偏好；暂停任务不自动恢复。
- 更新后读取实际配置核对文本和元数据；项目归属同时以 execution_mode.json 核验。

## cluster-tick

```text
仅对 cluster_project 执行一轮前台研究。PROJECT_ROOT=D:/project，使用 python -B；先读 C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/SKILL.md 的前台规则及 references/foreground.md。
以最新项目目标、资源、授权和紧凑快照续做候选，按预算准备储备、局部修订与准入；不跨项目或改调度。完整六段留档并收尾；每轮按 references/visible_reporting.md 输出中文简报：结论、实验进展、本轮成果、下一步或需确认事项。未知如实标注，不粘贴原始日志。
```

## lighttext-tick

```text
仅对 lighttext_project 执行一轮前台研究。PROJECT_ROOT=D:/project，使用 python -B；先读 C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/SKILL.md 的前台规则及 references/foreground.md。
以最新项目目标、资源、授权和紧凑快照续做候选，按预算准备储备、局部修订与准入；不跨项目或改调度。完整六段留档并收尾；每轮按 references/visible_reporting.md 输出中文简报：结论、实验进展、本轮成果、下一步或需确认事项。未知如实标注，不粘贴原始日志。
```

## adares-tick

```text
仅对 AdaRES_project（不是 AdaQ3D_project）执行一轮前台研究。PROJECT_ROOT=D:/project，使用 python -B；先读 C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/SKILL.md 的前台规则及 references/foreground.md。
以最新项目目标、资源、授权和紧凑快照续做候选，按预算准备储备、局部修订与准入；不跨项目或改调度。完整六段留档并收尾；每轮按 references/visible_reporting.md 输出中文简报：结论、实验进展、本轮成果、下一步或需确认事项。未知如实标注，不粘贴原始日志。
```

## multiview-tick

```text
仅处理原 multiview_project，不操作论文项目。PROJECT_ROOT=D:/project，使用 python -B；先读 C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/SKILL.md 的前台规则及 references/foreground.md。
按最新目标、资源、授权及紧凑快照推进合法到期工作；保留阶段冻结，D99已完成不重开或追加训练，M92不恢复，D98真人审查不代签。不跨项目或改调度。
按契约保存完整六段报告并收尾；通知时按 references/visible_reporting.md 输出中文简报：结论、实验进展、本轮成果、下一步或需确认事项。仅实质发现、准入、完成/失败或需用户决定时通知，健康无变化保持静默。
```
