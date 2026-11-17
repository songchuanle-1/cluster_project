"""Record a due GPU recheck with the same actual resource blocker."""

import argparse
import csv
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

PROJECT = Path("D:/project/cluster_project")
IDS = [
    "m95-native-main-role-weight-precedence",
    "m95-native-relation-other-sign-conflict",
    "m95-native-secondary-positive-mass",
    "m95-native-between-pair-support",
]
GOAL_SHA = "24083b8deaf464c78ad11ac83c00c573d637c0494935ee11e965327e8a2fda2e"
PDC_SHA = "00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    token = args.token
    assert len(token) == 32 and all(c in "0123456789abcdef" for c in token)
    bundle = PROJECT / "pipeline/diagnostic_bundles" / ("tick_" + token)
    observation_path = bundle / "resource_observation.json"
    guard_path = PROJECT / "pipeline/diagnostic_bundles/transport_port_75d7e1ea35634b1fa29749fcf54163c8" / ("launch_guard_" + token + ".json")
    owner_path = PROJECT / "pipeline/headless/.foreground.lockdir/owner.json"
    owner = tick.load(owner_path)

    def guard():
        current = tick.load(owner_path)
        assert current == owner and current["token"] == token
        assert current["thread_id"] == os.environ["CODEX_THREAD_ID"]
        assert current["thread_id"] == tick.load(PROJECT / "pipeline/execution_mode.json")["target_thread_id"]
        assert (datetime.fromisoformat(current["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
        assert tick.digest(PROJECT / "pipeline/goal.json") == GOAL_SHA
        assert tick.digest(PROJECT / "Cluster/scripts/validate_pdc_20261009.py") == PDC_SHA

    guard()
    observation = tick.load(observation_path)
    launch = tick.load(guard_path)
    view = tick.load(PROJECT / "pipeline/headless/.tick_model_view.json")
    assert view["generated_at"] == owner["generated_at"]
    assert view["research"]["reserve_budget"] == 0
    assert view["research"]["reserve_count"] == 4
    assert view["research"]["reserve_target"] == 2
    assert view["queue"]["candidate_budget"] == 1
    assert observation["token"] == launch["token"] == token
    observed = datetime.fromisoformat(observation["observed_at"])
    assert datetime.fromisoformat(owner["generated_at"]) <= observed <= datetime.now(timezone.utc)
    assert launch["returncode"] == 0
    assert json.loads(launch["stdout"]) == {
        "status": "BLOCKED", "reason": "Exclusive GPU0 slot occupied by PID 2634704", "gpu_launches": 0}
    gpu = next(csv.reader([observation["gpu"]], skipinitialspace=True))
    assert gpu[:2] == ["0", "GPU-7f82edb9-f620-8045-caea-a75232265cd1"]
    assert list(map(int, gpu[2:])) == [32607, 31943, 159, 92]
    compute = {int(pid): int(memory) for pid, memory in
               csv.reader(observation["compute"].splitlines(), skipinitialspace=True)}
    assert compute == {2634704: 20016, 1404754: 11828}
    assert observation["registered_pid"] == {"pid": 2634704, "exists": False}
    assert observation["locks"]["/tmp/cluster_project_gpu0_m201_migration.lock"] == "held"

    def ref(path):
        return {"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)}

    references = [ref(observation_path), ref(guard_path)]
    work_path = PROJECT / "pipeline/research_work.json"
    original_hash = tick.digest(work_path)
    work = tick.load(work_path)
    retry = (datetime.now().astimezone() + timedelta(minutes=90)).isoformat()
    condition = (
        "Fresh pinned server4/GPU0 observation with no NVML compute process and "
        ">=30000MiB idle-equivalent free memory; all original training/diagnostic "
        "flocks truly available. Do not reset GPU, delete locks, kill unknown "
        "owners or assume sudo."
    )
    for cid in IDS:
        matches = [c for c in work["candidates"] if c["id"] == cid]
        assert len(matches) == 1
        candidate = matches[0]
        assert candidate["stage"] == "blocked"
        assert candidate["blocker_kind"] == "gpu_context_or_lock_not_released"
        assert candidate["required_server"] == "server-4"
        assert datetime.fromisoformat(candidate["retry_after"]) <= observed
        if cid != IDS[-1]:
            assert all(not gate["passed"] for gate in candidate["gates"].values())
        for entry in references:
            assert entry not in candidate["evidence"], "Do not replay evidence"
            candidate["evidence"].append(entry)
        candidate.update(
            blocker=(
                "Fresh " + observation["observed_at"] + ": GPU0 NVML PID2634704 "
                "uses20016MiB/exact PID absent; same unattributed PID1404754 "
                "uses11828MiB; total used31943/free159MiB/util92%. Training flock "
                "held/kernel owner2634697 absent. Frozen guard refused; residual "
                "cause/cleanup authority and unattributed process ownership unknown."
            ),
            retry_after=retry, unblock_condition=condition,
            occupation_evidence=ref(observation_path),
            execution_status=(
                "Current" + token + ": due frozen check-only BLOCKED; exact "
                "resource values vary slightly but the same two PIDs remain; "
                "original context/flock unavailable.0GPU/native forwards/optimizer/"
                "recovery launches. Gates and old failures unchanged; completed "
                "CPU work not repeated."
            ),
        )
        candidate.setdefault("attempted_alternatives", []).append(
            "Due current-token frozen check-only refusal plus pinned GPU0/exact "
            "three-flock observation at" + observation["observed_at"] +
            "; completed non-GPU preparations retained, not rerun; no reset/signal."
        )
    work["design_cycle"] = {
        "stop_reason": "external_resource_blocked", "attempted_ids": IDS,
        "evidence": references, "resume_condition": condition, "retry_after": retry,
        "scope": "Due observation confirms the same two-PID occupation and residual context/training flock block. Not route exhaustion or scientific benefit. Resource cooldown90minutes is within2hours; monitor/goal ticks remain enabled. No signals or cleanup.",
    }
    notes_path = PROJECT / "pipeline/reports" / ("notes_" + token + ".json")
    notes = {
        "actions": [
            "本轮cluster_project/design；快照" + owner["generated_at"] + "，截止" + owner["deadline_at"] + "不可变。任务归属、最新19约束/11禁令、server4 GPU0单槽和后台Disabled核实；begin仅一次，0-3段保留脚本preflight事实表。",
            "已读最新Research Reserve和Implementation Revisions契约。训练准入预算1，储备4/目标2、储备准备预算0；续做四原ID，不新建占位候选。本轮仍是实际资源阻塞而非新的实现失败，没有依据修改层/连接或消耗修订次数；原门槛、冻结、禁令和历史否决保留。累计99记录/91历史否决未分类/0修订/5收据仅为事实计数，不是成功率。",
            "四稳定ID到期续查，冻结启动器check-only实际BLOCKED。资源实测" + observation["observed_at"] + "：RTX5090总32607MiB/使用31943/空余159/利用率92%；原NVML PID2634704占20016MiB且/proc不可见，已有未归属PID1404754占11828MiB，未探查或操作其命令和所属项目。相较12:09:21实测空余115MiB/利用率100%，仅数值波动，阻塞状态未改变。原训练flock持有/内核锁PID2634697不可见，两诊断锁可用；13:10steady未新测资源，残留原因和可安全清理权限仍未知。",
            "四原ID继续blocked/gpu_context_or_lock_not_released，追加两项共同证据哈希，不冒称三独立机制；三scalar六门槛均false、旧FD/full-forward FAIL保留。BPS旧准入不重写；同一M201仍协议中断stopped_unknown，历史best0.489848792552948@18/完成26/no_improve8及epoch26完整642优化器状态恢复计划保留，未冷启动或改seed/schedule/patience。",
            "已有CPU准备和监控测试不重复。本轮GPU/native前向/参数梯度/优化器更新/续训启动/新候选/准入均0；无sudo/reset/删除锁/外部信号/其他项目/调度操作，用户PDC文件SHA不变。按真实external_resource_blocked收尾，重试" + retry + "；90分钟资源冷却不改变正常monitor/goal tick或准入，未声称全路线耗尽。",
            "科学状态blocked；执行状态在report时待postflight，只有finish成功并确认租约释放才COMPLETED。实际产出：1次冻结资源拒绝、1次实机占用/锁观察、4稳定ID证据与重试更新。收据只覆盖begin到receipt局部用量窗口，不含早读/迟到记录/最终回复；缓存已包含输入，推理已包含输出，非账单，缺失值未知，最终计数收尾后读取。",
        ],
        "decisions": [
            "无新科学或训练准入决策，沿用原冻结诊断与同一M201完整续训恢复条件，资源/训练锁真释放之前不启动。",
            "储备已达到有界目标且新增准备预算为0，不为储备数量制造变体。局部实现修订仅在明确缺陷、事先登记单一改动与对照后进行；当前GPU资源阻塞本身不是更改机制实现的理由，未重新开放91历史否决ID。",
            "相同未归属进程持续占用GPU，原残留和训练锁也未释放；不驱逐、不复位、不删除锁、不扩大GPU白名单。记录本轮资源证据并设置90分钟资源冷却，finish通过后才生效；资源/项目证据变化或重试到期再续做。下一自动调度时间本轮未读取，未知，不把retry_after当作自动调度时间。",
        ],
    }
    memory_path = PROJECT / "pipeline/codex_memory.md"
    lines = memory_path.read_text(encoding="utf-8").splitlines()
    index = lines.index("## Last Tick") + 1
    assert lines[index].startswith("- Current")
    previous = lines[index].split()[1].removeprefix("Current")
    prior_receipt = tick.load(PROJECT / "pipeline/tick_receipts" / (previous + ".json"))
    assert prior_receipt["status"] == "FINALIZED" and prior_receipt["postflight"] == "PASS"
    assert prior_receipt["context_committed"] is True
    lines[index] = (
        "- Current" + token + " design/snapshot" + owner["generated_at"] +
        "/deadline" + owner["deadline_at"] + "immutable;due4/budget1/running0. Actual"
        + observation["observed_at"] + " pinnedserver4/GPU0free159/used31943/"
        "total32607MiB/util92;SAMEunattributedNVML1404754uses11828MiB/noinspection"
        "/signals;originalNVML2634704uses20016MiB/exactPIDabsent;"
        "trainingflockheld/kernel2634697absent/2diagnosticlocksavailable;"
        "frozencheck-onlyBLOCKED/0GPU. Same4IDs/scalar6false/oldFAILs/frozen75d7"
        "retained;2newsharedhashedrefs/90minretry=" + retry +
        ". No repeatedCPU/newcandidate/admission/optimizer/recovery/reset/sudo/"
        "lockdeletion/foreignsignal/schedulerchange. SameM201stopped_unknown/"
        "protocolinterrupted/best.489848792552948@18/completed26/noimprove8;"
        "full642optimizer+schedulerCPUrestorePASS/checkpointSHAf2f6fb53bd3a6388"
        "e1bf05e8d7c5099bacf94e5f81f06d4584d2a1707426d8df/sourcef8457d3b/"
        "seed1999/epochs50/max70/patience10/next27replay/NOmid-epochRNGbitwiseclaim."
        " PriorSubstantive" + previous + "receiptFINALIZED/PASS/contextcommitted"
        "(receiptisnotreleaseproof;thatturnreleaseverifiedintask). Prior1310"
        "steady6f3fc422b0a84866adeb93b51807643fACTUALautoCOMPLETE/PASS/lease+"
        "pendingabsent13:10:34/noGPUrecheck/0researchchanges. "
        "Newreservecontracttarget2/count4/budget0/reserve_onlyfalse;"
        "99records/91rejectedunclassified/4complete/4blocked/5receiptsNOTsuccessrate;"
        "0implementationrevisions/nohistoryreclassification/originalfreezesretained."
        "Currentexternal_resource_blocked/notrouteexhaustion;"
        "postflightpendingatmemorywrite,actualreceipt/taskresultauthoritative;"
        "PDCusershaunchanged."
    )
    assert len(lines) < 120
    guard()
    assert tick.digest(work_path) == original_hash
    tick.save(work_path, work)
    tick.save(notes_path, notes)
    memory_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"updated_ids": IDS, "new_shared_evidence": references,
                      "retry_after": retry, "notes": str(notes_path),
                      "memory_lines": len(lines), "scientific_status": "blocked"}))


if __name__ == "__main__":
    main()
