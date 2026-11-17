"""Persist the actual bounded CPU result while the original tick lease is held."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path("D:/project/cluster_project")
BUNDLE = ROOT / "pipeline/diagnostic_bundles/tick_9dfa43fa"
TOKEN = "9dfa43fa89ad4dc4832126a940ed821e"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CID = "hierarchy-native-distribution-embedding-composition"
ACTUAL_SHA = "e9d384828f55b55ff23e4c0a0d67e68f863021e9563d0e5c98d47601390efd5f"
RECEIPT_SHA = "52bf897dc89729063ffb429035b1cd07f14d3ea8d3e690812a4e3adfb48ed266"
SERVERS_SHA = "62e4595edb002ed4c1340372ef2afc3d5dc9ba75a2a40f74b6752db61cbad9b3"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def reference(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path)}


def create(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded(value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print("DEFAULT_NOP")
        return
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("CODEX_THREAD_ID") == THREAD
    owner_path = ROOT / "pipeline/headless/.foreground.lockdir/owner.json"
    owner = read(owner_path)
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    for name, field in [
        (".tick_context.json", "context_sha256"),
        (".tick_context_state.next.json", "pending_sha256"),
    ]:
        assert digest(ROOT / "pipeline/headless" / name) == owner[field]
    receipt_path = ROOT / "pipeline/admissions/M233-NDE.json"
    servers_path = ROOT / "SERVERS.yaml"
    assert digest(receipt_path) == RECEIPT_SHA
    assert digest(servers_path) == SERVERS_SHA
    actual_path = BUNDLE / "faketensor_cpu_prepare/cpu_actual.json"
    review_path = BUNDLE / "operational_review/faketensor_cpu_actual_independent_review.json"
    assert digest(actual_path) == ACTUAL_SHA
    assert args.review_sha256 and digest(review_path) == args.review_sha256
    actual = read(actual_path)
    review = read(review_path)
    assert review.get("passed") is True
    assert actual["owner"]["token"] == TOKEN
    assert actual["returncode"] == 0 and actual["certainty"] == "terminal"
    observation = actual["observation"]
    assert observation["status"] == "CPU_DIAGNOSTIC_OBSERVATION_COMPLETE"
    assert len(observation["cases"]) == 3
    assert all(case["returned"] for case in observation["cases"])
    assert observation["cases"][0]["observation"]["expected_false"] is True
    assert all(observation[key] is True for key in [
        "python_rng_restored_exact", "torch_CPU_rng_restored_exact",
        "numpy_rng_restored_exact",
    ])
    assert observation["cuda_initialized_before"] is False
    assert observation["cuda_initialized_after"] is False
    assert observation["constructor_text_control"]["expected_TypeError"] is True
    assert observation["root_cause"] == "UNKNOWN"
    assert not actual["GPU_use"] and not actual["remote_files_written"]
    work_path = ROOT / "pipeline/research_work.json"
    memory_path = ROOT / "pipeline/codex_memory.md"
    queue_path = ROOT / "pipeline/queue.json"
    work_sha_before = digest(work_path)
    memory_sha_before = digest(memory_path)
    queue_sha_before = digest(queue_path)
    work = read(work_path)
    candidate = next(item for item in work["candidates"] if item["id"] == CID)
    assert candidate["stage"] == "complete"
    assert candidate["native_full_training"]["status"] == "crashed"
    assert not candidate["queued"] and candidate["training_started"] is True
    revision_before = copy.deepcopy(candidate["revision_history"])
    others_before = copy.deepcopy([item for item in work["candidates"] if item["id"] != CID])
    stamp = datetime.now(timezone.utc).isoformat()
    refs = [reference(actual_path), reference(review_path)]
    explanation = (
        "Fresh CPU Parameter isinstance(FakeTensor), Tiny identity _apply, and Tiny "
        "CPU float64 _apply all returned successfully, once each. Python/Torch CPU/"
        "NumPy RNG restored exactly; CUDA remained uninitialized. The explicit "
        "zero-argument FakeTensor constructor TypeError is a separate text control. "
        "This does not reproduce or repair the dead native training process; its "
        "root cause, efficacy and novelty remain UNKNOWN. No training or GPU execution."
    )
    diagnosis = {
        "schema_version": 1, "recorded_at": stamp, "owner_token": TOKEN,
        "candidate_id": CID, "experiment_id": "M233-NDE",
        "scope": "FRESH_BOUNDED_CPU_FAKETENSOR_TYPE_PATH_ONLY",
        "result": "passed", "observation": explanation, "evidence": refs,
        "source_commit": observation["source_commit"],
        "runtime_root": observation["runtime_root"],
        "runtime_HEAD": observation["runtime_HEAD"],
        "producer_sha256": actual["producer_sha256"],
        "request_sha256": actual["request_sha256"],
        "root_cause": "UNKNOWN", "mechanism_rejected": False,
        "original_training_reproduced": False, "repair_proven": False,
        "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
        "training_or_restart_authorized": False, "GPU_use": False,
        "canonical_terminal_archive": reference(BUNDLE / "canonical_terminal_archive.json"),
    }
    diagnosis_path = BUNDLE / "faketensor_cpu_diagnosis.json"
    create(diagnosis_path, diagnosis)
    refs.append(reference(diagnosis_path))
    previous_attempt = work.get("tick_attempt")
    assert previous_attempt and previous_attempt["tick_started_at"] != owner["generated_at"]
    work.setdefault("tick_attempt_history", []).append(previous_attempt)
    work["tick_attempt"] = {
        "tick_started_at": owner["generated_at"], "candidate_id": CID,
        "kind": "implementation_test", "result": "passed",
        "command": [
            "python", "-B", "-X", "utf8",
            str(BUNDLE / "faketensor_cpu_prepare/run_cpu_probe_once.py"),
            "--execute-root", "--review",
            str(BUNDLE / "operational_review/faketensor_cpu_source_independent_review.json"),
            "--review-sha256",
            "5eac5a54f5a87da60d8619d8e73c12bf33b4dfaf6d36e21860a6702ce6d8298f",
        ],
        "observation": explanation, "evidence": refs,
    }
    for entry in refs:
        if entry not in candidate["evidence"]:
            candidate["evidence"].append(entry)
    candidate["faketensor_cpu_diagnostic"] = {
        "recorded_at": stamp, "owner_token": TOKEN, "result": "passed",
        "scope": diagnosis["scope"], "evidence": refs,
        "root_cause": "UNKNOWN", "repair_proven": False,
    }
    candidate["updated_at"] = stamp
    candidate["next_action"] = (
        "保留M233 crashed归档ca1f72e20e4b4d469abf0ec40a6b1528、原始traceback及全部历史失败。"
        "仅partial epoch1/932，完整epoch/验证0、无训练pth、best UNKNOWN。"
        "本轮新CPU三项类型路径核验通过且独审，不重现或修复旧训练进程，根因UNKNOWN。"
        "后续仅在有可区分的新故障对象或新证据时推进有界诊断，避免重复同一fresh CPU健康测试。"
        "禁止自动重启/resume、重放已消费shim/旧lease；人工暂停和全部资源/科学约束保持。"
        "没有证据支持的独立机制时不为配额新增。"
    )
    work["next_action"] = candidate["next_action"]
    old_diagnosis = work.get("latest_runtime_failure_diagnosis")
    if old_diagnosis:
        work.setdefault("runtime_failure_diagnosis_history", []).append(old_diagnosis)
    work["latest_runtime_failure_diagnosis"] = {
        "recorded_at": stamp, "experiment_id": "M233-NDE",
        "root_cause": "UNKNOWN", "scope": diagnosis["scope"],
        "evidence": refs, "training_repair_or_reproduction": False,
        "next_observation": "Distinct future live failure-object evidence only; no old-run replay.",
    }
    archive = read(BUNDLE / "canonical_terminal_archive.json")
    work["last_event_tick"] = owner["generated_at"]
    work["last_terminal_event"] = {
        "recorded_at": archive["recorded_at"], "experiment_id": "M233-NDE",
        "status": "crashed", "archive_id": archive["archive_id"],
    }
    work["updated_at"] = stamp
    assert candidate["revision_history"] == revision_before
    assert [item for item in work["candidates"] if item["id"] != CID] == others_before
    memory = memory_path.read_text(encoding="utf-8-sig")
    old_line = "- 独立有限路线复核未找到现有诊断支持且不重叠的新机制，不为配额创建。新FakeTensor专门CPU类型路径探针准备中；不重复旧128遍历/旧健康provenance，不用fresh CPU健康冒充旧进程已修复。"
    new_line = "- 独立有限路线复核未找到现有诊断支持且不重叠的新机制，不为配额创建。19:46Z新FakeTensor CPU探针实际3/3通过，Python/Torch/NumPy RNG精确恢复、CUDA false→false；独审通过。零参数构造报错仅文本对照，不重现原故障或证明修复。"
    assert memory.count(old_line) == 1
    memory = memory.replace(old_line, new_line)
    old_end = "- 需保存当前CPU实际结果和独审后report/finish并核释放；不重放已消费生产入口或旧lease。后续诊断需实际对象/绑定证据，不能从旧进程已丢失状态补签。"
    new_end = "- 当前CPU实际结果/独审/新tick_attempt已保存，待canonical report/finish核验释放；不重放已消费生产入口或旧lease。根因仍UNKNOWN；后续诊断需可区分的新对象/证据，不从旧进程已丢失状态补签。"
    assert memory.count(old_end) == 1
    memory = memory.replace(old_end, new_end).replace("- 本轮派发前YAML检查", "- 前轮派发前YAML检查")
    assert len(memory.splitlines()) < 120
    assert digest(work_path) == work_sha_before and digest(memory_path) == memory_sha_before
    assert read(owner_path)["token"] == TOKEN
    work_path.write_text(encoded(work), encoding="utf-8", newline="\n")
    memory_path.write_text(memory, encoding="utf-8", newline="\n")
    assert read(work_path)["tick_attempt"]["evidence"] == refs
    assert digest(receipt_path) == RECEIPT_SHA and digest(servers_path) == SERVERS_SHA
    assert digest(queue_path) == queue_sha_before
    notes = {
        "actions": [
            "19:09/19:12Z原生两次核验M233 PID已退出，最后partial epoch1 step932/4686；完整epoch/验证0、无训练pth、best UNKNOWN。",
            "19:26Z按canonical finalize_task锁内归档crashed，archive ca1f72e20e4b4d469abf0ec40a6b1528；完整stdout302970字节已保存及独审，其他队列行保持。",
            "19:46Z只执行一次新FakeTensor CPU类型路径诊断，3/3通过，RNG精确恢复且CUDA未初始化；源代码与实际结果分别独审，新结果仅追加候选外层证据。",
        ],
        "decisions": [
            "FakeTensor.__new__异常仍为runtime implementation-inconclusive，根因UNKNOWN；新CPU健康与零参数文本对照均不能证明原故障已重现或修复，不作效力/novelty结论。",
            "M233完整历史准入与最终revision保持不可变；不重启/resume或重放已消费入口，M206/M227人工暂停及server4 GPU0资源授权保持。",
            "本轮有限独立路线复核无证据支持的新机制，不为配额创建或建立全局冷却；当前真实implementation_test已留档，后续依新对象/证据继续。",
        ],
    }
    notes_path = BUNDLE / "tick_notes.json"
    create(notes_path, notes)
    audit = {
        "recorded_at": stamp, "owner_token": TOKEN,
        "work_before_sha256": work_sha_before, "work_after": reference(work_path),
        "memory_before_sha256": memory_sha_before, "memory_after": reference(memory_path),
        "candidate_id": CID, "attempt_evidence": refs,
        "revision_history_unchanged": True, "other_candidate_records_unchanged": True,
        "receipt_unchanged_sha256": RECEIPT_SHA, "SERVERS_unchanged_sha256": SERVERS_SHA,
        "queue_unchanged_sha256": queue_sha_before, "notes": reference(notes_path),
        "report_finish": "NOT_YET_EXECUTED",
    }
    create(BUNDLE / "current_tick_persistence.json", audit)
    print(json.dumps({
        "status": "CURRENT_ACTUAL_CPU_OUTCOME_PERSISTED",
        "diagnosis": reference(diagnosis_path), "notes": str(notes_path),
        "revision_receipt_queue_resources_preserved": True,
    }))


if __name__ == "__main__":
    main()
