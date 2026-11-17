"""Persist the actual resource block and bounded research output, not a PASS."""
import ast
from datetime import datetime, timedelta, timezone
import json
import os
import shutil
import subprocess
from study import ROOT, OUT, CID, TOKEN, GOAL, guard, now, save, evidence, tick

guard(180)
census = tick.load(OUT / "native_resolution_result.json")
incidence = tick.load(OUT / "native_training_incidence.json")
resources = tick.load(OUT / "current_resources_and_training.json")
attempt = tick.load(OUT / "native_pair_0_result.json")
execution = tick.load(OUT / "native_pair_0_execution.json")
assert census["expected_train_scenes"] == census["loaded_train_scenes"] == census["exact_support_scenes"] == 562
assert census["small_scene_count"] == 28 and not census["failures"] and not census["sampling_unknown_scenes"]
assert incidence["native_dataset_groups"] == 9372 and incidence["native_small_scene_groups"] == 240
assert execution["returncode"] == 1 and not attempt["execution_completed"]
assert attempt["error"] == "Occupied authorized GPU;no sharing or eviction"
assert resources["server4"]["cards"]["1"]["contexts"].startswith("2292978,")
assert all(resources["server4"]["cards"]["1"]["locks_available"].values())
assert resources["server3"]["ssh_returncode"] == 255
syntax = []
for path in (OUT / "native/native_resolution_task.py", OUT / "native/native_runtime.py"):
    ast.parse(path.read_text(encoding="utf-8"))
    syntax.append({"source": evidence(path), "python_ast_parse": True,
                   "scope": "Syntax only; not native execution/control/backward PASS."})
retry = datetime.now(timezone.utc) + timedelta(hours=1)
work = tick.load(ROOT / "pipeline/research_work.json")
aux_ids = ["m95-native-relation-other-sign-conflict", "m95-native-main-role-weight-precedence",
           "m95-native-secondary-positive-mass", "m95-native-between-pair-support"]
