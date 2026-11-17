"""Persist reviewed diagnostic results under this lease, never a model revision."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from run_kernel_suffix_once import ROOT, HERE, guard, read, sha, save

CID = "fine-leaf-receiver-conditioned-vector-exchange"


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def main():
    owner = guard()
    final = read(HERE / "diagnosis.final.json")
    assert final["owner"] == owner
    assert final["root_cause"] == "UNKNOWN"
    assert final["historical_crash_reproduced"] is False
    assert final["training_repair_verified"] is False
    assert final["tick_attempt"]["result"] in ("passed", "failed", "blocked")
    assert final["tick_attempt"]["kind"] in ("implementation_test", "resource_check")
    refs = final["evidence"]
    assert refs and all(
        (ROOT / item["path"]).resolve().is_relative_to(HERE)
        and sha(ROOT / item["path"]) == item["sha256"] for item in refs)
    notes = read(HERE / "report_notes.json")
    assert all(isinstance(notes[k], list) and notes[k]
               and all(isinstance(x, str) and x for x in notes[k])
               for k in ("actions", "decisions"))
    assert not (HERE / "record.actual.json").exists()

    before = read(HERE / "integrity_before.json")
    repo = Path(before["local_main_root"])
    assert subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip() == before["local_main_HEAD"]
    assert sha(repo / ".git/index") == before["git_index_sha256"]
    work_path = ROOT / "pipeline/research_work.json"
    work = read(work_path)
    candidate = next(x for x in work["candidates"] if x["id"] == CID)
    assert candidate["stage"] == "complete" and candidate["terminal_status"] == "crashed"
    assert digest(candidate["revision_history"]) == before["revision_history_sha256"]
    revisions = deepcopy(candidate["revision_history"])
    terminal = deepcopy(candidate["terminal_observation"])
    now = datetime.now(timezone.utc).isoformat()
    history_entry = {
        "owner": owner, "recorded_at": now,
        "scope": final["scope"], "root_cause": "UNKNOWN",
        "diagnosis": {
            "path": str((HERE / "diagnosis.final.json").relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha(HERE / "diagnosis.final.json"),
        },
        "evidence": refs,
        "historical_worker_native_fault_frame_obtained": False,
        "historical_crash_reproduced": False,
        "training_repair_verified": False,
        "no_training_or_model_revision": True,
    }
    candidate.setdefault("worker_diagnosis_history", []).append(history_entry)
    for item in refs:
        if item not in candidate.setdefault("evidence", []):
            candidate["evidence"].append(item)
    diagnosis_ref = history_entry["diagnosis"]
    if diagnosis_ref not in candidate["evidence"]:
        candidate["evidence"].append(diagnosis_ref)
    candidate["next_action"] = final["next_action"]
    candidate["updated_at"] = now
    old_attempt = work.get("tick_attempt")
    if old_attempt:
        history = work.setdefault("tick_attempt_history", [])
        if old_attempt not in history:
            history.append(deepcopy(old_attempt))
    work["tick_attempt"] = {
        "tick_started_at": owner["generated_at"], "candidate_id": CID,
        **final["tick_attempt"], "evidence": refs + [diagnosis_ref],
    }
    work["last_event_tick"] = owner["generated_at"]
    work["next_action"] = final["next_action"]
    work["updated_at"] = now
    assert candidate["revision_history"] == revisions
    assert candidate["terminal_observation"] == terminal

    memory_path = ROOT / "pipeline/codex_memory.md"
    memory = memory_path.read_text(encoding="utf-8")
    assert memory.count("## ") == 7 and "## Last Tick\n" in memory
    memory = memory.split("## Last Tick\n", 1)[0] + "## Last Tick\n" + final["memory_last_tick"] + "\n"
    memory = memory.replace("21原owner启动后本轮已自然crashed归档",
                            "21原owner启动后已自然crashed归档")
    assert len(memory.splitlines()) < 120 and memory.count("## ") == 7
    save(HERE / "research_work.before.json", read(work_path))
    save(HERE / "memory.before.json", {"text": memory_path.read_text(encoding="utf-8")})
    guard()
    work_path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    memory_path.write_text(memory, encoding="utf-8")
    reread = read(work_path)
    current = next(x for x in reread["candidates"] if x["id"] == CID)
    assert current["revision_history"] == revisions
    assert current["terminal_observation"] == terminal
    assert digest(current["revision_history"]) == before["revision_history_sha256"]
    assert sha(repo / ".git/index") == before["git_index_sha256"]
    assert subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip() == before["local_main_HEAD"]
    save(HERE / "record.actual.json", {
        "owner": owner, "recorded_at": now,
        "work_sha256": sha(work_path), "memory_sha256": sha(memory_path),
        "completed_revision_history_unchanged": True,
        "terminal_archive_observation_unchanged": True,
        "main_HEAD_and_index_unchanged": True,
        "candidate_stage": current["stage"],
        "candidate_terminal_status": current["terminal_status"],
        "new_queue_or_training_or_model_revision": False,
    })
    print(json.dumps({
        "status": "DIAGNOSTIC_EVIDENCE_RECORDED_ONLY",
        "path": str(HERE / "record.actual.json"),
        "sha256": sha(HERE / "record.actual.json"),
        "revision_history_unchanged": True,
    }))


if __name__ == "__main__":
    main()
