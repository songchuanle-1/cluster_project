"""Persist reviewed diagnostic results under this lease, never a model revision."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import argparse,os,sys
ROOT=Path("D:/project/cluster_project")
HERE=Path(__file__).resolve().parent
EXPECTED_OWNER={'token': '4ecb5020c4c54abeb26dc874ed90080e', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-10T01:06:58.009358+00:00', 'deadline_at': '2026-11-10T02:06:58.009358+00:00', 'context_sha256': 'a143a825802aa28c5db3b61c93314f0b2d764e02ed0cb7008d88c8e6bc280f4d', 'pending_sha256': '71bc1ed72a827fe476a5e8492671d879e0d24bec5b16a3bd674f3022994ea08d'}
KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
SOURCE_BASELINE=ROOT/"pipeline/diagnostic_bundles/tick_558ef1ee/rvec_deployment_prepare/baseline.json"
def read(path):return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
 with Path(path).open("x",encoding="utf-8",newline="\n") as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write("\n")
def guard():
 assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS")=="0"
 value=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json");owner={k:value[k] for k in KEYS}
 assert owner==EXPECTED_OWNER and owner["thread_id"]==os.environ.get("CODEX_THREAD_ID")
 assert datetime.now(timezone.utc)<datetime.fromisoformat(owner["deadline_at"])
 for n,k in ((".tick_context.json","context_sha256"),(".tick_context_state.next.json","pending_sha256")):assert sha(ROOT/"pipeline/headless"/n)==owner[k]
 mode=read(ROOT/"pipeline/execution_mode.json");assert mode["mode"]=="foreground" and mode["target_thread_id"]==owner["thread_id"]
 assert sha(SOURCE_BASELINE)=="7dac0d4325086e4d338f32fe49d45d970d43653691d67bee8f69c18ffdbbe12a"
 return owner


CID = "fine-leaf-receiver-conditioned-vector-exchange"


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root",action="store_true")
    parser.add_argument("--diagnosis-sha256")
    parser.add_argument("--notes-sha256")
    args=parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status":"DEFAULT_NOP_NO_SHARED_MUTATION"}));return
    owner = guard()
    assert args.diagnosis_sha256 and sha(HERE/"diagnosis.final.json")==args.diagnosis_sha256
    assert args.notes_sha256 and sha(HERE/"report_notes.json")==args.notes_sha256
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
    assert before["owner"] == owner
    assert sha(ROOT/"pipeline/goal.json")==before["goal_sha256"] and sha(ROOT/"SERVERS.yaml")==before["servers_sha256"]
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
    assert digest(candidate["terminal_observation"]) == before["terminal_observation_sha256"]
    source_before=read(SOURCE_BASELINE)
    protected_source={str(ROOT/"Cluster"/name):expected for name,expected in {**source_before["dirty_files_exact28"],**source_before["working_tree_r0_files_exact9"]}.items()}
    assert all(sha(path)==expected for path,expected in protected_source.items())
    original_work=deepcopy(work)
    invariant_maps={c["id"]:{k:deepcopy(c.get(k)) for k in ("revision_history","terminal_observation")} for c in work["candidates"]}
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
        **final["tick_attempt"], "tick_started_at": owner["generated_at"], "candidate_id": CID, "evidence": refs + [diagnosis_ref],
    }
    work["last_event_tick"] = owner["generated_at"]
    work["next_action"] = final["next_action"]
    work["updated_at"] = now
    assert candidate["revision_history"] == revisions
    assert candidate["terminal_observation"] == terminal
    assert all(c==next(old for old in original_work["candidates"] if old["id"]==c["id"]) for c in work["candidates"] if c["id"]!=CID)

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
    assert all({k:c.get(k) for k in ("revision_history","terminal_observation")}==invariant_maps[c["id"]] for c in reread["candidates"])
    assert all(sha(path)==expected for path,expected in protected_source.items())
    assert sha(ROOT/"pipeline/goal.json")==before["goal_sha256"] and sha(ROOT/"SERVERS.yaml")==before["servers_sha256"]
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
