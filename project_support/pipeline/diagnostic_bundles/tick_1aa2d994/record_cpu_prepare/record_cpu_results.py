"""Default NOP. Current-owner root records reviewed CPU proofs on two existing candidates."""
import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
OWNER = {
    "token": "1aa2d994ab004c93b2ea069c90ef9356",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-10T05:07:20.849412+00:00",
    "deadline_at": "2026-11-10T06:07:20.849412+00:00",
    "context_sha256": "eff960250947a7e168ea5f144742d7a877fd810d38f3f958cca86ab058cc9a93",
    "pending_sha256": "d7e6661624a7282adbfadedf6e35e015206fb97cb7ab4add04a79974af7a6f58",
}
SPECS = (
    ("sinc", "M235-SINC", "fine-leaf-geometric-simplex-incidence-composition",
     "cpu_core_prepare/cpu.actual.json", "cpu_core_prepare/sinc_cpu_actual_result_review_actual_chain_fast.json",
     "cpu_core_prepare/FROZEN.json", "peer_prepare/sinc_cpu_core_independent_review.json",
     ROOT / "pipeline/diagnostic_bundles/tick_79656807/m235_commit/commit_proof.json"),
    ("cso", "M236-CSO", "fine-leaf-full-covariance-shape-composition",
     "cso_cpu_execution/run_actual.json", "peer_prepare/cso_cpu_actual_independent_review.json",
     "cso_cpu_prepare/FROZEN.json", "peer_prepare/cso_cpu_core_independent_review.json",
     TICK / "m236_commit/commit_proof.json"),
)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard():
    assert sys.dont_write_bytecode and not sys.flags.optimize and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
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
    repo = ROOT / "Cluster"
    assert sha(repo / ".git/index") == before["index_sha256"]
    assert subprocess.check_output(["git", "--no-optional-locks", "-C", str(repo), "rev-parse", "HEAD"],
                                   text=True).strip() == before["local_main_HEAD"]
    assert all(sha(repo / name) == value for name, value in before["dirty_sha256"].items())


def observation(actual_path, review_path, cid, eid):
    actual, review = read(actual_path), read(review_path)
    remote = actual.get("observation") or {}
    result = remote.get("result") or {}
    # Check both transport layers BEFORE accepting any inner success flag.
    terminal_zero = (actual.get("certainty") == "terminal" and actual.get("returncode") == 0
                     and remote.get("certainty") == "terminal" and remote.get("returncode") == 0)
    passed = terminal_zero and (result.get("all_fixed_tests_passed") is True
                               or (result.get("passed") is True and result.get("execution_completed") is True))
    assert passed, "CPU PASS requires outer rc0 AND remote rc0 AND the actual fixed-test success."
    assert actual["owner"] == result["owner"] == review["owner"] == OWNER
    assert result["candidate_id"] == cid and result["experiment_id"] == eid
    assert review["passed"] is True and review["material_concerns"] == []
    assert review["actual_sha256"] == sha(actual_path)
    assert review["reviewer_thread_id"] not in (OWNER["thread_id"], "/root/fresh_ops")
    assert result["resources"] == "NOT_RUN"
    if eid == "M235-SINC":
        assert result["native_TRAIN"] == "NOT_RUN" and result["GPU_use"] is False
        assert all(result["parameter_updated"].values()) and len(result["parameter_updated"]) == 7
    else:
        assert result["native_backward"] == "NOT_RUN" and result["native_train_function_executed"] is False
        assert result["cuda_device_requested"] is False
    return {"result": "passed", "scope": "REMOTE_CPU_ONLY_SYNTHETIC_EXACT_CORE_IMPLEMENTATION",
            "outer_returncode": 0, "remote_returncode": 0, "reviewed": True,
            "native_TRAIN": "NOT_RUN", "resources": "NOT_RUN", "evidence": [ref(actual_path), ref(review_path)]}


