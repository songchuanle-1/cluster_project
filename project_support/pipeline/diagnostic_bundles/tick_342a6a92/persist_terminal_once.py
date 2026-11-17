"""Persist the genuine archived M234 partial result without changing its revision."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
from reconcile_existing_once import guard, read, sha, save, ROOT, HERE


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP"}))
        return
    owner = guard()
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 60
    intent, output = HERE / "persist_terminal.intent.json", HERE / "persist_terminal.actual.json"
    assert not intent.exists() and not output.exists(), "Reconcile without replay."
    archive_path = HERE / "archive_execution_v2/archive_actual.json"
    archive = read(archive_path)
    assert archive["passed"] is True and archive["certainty"] == "terminal"
    assert archive["owner"] == owner and archive["state"] == "crashed"
    terminal_path = HERE / "reconcile.actual.json"
    assert sha(terminal_path) == "a2c1b89d1d60bbd25175900d41984d374ea21fc2e486ae5e56229f11bdbe6bad"
    terminal = read(terminal_path)["observation"]
    assert terminal["process"]["exists"] is False and terminal["project_trainers"] == []
    assert terminal["logs"]["registered_stdout"]["latest_native_step"] == [2, 4297]
    meta_path = HERE / "checkpoint_metadata.local_parse_v2.actual.json"
    assert sha(meta_path) == "2a6fd06e70e6b3b8825957b391198ef51fea638b09f822844e8467ca8bdfdaea"
    metadata = read(meta_path)
    assert metadata["owner"] == owner and metadata["passed"] is True
    for row in metadata["checkpoints"]:
        assert row["meta"]["epoch"] == 1 and row["meta"]["best_miou"] == 0.3192218840122223
        assert row["meta"]["epochs_no_improve"] == 0
        assert sha(row["prefix_source"]["path"]) == row["prefix_source"]["sha256"]
    sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        queue = read(ROOT / "pipeline/queue.json")
        assert not [t for tasks in queue["gpu_queues"].values() for t in tasks if t["id"] == "M234-RVE"]
        exp = read(ROOT / "pipeline/experiments/M234-RVE.json")
        assert exp["status"] == "crashed" and exp["archive_id"] == archive["archive_id"]
        path = ROOT / "pipeline/research_work.json"
        original = path.read_bytes()
        work = json.loads(original)
        candidate = next(c for c in work["candidates"] if c["id"] == "fine-leaf-receiver-conditioned-vector-exchange")
        revisions = copy.deepcopy(candidate["revision_history"])
        preserved = copy.deepcopy([c for c in work["candidates"] if c["id"] != candidate["id"]])
        now = datetime.now(timezone.utc).isoformat()
        paths = [
            terminal_path, HERE / "operational_review/m234_terminal_actual_independent_review.json",
            HERE / "checkpoint_metadata.actual.json", HERE / "metadata_prefix.actual.json",
            meta_path, archive_path, HERE / "archive_prepare_v2/FROZEN.json",
            ROOT / "pipeline/experiments/M234-RVE.json",
        ]
        paths.extend(p for p in (HERE / "operational_review").glob("*metadata*actual*review.json"))
        paths.extend(p for p in (HERE / "operational_review").glob("*archive*v2*review.json"))
        for item in paths:
            entry = ref(item)
            if entry not in candidate["evidence"]:
                candidate["evidence"].append(entry)
        next_action = (
            "Preserve M234 crashed run, exact logs and epoch1 best/last; no automatic restart/resume "
            "or consumed producer replay. DataLoader worker3815203 segfault is observed, underlying "
            "cause UNKNOWN. Diagnose missing worker/runtime history without repeating passed gates "
            "or treating partial training as mechanism falsification."
        )
        candidate.update(stage="complete", terminal_status="crashed", failure_scope="implementation",
                         blocker=None, dispatch_hold=None, next_action=next_action, updated_at=now)
        candidate.setdefault("operational_readiness_history", []).append(
            copy.deepcopy(candidate.get("current_owner_operational_readiness")))
        candidate["current_owner_operational_readiness"] = {
            "owner": owner, "kind": "READONLY_TERMINAL_RECONCILIATION",
            "status": "crashed", "process_alive": False, "new_launch_or_renewal": False,
            "terminal_evidence": ref(terminal_path), "canonical_archive": ref(archive_path),
        }
        candidate["terminal_observation"] = {
            "owner": owner, "archive_id": archive["archive_id"], "status": "crashed",
            "partial_epoch": 2, "partial_batch": 4297, "batches_per_epoch": 4686,
            "saved_complete_epoch": 1, "saved_checkpoint_best_miou": 0.3192218840122223,
            "saved_epochs_no_improve": 0, "full_training_complete": False,
            "observed_failure": "DataLoader worker3815203 segmentation fault; main RuntimeError",
            "underlying_root_cause": "UNKNOWN", "automatic_restart_authorized": False,
            "checkpoint_tensor_optimizer_contents_validated": False,
            "source_commit": "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e",
            "terminal_evidence": ref(terminal_path), "checkpoint_metadata": ref(meta_path),
            "canonical_archive": ref(archive_path),
            "canonical_archive_best_unknown_separate_from_checkpoint_metric": True,
        }
        assert candidate["revision_history"] == revisions
        assert preserved == [c for c in work["candidates"] if c["id"] != candidate["id"]]
        if work.get("tick_attempt"):
            work.setdefault("tick_attempt_history", []).append(work["tick_attempt"])
        work["tick_attempt"] = {
            "tick_started_at": owner["generated_at"], "candidate_id": candidate["id"],
            "kind": "resource_check", "result": "blocked",
            "command": "python -B -X utf8 " + str(HERE / "reconcile_existing_once.py") + " --execute-root",
            "observation": (
                "Exact read-only reconciliation confirms native crash at partial[2,4297], PID absent "
                "and no project trainer. GPU0 free6677MiB below original20000MiB startup budget; "
                "three original lock inodes preserved. No new diagnostic/training, signal or restart. "
                "This resource observation is timestamped; it is not efficacy or a hypothetical hold."
            ),
            "evidence": [ref(terminal_path), ref(HERE / "operational_review/m234_terminal_actual_independent_review.json")],
        }
        work.update(updated_at=now, last_event_tick=owner["generated_at"], next_action=next_action)
        work["last_terminal_event"] = {
            "id": "M234-RVE", "status": "crashed", "archive_id": archive["archive_id"],
            "recorded_at": now, "evidence": ref(archive_path),
        }
        memory_path = ROOT / "pipeline/codex_memory.md"
        memory = memory_path.read_text(encoding="utf-8")
        left, tail = memory.split("## Running And Queue\n", 1)
        _, right = tail.split("\n## Open Questions And Risks", 1)
        memory = left + (
            "## Running And Queue\n"
            "- M234-RVE已canonical crashed归档；原PID3813109不存在，项目trainer为空；队列/running仅清除此实验，M206/M227独立人工暂停保持。\n"
            "- 原生最后partial epoch2/batch4297 of4686；DataLoader worker3815203段错误引发main RuntimeError，未见OOM/正常终态；根因UNKNOWN，不重启。\n"
            "- best/last checkpoint均保存epoch1，exactbest .3192218840122223/noimp0；仅64KiB ZIP元数据前缀+非执行pickletools/struct解析，未验证tensor/optimizer完整内容。\n"
            "- 原21 source d21477b0/已消费stage/marker保留，不续签或重放；完整stdout/native日志已保存，canonical archivebestUNKNOWN与checkpointbest分开记录。\n"
            "- 13:19Z只读实测GPU0 free6677MiB<20000；三原锁dev66308/inodes92537152/53/54可用，外部任务不动。仅GPU0/max1/原协议和资源预算保持。\n"
        ) + "\n## Open Questions And Risks" + right
        memory = memory.replace(
            "21原owner真实启动；6d当前只读核验持续进度并对账",
            "21原owner启动后本轮已自然crashed归档，partial结果与epoch1 checkpoint分开保留")
        memory = memory.split("## Last Tick\n", 1)[0] + (
            "## Last Tick\n"
            "- 342a6a92，快照13:08:28Z/原deadline14:08:28Z；只读精确终态/源码/producer/GPU0核验，未发信号、重启、迁移或改训练数字。\n"
            "- 终态actual a2c1b89d/独审f60b33c4；原始primitive metadata不支持NumPy scalar的UNKNOWN结果124f90ba保留。\n"
            "- 实际64KiB前缀capture52c0903d；strict非执行f4解析2a6fd06e确认epoch1/best .3192218840122223，partial2/4297另记。\n"
            "- canonical finalize已完成，候选外层stage=complete/statuscrashed只表示运行结束；全部passed revision_history/native资源门槛与负证据保持，不作机制否定或novelty/效力结论。\n"
            "- 当前resource_check blocked有真实证据；报告/finish以后续实际收据为准。后续先诊断缺失worker/runtime历史，不重复通过的短检或自动重放已消费入口。\n"
        )
        assert len(memory.splitlines()) < 120 and memory.count("\n## ") == 7
        notes = {
            "actions": [
                "核实M234原PID已消失、无项目trainer；原生日志在第2轮4297/4686步报告DataLoader worker段错误，主进程异常退出，根因UNKNOWN。",
                "安全读取每个checkpoint最多64KiB元数据前缀，非执行解析确认best/last均epoch1、best mIoU=.3192218840122223/noimp0；完整训练与第2轮未完成。",
                "按独立复核通过的终态调用原canonical归档，仅移除M234运行登记并保存完整原始日志；其他任务/人工暂停/源码/预算保持。",
                "候选只更新外层终态和真实证据，完整已passed修订不变；本轮新资源观察free6677MiB低于20000MiB，未启动新GPU任务。",
            ],
            "decisions": [
                next_action,
                "保留partial结果、完整epoch1检查点及所有失败证据；canonical archive未知best和精确checkpointbest分开，不补签未知数据。",
                "保持仅server4GPU0、可共享/max1/原20GB预算及M206/M227人工暂停；不为额度新增变体、不将运行异常当作机制证伪。",
            ],
        }
        save(intent, {"owner": owner, "work_before_sha256": sha(path),
                      "archive_sha256": sha(archive_path), "metadata_sha256": sha(meta_path),
                      "revision_history_unchanged": True, "no_replay": True})
        save(HERE / "report_notes.json", notes)
        temporary = path.with_name("research_work.342a6a92.tmp")
        assert not temporary.exists()
        save(temporary, work)
        assert path.read_bytes() == original
        guard()
        os.replace(temporary, path)
        memory_path.write_text(memory, encoding="utf-8", newline="\n")
        save(output, {"owner": owner, "stage": "complete", "terminal_status": "crashed",
                      "archive_id": archive["archive_id"], "revision_history_unchanged": True,
                      "other_candidates_unchanged": True, "work_sha256": sha(path),
                      "memory_sha256": sha(memory_path), "new_training_or_signals": False})
        print(json.dumps({"path": str(output), "sha256": sha(output),
                          "stage": "complete", "state": "crashed", "revision_history_unchanged": True}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
