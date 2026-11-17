"""Bind completed diagnostic artifacts while the exact foreground lease is held."""

import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
from pipeline_monitor import log_decision

PROJECT = Path("D:/project/cluster_project")
PIPELINE = PROJECT / "pipeline"
TOKEN = "f8bdf4cb21774bf2af11f959fa12d89a"
BUNDLE = Path(__file__).resolve().parent
OWNER = PIPELINE / "headless/.foreground.lockdir/owner.json"


def guard():
    owner = tick.load(OWNER)
    assert owner["token"] == TOKEN
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert tick.digest(PIPELINE / "headless/.tick_context.json") == owner["context_sha256"]


def reference(path):
    return {"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)}


guard()
population = tick.load(BUNDLE / "result.json")
coherence = tick.load(BUNDLE / "coherence_result.json")
oracle = tick.load(BUNDLE / "teacher_pair_result.json")
for name in ("execution.json", "coherence_execution.json", "teacher_pair_execution.json"):
    assert tick.load(BUNDLE / name)["returncode"] == 0
for name in ("native_capture_execution.json", "native_capture_v2_execution.json"):
    assert tick.load(BUNDLE / name)["returncode"] == 1
assert all(result["complete"] for result in (population, coherence, oracle))
assert tick.digest(BUNDLE / "result.json") == "e930143cfd9476c6336ba4f0a89278a86280d6d15d70450c1de30c7bb73a01c5"
assert tick.digest(BUNDLE / "coherence_result.json") == "0d1ba3cd54a5a2b3d4d584ad4a5831ab6a9aef7b392d5751b40adf2045447036"
assert tick.digest(BUNDLE / "teacher_pair_result.json") == "9a88cdecefe088df989484c31c3b63aa53aac1c49ea2a9e8abe21451485fba9e"
crows = [item for row in coherence["rows"] for item in row["readouts"]]
orows = [item for row in oracle["rows"] for item in row["readouts"]]
assert len(crows) == len(orows) == 237
cs = {
    "exact_changes": sum(row["delta"] != 0 for row in crows),
    "changes_above_1e6": sum(abs(row["delta"]) > 1e-6 for row in crows),
    "positive_above_1e6": sum(row["delta"] > 1e-6 for row in crows),
    "negative_above_1e6": sum(row["delta"] < -1e-6 for row in crows),
    "coherent_nonzero": sum(row["coherent"] != 0 for row in crows),
    "fragmented_nonzero": sum(row["fragmented"] != 0 for row in crows),
    "gt_self_nonzero": sum(
        row["gt_self_coherent"] != 0 or row["gt_self_fragmented"] != 0
        for row in coherence["rows"]
    ),
}
zero_gained = [
    row for row in oracle["rows"]
    if any(item["unrestricted"] == 0 and item["gt_minimum_pair_oracle"] > 1e-6
           for item in row["readouts"])
]
ts = {
    "changes_above_1e6": sum(abs(row["delta"]) > 1e-6 for row in orows),
    "unrestricted_zero_oracle_positive": sum(
        row["unrestricted"] == 0 and row["gt_minimum_pair_oracle"] > 1e-6
        for row in orows
    ),
    "zero_gained_expressions": len(zero_gained),
    "zero_gained_scenes": len({row["scene"] for row in zero_gained}),
    "oracle_nonzero": sum(row["gt_minimum_pair_oracle"] != 0 for row in orows),
    "negative_above_1e6": sum(row["delta"] < -1e-6 for row in orows),
    "maximum_delta": max(row["delta"] for row in orows),
    "gt_self_nonzero": sum(
        row["gt_self_unrestricted"] != 0 or row["gt_self_oracle"] != 0
        for row in oracle["rows"]
    ),
}
assert cs["changes_above_1e6"] == 44 and ts["unrestricted_zero_oracle_positive"] == 53

remote = """
import subprocess,json,datetime
r={'remote_time':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'hostname':subprocess.check_output(['hostname'],text=True).strip()}
assert r['hostname']=='das'
r['gpu']=subprocess.check_output(['nvidia-smi','-i','7',
 '--query-gpu=uuid,memory.used,memory.free,memory.total,utilization.gpu',
 '--format=csv,noheader,nounits'],text=True).strip()
assert 'GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a' in r['gpu']
r['compute']=subprocess.check_output(['nvidia-smi','-i','7',
 '--query-compute-apps=pid,process_name,used_memory',
 '--format=csv,noheader,nounits'],text=True).strip()
r['training']=subprocess.check_output(['ps','-p','2867534',
 '-o','pid=,etime=,args='],text=True).strip()
r['locks']={p:subprocess.run(['flock','-n',p,'true']).returncode for p in [
 '/tmp/cluster_project_gpu7_exclusive.lock',
 '/tmp/cluster_project_gpu7_diagnostic.lock',
 '/tmp/cluster_project_gpu7_slot2_diagnostic.lock']}
procs=subprocess.check_output(['ps','-eo','pid=,args='],text=True)
r['native_capture_processes']=[x for x in procs.splitlines()
 if 'native_capture' in x and 'python' in x
 and 'bps_population_f8bdf4cb21774bf2af11f959fa12d89a' in x]
log='/data3/songcl/Project/Cluster_project/Cluster/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps_20261014_095849.log'
r['log_tail']=subprocess.check_output(['tail','-c','12000',log],text=True).splitlines()[-4:]
print(json.dumps(r))
"""
result = subprocess.run(
    ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
     "songcl@100.64.3.28", "python3", "-"],
    input=remote, capture_output=True, text=True, encoding="utf-8", timeout=40,
)
audit = {
    "token": TOKEN, "local_observed_at": datetime.now().astimezone().isoformat(),
    "returncode": result.returncode, "stderr": result.stderr,
    "earlier_readonly_probe_errors": [
        "Remote default python absent; no project writes.",
        "PowerShell quote escaping caused SyntaxError; no project writes.",
        "Successful tail -n probe expanded carriage-return progress; replaced with bounded tail -c and final four records.",
    ],
}
if result.returncode == 0:
    audit["remote"] = json.loads(result.stdout)
