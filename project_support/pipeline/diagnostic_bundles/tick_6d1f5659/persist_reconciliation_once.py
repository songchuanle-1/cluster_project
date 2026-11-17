"""Reconcile only M234 audit fields from reviewed actual running-process evidence."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from observe_existing_once import guard, read, sha, save, ROOT, HERE, SOURCE

SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
ID = "fine-leaf-receiver-conditioned-vector-exchange"
PEER = HERE / "operational_review/current_existing_training_actual_independent_review.json"
PEER_SHA = "78924924bd17705834b1eeef73e43463e6d60ddb79b282f6ed929590761820b9"


def reference(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SHARED_MUTATION"}))
        return
    owner = guard()
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    intent, result = HERE / "persist.intent.json", HERE / "persist.actual.json"
    assert not intent.exists() and not result.exists(), "Reconcile without replay."
    assert sha(PEER) == PEER_SHA
    peer = read(PEER)
    assert peer["passed"] is True and peer["owner"] == owner and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (owner["thread_id"], "/root")
    before_path, after_path = HERE / "before.actual.json", HERE / "after.actual.json"
    assert sha(before_path) == "f724ccfc4c0b28ae060db12e66e9304c727f8add01859f336671d29b93c067a6"
    assert sha(after_path) == "cc4a42f0da210463f745ad7ea0fd02ccfc1e0ff08640b65a86caf96b6384ae16"
    observed = read(after_path)
    assert observed["owner"] == owner and observed["passed"] is True
    assert observed["native_step_growth_observed"] is True
    live = observed["observation"]
    assert live["pid"] == 3813109 and live["start_ticks"] == "183481242"
    assert live["source_commit"] == SOURCE and live["latest_native_step"] == [2, 3255]
    assert live["all_three_original_lock_inodes_inherited"] is True
    assert not any(live["error_markers"].values())
    old = ROOT / "pipeline/diagnostic_bundles/tick_21ebd237"
    historical_names = [
        "source_verify_execution/verify_actual.json",
        "operational_review/source_verifier_packet_independent_review.json",
        "rvec_production_prepare/FROZEN.json",
        "operational_review/rvec_production_delta_independent_review.json",
        "rvec_setup_execution/stage_actual.json", "rvec_setup_execution/collect_actual.json",
        "rvec_setup_execution/collect_result.json",
        "operational_review/rvec_collect_actual_independent_review.json",
        "rvec_setup_execution/production_activation.json",
        "rvec_setup_execution/render_actual.json", "rvec_setup_execution/render_result.json",
        "operational_review/rvec_render_actual_independent_review.json",
        "rvec_pointer_execution/switch_result.json",
        "rvec_dispatch_execution/rvec_prelaunch_actual_resources.json",
        "rvec_dispatch_execution/rvec_dispatch_result.json",
        "dispatch_proof_execution/dispatch_proof.json",
        "launch_observe_prepare/before.actual.json",
    ]
    historical = [reference(old / name) for name in historical_names]
    launch = read(old / "dispatch_proof_execution/dispatch_proof.json")
    assert launch["owner"]["token"] == "21ebd23722904fa3ac93d7330cbb58c1"
    assert launch["pid"] == live["pid"] and launch["start_ticks"] == live["start_ticks"]
    assert sha(old / "dispatch_proof_execution/dispatch_proof.json") == observed["historical_dispatch_proof_sha256"]
    current = [reference(path) for path in (
        HERE / "current_observer_binding.json", before_path, after_path,
        HERE / "native_summary.actual.json", PEER)]
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        queue_path, work_path = ROOT / "pipeline/queue.json", ROOT / "pipeline/research_work.json"
        queue, work = read(queue_path), read(work_path)
        before_work, before_queue = copy.deepcopy(work), copy.deepcopy(queue)
        candidate = next(item for item in work["candidates"] if item["id"] == ID)
        revisions = copy.deepcopy(candidate["revision_history"])
        assert hashlib.sha256(canonical(revisions).encode()).hexdigest() == "1e95d5a69b034f738cfce3459cd6ff564ee65c0e4ff699a15079732c9f78d70c"
        task = next(item for item in queue["gpu_queues"]["server-4"] if item["id"] == "M234-RVE")
        assert task["status"] == "running" and task["pid"] == live["pid"]
        assert task["launch_verified"] is True and task["launch_verification"] == "training_progress"
        assert task["code_commit"] == SOURCE and str(task["gpu"]) == "0"
        assert task["log"] == live["log"]
        protected_tasks = {server: [item for item in tasks if item["id"] != "M234-RVE"]
                           for server, tasks in queue["gpu_queues"].items()}
        protected_candidates = [item for item in work["candidates"] if item["id"] != ID]
        now = datetime.now(timezone.utc).isoformat()
        for entry in historical + current:
            if entry not in candidate["evidence"]:
                candidate["evidence"].append(entry)
        candidate.setdefault("runtime_resource_block_history", []).append({
            "blocker": candidate.get("blocker"),
            "runtime_resource_block": candidate.get("runtime_resource_block"),
            "reconciled_at": now, "observation": reference(after_path),
        })
        candidate.pop("runtime_resource_block", None)
        candidate["blocker"] = None
        candidate["dispatch_hold"] = None
        candidate.update(stage="training", queued=True, deployed=True, source_synced=True,
                         training_started=True, runtime_code_commit=SOURCE, updated_at=now)
        next_action = (
            "Protect and monitor the existing M234 PID3813109/start183481242 on server4 GPU0; "
            "observe native training/validation and natural terminal state with bounded reads. "
            "Never relaunch or replay the consumed21 production entry. M206/M227 remain manually paused. "
            "Interim metrics and checkpoint metadata are not completed training, efficacy or novelty."
        )
        candidate["next_action"] = next_action
        candidate.setdefault("operational_readiness_history", []).append(
            copy.deepcopy(candidate.get("current_owner_operational_readiness")))
        candidate["current_owner_operational_readiness"] = {
            "owner": owner, "kind": "READONLY_EXISTING_TRAINER_RECONCILIATION",
            "original_launch_owner": launch["owner"],
            "launch_verified": True, "native_step_growth_observed": True,
            "pid": live["pid"], "start_ticks": live["start_ticks"],
            "source_commit": SOURCE, "latest_native_step": live["latest_native_step"],
            "observation": reference(after_path), "independent_review": reference(PEER),
            "new_launch_or_renewed_lease": False,
        }
        assert candidate["revision_history"] == revisions
        if work.get("tick_attempt"):
            work.setdefault("tick_attempt_history", []).append(work["tick_attempt"])
        work["tick_attempt"] = {
            "tick_started_at": owner["generated_at"], "candidate_id": ID,
            "kind": "resource_check", "result": "passed",
            "command": (
                "python -B -X utf8 " + str(HERE / "observe_existing_once.py") +
                " --execute-root --label after --previous " + str(before_path) +
                " --previous-sha256 f724ccfc4c0b28ae060db12e66e9304c727f8add01859f336671d29b93c067a6"
            ),
            "observation": (
                "Read-only current running-process resource/identity check passed: authorized GPU0, "
                "same PID/start/d214 and consumed original marker, all three original lock FDs, "
                "one registered project task/max1, native steps [2,2991] to [2,3255], no sampled errors. "
                "No launch, diagnostic GPU computation, signal, restart or original-owner relabelling."
            ),
            "evidence": [reference(before_path), reference(after_path), reference(PEER)],
        }
        work.update(updated_at=now, last_event_tick=owner["generated_at"], next_action=next_action)
        task.update(training_started=True, dispatch_phase="verified")
        assert protected_candidates == [item for item in work["candidates"] if item["id"] != ID]
        assert protected_tasks == {server: [item for item in tasks if item["id"] != "M234-RVE"]
                                   for server, tasks in queue["gpu_queues"].items()}
        memory_path = ROOT / "pipeline/codex_memory.md"
        memory = memory_path.read_text(encoding="utf-8")
        running = (
            "## Running And Queue\n"
            "- M234-RVE实际running，原PID3813109/start183481242/source d21477b0；原21 owner启动，6d仅只读观察，不续签或重放原入口。\n"
            "- 本轮同进程native[2,2991]->[2,3255]增长，三原锁FD dev66308/inodes92537152/53/54保持；限流样本无错误/终态标记。\n"
            "- 21原生产stage rvec_path_prod_21ebd237已消费，SERVERS SHAe622e3d4；禁止再执行。runtime仍Cluster_nsd_20261107，本地主HEAD0747/index/user28/r0九文件保持。\n"
            "- 原生实时FD发现workdir Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rvec/20261109_175800；best/last.pth文件各918230926B，未加载内容。\n"
            "- canonical监控阶段Best约.3192、训练epoch2、noimp0/10；本轮128KiB native tail缺精确验证与完整epoch计数，均不补猜。完整训练/效力/novelty未完成。\n"
            "- 6503MiB旧阻塞保留为历史，由21真实启动和当前进度解除；资源只允许server4GPU0/max1/原20000MiB启动预算/可共享外部负载。M206/M227独立人工暂停保持。\n"
        )
        left, tail = memory.split("## Running And Queue\n", 1)
        _, right = tail.split("\n## Open Questions And Risks", 1)
        memory = left + running + "\n## Open Questions And Risks" + right
        memory = memory.replace(
            "本轮另存新owner ee6f5eda只读验证和CPU生产render通过",
            "21原owner真实启动；6d当前只读核验持续进度并对账")
        memory = memory.replace("本轮r1构造对照", "历史r1构造对照")
        memory = memory.split("## Last Tick\n", 1)[0] + (
            "## Last Tick\n"
            "- 6d1f5659，快照2026-11-09T11:09:33Z/原deadline12:09:33Z；仅观察既有M234，未启动、重测、改代码或新增配额候选。\n"
            "- 21 canonical派发/proof/单次观察按原owner补入候选外层；21收尾INCOMPLETE/released保留，未改写历史收据或租约。\n"
            "- 当前before f724ccfc / after cc4a42f0 / native summary2cb7ed25 / 独审78924924通过；原native两步/common841/core和资源证据复用不重测。\n"
            "- 候选stage=training，旧6503显存block转历史；queue仅修正M234训练已开始/verified事实，其他任务不动，完整revision_history保持。\n"
            "- 当前真实只读resource_check作为本轮attempt；报告/finish结果以后续真实收据为准。下一轮继续限流监控原生训练/验证和自然终态，不重放已消费入口。\n"
        )
        assert len(memory.splitlines()) < 120 and memory.count("\n## ") == 7
        notes = {
            "actions": [
                "只读核验既有M234同PID/start/d214，原生第2轮步数2991至3255增长，三把原锁FD保持，样本无错误或终态标记。",
                "从实际打开的原生logger FD发现workdir和best/last checkpoint文件；本轮限流tail未覆盖精确验证，未补猜完整epoch数或checkpoint内容。",
                "补记21实际启动证据并纠正候选和队列的过时等待字段；所有原owner/hash、失败及已完成修订保持，未续签、重放或重新启动。",
                "本轮完成真实运行资源检查和独立复核；仅更新M234事实与七节记忆，report/finish的真实结果仍待收据。",
            ],
            "decisions": [
                next_action,
                "保持仅server4GPU0/共享外部任务/max1和原启动显存预算；不触碰M206/M227人工暂停，不改变目标、数据、训练数字、bans或调度。",
                "本轮优先补齐已启动候选的真实进度与审计缺项，不为候选额度新增变体，不将阶段指标写成效力或novelty。",
            ],
        }
        evidence_before = {"work": sha(work_path), "queue": sha(queue_path), "memory": sha(memory_path)}
        save(intent, {"owner": owner, "recorded_at": now, "before": evidence_before,
                      "review_sha256": PEER_SHA, "only_M234_reconciliation": True, "no_replay": True})
        save(HERE / "research_work.before.json", before_work)
        save(HERE / "queue.before.json", before_queue)
        save(HERE / "report_notes.json", notes)
        guard()
        monitor.save_queue(str(ROOT), queue)
        temporary = work_path.with_name("research_work.6d1f5659.tmp")
        assert not temporary.exists()
        save(temporary, work)
        assert sha(work_path) == evidence_before["work"]
        os.replace(temporary, work_path)
        memory_path.write_text(memory, encoding="utf-8", newline="\n")
        assert read(work_path)["candidates"] == work["candidates"]
        assert read(queue_path) == queue
        save(result, {
            "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
            "before": evidence_before,
            "after": {"work": sha(work_path), "queue": sha(queue_path), "memory": sha(memory_path)},
            "stage": "training", "training_started": True,
            "native_step_growth_observed": True, "revision_history_unchanged": True,
            "other_candidates_and_tasks_unchanged": True,
            "old_launch_owner_preserved": True, "new_launch_or_GPU_compute": False,
        })
        print(json.dumps({"path": str(result), "sha256": sha(result),
                          "stage": "training", "revision_history_unchanged": True,
                          "memory_lines": len(memory.splitlines()), "report_notes": str(HERE / "report_notes.json")}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
