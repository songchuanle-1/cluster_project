"""Deterministic fact tables. No probes, project writes, or model invocations."""
from datetime import datetime, timezone


ISSUE_LABELS = {
    "monitor_busy": "监控锁被占用，本次未查询；不能视为正常预检",
    "stop_unconfirmed": "停止未确认，保留活动记录；不作为成功终态放行依赖",
    "archive_pending": "归档未完成，保留重放记录；核对台账、分析及队列清理",
    "unreachable": "服务器不可达，实时进程与资源未知",
    "source_marker": "远端源码版本标识无法核验；检查连接、目录和挂载，不是新授权请求",
    "sync_failed": "代码同步受阻，尚未启动该实验",
    "launch_failed": "启动失败，需核对实际进程，不能盲重启",
    "process_unknown": "进程观测失败，运行数量未知；不是无训练任务",
    "admission_blocked": "准入凭据未通过核验；检查具体证据，不等同于缺少用户授权",
    "claim_uncertain": "认领或启动中断，需核对配置、PID 和日志；未授权盲重启",
    "dependency_blocked": "前置依赖尚未确认成功完成；失败或未知状态不会自动放行",
    "source_integrity": "实际源码与提交内容不一致或无法核验；保留现场，不自动覆盖",
}


def clean(value):
    if value is None or value == "":
        return "未知"
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def table(headers, rows):
    return ["| " + " | ".join(headers) + " |",
            "|" + "|".join("---" for _ in headers) + "|",
            *["| " + " | ".join(clean(v) for v in row) + " |" for row in rows]]


