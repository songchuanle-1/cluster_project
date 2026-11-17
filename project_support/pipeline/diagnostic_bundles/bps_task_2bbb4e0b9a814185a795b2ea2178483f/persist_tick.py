"""Persist this tick's native directional diagnostics without changing gates."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
from pipeline_monitor import log_decision

PROJECT = Path("D:/project/cluster_project")
PIPE = PROJECT / "pipeline"
BUNDLE = Path(__file__).resolve().parent
TOKEN = "2bbb4e0b9a814185a795b2ea2178483f"
owner = tick.load(PIPE / "headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
assert not (BUNDLE / "summary.json").exists(), "Never replay this persistence"
head = tick.load(BUNDLE / "task_head_result.json")
mask = tick.load(BUNDLE / "mask_direction_result.json")
resolution = tick.load(BUNDLE / "resolution_result.json")
assert head["complete"] and mask["status"] == "completed"
assert all(tick.load(BUNDLE / (name + "_execution.json"))["returncode"] == 0
           for name in ("task_head", "mask_direction"))
assert head["checkpoint_sha256"] == mask["native_result"]["checkpoint_sha256"] == (
    "f17f2ec3b08422f033a6683a4030bff1d69a1112514c6ac96dcb38870be735fd")


def difference(left, right):
    if isinstance(left, dict):
        assert left.keys() == right.keys()
        return max([difference(left[key], right[key]) for key in left], default=0)
    if isinstance(left, list):
        assert len(left) == len(right)
        return max([difference(a, b) for a, b in zip(left, right)], default=0)
    if isinstance(left, (float, int)) and not isinstance(left, bool):
        return abs(left - right)
    assert left == right
    return 0


expressions = [e for row in head["rows"] for e in row["trials"][0]["task_calibration"]["expressions"]]
heads = [row["trials"][0]["task_calibration"]["fixed_head"] for row in head["rows"]]
hs = {
    "groups": len(head["rows"]), "expressions_per_trial": len(expressions),
    "forwards": 2 * len(head["rows"]),
    "native_repeat_failures": sum(not row["pass_repeat1e6"] for row in head["rows"]),
    "source_identity_failures": sum(not row["pass_native_identity1e6"] for row in head["rows"]),
    "analytic_max_delta": max(row["trials"][0]["task_calibration"]["analytic_autograd_max_delta"] for row in head["rows"]),
    "fixed_head_identity_max_delta": max(h["head_identity_max_loss_delta"] for h in heads),
    "whole_task_readout_repeat_max_delta": max(
        difference(row["trials"][0]["task_calibration"], row["trials"][1]["task_calibration"])
        for row in head["rows"]),
    "peak_allocated_mib": head["peak_allocated_mib"], "roles": {},
}
for role in ("main_secondary", "relation_other", "fractional_secondary", "fractional_repelling"):
    active = [e["role_task_alignment"][role] for e in expressions if role in e["role_task_alignment"]]
    effects = [h["conditions"][role]["effects"] for h in heads if h["conditions"][role]["effects"] is not None]
    hs["roles"][role] = {
        "active_expressions": len(active),
        "mask_opposed_expressions": sum(e["mask"]["dot"] < 0 for e in active),
        "indicator_opposed_expressions": sum(e["indicator"]["dot"] < 0 for e in active),
        "combined_opposed_expressions": sum(e["mask_plus_indicator"]["dot"] < 0 for e in active),
        "active_groups": len(effects),
        "fixed_head_measured_combined_increase_groups": sum(e["mask_plus_indicator"]["descent_loss_delta"] > 0 for e in effects),
    }
original = [h["conditions"]["original"]["effects"] for h in heads]
hs["whole_semantic"] = {
    "mask_descent_increase_groups": sum(e["mask"]["descent_loss_delta"] > 0 for e in original),
    "combined_descent_increase_groups": sum(e["mask_plus_indicator"]["descent_loss_delta"] > 0 for e in original),
    "mask_fd_failures1e6": sum(e["mask"]["central_absolute_error"] > 1e-6 for e in original),
    "combined_fd_failures1e6": sum(e["mask_plus_indicator"]["central_absolute_error"] > 1e-6 for e in original),
}
mrows = mask["rows"][::2]
queries = [q for row in mrows for q in row["matched_queries"] if q["available_events"]]
ms = {
    "groups": len(mrows), "forwards": 2 * len(mrows), "matched_event_queries": len(queries),
    "native_repeat_failures": sum(not row["pass_repeat1e6"] for row in mask["native_result"]["rows"]),
    "max_gradient_repeat_delta": max(row["gradient_repeat_max_delta"] for row in mask["rows"][1::2]),
    "max_component_identity_delta": max(row["component_identity_abs_delta"] for row in mask["rows"]),
    "peak_allocated_mib": mask["native_result"]["peak_allocated_mib"], "conditions": {},
}
for name in ("original", "identity", "oracle"):
    active = [row["conditions"][name] for row in mrows if row["conditions"][name]["gradient_norm"]]
    ms["conditions"][name] = {
        "active_groups": len(active),
        "analytic_opposed_groups": sum(c["task_dot"] < 0 for c in active),
        "measured_task_increase_groups": sum(c.get("descent_task_delta", 0) > 0 for c in active),
        "derivative_failures1e6": sum(c["pass_derivative1e6"] is False for c in active),
        "max_derivative_error": max([c.get("finite_difference_abs_error", 0) for c in active], default=0),
        "active_queries": sum(q["conditions"][name]["mask_gradient_norm"] > 0 for q in queries),
        "opposed_queries": sum(q["conditions"][name]["task_dot"] < 0 for q in queries),
    }
remote_code = """
import json,datetime,subprocess
r={'remote_time':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'hostname':subprocess.check_output(['hostname'],text=True).strip()}
assert r['hostname']=='das'
r['gpu']=subprocess.check_output(['nvidia-smi','-i','7','--query-gpu=uuid,memory.used,memory.free,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert 'GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a' in r['gpu']
r['compute']=subprocess.check_output(['nvidia-smi','-i','7','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],text=True).strip()
r['locks']={p:subprocess.run(['flock','-n',p,'true']).returncode for p in ['/tmp/cluster_project_gpu7_exclusive.lock','/tmp/cluster_project_gpu7_diagnostic.lock','/tmp/cluster_project_gpu7_slot2_diagnostic.lock']}
p='/data3/songcl/Project/Cluster_project/Cluster/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps_20261014_095849.log'
lines=subprocess.check_output(['tail','-c','2097152',p],text=True).splitlines()
r['training_tail']=lines[-4:];r['recent_metrics']=[x for x in lines if x.startswith(('mIOU:','spmIOU:'))][-4:]
print(json.dumps(r))
"""
remote = subprocess.run(
    ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "songcl@100.64.3.28", "python3", "-"],
    input=remote_code, capture_output=True, text=True, encoding="utf-8", timeout=40,
)
resource = {"local_observed_at": datetime.now().astimezone().isoformat(),
            "returncode": remote.returncode, "stderr": remote.stderr,
            "remote": json.loads(remote.stdout) if remote.returncode == 0 else None}
tick.save(BUNDLE / "resource_audit.json", resource)
summary = {
    "token": TOKEN, "recorded_at": datetime.now().astimezone().isoformat(),
    "checkpoint_sha256": head["checkpoint_sha256"],
    "task_head": hs, "mask_direction": ms,
    "resolution": {key: value for key, value in resolution.items()
                   if key not in ("measurements", "complement_rows")},
    "forwards": hs["forwards"] + ms["forwards"],
    "new_candidates": 0, "new_admissions": 0, "new_training_launches": 0,
    "optimizer_steps": 0, "requested_or_accumulated_model_parameter_gradients": 0,
    "scientific_scope": "Local fixed-head/isolated-mask responses only. Exact repeats and analytic identity do not clear FD1e-6 failures, old source failures, global task harm, full-model intervention, trained efficacy or independent structural admission.",
}
summary_path = BUNDLE / "summary.json"
tick.save(summary_path, summary)
decision = log_decision(
    str(PROJECT), "other", "语义吸引/GT配对oracle活动是否意味着一致的原生任务更新？",
    "保留局部方向不一致及有限差分FAIL；不从局部组件外推完整语义更新伤害，不启动PCGrad/权重/分母/优先级或裸oracle修复。",
    "MAIN组合相反2/8、fractional5/19，完整原始语义组合下降实测无增加0/25；互补147比较误差6.73e-13。原关系127活跃查询24相反，oracle208/60；主FD失败549/758，其中339处于最终标量量化预算内也不改PASS。",
    str(summary_path),
)


def ref(path):
    return {"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)}


work_path = PIPE / "research_work.json"
work = tick.load(work_path)
bps = next(c for c in work["candidates"] if c["id"] == "m95-native-between-pair-support")
assert bps["stage"] == "training"
paths = sorted(path for path in BUNDLE.iterdir() if path.is_file()) + [
    PIPE / "designs" / name for name in (
        "bps_task_head_prereg_20261014_1414.md",
        "bps_mask_direction_prereg_20261014_1416.md",
        "bps_direction_resolution_prereg_20261014_1425.md",
    )
] + [Path(decision)]


def bind(candidate, files):
    known = {(e["path"], e["sha256"]) for e in candidate["evidence"]}
    for path in files:
        entry = ref(path)
        if (entry["path"], entry["sha256"]) not in known:
            candidate["evidence"].append(entry)
            known.add((entry["path"], entry["sha256"]))


bind(bps, paths)
bps["supplemental_task_direction_diagnostic"] = {
    "status": "local_directions_measured_primary_FD_failures_retained", "summary": ref(summary_path)}
bps["execution_status"] = "Current2bbb tick:50nativehead+96maskforwards/CPUresolution/0optimizer/newcandidate/admission/launch. Head/mask exact native repeats;primaryFD1e-6failures retained. M201 training continues;closure not yet run."
bps["scientific_scope"] += " Currentfixednativeepoch4 mask-task direction original127activequeries24opposed/oracle208active60opposed;localmask-onlynotmodelharm. FDfail8of21original/20of44oracle retained;notoraclerepair/efficacy."
scalar_files = [BUNDLE / name for name in (
    "task_head.py", "run_remote.py", "task_head_execution.json", "task_head_pull.json",
    "task_head_result.json", "resolution_controls.py", "resolution_result.json",
    "summary.json", "persist_tick.py",
)] + [PIPE / "designs/bps_task_head_prereg_20261014_1414.md",
      PIPE / "designs/bps_direction_resolution_prereg_20261014_1425.md"]
for cid, role in (
    ("m95-native-main-role-weight-precedence", "main_secondary"),
    ("m95-native-relation-other-sign-conflict", "relation_other"),
    ("m95-native-secondary-positive-mass", "fractional_secondary"),
):
    candidate = next(c for c in work["candidates"] if c["id"] == cid)
    assert candidate["stage"] == "validation" and all(not gate["passed"] for gate in candidate["gates"].values())
    bind(candidate, scalar_files)
    candidate["task_head_diagnostic"] = {
        "status": "executed_FD_limit_retained_not_admitted", "role": role,
        "readout": hs["roles"][role], "summary": ref(summary_path)}
    candidate["execution_status"] = "Current2bbb fixed25groups97expr50nativeforwards;finaltensor identity/capturedheads/role-local task directions and fixedhead interventions executed. Exact native/readout repeats, analytic max2.629e-8;FD1e-6failures and old fullforwardFAILs retained. No parameter update or new core admission."
    candidate["scientific_scope"] += " CurrentfixedM201epoch4 task-head local response:MAINcombinedopposed2of8/REL0of9/fractional5of19;fullsemanticcombinedmeasuredincrease0of25. Partial role+complement identity6.73e-13;FDfailuresremain,notglobalharm or independent repair."
    candidate["next_action"] = "Preserve original source facts, M95 failures and frozen M201 checkpoint diagnostics including finite-difference limits and complete-versus-partial direction controls. Continue only a separately falsifiable structural/task-level control or converged original VAL evaluation when available. Do not infer independent core or launch PCGrad/weight/priority/mass tuning from local opposition."
tick.save(work_path, work)
notes = {
    "actions": [
        "本轮design快照2026-10-14 14:08:04+08，截止15:08:04不变；归属/GPU7两槽/18约束11禁令/后台Disabled/PDC用户改动哈希核实；无重复preflight。",
        "先续三条旧scalar：固定epoch4原检查点与25组97表达式/50前向，最终tensor身份、原生loss身份、mask/logit梯度重复通过；analytic最大误差2.629e-8，固定头identity0。局部MAIN组合相反2/8、REL0/9、fractional5/19，完整语义组合实测增加0/25；不是模型更新或全局伤害。",
        "BPS固定48组40场景192表达式/96前向，孤立掩码梯度与原生BCE+Dice任务方向：原127活跃查询24相反，oracle208活跃60相反；组层原4/21 analytic相反但实测增加2/21，oracle15/44与13/44。身份/梯度重复0；原始relation组件照常返回模型。",
        "主有限差分1e-6FAIL保留：原关系8/21、oracle20/44；所有固定头/掩码可测方向合计549/758超阈值。CPU分辨率339个失败位于最终标量量化预算内也不改PASS；不能解释剩余全部误差。互补147比较最大误差6.73e-13，13个部分反向但整体同向。",
        "本轮146次原生前向/CPU辅助控制，无优化器、请求或累积模型参数梯度、新候选/模型/准入/训练启动。两个远端任务均已结束；即时训练、GPU、外部进程及三锁证据见resource_audit.json，本地/远端时钟分别记录。",
        "科学状态BPS=training/补充diagnosis、三scalar=validation且六门槛false，旧FAIL不覆盖。本报告postflight尚未执行；前轮确实abort1于13:42:44释放，context未提交/锁和pending不存在已核实。本轮执行及用量由收据后在任务报告补充，缺失记未知。",
    ],
    "decisions": [
        "语义吸引不等于任务方向一致；局部部分相反也不等于完整语义更新有害。不据此扩展PCGrad/权重/分母/优先级变体，原训练和所有约束不变。",
        "Oracle增加活动但也增加孤立任务方向相反；真实见证、独立结构、模型参数级因果控制及VAL效应仍未知。主1e-6有限差分失败不能被量化解释或重复通过覆盖。",
        "容量缺口和三validation状态未改变，已知收尾拒绝条件未修复；不为通过验收而造假闭合/冷却、等待凑截止或重复相同失败。保留真实证据后按契约收尾。下一调度时间未知。",
    ],
}
notes_path = PIPE / "reports" / ("notes_" + TOKEN + ".json")
tick.save(notes_path, notes)
report = tick.report("cluster_project", TOKEN, str(notes_path))
print(json.dumps({"summary": summary, "resource": resource, "report": str(report),
                  "bps_evidence_count": len(bps["evidence"]), "decision": decision},
                 ensure_ascii=False, indent=2))
