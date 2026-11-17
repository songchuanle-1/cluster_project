"""Summarize genuine native evidence, bind stable IDs, and render the tick report."""

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

TOKEN = "16d02ebf70a846bdad7f1c4f4d30b0c9"
PROJECT = Path("D:/project/cluster_project")
PIPE = PROJECT / "pipeline"
BUNDLE = Path(__file__).resolve().parent
owner = tick.load(PIPE / "headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
assert tick.digest(PIPE / "headless/.tick_context.json") == owner["context_sha256"]
assert not (BUNDLE / "summary.json").exists(), "Do not replay evidence persistence"


def ref(path):
    return {"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)}


native = tick.load(BUNDLE / "result.json")
audit = tick.load(BUNDLE / "adapter_audit.json")
scalar = tick.load(BUNDLE / "scalar_result.json")
assert tick.load(BUNDLE / "execution.json")["returncode"] == 0
assert tick.load(BUNDLE / "scalar_execution.json")["returncode"] == 0 and scalar["complete"]
nrows = native["rows"]
queries = [item for row in nrows for item in row["captures"][0]["matched_event_queries"]]
ns = {
    "groups": len(nrows), "scenes": len({scene for row in nrows for scene in row["scan_ids"]}),
    "expression_appearances_per_trial": sum(len(row["ann_ids"]) for row in nrows),
    "forwards": 2 * len(nrows), "matched_event_queries_per_trial": len(queries),
    "repeat_failures": sum(not row["pass_repeat1e6"] for row in nrows),
    "decomposition_failures": sum(not row["pass_decomposition1e6"] for row in nrows),
    "max_mask_repeat_delta": max(row["mask_repeat_max_abs_delta"] for row in nrows),
    "max_loss_repeat_delta": max(row["full_loss_repeat_abs_delta"] for row in nrows),
    "max_decomposition_delta": max(c["decomposition_abs_delta"] for row in nrows for c in row["captures"]),
    "original_exact_nonzero": sum(q["normalized_component"] != 0 for q in queries),
    "oracle_exact_nonzero": sum(q["normalized_oracle"] != 0 for q in queries),
    "oracle_changes_above1e6": sum(abs(q["normalized_oracle"] - q["normalized_component"]) > 1e-6 for q in queries),
    "zero_to_positive_above1e6": sum(q["normalized_component"] == 0 and q["normalized_oracle"] > 1e-6 for q in queries),
    "negative_changes_below_minus1e6": sum(q["normalized_oracle"] - q["normalized_component"] < -1e-6 for q in queries),
    "strict_loads": len(audit["loads"]), "buffer_negative_control": audit["perturbed_buffer_negative_control"],
    "peak_allocated_mib": native["peak_allocated_mib"],
}
ss = {
    "groups": len(scalar["rows"]),
    "expression_appearances_per_trial": sum(len(row["selection"]["ann_ids"]) for row in scalar["rows"]),
    "forwards": 2 * len(scalar["rows"]),
    "repeat_failures": sum(not row["pass_repeat1e6"] for row in scalar["rows"]),
    "native_identity_failures": sum(not row["pass_native_identity1e6"] for row in scalar["rows"]),
    "max_mask_delta": max(row["max_mask_repeat_delta"] for row in scalar["rows"]),
    "max_logit_gradient_delta": max(row["max_gradient_repeat_delta"] for row in scalar["rows"]),
    "peak_allocated_mib": scalar["peak_allocated_mib"], "conditions": {},
}
for condition in ("original", "identity", "precedence", "mass", "relation_overlap_removed"):
    ss["conditions"][condition] = {}
    for subset in ("main_secondary", "relation_other", "fractional_secondary"):
        records = [row["trials"][0]["conditions"][condition] for row in scalar["rows"]]
        ss["conditions"][condition][subset] = {
            key: sum(item["subsets"][subset][key] for item in records)
            for key in ("count", "attracting", "repelling", "zero")
        }
        ss["conditions"][condition][subset]["sign_flips_from_original"] = sum(
            item["subset_sign_flips"][subset] for item in records
        )

bank_execution = tick.load(BUNDLE / "bank_execution.json")
bank = tick.load(BUNDLE / "bank_result.json")
bank_native = tick.load(BUNDLE / "bank_native_result.json") if (BUNDLE / "bank_native_result.json").exists() else None
bs = {"execution_returncode": bank_execution["returncode"], "status": bank["status"]}
if bank_execution["returncode"] == 0 and bank["status"] == "completed":
    assert bank_native is not None and len(bank["rows"]) == 2 * len(bank_native["rows"]) == 96
    first = bank["rows"][::2]
    second = bank["rows"][1::2]
    max_readout_delta = 0.0
    for left, right in zip(first, second):
        assert len(left["expressions"]) == len(right["expressions"])
        for a, b in zip(left["expressions"], right["expressions"]):
            assert a["selected_query"] == b["selected_query"] and a["available_events"] == b["available_events"]
            for key in ("ious", "original", "oracle"):
                if key in a:
                    assert len(a[key]) == len(b[key])
                    max_readout_delta = max(max_readout_delta, max(abs(x - y) for x, y in zip(a[key], b[key])))
    expressions = [e for row in first for e in row["expressions"]]
    available = [e for e in expressions if e["available_events"]]
    low_queries = [(iou, value, oracle) for e in available for iou, value, oracle in zip(e["ious"], e["original"], e["oracle"]) if iou < .5]
    bs.update(
        groups=len(first), expressions=len(expressions),
        all_bank_queries=sum(e["query_count"] for e in expressions),
        geometry_available_expressions=len(available),
        geometry_unavailable_expressions=len(expressions) - len(available),
        geometry_available_queries=sum(e["query_count"] for e in available),
        low_iou_queries=len(low_queries),
        low_iou_original_exact_zero=sum(value == 0 for _, value, _ in low_queries),
        low_iou_zero_oracle_positive_above1e6=sum(value == 0 and oracle > 1e-6 for _, value, oracle in low_queries),
        selected_low_iou_expressions=sum(e["selected_iou"] < .5 for e in expressions),
        selected_low_iou_but_bank_at_least_half=sum(e["selected_iou"] < .5 <= e["bank_best_iou"] for e in expressions),
        available_selected_low_iou=sum(e["selected_iou"] < .5 for e in available),
        available_selected_low_iou_original_zero=sum(e["selected_iou"] < .5 and e["selected_original"] == 0 for e in available),
        max_readout_repeat_delta=max_readout_delta,
        max_component_identity_delta=max(row["component_identity_abs_delta"] for row in bank["rows"]),
        native_repeat_failures=sum(not row["pass_repeat1e6"] for row in bank_native["rows"]),
        scope="Unnormalized per-query support costs; native TRAIN support IoU and indication argmax. No wrong-same-class identity, deployed VAL, causal task harm or efficacy claim.",
    )

remote_code = """
import datetime,json,subprocess
r={'remote_time':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'hostname':subprocess.check_output(['hostname'],text=True).strip()}
assert r['hostname']=='das'
r['gpu']=subprocess.check_output(['nvidia-smi','-i','7','--query-gpu=uuid,memory.used,memory.free,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert 'GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a' in r['gpu']
r['compute']=subprocess.check_output(['nvidia-smi','-i','7','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],text=True).strip()
r['locks']={p:subprocess.run(['flock','-n',p,'true']).returncode for p in ['/tmp/cluster_project_gpu7_exclusive.lock','/tmp/cluster_project_gpu7_diagnostic.lock','/tmp/cluster_project_gpu7_slot2_diagnostic.lock']}
p='/data3/songcl/Project/Cluster_project/Cluster/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps_20261014_095849.log'
r['training_tail']=subprocess.check_output(['tail','-c','12000',p],text=True).splitlines()[-4:]
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
    "checkpoint_sha256": native["checkpoint_sha256"], "checkpoint_meta": native["checkpoint_meta"],
    "native_capture": ns, "scalar_checkpoint": ss, "query_bank": bs,
    "new_candidates": 0, "new_admissions": 0, "new_training_launches": 0,
    "optimizer_steps": 0, "model_parameter_backward_calls": 0,
    "scientific_scope": "Native checkpoint-specific diagnostics, not independent structural repair, trained efficacy, verified witness labels, VAL assessment or global route exhaustion. Historical failures and all gates preserved.",
}
tick.save(BUNDLE / "summary.json", summary)
decision = log_decision(
    str(PROJECT), "other", "新冻结BPS检查点能否承接关系与旧标量诊断？",
    "原生捕获、固定旧样本和完整掩码库只作诊断；保留M201训练和旧标量未通过门槛，不启动分母/优先级变体。",
    "V3逐值buffer核验及负对照通过；96次原生前向重复/分解通过。旧样本25组50次前向：MAIN92/REL-OTHER46均吸引，fractional199原始27排斥，分母改动73排斥；不是任务伤害/收益。",
    str(BUNDLE / "summary.json"),
)
work_path = PIPE / "research_work.json"
work = tick.load(work_path)
bps = next(c for c in work["candidates"] if c["id"] == "m95-native-between-pair-support")
assert bps["stage"] == "training"
preregs = [PIPE / "designs" / name for name in (
    "bps_native_buffer_adapter_prereg_20261014_1312.md",
    "bps_scalar_checkpoint_prereg_20261014_1318.md",
    "bps_query_bank_prereg_20261014_1325.md",
)]
all_files = sorted(path for path in BUNDLE.iterdir() if path.is_file()) + preregs + [Path(decision)]


def bind(candidate, files):
    known = {(item["path"], item["sha256"]) for item in candidate["evidence"]}
    for path in files:
        item = ref(path)
        if (item["path"], item["sha256"]) not in known:
            candidate["evidence"].append(item)
            known.add((item["path"], item["sha256"]))


bind(bps, all_files)
bps["supplemental_native_checkpoint_diagnostic"] = {"status": "measured_not_admitted_repair", "summary": ref(BUNDLE / "summary.json")}
bps["execution_status"] = "Current16d02ebf tick:96BPSforwards/50scalarforwards/nativebankdiagnostic;nooptimizer/newvariant/admission/launch. Original gated M201 training continues; tick postflight pending."
bps["scientific_scope"] += " Currentepoch4 frozen native capture48groups192expressions262matched-eventqueries/20zero-to-oraclepositiveabove1e-6, repeats0/decomposition<=1e-6. Native bank/scalar readouts are diagnostic only;noVALefficacy or historicalFAILoverwrite."
scalar_files = [BUNDLE / name for name in (
    "scalar_checkpoint.py", "run_scalar.py", "scalar_execution.json",
    "scalar_pull.json", "scalar_result.json", "summary.json", "persist_results.py",
)] + [preregs[1]]
for candidate_id, subset in (
    ("m95-native-main-role-weight-precedence", "main_secondary"),
    ("m95-native-relation-other-sign-conflict", "relation_other"),
    ("m95-native-secondary-positive-mass", "fractional_secondary"),
):
    candidate = next(c for c in work["candidates"] if c["id"] == candidate_id)
    assert candidate["stage"] == "validation"
    assert all(not gate["passed"] for gate in candidate["gates"].values())
    bind(candidate, scalar_files)
    candidate["checkpoint_specific_diagnostic"] = {
        "status": "executed_not_admitted", "checkpoint": native["checkpoint_sha256"],
        "subset": subset, "summary": ref(BUNDLE / "summary.json"),
        "original": ss["conditions"]["original"][subset],
    }
    candidate["execution_status"] = "NewfrozenM201epoch4 fixed25groups/50nativeforwards/97expressionappearances pertrial; source-identity/repeatsPASS1e-6. Logit-only conditions executed; all six admission gates remain false and historical source facts/full-forward failures retained."
    candidate["scientific_scope"] += " CurrentM201epoch4 checkpoint-specific diagnostic:MAIN92andREL-OTHER46attracting;fractional199includes27repelling,masscondition73repelling/46signflips. Not independent core/fullmodelintervention/causalharm/efficacy;oldM95readoutsare not silently replaced."
    candidate["next_action"] = "Preserve original source facts, frozen M95 failures and newly executed M201 epoch4 diagnostics. Compare converged original ScanRefer VAL and frozen error subsets under the existing BPS evaluation plan when available; only a separately falsifiable structural core with matched native controls can become a training candidate. No denominator/priority tuning successor or automatic gate PASS."
tick.save(work_path, work)
notes = {
    "actions": [
        "本轮design快照2026-10-14 13:09:28+08，截止14:09:28不变；归属/GPU7两槽/18约束11禁令及后台Disabled已核实。原用户PDC哈希未变。",
        "修复仅诊断工具：两个具名buffer形状类型逐值相等，扰动负对照被拒绝；其余1163状态项仍strict=True。原V1/V2及失败原样保留，冻结epoch4 checkpoint SHA=f17f2ec3...，best_miou0.4201701879501343。",
        f"原生BPS捕获{ns['groups']}组/{ns['scenes']}场景/{ns['expression_appearances_per_trial']}表达式输入，{ns['forwards']}次前向；mask/loss重复最大差{ns['max_mask_repeat_delta']}/{ns['max_loss_repeat_delta']}，分解最大差{ns['max_decomposition_delta']:.3g}；失败{ns['repeat_failures']}/{ns['decomposition_failures']}。{len(queries)}匹配事件查询，26oracle差异超过1e-6，其中20零转正；不是见证标签或收益。",
        "三旧scalar稳定ID续做固定25组/97表达式/50前向：原始MAIN-secondary92及REL-OTHER46均吸引；fractional199中27排斥，分母条件变为73排斥/46符号变化；identity及原生重复通过，旧M95失败不覆盖，六准入门槛仍false。",
        f"完整查询库诊断状态{bs['status']}，执行返回{bs['execution_returncode']}；明细及分母见summary.json。原始关系组件照常返回criterion，oracle仅作诊断；无优化器/模型参数反向/新增模型/准入/启动。",
        "本轮后续实时训练、显存、外部进程及三诊断锁核验见resource_audit.json，本地与远端时间分别记录。所有远端诊断已结束；M201训练不重启。",
        "科学状态BPS=training/补充diagnosis，三scalar=validation且缺独立结构；本报告尚未postflight，执行结果及用量等收据后在任务报告补充，未知不记0。",
    ],
    "decisions": [
        "新checkpoint读数不等于旧M95校准结果，更不等于效果；不启动优先级/归一化调参，不改变历史失败、科学门槛或M201训练。",
        "保留诊断性GT最小配对与真实见证/部署效果的区别；查询库低IoU+零损失不自动等于同类误绑定或任务伤害。后续需要冻结任务层匹配对照及原VAL评估。",
        "本轮确有四个稳定候选的真实新证据；若收尾仍因容量缺口/未完研究拒绝，保留具体错误，不伪造耗尽/资源阻塞/冷却，不等待凑截止。下一自动调度时间未读取，未知。",
    ],
}
notes_path = PIPE / "reports" / ("notes_" + TOKEN + ".json")
tick.save(notes_path, notes)
report = tick.report("cluster_project", TOKEN, str(notes_path))
print(json.dumps({"summary": summary, "resource": resource, "report": str(report), "decision": decision}, ensure_ascii=False, indent=2))