def gpu_observation(path):
    actual = read(path)
    item = actual.get("observation") or {}
    assert actual["owner"] == OWNER and actual["returncode"] == 0
    assert item["hostname"] == "dl04-MS-7E06" and item["uid"] == 1001
    assert item["physical_gpu"] == 0 and item["gpu_uuid"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
    assert item["inventory"]["returncode"] == item["compute"]["returncode"] == item["head"]["returncode"] == 0
    assert item["head"]["stdout"].strip() == "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
    free = item["memory_free_mib"]
    assert isinstance(free, int) and 0 <= free <= item["memory_total_mib"]
    return item, ref(path)


def replace_section(memory, title, body):
    pattern = r"(?ms)^## " + re.escape(title) + r"\n.*?(?=^## |\Z)"
    updated, count = re.subn(pattern, lambda _: "## " + title + "\n" + body.rstrip() + "\n\n", memory)
    assert count == 1
    return updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--gpu-actual", type=Path, default=TICK / "gpu0_after_cpu.actual.json")
    for key, _, _, actual, review, *_ in SPECS:
        parser.add_argument("--" + key + "-actual", type=Path, default=TICK / actual)
        parser.add_argument("--" + key + "-review", type=Path, default=TICK / review)
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SHARED_WRITES_OR_SSH"}))
        return
    guard()
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER and all(sha(HERE / n) == h for n, h in frozen["files"].items())
    assert all(sha(ROOT / item["path"]) == item["sha256"] for item in frozen["anchors"])
    assert not (HERE / "record.intent.json").exists() and not (HERE / "record.actual.json").exists()
    assert not (TICK / "report_notes.json").exists(), "Preserve existing notes; reconcile before writing."
    # Prefer any newer saved valid resource observation, rather than falsely blocking on an old one.
    resource_candidates = [Path(args.gpu_actual).resolve()] + list(TICK.glob("gpu0*.actual.json"))
    observations = []
    for path in dict.fromkeys(resource_candidates):
        assert path.is_relative_to(TICK)
        item, evidence = gpu_observation(path)
        observations.append((datetime.fromisoformat(item["observed_at"]), item, evidence))
    _, gpu, gpu_ref = max(observations, key=lambda entry: entry[0])
    if gpu["memory_free_mib"] >= 20000:
        print(json.dumps({"status": "GPU0_MEMORY_READY_NATIVE_FIRST_NO_SHARED_RECORD_WRITTEN",
                          "memory_free_mib": gpu["memory_free_mib"], "resource_evidence": gpu_ref}))
        return
    assert gpu["project_trainers"] == [], "A project trainer appeared; reconcile before marking native NOT_RUN."
    work_path, memory_path = ROOT / "pipeline/research_work.json", ROOT / "pipeline/codex_memory.md"
    original = read(work_path)
    work = deepcopy(original)
    assert len(work["candidates"]) == 162
    old_work_sha, old_memory_sha = sha(work_path), sha(memory_path)
    ids = {spec[2] for spec in SPECS}
    now = datetime.now(timezone.utc)
    retry = (now + timedelta(hours=1)).isoformat()
    evidence, summaries = [gpu_ref], []
    for key, eid, cid, _, _, packet, packet_review, proof_path in SPECS:
        matches = [c for c in work["candidates"] if c["id"] == cid]
        assert len(matches) == 1
        candidate = matches[0]
        assert candidate["experiment_id"] == eid and candidate["native"] == candidate["resources"] == "NOT_RUN"
        assert candidate["source_commit"] is None and candidate["code_commit"] is None
        measured = observation(getattr(args, key + "_actual"), getattr(args, key + "_review"), cid, eid)
        proof = read(proof_path)
        assert proof["experiment_id"] == eid and proof["stable_id"] == cid
        assert re.fullmatch(r"[0-9a-f]{40}", proof["commit"])
        assert proof["frozen_manifest_sha256"] == candidate["source_preparation"]["sha256"]
        assert proof["frozen_source_unchanged"] is True and proof["main_head_index_all_dirty_files_exact_unchanged"] is True
        refs = measured["evidence"] + [ref(TICK / packet), ref(TICK / packet_review), ref(proof_path), gpu_ref]
        assert read(TICK / packet)["owner"] == read(TICK / packet_review)["owner"] == OWNER
        candidate.update(stage="blocked", blocked_from_stage="implementation",
            blocker_kind="live_external_gpu_occupation", required_server="server-4",
            blocker=f"最新GPU0实际free={gpu['memory_free_mib']}MiB<20000MiB；外部进程保留，无需空卡或零context。",
            unblock_condition="最新真实GPU0 free>=20000MiB，并在新owner有效租约内核验原三锁、GPU UUID和cap1；随后先native common-init/TRAIN2再资源实测。",
            blocker_detail={"memory_free_mib": gpu["memory_free_mib"], "minimum_free_mib": 20000,
                            "rule": "free_MiB<20000; neither an empty GPU nor zero contexts is required",
                            "observed_at": gpu["observed_at"], "evidence": gpu_ref},
            retry_after=retry, cpu_implementation_test=measured, implementation_test=measured,
            Torch_autograd="CORE_CPU_PASSED_NATIVE_NOT_RUN", source_only=False, core_executed=True,
            full_forward="NOT_RUN", native="NOT_RUN", native_status="NOT_RUN",
            resources="NOT_RUN", resource_status="NOT_RUN", efficacy="UNKNOWN", novelty="UNKNOWN",
            scientific_admission=False, queued=False, full_training_started=False,
            retained_version_proof={**ref(proof_path), "commit": proof["commit"],
                "parent_commit": proof["parent_commit"], "proof_tick": proof["tick"],
                "historical_source_commit_NULL_preserved": True},
            updated_at=now.isoformat(),
            next_action="约1小时后复查GPU0实际free；达到20000MiB即在原三锁/cap1及新owner下先执行native common-init/TRAIN2，再同口径资源实测；不要求空卡、不干预外部进程。")
        for item in refs:
            if item not in candidate.setdefault("evidence", []):
                candidate["evidence"].append(item)
        assert candidate["source_commit"] is None and candidate["code_commit"] is None
        evidence += refs
        summaries.append({"candidate_id": cid, "experiment_id": eid, "cpu": "PASSED_REVIEWED", "native": "NOT_RUN",
                          "resources": "NOT_RUN", "retained_commit": proof["commit"]})
    assert all(c == next(old for old in original["candidates"] if old["id"] == c["id"])
               for c in work["candidates"] if c["id"] not in ids)
    if work.get("tick_attempt"):
        work.setdefault("tick_attempt_history", []).append(deepcopy(work["tick_attempt"]))
    work["tick_attempt"] = {"kind": "implementation_test", "result": "passed", "tick_started_at": OWNER["generated_at"],
        "candidate_id": SPECS[0][2], "experiment_id": "M235-SINC",
        "candidate_ids": sorted(ids), "evidence": evidence,
        "command": "python -B -X utf8 " + str(TICK / "cpu_core_prepare/run_cpu_once.py") + " --execute-root"
            + " ; python -B -X utf8 " + str(TICK / "cso_cpu_prepare/run_cpu_once.py") + " --execute-root",
        "command_review_arguments": "原review路径及SHA见两个actual所绑定的intent/request；此字段仅省略已有实际review参数，不代表重新执行。",
        "observation": "仅synthetic CPU核心reference/autograd/update/结构对照PASS；native TRAIN2/resources NOT_RUN。"}
    work.update(updated_at=now.isoformat(), last_event_tick=OWNER["generated_at"],
                next_action=f"GPU0实际free{gpu['memory_free_mib']}MiB<20000，约1小时复查；足够后先native，外部进程保留。")
    memory = memory_path.read_text(encoding="utf-8")
    assert memory.count("## ") == 7
    memory = replace_section(memory, "Active Hypotheses",
        "- M235-SINC / M236-CSO：本轮精确源码远端synthetic CPU参考/输入及全参数反传/真实更新与结构对照均通过并独审；native TRAIN2/common-init/resources仍NOT_RUN，效能/novelty UNKNOWN。\n"
        "- SINC为几何simplex-incidence组合；CSO为完整协方差矩阵平方根组合。旧source_commit/code_commit NULL保持，真实retained commit通过独立proof追加，不补签旧证据。")
    memory = replace_section(memory, "Closed Or Failed Directions",
        "- M234-RVE complete/crashed；原source d214、训练/worker失败及checkpoint历史保留，根因UNKNOWN；不自动重启或声称修复。\n"
        "- M233-NDE与M232-NSD等旧方向保留原crash/数值/资源历史；CPU检查不抹去旧失败。M206/M227人工暂停保持。\n"
        "- 其余原160候选逐对象完全保持；所有bans、scope/numerical/human holds沿用共享ledger。")
    memory = replace_section(memory, "Running And Queue",
        f"- 最新只读GPU0观察{gpu['observed_at']}：free={gpu['memory_free_mib']}MiB<20000，util={gpu['utilization_percent']}%；project_trainers={gpu['project_trainers']}。\n"
        "- M235/M236 blocked/live_external_gpu_occupation，约1小时后复查；free>=20000即可按原三锁/cap1准备native，无需空卡/无context。GPU1未授权，外部任务不动。\n"
        "- 未启动native或完整训练、未入队；旧79656807轮INCOMPLETE已释放，当前1aa2d994 owner独立有效。")
    memory = replace_section(memory, "Last Tick",
        "- 本轮两套真实CPU actual均outer+remote rc0且独审PASS；SINC9固定cases/7参数，CSO21固定checks/9参数。synthetic优化器步不等于native AdamW/task训练。\n"
        "- M235 retained b1e639b3ceb14bb5c65d9f81a084d41c834b951c；M236 retained af45707d7b6089f764843337c5f88af285383f88；仅追加proof。\n"
        f"- 最新GPU0 free{gpu['memory_free_mib']}MiB<20000，资源不足，retry_after={retry}；新资源若足够必须先native，不沿用旧阻塞。\n"
        "- goal/SERVERS/主HEAD/index/dirty文件不改；旧160候选与历史保持。报告/finish由root在租约2026-11-10 06:07:20Z前收尾。")
    assert memory.count("## ") == 7 and len(memory.splitlines()) < 120
    notes = {"owner": OWNER, "actions": [
        "真实运行并独审M235-SINC与M236-CSO精确源码CPU核心测试，outer与remote均rc0；仅登记CPU实现PASS。",
        "追加M235/M236真实retained commit独立proof，旧source_commit/code_commit NULL及旧owner证据保持。",
        f"最新GPU0只读实际free={gpu['memory_free_mib']}MiB<20000；项目trainer为空，外部进程保留，未发native intent或入队。"],
        "decisions": ["按live_external_gpu_occupation阻塞原native步骤，约1小时复查；门槛是free>=20000MiB，不要求空卡或没有context。",
            "CPU实现正确性不等于native任务/common-init/TRAIN2、资源或效能PASS；native/resources仍NOT_RUN，效能与novelty UNKNOWN。",
            "资源一旦达到门槛，应先执行native而不是沿用本次阻塞；GPU0-only/cap1/原三锁、M206/M227暂停与旧160候选保持。",
            "上轮79656807 INCOMPLETE已释放，本轮owner独立收尾，不借用或延长旧租约。"],
        "cpu_candidates": summaries, "gpu_observation": gpu_ref, "retry_after": retry}
    save(HERE / "research_work.before.json", original)
    save(HERE / "memory.before.json", {"text": memory_path.read_text(encoding="utf-8")})
    save(HERE / "record.intent.json", {"owner": OWNER, "work_before_sha256": old_work_sha,
                                      "memory_before_sha256": old_memory_sha, "no_replay": True})
    guard()
    assert sha(work_path) == old_work_sha and sha(memory_path) == old_memory_sha
    work_path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    memory_path.write_text(memory, encoding="utf-8")
    save(TICK / "report_notes.json", notes)
    after = read(work_path)
    assert len(after["candidates"]) == 162
    assert all(c == next(old for old in original["candidates"] if old["id"] == c["id"])
               for c in after["candidates"] if c["id"] not in ids)
    guard()
    save(HERE / "record.actual.json", {"owner": OWNER, "recorded_at": now.isoformat(),
        "research_work_sha256": sha(work_path), "memory_sha256": sha(memory_path),
        "notes_sha256": sha(TICK / "report_notes.json"), "old160_object_exact": True,
        "candidate_count_unchanged": True, "source_commit_NULL_not_backfilled": True,
        "no_native_or_queue_launch": True, "cpu_candidates": summaries, "gpu_observation": gpu_ref})
    print(json.dumps({"status": "REVIEWED_CPU_IMPLEMENTATION_RESULTS_RECORDED_ONLY",
                      "path": str(HERE / "record.actual.json"), "sha256": sha(HERE / "record.actual.json")}))


if __name__ == "__main__":
    main()
