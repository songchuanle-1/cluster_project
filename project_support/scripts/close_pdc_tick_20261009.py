"""Record verified native launch evidence and an honest deadline disposition."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import closure
import foreground_tick as fg

TOKEN = "0a9fe7bf97ae444581a60722f0f5b2e6"


def ev(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    owner = fg.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    if owner["token"] != TOKEN or owner["thread_id"] != os.environ["CODEX_THREAD_ID"]:
        raise ValueError("Current owning lease required")
    context = fg.load(ROOT / "pipeline/headless/.tick_model_view.json")
    remaining = (datetime.fromisoformat(context["deadline_at"]) -
                 datetime.now(timezone.utc)).total_seconds()
    if not 0 < remaining <= 180:
        raise ValueError("Actual deadline is not near; continue work or honest abort")
    exp = fg.load(ROOT / "pipeline/experiments/M198-PDC.json")
    if exp.get("launch_verified") is not True or exp["status"] != "running":
        raise ValueError("Increasing native progress not verified by dispatcher")
    command = (
        f"if kill -0 {int(exp['pid'])} 2>/dev/null; then "
        f"tail -c 24000 '{exp['log']}'; else echo __DEAD__; fi")
    text = subprocess.check_output(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
         "songcl@100.64.3.28", command], timeout=30).decode("utf-8", errors="replace")
    steps = closure.steps(text)
    if "__DEAD__" in text or "Traceback" in text or len(set(steps)) < 2 or max(s for _, s in steps) <= 0:
        raise ValueError("Native launch evidence regressed; reconcile, do not claim training")
    gpu = subprocess.check_output(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
         "songcl@100.64.3.28",
         "nvidia-smi -i 7 --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"],
        timeout=30).decode().strip()
    launch_path = "pipeline/reports/pdc_launch_verified_20261009.json"
    absolute = ROOT / launch_path
    if absolute.exists():
        raise ValueError("Fresh launch evidence required")
    launch = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "id": "M198-PDC", "server": "server-6", "gpu": 7,
        "pid": exp["pid"], "log": exp["log"], "native_steps": steps,
        "launch_verified": True, "gpu_util_memory_mib_total_mib": gpu,
        "trained_miou": "unknown", "completed_epochs": "unknown",
    }
    with absolute.open("x", encoding="utf-8") as stream:
        json.dump(launch, stream, indent=2, allow_nan=False)
    work = fg.load(ROOT / "pipeline/research_work.json")
    candidate = next(row for row in work["candidates"]
                     if row["id"] == "m95-native-point-detail-field")
    candidate.update(
        stage="training", next_action="Monitor M198-PDC native training and frozen VAL/scene/Pareto/harm plan; do not restart M197 or duplicate PDC.",
        latest_progress="M198-PDC six-gate receipt admitted and safe ff-only source synchronized; server6 GPU7 increasing native Train steps verified. Efficacy unknown.")
    candidate["evidence"].append(ev(launch_path))
    work["design_cycle"] = {
        "stop_reason": "tick_deadline_near",
        "attempted_ids": [candidate["id"]],
        "evidence": [ev(launch_path), ev("pipeline/reports/pdc_sorted_admission_audit_20261009.json")],
        "resume_condition": "Next authorized tick monitors M198 and, if capacity remains, diagnoses a genuinely independent mechanism; no duplicate PDC control training or filler.",
        "details": "One real experiment admitted/training after completed native diagnosis, repeated reproducibility repairs and resource tests. Real original deadline is within180s; no claim that other routes are exhausted.",
    }
    fg.save(ROOT / "pipeline/research_work.json", work)
    notes = {
        "actions": [
            "科学状态：M198-PDC已training；执行状态仍待finish，不能从准入或PID推断本轮完成。",
            "独立预测盲32场景/128表达中19个存在混合边界及原生点特征细节；原83表达零混合边界的负证据保留。实现均值守恒查询到点的掩码新路径，增加9280参数。",
            "保存初始严格重复FAIL、CSR/H100及导入错误、Native算法资源超限结果；未放宽1e-6。最终使用排序分段均值与作用域内排序稀疏索引，保留原implicit-GEMM；两组及实际batch2三臂对照/全损失反向全部PASS。",
            "修正远端旧helper错误的loss口径；独立复制已校正predict协议，不覆盖历史脚本。最终同口径baseline9.700876364G、champion9.762532428G、候选9.770301004G。相对champion增量0.007768576G、median8.085824549ms、P908.575477265ms、显存121.6142578125MiB(+12.46%)；相对baseline增量0.069424640G、median-30.998526141ms、P90-24.087575264ms、显存+117.1103515625MiB(+11.94%)。计数未覆盖算子单列。",
            f"启动后证据时间{launch['observed_at']}：server6 GPU7，PID{exp['pid']}，native Train步数{steps[0]}→{steps[-1]}，实时GPU利用率/显存MiB/总量MiB={gpu}。指标及完整epoch结果未知。前0-3段保持08:59:15 preflight快照，不冒充启动后状态。",
            "六项准入真实收据、唯一独立model/config、已测试commit9a315ace4f9ace79f674a09aa89e214d9fb8f362、安全ff同步和递增训练验收齐备。Windows后台Disabled，其他服务器/项目及无关BCCA文件未操作。",
            "收据用量窗口仅begin至收据，最终答复及此前读取不在窗口；缓存属输入、推理属输出，不重复相加，不作账单。实际产出为一个新结构实验及其诊断、原生/资源/准入/启动证据；精确用量以finish收据为准，缺失记未知。",
        ],
        "decisions": [
            "按正式next_batch决策准入M198-PDC，保持seed1999、epochs50/max_iters70及18约束/11禁项；训练效果与穷尽新颖性未验证。",
            "原时限将至，第二槽保留空闲；只依据真实tick_deadline_near收尾，不宣称路线穷尽或资源阻塞。下一轮先监控M198并按冻结VAL/场景不确定性/子集伤害/Pareto规则评估，不生成排名/池化改名或凑数变体。",
        ],
    }
    fg.save(ROOT / ("pipeline/reports/tick_notes_" + TOKEN + ".json"), notes)
    print(json.dumps({"native_first": steps[0], "native_last": steps[-1],
                      "gpu": gpu, "observed_at": launch["observed_at"],
                      "remaining_seconds": remaining, "evidence": ev(launch_path)}))


if __name__ == "__main__":
    main()
