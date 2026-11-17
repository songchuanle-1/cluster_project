"""Default NOP. Current-owner root-only registration of M235-SINC and M236-CSO."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parents[1]
OWNER = {
    "token": "4ecb5020c4c54abeb26dc874ed90080e",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-10T01:06:58.009358+00:00",
    "deadline_at": "2026-11-10T02:06:58.009358+00:00",
    "context_sha256": "a143a825802aa28c5db3b61c93314f0b2d764e02ed0cb7008d88c8e6bc280f4d",
    "pending_sha256": "71bc1ed72a827fe476a5e8492671d879e0d24bec5b16a3bd674f3022994ea08d",
}
SPECS = (
    ("sinc", "M235-SINC", "fine-leaf-geometric-simplex-incidence-composition", "new_design_b", "source_manifest.json"),
    ("cso", "M236-CSO", "fine-leaf-full-covariance-shape-composition", "new_design_a", "candidate.json"),
)
BASELINE = ROOT / "pipeline/diagnostic_bundles/tick_558ef1ee/rvec_deployment_prepare/baseline.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def ref(path):
    path = Path(path).resolve()
    assert path.is_relative_to(TICK)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    assert sys.dont_write_bytecode and not sys.flags.optimize
    assert os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: live[key] for key in OWNER} == OWNER
    assert datetime.now(timezone.utc) < datetime.fromisoformat(OWNER["deadline_at"])
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == OWNER[key]
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == OWNER["thread_id"]
    before = read(TICK / "integrity_before.json")
    assert before["owner"] == OWNER
    assert sha(ROOT / "pipeline/goal.json") == before["goal_sha256"]
    assert sha(ROOT / "SERVERS.yaml") == before["servers_sha256"]
    repo = Path(before["local_main_root"])
    assert sha(repo / ".git/index") == before["git_index_sha256"]
    assert subprocess.check_output(["git", "--no-optional-locks", "-C", str(repo), "rev-parse", "HEAD"],
                                   text=True).strip() == before["local_main_HEAD"]
    assert sha(BASELINE) == "7dac0d4325086e4d338f32fe49d45d970d43653691d67bee8f69c18ffdbbe12a"
    baseline = read(BASELINE)
    protected = {**baseline["dirty_files_exact28"], **baseline["working_tree_r0_files_exact9"]}
    assert all(sha(ROOT / "Cluster" / path) == value for path, value in protected.items())
    return before


def dictionaries(value):
    if isinstance(value, dict):
        yield value
        for part in value.values():
            yield from dictionaries(part)
    elif isinstance(value, list):
        for part in value:
            yield from dictionaries(part)


def observation(actual_path, review_path, cid, mode):
    if actual_path is None:
        assert review_path is None
        return {"status": "NOT_RUN", "evidence": [], "reviewed": False, "actual_passed": False}
    path = Path(actual_path).resolve()
    evidence = [ref(path)]
    actual = read(path)
    assert actual.get("owner") == OWNER, "Actual must belong to this tick owner."
    nodes = list(dictionaries(actual))
    results = [node for node in nodes if node.get("candidate_id") == cid and node.get("mode") == mode]
    result = results[0] if results else {}
    terminal = actual.get("certainty") == "terminal"
    if mode == "smoke":
        passed = (terminal and result.get("execution_completed") is True
                  and result.get("native_smoke_checks_passed") is True
                  and result.get("optimizer_steps") == 2
                  and result.get("native_criterion_backwards") == 2
                  and result.get("native_loss_forwards") == 2
                  and result.get("backward_finite") is True
                  and result.get("native_tracked_each_parameter_updated") is True
                  and result.get("original_common_initialization_comparison", {}).get("passed") is True)
    else:
        passed = (terminal and result.get("execution_completed") is True
                  and result.get("batch_size") == 1 and result.get("lang_num_max") == 1
                  and result.get("warmup") == 20 and result.get("repeat") == 100
                  and result.get("profile", {}).get("within10G") is True)
    reviewed = False
    if review_path:
        review_file = Path(review_path).resolve()
        evidence.append(ref(review_file))
        review = read(review_file)
        assert review.get("owner") == OWNER
        assert review.get("passed") is True and review.get("material_concerns", []) == []
        assert any(node.get("sha256") == sha(path) or node.get("actual_sha256") == sha(path)
                   for node in dictionaries(review)), "Review must explicitly bind the supplied actual SHA."
        reviewed = True
    failure = (actual.get("returncode") not in (None, 0)
               or any(node.get("error_type") for node in nodes)
               or (terminal and result and result.get("execution_completed") is False))
    status = "PASSED" if passed and reviewed else ("OBSERVED_PASSED_AWAITING_REVIEW" if passed else
             ("FAILED_OR_INCONCLUSIVE" if failure else "UNCERTAIN_OR_INCOMPLETE"))
    return {"status": status, "evidence": evidence, "reviewed": reviewed, "actual_passed": passed,
            "result_summary": {key: result.get(key) for key in
                ("execution_completed", "optimizer_steps", "native_criterion_backwards", "error_type", "error")},
            "actual_candidate_result_found": bool(result)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--tick-attempt-actual", type=Path)
    for key, *_ in SPECS:
        for kind in ("native", "resources"):
            parser.add_argument("--" + key + "-" + kind + "-actual", type=Path)
            parser.add_argument("--" + key + "-" + kind + "-review", type=Path)
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SHARED_WRITES_OR_SSH"}))
        return
    guard()
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER and all(sha(HERE / n) == h for n, h in frozen["files"].items())
    assert all(sha(ROOT / a["path"]) == a["sha256"] for a in frozen["anchors"])
    assert not (HERE / "record.intent.json").exists() and not (HERE / "record.actual.json").exists()
    assert not (TICK / "report_notes.json").exists(), "Preserve pre-existing root notes; reconcile instead of overwriting."
    work_path, memory_path = ROOT / "pipeline/research_work.json", ROOT / "pipeline/codex_memory.md"
    work = read(work_path)
    original = deepcopy(work)
    assert len(work["candidates"]) == 160
    assert not any(c["id"] in {spec[2] for spec in SPECS} for c in work["candidates"])
    assert not any(c.get("experiment_id") in {"M235-SINC", "M236-CSO"} for c in work["candidates"])
    old_work_sha, old_memory_sha = sha(work_path), sha(memory_path)
    now = datetime.now(timezone.utc).isoformat()
    added, all_evidence = [], []
    for key, eid, cid, directory, manifest_name in SPECS:
        folder = TICK / directory
        source_frozen, source = read(folder / "FROZEN.json"), read(folder / manifest_name)
        assert source_frozen["owner"] == source["owner"] == OWNER
        assert all(sha(folder / name.replace("\\", "/")) == value for name, value in source_frozen["files"].items())
        evidence = [ref(folder / name) for name in ("FROZEN.json", manifest_name, "DESIGN.md", "software_check.json")]
        native = observation(getattr(args, key + "_native_actual"), getattr(args, key + "_native_review"), cid, "smoke")
        resources = observation(getattr(args, key + "_resources_actual"), getattr(args, key + "_resources_review"), cid, "resources")
        evidence += native["evidence"] + resources["evidence"]
        passed = native["status"] == resources["status"] == "PASSED"
        source_files = source.get("source_files_exact9") or {
            name.replace("\\", "/").removeprefix("isolated_source/"): value for name, value in source["files"].items()}
        candidate = {
            "id": cid, "candidate_id": cid, "experiment_id": eid, "profile": "experiment_first",
            "stage": "validation" if passed else "implementation", "created_at": now, "updated_at": now,
            "created_in_tick": OWNER["token"], "created_tick": OWNER["generated_at"], "owner": OWNER,
            "source_parent_commit": source["source_parent_commit"], "source_commit": None, "code_commit": None,
            "source_commit_status": "EXACT_FROZEN_SOURCE_SNAPSHOT_NO_NEW_RETAINED_GIT_COMMIT_CLAIM",
            "source_files_exact9": source_files, "source_only": native["status"] == "NOT_RUN",
            "source_preparation": ref(folder / "FROZEN.json"), "source_version": ref(folder / manifest_name),
            "mechanism": source.get("mechanism", "Native fine-leaf Delaunay simplex-incidence learned factor composition; exact source and design retained."),
            "matched_control": "Original M95 YAML/data/seed1999/loss/optimizer/pretrain/precision/epochs50/max_iters70; native TRAIN2/common-init/full resource protocol unchanged.",
            "native": native["status"], "native_status": native["status"], "native_observation": native,
            "resources": resources["status"], "resource_status": resources["status"], "resource_observation": resources,
            "Torch_autograd": native["status"], "full_forward": native["status"],
            "efficacy": "UNKNOWN", "novelty": "UNKNOWN", "scientific_admission": passed,
            "queued": False, "full_training_started": False, "training_repair_verified": False,
            "resource_scope": {"allowed_gpus": [0], "max_tasks_per_gpu": 1, "GPU1_admitted": False},
            "next_action": "在原协议和本轮真实source绑定下继续native/common-init/TRAIN2或资源实测；按实际失败定位，不伪造PASS、不有利重跑。"
                if not passed else "独立审查已完成的native/resource证据后，按canonical门槛准备原固定计划validation/训练；尚未入队。",
            "evidence": evidence,
        }
        work["candidates"].append(candidate)
        added.append(candidate)
        all_evidence += evidence
    if work.get("tick_attempt"):
        work.setdefault("tick_attempt_history", []).append(deepcopy(work["tick_attempt"]))
    selected = next((c for c in added if c["native_observation"]["evidence"]), added[0])
    attempt_refs = selected["native_observation"]["evidence"] or selected["evidence"][:4]
    state = selected["native_observation"]
    outcome = "passed" if state["actual_passed"] else ("failed" if state["status"] == "FAILED_OR_INCONCLUSIVE" else "blocked")
    if args.tick_attempt_actual:
        explicit = ref(args.tick_attempt_actual)
        assert read(args.tick_attempt_actual).get("owner") == OWNER
        assert explicit in all_evidence, "Supply a candidate native/resource actual already included above."
        attempt_refs = [explicit]
        selected = next(c for c in added if explicit in c["evidence"])
        state = next(x for x in (selected["native_observation"], selected["resource_observation"]) if explicit in x["evidence"])
        outcome = "passed" if state["actual_passed"] else ("failed" if state["status"] == "FAILED_OR_INCONCLUSIVE" else "blocked")
    work["tick_attempt"] = {
        "kind": "resource_check" if args.tick_attempt_actual and state is selected["resource_observation"] else "implementation_test",
        "result": outcome, "candidate_id": selected["id"], "experiment_id": selected["experiment_id"],
        "tick_started_at": OWNER["generated_at"], "evidence": attempt_refs,
        "command": "本轮current-owner私有stage原native协议一次执行；详见绑定actual/request；未提供actual时仅源码准备，native为NOT_RUN。",
        "observation": "真实结果状态：" + state["status"] + "；新建M235/M236，未把新实验记为M234；未运行门槛保持NOT_RUN。",
    }
    work.update(last_event_tick=OWNER["generated_at"], updated_at=now,
                next_action="优先M235-SINC与M236-CSO原生实验；按真实native/resource结果推进；GPU0-only/cap1保持，GPU1观察不等于授权。")
    assert work["candidates"][:160] == original["candidates"] and len(work["candidates"]) == 162
    memory = memory_path.read_text(encoding="utf-8")
    assert memory.count("## ") == 7 and "## Last Tick\n" in memory
    memory = memory.split("## Last Tick\n", 1)[0] + "## Last Tick\n" + "\n".join([
        "- 4ecb5020本轮按人工“双卡都空了，快设计实验”转向新机制实验，登记M235-SINC与M236-CSO；旧160候选及M234崩溃历史逐对象保留。",
        "- M235-SINC fine-leaf-geometric-simplex-incidence-composition：native=" + added[0]["native"] + "，resources=" + added[0]["resources"] + "；stage=" + added[0]["stage"] + "。",
        "- M236-CSO fine-leaf-full-covariance-shape-composition：native=" + added[1]["native"] + "，resources=" + added[1]["resources"] + "；stage=" + added[1]["stage"] + "。",
        "- 双卡真实空闲观察单独保留；SERVERS/资源授权仍GPU0-only、cap1、启动前free>=20000MiB及原三锁；GPU1未授权。M206/M227继续暂停。",
        "- 原YAML/data/seed1999/loss/optimizer/precision/50epoch/max_iters70、M95对照/common-init/自然TRAIN2/完整资源口径保持；ctorv5受限探针不作为新模型门槛。",
        "- 新候选效能/novelty UNKNOWN；完整训练未启动、未入队；失败/不确定结果如实保留，不自动重放。租约截止2026-11-10 02:06:58Z。",
    ]) + "\n"
    assert memory.count("## ") == 7 and len(memory.splitlines()) < 120
    notes = {"owner": OWNER, "actions": [
        "按人工“双卡都空了，快设计实验”的优先级准备并登记M235-SINC、M236-CSO两个新候选，保留完整冻结源码与设计证据。",
        "复用原M95对照与b410原生TRAIN2/common-init/finite backward/core update和同口径资源工具；真实结果状态随actual保存，未执行项保持NOT_RUN。",
        "保留原160候选及M234历史、dirty28/r0源码、主HEAD/index和goal/SERVERS；本收尾不启动训练或SSH。"],
        "decisions": ["新实验独立编号，不将新候选记作M234，不把静态源码检查当native/resource PASS。",
                      "资源继续GPU0-only/cap1/原三锁及20GB规则；双卡空闲观察不自动授予GPU1启动资格。",
                      "M206/M227暂停保持；原协议与科学门槛不变，效能和novelty仍UNKNOWN。"],
        "new_candidates": [{"experiment_id": c["experiment_id"], "candidate_id": c["id"], "stage": c["stage"],
                            "native": c["native"], "resources": c["resources"]} for c in added]}
    save(HERE / "research_work.before.json", original)
    save(HERE / "memory.before.json", {"text": memory_path.read_text(encoding="utf-8")})
    save(HERE / "registration.proposed.json", {"owner": OWNER, "new_candidates": added, "tick_attempt": work["tick_attempt"]})
    save(HERE / "record.intent.json", {"owner": OWNER, "work_before_sha256": old_work_sha,
                                      "memory_before_sha256": old_memory_sha, "no_replay": True})
    guard()
    assert sha(work_path) == old_work_sha and sha(memory_path) == old_memory_sha
    work_path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    memory_path.write_text(memory, encoding="utf-8")
    save(TICK / "report_notes.json", notes)
    persisted = read(work_path)
    assert persisted["candidates"][:160] == original["candidates"] and len(persisted["candidates"]) == 162
    guard()
    save(HERE / "record.actual.json", {"owner": OWNER, "recorded_at": now, "work_sha256": sha(work_path),
         "memory_sha256": sha(memory_path), "notes_sha256": sha(TICK / "report_notes.json"),
         "old160_candidates_object_exact": True, "old_histories_unchanged": True, "new_candidates": notes["new_candidates"],
         "new_queue_or_full_training": False, "memory_sections": 7, "memory_lines": len(memory.splitlines())})
    print(json.dumps({"status": "TWO_NEW_CANDIDATES_RECORDED", "path": str(HERE / "record.actual.json"),
                      "sha256": sha(HERE / "record.actual.json"), "notes_sha256": sha(TICK / "report_notes.json")}))


if __name__ == "__main__":
    main()