else:
    audit["remote"] = None
    audit["stdout"] = result.stdout[:1000]
guard()
tick.save(BUNDLE / "release_audit.json", audit)
summary = {
    "token": TOKEN, "recorded_at": datetime.now().astimezone().isoformat(),
    "population": population["counts"], "coherence": cs, "teacher_pair_oracle": ts,
    "native_capture": {
        "attempts": 2, "successful_forwards": 0, "optimizer_steps": 0,
        "v1_failure": "KeyError: state_dict",
        "v2_failure": "Unexpected position_ids/token_type_ids checkpoint keys; named buffer persistence/equality verification pending",
        "frozen_checkpoint_meta_epoch": 4,
        "frozen_checkpoint_meta_best_miou": 0.4201701879501343,
        "v3_status": "not_created_or_launched",
        "next_action": "Preregister exact equality verification for only the two named buffers; preserve strict loading for all other weights and the same frozen checkpoint. Then execute same-forward/repeat/decomposition checks at unchanged1e-6 with600sec runner+report margin in a later authorized lease.",
    },
    "scope": "Raw unaugmented TRAIN ideal physical masks. GT-minimum-cost oracle is not a verified witness, deployable repair, native model prediction, task harm, trained efficacy or novelty proof.",
    "training": "Existing M201-BPS continues unchanged; no new variant/admission/launch.",
    "closure": "Three scalar-role validation candidates unchanged. Known Unfinished candidate made no durable progress remains unrepaired; do not repeat unchanged finish or fake blocked/rejected/complete/cooldown. Preserve and abort exact token.",
}
tick.save(BUNDLE / "summary.json", summary)
decision = log_decision(
    str(PROJECT), "other",
    "扩展BPS理想物体掩码总体及配对控制，是否能外推全零或据此新增训练？",
    "撤回全局全零外推；保留同一BPS科学边界和现有训练。原生捕获适配失败仅保留证据，不新增变体或放宽加载/重复门槛；本轮精确abort。",
    "237个读数35非零；coherence44差异且方向不统一；GT配对oracle53零转正但不是已验证见证。两次原生捕获均在前向前失败；剩余窗口不足600秒执行加120秒收尾。",
    str(BUNDLE / "summary.json"),
)
guard()
work_path = PIPELINE / "research_work.json"
work = tick.load(work_path)
matches = [candidate for candidate in work["candidates"]
           if candidate["id"] == "m95-native-between-pair-support"]
assert len(matches) == 1 and matches[0]["stage"] == "training"
candidate = matches[0]
files = [
    BUNDLE / name for name in (
        "probe.py", "result.json", "execution.json",
        "coherence.py", "coherence_result.json", "coherence_execution.json",
        "teacher_pair.py", "teacher_pair_result.json", "teacher_pair_execution.json",
        "native_capture.py", "native_capture_execution.json",
        "native_capture_v2.py", "native_capture_v2_execution.json",
        "persist_tick.py", "release_audit.json", "summary.json",
    )
] + [
    PIPELINE / "designs" / name for name in (
        "bps_physical_population_prereg_20261014_1215.md",
        "bps_population_coherence_prereg_20261014_1221.md",
        "bps_teacher_pair_prereg_20261014_1225.md",
        "bps_native_pair_capture_prereg_20261014_1237.md",
        "bps_native_capture_adapter_20261014_1247.md",
    )
] + [Path(decision)]
known = {(item["path"], item["sha256"]) for item in candidate["evidence"]}
for path in files:
    ref = reference(path)
    if (ref["path"], ref["sha256"]) not in known:
        candidate["evidence"].append(ref)
        known.add((ref["path"], ref["sha256"]))
