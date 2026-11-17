"""Register one frozen candidate after its actual reviewed CPU implementation test."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "10a3f8b7d1bc4c5083b9b476c4d6fb94"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CID = "fine-leaf-receiver-conditioned-vector-exchange"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def create(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text(value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--actual-sha256")
    parser.add_argument("--source-review")
    parser.add_argument("--test-review")
    parser.add_argument("--actual-review")
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
        assert sha(ROOT / "pipeline/headless" / name) == owner[field]
    actual_path = HERE / "rvec_cpu_prepare/cpu_actual.json"
    assert sha(actual_path) == args.actual_sha256
    actual = read(actual_path)
    observation = actual["observation"]
    assert actual["certainty"] == "terminal" and actual["returncode"] == 0
    assert observation["owner"]["token"] == TOKEN
    assert observation["candidate_id"] == CID
    assert observation["all_fixed_tests_passed"] is True
    assert len(observation["cases"]) == 8
    assert all(case["passed"] for case in observation["cases"])
    assert observation["complete_operator_toy_update"]["passed"] is True
    assert all(observation[key] is True for key in [
        "python_rng_restored_exact", "torch_CPU_rng_restored_exact", "numpy_rng_restored_exact",
    ])
    assert observation["cuda_initialized_before"] is False
    assert observation["cuda_initialized_after"] is False
    review_paths = list(dict.fromkeys(
        Path(value) for value in [args.source_review, args.test_review, args.actual_review]
    ))
    for path in review_paths:
        assert path.resolve().is_relative_to(HERE.resolve())
        assert read(path)["passed"] is True
    frozen_path = HERE / "rvec_prepare/FROZEN.json"
    assert sha(frozen_path) == "2b03e0cb27ba8d8250ea8d5d053ca2cc7e3f461baa89e1c89a0297009b9b6683"
    frozen = read(frozen_path)
    source_files = frozen["source_files_exact9"]
    assert len(source_files) == 9
    for name, expected in frozen["files"].items():
        assert sha(HERE / "rvec_prepare" / name) == expected
    proposal = read(HERE / "rvec_prepare/proposal.json")
    work_path = ROOT / "pipeline/research_work.json"
    memory_path = ROOT / "pipeline/codex_memory.md"
    queue_path = ROOT / "pipeline/queue.json"
    servers_path = ROOT / "SERVERS.yaml"
    receipt_path = ROOT / "pipeline/admissions/M233-NDE.json"
    protected = {str(path): sha(path) for path in [queue_path, servers_path, receipt_path]}
    assert protected[str(servers_path)] == "62e4595edb002ed4c1340372ef2afc3d5dc9ba75a2a40f74b6752db61cbad9b3"
    assert protected[str(receipt_path)] == "52bf897dc89729063ffb429035b1cd07f14d3ea8d3e690812a4e3adfb48ed266"
    work_sha_before, memory_sha_before = sha(work_path), sha(memory_path)
    work = read(work_path)
    old_candidates = copy.deepcopy(work["candidates"])
    assert all(c["id"] != CID and c.get("experiment_id") != "M234-RVE" for c in old_candidates)
    now = datetime.now(timezone.utc).isoformat()
    refs = [
        reference(HERE / "rvec_preregistration.json"), reference(frozen_path),
        reference(HERE / "rvec_prepare/source_version.json"),
        reference(HERE / "rvec_prepare/software_validation.json"),
        reference(HERE / "rvec_cpu_prepare/FROZEN.json"),
        reference(HERE / "rvec_cpu_prepare/source_binding.json"),
        reference(HERE / "rvec_cpu_prepare/cpu_request.json"),
        reference(HERE / "rvec_cpu_prepare/cpu_intent.json"),
        reference(actual_path),
    ] + [reference(path) for path in review_paths]
    assessment_path = HERE / "native_readiness_assessment.json"
    if assessment_path.exists():
        refs.append(reference(assessment_path))
    explanation = (
        "One fresh CPU implementation test of the exact isolated RVE operator passed all "
        "eight fixed cases: optimized/reference outputs and all differentiable feature/"
        "parameter gradients, inherited support/tie/padding checks, neighbor derivatives "
        "and matched own-only donor cuts, plus one finite complete-operator toy update. "
        "Python/Torch CPU/NumPy RNG restored; CUDA remained uninitialized. Native model, "
        "original task loss/two TRAIN steps/common-init, full native core update and paired "
        "resources are NOT_RUN. This is not admission, efficacy, novelty or runtime-crash repair."
    )
    next_action = (
        "复用本轮受审冻结九文件及有效CPU实测，不重制或重跑同一软件检查。"
        "下一步保存这九文件的独立源码版本，并为当前执行owner另存、核验source/runtime/root/"
        "GPU0 UUID/producer的原生stage与lease；先完成原YAML两自然TRAIN步、共同初始化、"
        "原损失有限backward/整core更新，以及同口径10G/延迟/显存实测和独立复核。"
        "全部实际通过才准入入队，启动前重新核真实free>=20000MiB和三协作锁。"
        "不复用旧owner意图/生产shim，不恢复M206/M227或已退出的历史实验。"
    )
    candidate = {
        "schema_version": 1, "id": CID, "candidate_id": CID, "experiment_id": "M234-RVE",
        "profile": "experiment_first", "stage": "validation",
        "created_at": now, "recorded_at": now, "updated_at": now,
        "created_tick": owner["generated_at"], "created_in_tick": TOKEN,
        "source_parent_commit": proposal["source_parent_commit"],
        "hypothesis": proposal["hypothesis"], "whole_graph": proposal["formula"],
        "matched_control": "Original M95/FLE protocol and exact support; source own-only control retains self transform while cutting all donors, including fallback rows.",
        "config": "configs/Quard/ctf_hcg_csort_rvec/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rvec.yaml",
        "source_version": reference(HERE / "rvec_prepare/source_version.json"),
        "source_files_exact9": source_files, "source_only": True,
        "code_commit": None, "source_commit": None, "runtime_root": None,
        "execution_binding": None,
        "CPU_execution_binding": reference(HERE / "rvec_cpu_prepare/source_binding.json"),
        "implementation_test": {"result": "passed", "scope": "ISOLATED_ACTUAL_CPU_OPERATOR_ONLY",
                                "observation": explanation, "evidence": refs},
        "software_independent_review": {"passed": True, "evidence": [reference(path) for path in review_paths]},
        "native": "NOT_RUN", "native_task_loss": "NOT_RUN", "Torch_native_autograd": "NOT_RUN",
        "full_forward": "NOT_RUN", "resources": "NOT_RUN",
        "common_init": "NOT_RUN", "native_whole_core_update": "NOT_RUN",
        "native_smoke": None, "admission_receipt": None,
        "scientific_admission": "NOT_GRANTED", "queued": False, "deployed": False,
        "training_started": False, "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
        "required_server": "server-4", "required_physical_gpu": 0,
        "new_parameter_count": observation["operator"]["parameter_count"],
        "blocker": None, "failure_scope": None,
        "next_action": next_action, "evidence": refs,
        "historical_FLE_and_runtime_failures_preserved": proposal["historical_evidence"],
        "known_limitations": [
            "The nine-file integration was source-reviewed but not imported as a native model.",
            "Toy operator backward/update does not substitute for original native task loss/two steps/full-core evidence.",
            "Inherited FLE support retains all earlier tie/exact-distance/continuity limitations; no topology repair is claimed.",
            "Technical execution does not establish a population bottleneck, trained efficacy or novelty.",
        ],
    }
    work["candidates"].append(candidate)
    assert work["candidates"][:-1] == old_candidates
    work.setdefault("tick_attempt_history", []).append(work["tick_attempt"])
    test_review = read(Path(args.test_review))
    work["tick_attempt"] = {
        "tick_started_at": owner["generated_at"], "candidate_id": CID,
        "kind": "implementation_test", "result": "passed",
        "command": ["python", "-B", "-X", "utf8", str(HERE / "rvec_cpu_prepare/run_cpu_probe_once.py"),
                    "--execute-root", "--review", args.test_review,
                    "--review-sha256", sha(Path(args.test_review))],
        "observation": explanation, "evidence": refs,
    }
    assert test_review["source_review_passed"] and test_review["test_transport_review_passed"]
    work["updated_at"] = now
    work["last_event_tick"] = owner["generated_at"]
    work["next_action"] = next_action
    memory = memory_path.read_text(encoding="utf-8-sig")
    assert "## Active Hypotheses\n" in memory and "## Last Tick\n" in memory
    memory = memory.replace("## Active Hypotheses\n", (
        "## Active Hypotheses\n"
        "- M234-RVE稳定ID fine-leaf-receiver-conditioned-vector-exchange，validation/source-only，未准入/入队/部署/训练。九文件冻结2b03e0cb…；source parent0747，候选自身code_commit尚无。\n"
        "- 新路径在原fine-leaf边上先做receiver-relative-donor向量GELU再mean；K32/H8/原tie fallback、中粗层/HCG/CSORT/singleinst/全部训练数值保持。独立排重和源码复核通过，效力/novelty UNKNOWN。\n"
        "- RVE实际CPU8cases输出/全部可微输入与参数梯度等价、donorcut/跨leaf/并列与padding控制及一次完整孤立operator toy更新通过；RNG恢复/CUDA未初始化。原生模型/两TRAIN步/common-init/原loss整core更新/全部资源尚未测，不借用旧门槛PASS。\n"
    ), 1)
    memory = memory.split("## Last Tick\n", 1)[0] + (
        "## Last Tick\n"
        f"- {TOKEN} generated{owner['generated_at']}/deadline{owner['deadline_at']}，design预算2，仅新准备1项RVE；无合格待派发，M206/M227暂停保持。\n"
        "- 前轮9dfa receipt已核FINALIZED/PASS/context_committed/released。M233保持crashed归档ca1f72…；完整epoch/验证0、partial1/932、best UNKNOWN，无重启。\n"
        "- 本轮21:22Z pinned server4真实同root trainer0；GPU0 free24002MiB/used8108MiB/util53%，允许共享，未启动GPU计算；该观察不替代未来启动前重测。\n"
        "- 已受审冻结RVE九文件；24静态检查及一次新的实际CPU8cases通过，独立结果复核已保存。完整证据仅归入新stableID，既有候选/最终revision/准入/队列/资源配置保持。\n"
        "- 当前tick_attempt绑定真实新CPU命令/结果；待canonical report/finish核释放。无全局冷却，不为配额另建候选。\n"
        "- 下一步复用冻结包做源码版本保存及全新owner原生stage绑定，补原YAML两自然TRAIN步/common-init/原loss有限backward/整core更新/同口径资源与独审，通过后才准入。禁止重放旧lease/intent/shim或恢复人工暂停。\n"
    )
    assert len(memory.splitlines()) < 120
    assert sha(work_path) == work_sha_before and sha(memory_path) == memory_sha_before
    assert read(owner_path)["token"] == TOKEN
    work_path.write_text(text(work), encoding="utf-8", newline="\n")
    memory_path.write_text(memory, encoding="utf-8", newline="\n")
    assert all(sha(Path(path)) == expected for path, expected in protected.items())
    notes = {
        "actions": [
            "21:22Z核验server4身份/实际runtime HEAD0747及同root训练进程0；GPU0 free24002MiB，未启动GPU计算；人工暂停队列未派发。",
            "独立排重后新准备M234-RVE，冻结八Python文件+原生YAML；继承fine边支持/并列回退及中粗层路径，仅新增receiver-relative-donor向量变换。",
            "一次真实CPU实现测试完成8项固定case，输出/全输入与参数梯度等价、邻点路径与own-only切断、tie/padding及一次完整孤立operator toy更新通过，RNG恢复/CUDA未初始化；源码/测试入口/实际结果分别独审。",
        ],
        "decisions": [
            "仅注册1项source-only候选并保存当前真实implementation_test。原生模型/原loss两TRAIN步/common-init/整core更新及同口径资源未测，未准入/入队/部署/训练。",
            "后续复用受审冻结包和有效软件证据，先保存独立源码版本并为新执行owner另存核验实际原生stage/lease绑定，全部真实门槛通过后才准入。",
            "M233及历史失败根因仍UNKNOWN；本轮新operator测试不证明修复。保留既有负证据、人工暂停/资源/目标/bans/调度，不重放旧意图或为额度新增。",
        ],
    }
    notes_path = HERE / "tick_notes.json"
    create(notes_path, notes)
    create(HERE / "root_registration_audit.json", {
        "recorded_at": now, "owner_token": TOKEN, "candidate_id": CID,
        "creation_budget_used": 1, "old_candidates_unchanged": True,
        "work_before_sha256": work_sha_before, "work_after": reference(work_path),
        "memory_before_sha256": memory_sha_before, "memory_after": reference(memory_path),
        "protected_file_hashes_unchanged": protected, "actual_CPU": reference(actual_path),
        "notes": reference(notes_path), "report_finish": "NOT_YET_EXECUTED",
    })
    print(json.dumps({"status": "ONE_RVE_CANDIDATE_REGISTERED_CPU_ONLY_NO_ADMISSION",
                      "stage": "validation", "notes": str(notes_path),
                      "queue_resources_old_candidates_preserved": True}))


if __name__ == "__main__":
    main()