aux = [row for row in work["candidates"] if row["id"] in aux_ids]
assert len(aux) == 4 and all(row["stage"] == "blocked" and row["blocker_kind"] == "human_authorization" for row in aux)
retry = min(retry, *(datetime.fromisoformat(row["retry_after"]) for row in aux))
analysis = save("analysis.json", {
    "created_at": now(), "candidate_id": CID, "token": TOKEN,
    "native_support_census": {key: census[key] for key in ("expected_train_scenes", "loaded_train_scenes", "exact_support_scenes", "minimum_exact_support", "maximum_points", "small_scene_count", "source_controls")},
    "native_group_incidence": {"total": 9372, "small_scene_groups": 240,
                               "realized_training_batches": None},
    "native_pair_status": "First attempt rejected by fresh live external GPU occupation before GPU locks/CUDA/setup; 4-pair protocol still pending, not a scientific failure or completed experiment.",
    "evidence": [evidence(OUT / name) for name in ("resolution_protocol.json", "native_resolution_result.json", "native_training_incidence.json", "native_resolution_protocol.json", "native_cohort_selection.json", "native_pair_0_execution.json", "native_pair_0_result.json", "current_resources_and_training.json")],
    "syntax_checks": syntax,
    "resource_status": "At23:08Shanghai server4GPU0 held by M204, GPU1 held by external user/context2292978. All3GPU1 project locks available but compute occupation independently forbids sharing. server3GPU1 occupancy UNKNOWN because SSH255/refused; not called occupied or idle.",
    "scientific_status": "Actual TRAIN incidence and exact source clamp established; task impact/noise/novel attention/efficacy UNKNOWN. No trained repair or scientific admission.",
    "mainline_scope_recheck": {"goal_sha256": GOAL, "checked_ids": aux_ids,
                               "decision": "GPU1 resource addition does not restore auxiliary supervision priority or authorize M201/CPA restart; preserve all4unchanged holds and original retry conditions."},
    "this_tick_output": {"new_stable_candidates": 1, "train_scene_files_read": 562,
                         "metadata_cpu_studies": 1, "native_paired_protocols_frozen": 1,
                         "planned_native_scene_pairs": 4, "pre_cuda_resource_rejections": 1,
                         "executed_native_mask_pairs": 0, "native_backward_runs": 0,
                         "new_models": 0, "admissions": 0, "new_training": 0},
    "retry_after": retry.isoformat(),
    "stop_scope": "Live resource block of the current prepared primary candidate, not independent route exhaustion, no-information-gain, global pause, missing GPU1 permission or expired deadline.",
})
candidate = next(row for row in work["candidates"] if row["id"] == CID)
candidate.update(
    stage="blocked", failure_scope="inconclusive",
    blocker_kind="live_external_gpu_occupation", required_server="server-4", physical_gpu=1,
    blocker="Current native attempt aborted beforeCUDA: server4GPU1 has external context2292978/7556MiB; one-task/card and no-eviction/no-sharing guard applies. GPU0 is M204; server3 SSH255/refused leaves its GPU1 unknown and unavailable, not proven occupied.",
    retry_after=retry.isoformat(),
    unblock_condition="Fresh authorized GPU1 UUID/context/idleness checks and all3exclusive locks pass; or server3 recovers with exact frozen native source/data/checkpoint/runtime and GPU1/exclusive checks. Resource availability is not scientific admission or restart authority.",
    next_action="Resume the SAME frozen 4-pair point-path resolution protocol at pair0 under a NEW current-tick lease and fresh runtime/GPU checks. Do not reuse the failed execution lease, change256/cap/threshold, relabel missing mask readouts as PASS, or evict external jobs.",
    gate_result="CPU full TRAIN incidence28/562 and source clamp controls confirmed; native conditional task controls/mask effects/backward/resources remain unpassed or unrun. 1pre-CUDAresource rejection,0GPU mask pairs,0training.",
    scientific_admission=False, updated_at=now(), non_gpu_preparation_completed=True,
    wake_paths=["SERVERS.yaml", "pipeline/goal.json"],
)
candidate["evidence"].extend([evidence(OUT / "training_incidence_protocol.json"), evidence(OUT / "native_training_incidence.json"), evidence(OUT / "current_resources_and_training.json"), evidence(analysis)])
work["design_cycle"] = {
    "updated_at": now(), "stop_reason": "external_resource_blocked", "attempted_ids": [CID],
    "evidence": [evidence(analysis), evidence(OUT / "current_resources_and_training.json"), evidence(OUT / "native_pair_0_execution.json")],
    "resume_condition": candidate["unblock_condition"], "retry_after": retry.isoformat(),
    "scope": "Prepared primary native test blocked by actual external GPU occupation; do not infer all independent research routes exhausted or call server3 idle/occupied. Existing4auxiliary scope holds unchanged.",
}
guard()
tick.save(ROOT / "pipeline/research_work.json", work)
shutil.copyfile(ROOT / "pipeline/codex_memory.md", OUT / "memory_before.md")
index = ROOT / "pipeline/decisions/_index.md"
old_index = index.read_bytes()
environment = os.environ.copy()
environment["TZ"] = "CST-8"
decision = subprocess.run(["C:/Program Files/Git/bin/bash.exe",
    "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh",
    "cluster_project", "other", "Native batch-minimum incidence; GPU1 externally occupied.",
    "Keep frozen paired audit and M204; wait for legal GPU slot.",
    "全562个TRAIN场景中28个不足256超点，原生训练分组占240/9372；GPU1实际外部占用，首对测试在CUDA前拒绝，mask影响未知。保留GPU0的M204训练，不抢卡、不改调度、不恢复旧辅助路线。",
    str(analysis)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=environment, timeout=20)
assert decision.returncode == 0, decision.stderr
assert index.read_bytes().startswith(old_index), "Never normalize old index bytes"
decision_receipt = save("decision_record_receipt.json", {"observed_at": now(),
    "returncode": decision.returncode, "stdout": decision.stdout, "stderr": decision.stderr,
    "existing_index_bytes_preserved": True, "time_zone": "Asia/Shanghai(UTC+08:00)"})
notes = save("report_notes.json", {
    "actions": [
        "快照2026-10-19 22:32:22上海；实际任务归属与旧调度Disabled已核实，仅一次begin。目标0.5100、历史最佳0.5020、差0.0080；server4GPU1已获授权，本轮没有重复索要或改变资源/科学约束。",
        "本轮新建1个稳定诊断ID hierarchy-native-batch-minimum-resolution：先冻结动机/设计/判据，再在server4原生CPU环境只读普查全部562/562个TRAIN场景，无缺失或抽样未知。最低131超点，28个场景不足256；最大537406点均未触发原生2500000抽样上限。原生训练分组为240/9372，不能把28/562当作采样频率或精度损失。",
        "执行原生源AST配对控制：大同伴256、小同伴100、换序256；padding不改有效batch_offsets的控制仍256。仅证明检测和实际层级分辨率入射，不证明mask损伤、独立创新或可训练修复。",
        "按预注册字典序冻结4大/4小场景、32表达、原M95epoch16 checkpoint与原query/匹配/目标的4对原生点路径协议；首对在新鲜GPU1占用检查处返回1，尚未取得GPU锁/初始化CUDA/重放mask。原生mask对照、任务效果及backward均未知/未执行，未将尝试算作4对完成。",
        "23:08:56上海实查：server4GPU0为原M204，19863MiB；原生日志Train19/50的3122到3126/4686增长且mtime新鲜，无近期Traceback。GPU1为外部用户任务，7579MiB/14%，项目三锁均可用但有计算上下文，仍不能共享；23:08:58 server3SSH255连接拒绝，GPU占用未知。没有驱逐、reset、重启、迁移或更改其他项目。",
        "本轮实际产出：1稳定候选、562场景原生CPU普查、训练分组分母补证、1份4对测试冻结协议、1次CUDA前资源拒绝；0已执行GPU mask对、0backward、0新模型/准入/训练/队列项。完整原始失败、资源证据、判据及哈希已保存；四项旧辅助scope hold原样保留。",
        "用量收据窗口仅从本轮begin(2026-10-19T14:32:22Z)到finish生成收据，排除更早读取、末尾回复和后到记录；此处具体用量未知，以实际收据为准，不当账单，不把缓存与输入重复相加、reasoning与输出重复相加。本报告保存时finish尚未执行，不能先称本轮完成。",
    ],
    "decisions": [
        "本轮科学状态：原生分辨率耦合的实际数据入射已证实，条件mask因果影响/总体效果/新颖性仍未知；不把源代码问题直接包装成分层注意力贡献，也不启动Phase1单算子修补或数值调参。",
        "当前稳定候选按真实live_external_gpu_occupation阻塞，非GPU准备已完成；保留原4对测试和原1e-6控制，待实际合法空闲后用新租约续做pair0。具体恢复条件和一小时内重查记录于analysis.json及research_work。不是拖到deadline、全路线穷尽或科学否定。",
        "GPU1权限已具备，缺的是实际独占资源而非再次授权；保留M204现有原生训练和全部历史失败，不自动恢复M201/M204、不把4项辅助方向因到期或空槽重新升为主线。无新用户确认需求。",
    ],
})
print(json.dumps({"candidate_id": CID, "stage": "blocked", "retry_after": retry.isoformat(),
                  "analysis": evidence(analysis), "notes": evidence(notes),
                  "decision_receipt": evidence(decision_receipt), "finish_still_required": True}, indent=2))