candidate["supplemental_population_diagnostic"] = {
    "status": "measured_not_admitted_repair", "summary": reference(BUNDLE / "summary.json"),
    "native_capture_status": "two_adapter_failures_before_forward",
}
candidate["execution_status"] = (
    "Currentf8bdf tick executed3CPU probes/237physical alternatives;35originalnonzero/"
    "44coherencechanges/53oraclezero-to-positive. Two checkpoint adapters failed beforeforward;"
    "nooptimizer/newvariant/admission/launch. Frozencheckpointepoch4best.4201701879501343;"
    "M201trainingcontinues. ScalarvalidationIDs unchanged;INCOMPLETE/exact-tokenabortpending."
)
candidate["scientific_scope"] = (
    "Validated executable BPS mechanism now training. Expanded catalog1498expressions/"
    "416scenes includes108geometry-available and1390unavailable;49expressions yield237"
    "ideal same-class alternatives,35nonzero. This disconfirms global allzero extrapolation,"
    "not task harm/efficacy. GT-pair oracle and coherent-fragmented differences are diagnostics"
    "only;no native predictioncapture yet. Priorfloat32FAILs and scalar failures retained."
)
tick.save(work_path, work)
notes = {
    "actions": [
        "本轮续用原租约；设计快照2026-10-14 12:09:55+08，截止13:09:55+08不变。归属、GPU7两槽、18约束/11禁令核实；后台Disabled；原用户PDC修改哈希未变。",
        "三项远端CPU诊断执行返回0，CUDA隐藏/两线程：冻结TRAIN目录416场景1498表达式1502事件，108几何可用/1390不可用；25类别未知、34无同类替代；49表达式/40场景237物理掩码读数，202零/35非零，GT-self108全零。",
        "配对coherence原始臂精确复现237/237；55精确差异，44超过1e-6，其中coherent-minus-fragmented正4/负40；非零数35对62。GT-self两臂全零；GT减除后没有统一单调关系。",
        "GT最小代价配对oracle保留精确并列、不调容差；237原始臂复现，69差异超过1e-6；53原始零转正，23表达式/19场景；oracle88非零，49GT-self全零。不是已验证见证、模型输出或可部署效果。",
        "原生捕获V1缺state_dict，V2严格加载遇position_ids/token_type_ids多余键，均在前向前失败；成功前向/优化器步均0，完整stderr保留。冻结epoch4 checkpoint best_miou0.4201701879501343；没有创建/执行V3。",
        "补充只读资源/训练/三锁核验见release_audit.json；本地与远端时钟分列。外部PID262355不动；无新增模型、准入或训练。M201仍训练；未把GPU锁可用当作独占。",
        "本轮执行状态INCOMPLETE（尚未abort，实际结果在任务最终报告核实）；科学状态BPS=training/补充diagnosis，三scalar=validation且既有FAIL未变。既知closure Unfinished candidate made no durable progress未修复，不重复相同finish，不假造闭合/冷却。用量及产出等待收据，未知不记0。",
    ],
    "decisions": [
        "此前67物理掩码全零仅为有限样本；本轮35非零否定全局全零外推。coherence/GT-pair均有信息增益，但不证明真实模型伤害、收益或独立修复，不新增训练变体。",
        "保留现有M201训练及原seed1999/epochs50/max_iters70/收敛规则。下一次有租约且时间充足时先预注册两缓存buffer精确相等核验，其他权重仍strict=True，再续同一冻结checkpoint的原生捕获与1e-6复现检查；不改正在训练的模型。",
        "可用显存不是科学准入。没有全路线耗尽或资源阻塞证据；不能把同一机制三探针包装成两独立路线获得冷却。保留真实证据后精确abort并核实释放；下一调度时间未读取，未知。",
    ],
}
notes_path = PIPELINE / "reports" / ("notes_" + TOKEN + ".json")
tick.save(notes_path, notes)
print(json.dumps({
    "summary": summary, "audit": audit, "decision": decision,
    "report": str(tick.report("cluster_project", TOKEN, str(notes_path))),
    "bps_evidence_count": len(candidate["evidence"]),
}, ensure_ascii=False, indent=2))
