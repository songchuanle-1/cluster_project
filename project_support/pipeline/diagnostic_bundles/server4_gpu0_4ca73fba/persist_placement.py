from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "4ca73fbab48045ba9468a3965a1d383d"
CID = "m95-hierarchical-mask-feature-path-audit"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry(relative):
    return {"path": relative, "sha256": digest(ROOT / relative)}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text(encoding="utf-8"))
    assert owner["token"] == TOKEN and owner["thread_id"] == "01a04987-fdbe-7301-b2f0-f9b6ab60f74c"
    now = datetime.now(timezone.utc)
    assert now >= datetime.fromisoformat(owner["deadline_at"]) - timedelta(seconds=180)
    work_path = ROOT / "pipeline/research_work.json"
    assert digest(work_path) == "0bc3f87ddbe2ef6dc2718c5fb58fb960529acafdfb99b76e5260b8ba578bbad9"
    raw = work_path.read_bytes()
    work = json.loads(raw)
    assert (json.dumps(work, ensure_ascii=False, indent=2) + "\n").encode("utf-8") == raw.replace(b"\r\n", b"\n")
    before = json.loads(raw)
    (HERE / "work_before_placement.json").write_bytes(raw)
    evidence = [entry("pipeline/authorizations/server3_gpu1_server4_gpu0_20261016_4ca73fba.json"), entry("pipeline/diagnostic_bundles/server4_gpu0_4ca73fba/resource_probe.json"), entry("pipeline/decisions/20261016-042103_manual.md")]
    candidate = next(c for c in work["candidates"] if c["id"] == CID)
    old = next(c for c in before["candidates"] if c["id"] == CID)
    candidate["evidence"].extend(evidence)
    candidate["resource_placement_update"] = {"recorded_at": now.isoformat(), "slots": [["server-3", 1], ["server-4", 0]], "capacity": 2, "evidence": evidence, "scope": "Actual user resource override and new-host occupation/runtime checks, not new scientific tests, FLOPs repair or revision3 permission.", "server4_runtime_wrapper": "Prepared locally and isolation import succeeded in task output, NOT uploaded/deployed; runtime_preparation.json absent.", "previous_next_action": old["next_action"]}
    candidate["next_action"] = "Next fresh authorized lease: deploy/hash-check the prepared project-only server4 runtime wrapper and verify its conda activation without CUDA allocation. Keep server3GPU1 usable. For the core realization still wait for explicit ONE additional bounded same-ID resource revision or externally supplied compliant code;10G/strict controls/full native backward/resource/independence gates remain unchanged. No queue/training or automatic M201 recovery. Authorized cards: server3 physicalGPU1 and server4 physicalGPU0, one task each."
    assert candidate["stage"] == "blocked" and candidate["blocker_kind"] == "human_authorization"
    assert candidate["revision_history"] == old["revision_history"]
    assert candidate["gates"] == old["gates"]
    assert len(work["candidates"]) == 100
    assert all(c == next(p for p in before["candidates"] if p["id"] == c["id"]) for c in work["candidates"] if c["id"] != CID)
    work["design_cycle"] = {"stop_reason": "tick_deadline_near", "attempted_ids": [CID], "recorded_at": now.isoformat(), "evidence": evidence, "resume_condition": candidate["next_action"]}
    save(work_path, work)
    notes = {
        "actions": [
            "续接同一租约4ca73fbab48045ba9468a3965a1d383d，未重复begin或preflight；0至3段固定事实仍为2026-10-16北京时间11:18:05、容量1的旧快照，不代表后续资源授权。原deadline为12:18:05，12:18:52已核实到期；此后只保存此前实际动作和收尾，不延长截止或补跑研究。",
            "按两条直接用户指令，已将授权资源更新为server3物理GPU1和server4物理GPU0，各1槽、总容量2。server4严格SSH身份dl04-MS-7E06匹配，双RTX5090恢复；新GPU0 UUID958e741a-e5cf-127e-ffe8-9b984e1f404c，旧卡现为GPU1，不使用它。",
            "server4资源探针时间11:29:52：GPU0利用率0%、已用41MiB/总32607MiB、空闲32069MiB，无计算进程；三个旧锁均不存在，未创建或删除锁。server3本轮查询GPU1空闲24267MiB、利用率0%、无计算进程，既有3d-stmn环境PyTorch1.12+cu113可加载且CUDA未初始化；不把这些历史占用读数当作未来独占保证。",
            "server4环境位于/home/songcl/.conda/envs/project_cluster，PyTorch2.8+cu128。普通导入失败；隔离旧字节码读取后导入成功、CUDA未初始化，原失败保留。项目独立隔离入口与部署校验脚本仅本地准备，尚未部署，也未修改SERVERS的conda_source，下一轮先完成该受控操作，不能称训练环境全面就绪。",
            "将真实资源授权和新主机探针哈希归档到原稳定ID，仅更新资源续做说明。原四项通过门槛、10.034588748G超10G的失败、两次修订历史及其余99候选完整保留；没有新增机制测试、实现修订、准入、模型前后向、优化步数或训练启动。",
            "科学状态仍blocked/human_authorization；执行状态POSTFLIGHT_PENDING。真实deadline已到，按tick_deadline_near归档未完事项；finish实际结果及随后租约核验决定是否COMPLETED，否则abort。收据用量此时未知，只统计begin至收据可见的局部日志，不含前读/延迟记录/最终答复；缓存含于输入、推理含于输出，不重复相加，不是账单。"
        ],
        "decisions": [
            "保留server3 GPU1并新增server4 GPU0，不用其他卡、不重启M201、不驱逐或重置、不改调度。新资源容量不等于合格训练预算，不为填卡添加占位变体。",
            "资源授权不等于第三次实现修订授权；当前模型10G门槛和两次修订限制仍有效。先完成环境隔离部署核验，再按明确授权和原门槛续做核心机制。",
            "完整证据见pipeline/diagnostic_bundles/server4_gpu0_4ca73fba/resource_probe.json与资源授权文件；规范手动决策记录20261016-042103_manual.md的shell时间为UTC样式，用户可见本报告统一使用Asia/Shanghai。下次自动化精确触发时间未知。"
        ]
    }
    save(ROOT / ("pipeline/reports/notes_" + TOKEN + ".json"), notes)
    save(HERE / "placement_summary.json", {"recorded_at": now.astimezone(timezone(timedelta(hours=8))).isoformat(), "deadline_at_unchanged": owner["deadline_at"], "evidence": evidence, "changed_candidate_ids": [CID], "scientific_tests": 0, "training_launches": 0, "runtime_wrapper_deployed": False, "goal_sha256": digest(ROOT / "pipeline/goal.json"), "servers_sha256": digest(ROOT / "SERVERS.yaml"), "work_sha256": digest(work_path)})
    print(json.dumps({"notes_saved": True, "changed_candidate_ids": [CID], "other_candidates_unchanged": 99, "gates_and_revisions_unchanged": True, "deadline_at": owner["deadline_at"]}))


if __name__ == "__main__":
    main()