def render(context, notes=None):
    notes = notes or {}
    for key in ("actions", "decisions"):
        if key in notes and (not isinstance(notes[key], list) or
                             not all(isinstance(v, str) for v in notes[key])):
            raise ValueError("Report notes must contain lists of strings")
    final_notes = all(notes.get(key) for key in ("actions", "decisions"))
    q = context.get("queue", {})
    active = q.get("monitored_active_tasks", q.get("active_tasks"))
    observed = isinstance(active, list)
    active = active or []
    preflight = context.get("preflight", {})
    metric = context.get("goal", {}).get("metric") or {}
    generated = context.get("generated_at")
    try:
        age = int((datetime.now(timezone.utc) - datetime.fromisoformat(generated)).total_seconds())
    except (ValueError, TypeError):
        age = None
    lines = [f"# Research Pipeline Report - {context.get('project', 'unknown')}",
             f"快照时间：{clean(generated)}；生成报告时快照年龄：{clean(age)} 秒；模式：{context.get('mode')}",
             "", "## 0. Goal Status",
             f"- 目标：{clean(metric.get('name'))} / {clean(metric.get('target'))}；数据集：{clean(metric.get('dataset'))}",
             f"- 目标检查返回码：{clean(preflight.get('goal_rc'))}",
             "- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。",
             "```text", str(preflight.get("goal_output") or "本轮未取得目标检查结果。").strip(),
             "```", "", "## 1. GPU Overview",
             "- 仅列授权卡；未采集利用率、显存或进程时标为未知，不推断空闲。"]
    gpu_rows = []
    for server in q.get("servers", []):
        for gpu in server.get("allowed_gpus", []):
            gpu_rows.append([server["name"], gpu, None, None, None])
    lines += table(["Server", "GPU", "Util", "Memory", "Process"],
                   gpu_rows or [[None] * 5])
    lines += ["- 可用 GPU：未做实时占用确认，不能据此分配。",
              "- 监控摘要（begin 已执行，不再重复探测）：", "```text",
              str(preflight.get("monitor_output") or "本轮未取得监控结果。").strip(), "```",
              "", "## 2. Running Experiments"]
    rows = []
    for task in active:
        if task.get("status", task.get("state")) != "running":
            continue
        rows.append([task.get("id", task.get("exp_id")), task.get("config"),
                     task.get("server"), task.get("gpu"), task.get("epoch"),
                     task.get("best_miou"), task.get("acc50"), task.get("spmiou"),
                     task.get("no_improve"), "登记运行；实时进度须核实"])
    lines += table(["ID", "Config", "Server", "GPU", "Epoch", "Best mIoU",
                    "Acc@50", "spmIOU", "No-Impr", "Status"],
                   rows or [["无" if observed else None] + [None] * 8 +
                            ["队列无登记运行；远端进程须另核实" if observed else "本轮未检查"]])
    lines += ["", "## 3. Queue Status"]
    queued = [t for t in active if t.get("status", t.get("state")) in ("waiting", "claiming")]
    rows = [[i, t.get("id", t.get("exp_id")), t.get("config"),
             t.get("status", t.get("state")), ",".join(t.get("depends_on") or []) or "-",
             t.get("server")] for i, t in enumerate(queued, 1)]
    lines += table(["Position", "ID", "Config", "Status", "Depends On", "Server"],
                   rows or [[None, "无" if observed else None, None,
                             "无排队" if observed else "本轮未检查", None, None]])
    lines += [f"- 活跃 {clean(q.get('active_count'))}（运行 {clean(q.get('running_count'))} / "
              f"认领 {clean(q.get('claiming_count'))} / 等待 {clean(q.get('waiting_count'))}）"
              f"；目标 {clean(q.get('target_active'))}；准入预算 {clean(q.get('candidate_budget'))}。"]
    research = context.get("research_work", {})
    if preflight.get("operational_issues"):
        lines += ["- 本次执行故障（不等于缺候选或缺授权）："]
        lines += table(["服务器", "实验", "故障"], [
            [item.get("server"), item.get("task"), ISSUE_LABELS.get(item.get("reason"), "未知执行故障")]
            for item in preflight["operational_issues"]])
    if research.get("reserve_target") is not None:
        lines += [f"- 研究储备 {clean(research.get('reserve_count'))} / "
                  f"{clean(research.get('reserve_target'))}；储备准备预算 "
                  f"{clean(research.get('reserve_budget'))}，不增加训练并发或启动授权。"]
    if research.get("pending_count") is not None:
        lines += [f"- 储备只计可推进候选及已排队项；另有待人工 "
                  f"{clean(research.get('human_wait_count'))}、待资源 "
                  f"{clean(research.get('resource_wait_count'))}、数值诊断待解 "
                  f"{clean(research.get('research_wait_count'))}、未分类阻塞 "
                  f"{clean(research.get('unclassified_block_count'))}。"]
        lines += [f"- 非终态候选与排队项合计 {clean(research.get('pending_count'))}；"
                  f"总上限 {clean(research.get('pending_limit'))}。"
                  "阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。"]
    funnel = context.get("research_funnel", {})
    if funnel.get("observed"):
        stages = " / ".join(f"{clean(k)}={clean(v)}" for k, v in funnel.get("stages", {}).items())
        scopes = " / ".join(f"{clean(k)}={clean(v)}" for k, v in funnel.get("rejected_scopes", {}).items())
        lines += [f"- 候选累计记录 {clean(funnel.get('candidate_records'))}：{stages}。",
                  f"- 否决范围：{scopes or '无登记'}；实现修订累计 "
                  f"{clean(funnel.get('implementation_revisions'))}；收据文件 "
                  f"{clean(funnel.get('receipt_files'))}（含修订或重试，不代表成功率）。"]
    if research.get("deferred"):
        reason = ("非终态候选总数已达上限" if research.get("deferred_reason") == "pending_limit"
                  else "已排队项占满准备目标")
        lines += [f"- 研究等待：{reason}，且仅有未到复查时间的已举证阻塞；复查条件时间 "
                  f"{clean(research.get('deferred_until'))}，不代表已解锁或获得启动授权。"]
    if research.get("human_actions"):
        lines += ["- 待人工确认（列出动作不代表已授权）："]
        lines += table(["ID", "Required Confirmation", "Retry After"], [
            [item.get("id"), item.get("next_action"), item.get("retry_after")]
            for item in research["human_actions"]])
    lines += ["", "## 4. This Tick's Actions"]
    default_actions = ["begin 已执行监控和目标检查；此表基于该快照，不代表 tick 结束时的实时状态。",
                       "本报告尚未执行 postflight，结果以 finish 命令及收据为准。"]
    if context.get("mode") == "steady":
        default_actions.append("无新增可处理事件；直接生成报告，不重复设计或改写未变记忆。")
    else:
        default_actions.append("研究动作待本轮执行后通过 notes 补充，不能把此初始报告作为研究完成证明。")
    lines += ["- " + clean(x) for x in notes.get("actions", default_actions)]
    lines += ["", "## 5. Decisions Made"]
    lines += ["- " + clean(x) for x in notes.get("decisions", [
        "本轮无新决策。" if context.get("mode") == "steady" else "研究决策尚未填写。"])]
    if context.get("mode") != "steady" and not final_notes:
        lines += ["", "<!-- RESEARCH_NOTES_PENDING -->"]
    lines += ["", "Next tick: 以已保存自动化为准；本脚本未读取调度时间。", ""]
    return "\n".join(lines)
