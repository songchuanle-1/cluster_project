from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "37b313549dd24de2addbb7df6ee14331"
CID = "m95-hierarchical-mask-feature-path-audit"
AUX = {"m95-native-relation-other-sign-conflict", "m95-native-main-role-weight-precedence", "m95-native-secondary-positive-mass", "m95-native-between-pair-support"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path)}


def main():
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text(encoding="utf-8"))
    assert owner["token"] == TOKEN and owner["thread_id"] == "01a04987-fdbe-7301-b2f0-f9b6ab60f74c"
    now = datetime.now(timezone.utc)
    assert now < datetime.fromisoformat(owner["deadline_at"]) - timedelta(seconds=180)
    assert not (ROOT / "pipeline/authorizations/hds_resource_revision3.json").exists()
    old_bundle = ROOT / "pipeline/diagnostic_bundles/server4_gpu0_4ca73fba"
    result = json.loads((old_bundle / "runtime_preparation.json").read_text(encoding="utf-8"))
    assert result["runtime_loaded"] and result["probe"]["returncode"] == 0
    loaded = json.loads(result["probe"]["stdout"])
    assert loaded["cuda_initialized"] is False and loaded["torch"] == "2.8.0+cu128"
    assert result["sha256"] == "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
    for source, destination in [("runtime_preparation.json", "runtime_success.json"), ("runtime_preparation_windows_crlf_failure.json", "runtime_crlf_failure.json"), ("prepare_runtime.py", "prepare_runtime_used.py")]:
        target = HERE / destination
        assert not target.exists()
        shutil.copyfile(old_bundle / source, target)
    shutil.copyfile(ROOT / "SERVERS.yaml", HERE / "servers_after.yaml")
    work_path = ROOT / "pipeline/research_work.json"
    raw = work_path.read_bytes()
    before = json.loads(raw)
    assert (json.dumps(before, ensure_ascii=False, indent=2) + "\n").encode("utf-8") == raw.replace(b"\r\n", b"\n")
    (HERE / "work_before.json").write_bytes(raw)
    work = json.loads(raw)
    retry = (now + timedelta(hours=4)).isoformat()
    summary = {"observed_at": now.astimezone(timezone(timedelta(hours=8))).isoformat(), "scope": "Operational runtime and unchanged human authorization intake; not mechanism tests or admission.", "server4_conda_source": result["target"], "wrapper_sha256": result["sha256"], "runtime_loaded": True, "cuda_initialized": False, "native_ready": "not established by import", "scope_hold_ids": sorted(AUX), "all_five_blocker_kinds": "human_authorization", "third_revision_authorization_present": False, "gate_results_and_revision_history_unchanged": True, "new_candidates": 0, "native_forwards": 0, "native_backwards": 0, "optimizer_steps": 0, "training_launches": 0, "retry_after": retry, "hardware_occupation_this_tick": "unknown; no GPU test requested", "goal_sha256": digest(ROOT / "pipeline/goal.json"), "servers_sha256": digest(ROOT / "SERVERS.yaml"), "stop_detail": "External required human authorization is absent, not a claim of occupied GPUs or exhausted hypotheses."}
    save(HERE / "runtime_scope_summary.json", summary)
    evidence = [ref(HERE / name) for name in ("runtime_success.json", "runtime_crlf_failure.json", "runtime_scope_summary.json", "servers_after.yaml")]
    candidate = next(c for c in work["candidates"] if c["id"] == CID)
    candidate["evidence"].extend(evidence)
    candidate["runtime_preparation"] = {"observed_at": summary["observed_at"], "target": result["target"], "sha256": result["sha256"], "deployed_and_import_verified": True, "native_model_readiness": "not yet tested", "evidence": evidence}
    candidate["resource_placement_update"]["server4_runtime_wrapper"] = "Deployed and hash-verified; project-only Conda source bound after actual import passed with CUDA uninitialized. No full native model readiness or admission implied."
    candidate["next_action"] = "Preserve deployed server4 project-only runtime and server3GPU1. Await explicit ONE additional bounded same-ID resource realization or externally supplied compliant implementation; current10.034588748G still exceeds10G and both implementation revisions are consumed. After authorization preregister local VALUE aggregation repair, retest original strict controls/full native backward/same resources/independence, then real admission. No automatic M201 recovery or duplicate training. Authorized cards remain server3 physicalGPU1 and server4 physicalGPU0, one task each."
    candidate["retry_after"] = retry
    for c in work["candidates"]:
        if c["id"] in AUX:
            assert c["stage"] == "blocked" and c["blocker_kind"] == "human_authorization" and c["research_role"] == "auxiliary_scope_hold"
            c["retry_after"] = retry
            c["evidence"].append(ref(HERE / "runtime_scope_summary.json"))
    changed = AUX | {CID}
    assert len(work["candidates"]) == len(before["candidates"]) == 100
    for c in work["candidates"]:
        old = next(p for p in before["candidates"] if p["id"] == c["id"])
        assert c["stage"] == old["stage"] and c.get("gates") == old.get("gates") and c.get("revision_history") == old.get("revision_history")
        if c["id"] not in changed:
            assert c == old
    work["design_cycle"] = {"stop_reason": "external_resource_blocked", "blocker_kind": "human_authorization", "attempted_ids": [CID], "recorded_at": now.isoformat(), "evidence": evidence, "resume_condition": "Explicit bounded revision authorization or compliant external implementation; auxiliary routes additionally require human scope release. Goal/server/intake changes may wake earlier, timers never grant permission.", "stop_detail": summary["stop_detail"]}
    save(work_path, work)
    notes = {"actions": [
        "快照北京时间2026-10-16 13:09:54，design，原deadline14:09:54；begin已唯一执行监控和目标检查，均返回0。授权server3 GPU1+server4 GPU0，各1槽，活跃0、准入预算2、储备5/2、准备预算0；没有重复preflight。",
        "续做主线已登记的环境准备。严格已知主机密钥和hostname核验后上传项目专用server4入口，远端SHA256=6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0。首次核验因Windows文本管道CRLF失败，完整原样归档；改为UTF8字节传输后13:13:07+08核验通过。",
        "实际Conda解释器/home/songcl/.conda/envs/project_cluster/bin/python、PyTorch2.8.0+cu128正常加载，CUDA未初始化。通过后才把SERVERS的server4 conda_source绑定到项目独立入口；未改共享Python/依赖/模型、seed或schedule。此项仅证明部署和导入，不是完整原生模型、GPU计算、准入或训练。",
        "按ID及分页处理全部5项到期记录。主线保留原诊断/对照/原生反向/独立性4项通过和资源/约束2项失败：10.034588748G超过10G、实现修订2/2已用完。其余4项辅助路线的范围冻结未解除，只归档当前授权检查并将人工授权复查设为四小时后；所有100项科学阶段、门槛和修订历史不变，95项记录完全未动。",
        "当前科学状态blocked/human_authorization，执行状态POSTFLIGHT_PENDING。真实剩余前置条件是外部人工授权，不是显卡占用；用external_resource_blocked记录这一明确种类，不声称GPU不足、路线穷尽或deadline到达。未收到额外修订授权，不开启revision3，不制造新候选或填卡变体。",
        "本轮实际产出为项目专用环境入口部署与加载核验、1条传输失败留证、5项授权/操作记录更新；新候选/核心实现修订/原生前后向/优化步数/准入/训练全部0。实时GPU占用未知，不重复旧资源探针。收据用量此时未知，仅统计begin至收据的局部日志；缓存含于输入、推理含于输出，不重复相加，不视为账单。"
    ], "decisions": [
        "维持server3 GPU1和server4 GPU0两槽，只在现有科学准入门槛全部满足后派发。保留原始失败、四项辅助范围冻结及M201不自动恢复约束；环境编排修复不计为第三次模型实现修订。",
        "所有五项人工授权阻塞使用四小时复查和原goal/SERVERS/授权文件wake_paths；实际新授权可提前唤醒，计时本身不授予权限。不修改自动化或系统调度，不把操作记录数量当科研进展或成功率。",
        "运行finish，以真实postflight及租约释放核验决定是否COMPLETED；若不接受这一明确的人为授权阻塞，保留所有证据并abort，不改检查器、不假装GPU被占用、不等待截止。下次自动化精确触发时间未知。"
    ]}
    save(ROOT / ("pipeline/reports/notes_" + TOKEN + ".json"), notes)
    print(json.dumps({"runtime_loaded": True, "scientific_stages_gates_revisions_unchanged": 100, "fully_unchanged_candidates": 95, "administrative_updates": 5, "third_revision_authorized": False, "retry_after": retry}))


if __name__ == "__main__":
    main()
