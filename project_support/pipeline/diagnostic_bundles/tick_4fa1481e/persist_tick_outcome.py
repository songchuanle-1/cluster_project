"""Archive this tick's actual source/software work; no execution or admission."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "4fa1481eb5e14bd1a0637720635b6410"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha(path)}


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    before = read(HERE / "protected_assets_before.json")
    git = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks",
           "-c", "core.fsmonitor=false", "-C", str(ROOT / "Cluster")]
    def query(*args):
        return subprocess.check_output(git + list(args),
            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0"))
    assert query("rev-parse", "HEAD").decode().strip() == before["head"]
    index = Path(query("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = ROOT / "Cluster" / index
    assert sha(index) == before["index_sha256"]
    assert query("status", "--porcelain=v1", "--untracked-files=all", "-z").hex() == before["status_hex"]
    for name, expected in before["files"].items():
        assert sha(ROOT / "Cluster" / name) == expected, name
    for name, expected in before["protected_ledgers"].items():
        assert sha(ROOT / "pipeline" / name) == expected, name
    now = datetime.now(timezone.utc).isoformat()
    integrity = {
        "recorded_at": now, "owner_token": TOKEN, "passed": True,
        "main_HEAD": before["head"], "main_index_sha256": sha(index),
        "user_files_count": len(before["files"]),
        "protected_ledgers_count": len(before["protected_ledgers"]),
        "main_status_unchanged": True, "original_46_ref": query(
            "rev-parse", "refs/pipeline/candidates/M233-NDE").decode().strip(),
        "revision1_ref": query("rev-parse", "refs/pipeline/candidates/M233-NDE-r1").decode().strip(),
        "no_remote_stage_or_native_execution_created_by_this_tick": True,
    }
    assert integrity["original_46_ref"] == "46adb90573118902d0a7c7723ce8817a085f38b9"
    assert integrity["revision1_ref"] == "0747f6acec1c61018ec99acf2efa5329c9b3523c"
    write_new(HERE / "final_protected_integrity.json", integrity)
    selected = [
        "nde_revision1_preregistration.json", "nde_revision_policy_review.json",
        "nde_revision1_source/source_version.json", "nde_revision_source_independent_review.json",
        "nde_revision_native_prepare/FROZEN.json",
        "nde_revision_native_prepare/software_validation.json",
        "nde_revision_native_independent_review.json",
        "nde_revision_native_independent_review_v2.json",
        "nde_historical_champion_smoke_reuse_review.json",
        "nde_revision_ops_prepare/FROZEN.json",
        "nde_revision_ops_independent_review.json",
        "nde_revision_ops_disabled/FROZEN.json",
        "nde_revision_native_active/FROZEN.json",
        "nde_revision_ops_active/FROZEN.json",
        "nde_revision_ops_prepare/ACTIVE_COPY_HANDOFF.json",
        "nde_revision_ops_corrected_prepare/FROZEN.json",
        "nde_revision_ops_corrected_prepare/software_validation.json",
        "nde_revision_result_prepare/FROZEN.json",
        "resources_initial.json", "resources_process_probe_correction.json",
        "final_protected_integrity.json",
    ]
    corrected_review = HERE / "nde_revision_ops_corrected_independent_review.json"
    if corrected_review.is_file():
        selected.append(corrected_review.name)
    evidence = [ref(HERE / name) for name in selected]
    native_review = read(HERE / "nde_revision_native_independent_review_v2.json")
    assert native_review["passed"] and native_review["check_count"] == 57
    assert read(HERE / "nde_revision_source_independent_review.json")["passed"]
    current = ROOT / "pipeline/research_work.json"
    work = read(current)
    candidate = next(value for value in work["candidates"] if value["id"] ==
                     "hierarchy-native-distribution-embedding-composition")
    assert candidate["code_commit"] == integrity["revision1_ref"]
    assert len(candidate["revision_history"]) == 1
    assert candidate["revision_history"][0]["result"] == "pending"
    old_attempt = work.get("tick_attempt")
    if old_attempt:
        history = work.setdefault("tick_attempt_history", [])
        if not any(value.get("tick_started_at") == old_attempt.get("tick_started_at") for value in history):
            history.append(old_attempt)
    capture = {
        "recorded_at": now,
        "scope": "Actual isolated source-save command with AST/source-byte/Git protections; software only.",
        "command": [sys.executable, "-B", "-X", "utf8", str(HERE / "build_nde_revision1_source.py")],
        "source_saved_at": read(HERE / "nde_revision1_source/source_version.json")["recorded_at"],
        "actual_command_result": "REVISION_SOURCE_SAVED_NOT_TESTED",
        "code_commit": integrity["revision1_ref"],
        "source_AST_and_nine_file_save_passed": True,
        "native": "NOT_RUN", "resources": "NOT_RUN", "Torch_autograd": "NOT_RUN",
        "source_proof": ref(HERE / "nde_revision1_source/source_version.json"),
        "independent_source_review": ref(HERE / "nde_revision_source_independent_review.json"),
        "original_over_budget_result_preserved": True,
    }
    write_new(HERE / "source_save_execution_audit.json", capture)
    evidence.append(ref(HERE / "source_save_execution_audit.json"))
    archived = {(entry["path"], entry["sha256"]) for entry in candidate["evidence"]}
    candidate["evidence"].extend(entry for entry in evidence
        if (entry["path"], entry["sha256"]) not in archived)
    candidate["stage"] = "validation"
    candidate["native"] = "REVISION1_NOT_RUN_SOFTWARE_REVIEWED"
    candidate["resources"] = "REVISION1_NOT_RUN_ORIGINAL46_OVER10G_PRESERVED"
    candidate["Torch_autograd"] = candidate["full_forward"] = "REVISION1_NOT_RUN"
    candidate["scientific_admission"] = "NOT_ADMITTED"
    candidate["queued"] = candidate["deployed"] = candidate["training_started"] = False
    candidate["execution_binding"] = candidate["current_owner_activation"] = None
    candidate["no_execution_binding"] = True
    candidate["worker_preparation"] = {
        "preparation": ref(HERE / "nde_revision_native_prepare/preparation.json"),
        "frozen": ref(HERE / "nde_revision_native_prepare/FROZEN.json"),
        "independent_review": ref(HERE / "nde_revision_native_independent_review_v2.json"),
        "scope": "Disabled software mother, 57 software checks; not actual native execution.",
        "native": "NOT_RUN", "resources": "NOT_RUN", "equivalence": "NOT_RUN",
    }
    candidate["execution_adapter"] = {
        "corrected_disabled_preparation": ref(HERE / "nde_revision_ops_corrected_prepare/preparation.json"),
        "corrected_disabled_frozen": ref(HERE / "nde_revision_ops_corrected_prepare/FROZEN.json"),
        "failed_initial_review": ref(HERE / "nde_revision_ops_independent_review.json"),
        "active_unreleased_copy_not_approved_for_execution": ref(HERE / "nde_revision_ops_active/FROZEN.json"),
        "operational_ready": False, "no_release_binding_lease_stage_request": True,
    }
    if corrected_review.is_file():
        candidate["execution_adapter"]["corrected_software_review"] = ref(corrected_review)
    candidate["historical_champion_smoke_reuse_review"] = ref(
        HERE / "nde_historical_champion_smoke_reuse_review.json")
    candidate["next_action"] = (
        "复用已冻结revision1源0747及native软件/修正版ops，不再移植或重制。"
        "下轮先观察，再另存实际新owner/deadline/source/runtime/root/UUID/producer执行绑定并独审；"
        "不得续本轮lease/改签旧champion。真实余量>=原1020秒与free>=20000MiB/projectmax1/三锁满足才执行"
        "新candidate TRAIN2、candidate资源、缺champion资源，并执行另受审绑定的修订等价控制。"
        "旧champion smoke仅按原71owner/source46原始证据复用；common835/两自然批仍须实测逐项一致。"
        "本轮无原生/资源/等价执行或准入，不放宽10G或任何门，保留原46的10.036472908G失败。"
    )
    candidate["latest_software_preparation"] = {
        "owner_token": TOKEN, "recorded_at": now,
        "revision": 1, "source_commit": integrity["revision1_ref"],
        "native_software_review_passed": True,
        "initial_ops_review_passed": False,
        "ops_corrected_disabled_software_tests": 7,
        "original_run_safety_margin_seconds": 1020,
        "run_acceptance_window_end": "2026-11-08T01:56:04.022567+00:00",
        "deadline_safety_window_exhausted_without_launch": True,
        "equivalence_executed": False, "native_executed": False,
        "resources_executed": False, "technical_admission": False,
        "evidence": evidence,
    }
    candidate["updated_at"] = work["updated_at"] = now
    work["tick_attempt"] = {
        "tick_started_at": owner["generated_at"], "candidate_id": candidate["id"],
        "kind": "implementation_test", "result": "passed", "command": capture["command"],
        "observation": (
            "实际source保存/AST/九文件与主线保护检查通过，原ID预注册revision1仅core首affine三层代数分解；"
            "源码41及native软件57独审通过。ops初审实际拒绝stale digest/预注册证据逐字相等，原失败保持；"
            "另存修正版禁用软件7个抽取guard正负例通过。实际原生、数值等价和资源均未执行，"
            "未准入/入队/部署/训练，不能将软件PASS代签GPU门。"
        ),
        "evidence": [ref(HERE / "source_save_execution_audit.json"),
                     ref(HERE / "nde_revision1_source/source_version.json"),
                     ref(HERE / "nde_revision_native_independent_review_v2.json"),
                     ref(HERE / "nde_revision_ops_independent_review.json"),
                     ref(HERE / "nde_revision_ops_corrected_prepare/software_validation.json")],
    }
    current.write_text(json.dumps(work, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    memory = """# Codex Research Memory

## Goal And Phase
- 仅cluster_project；2026-11-04最新授权仅server4物理GPU0，与外部任务共享。max_tasks_per_gpu1/启动free>=20000MiB/三协作锁保持，不要求空卡或低利用率。GPU1/其他服务器禁用，M206/M227人工暂停/no自动恢复。
- 原目标.5100，M95冠军.5020/baseline.4894；原YAML/data/seed1999/epochs50/max_iters70/patience10/loss/optimizer/precision/10G及conditional15%显存规则不变。全部bans/Phase1禁调参/Phase2人工保持，不驱逐/信号/重启/迁移任务，不改调度。
- Pipeline-cluster_project Disabled；实际owner thread01a159c5-29ab-7a22-ba7f-e79174757253；canonical skill前台契约，python -B/PROJECT_ROOT=D:/project/PYTHONDONTWRITEBYTECODE=1。

## Champion And Baseline
- M95 .5020保持。WFC原生epoch30/noimp10自然早停，精确best.49711745977401733；archiveead6b5a9edf2466ea96e2587c931c865，last不是epoch30，不重启。
- NEC原生epoch23/noimp10自然早停，best.49454113841056824@13/last22；archive35d448b2c70544049fa18e199081d30d，不重启。
- MIC原生epoch26/noimp10自然早停，best.49881425499916077@16/last25；archived03c21a094d54ed0b17a50cc21deeeb7，旧generic.4990舍入校正保留，不重启。

## Active Hypotheses
- M233-NDE稳定ID hierarchy-native-distribution-embedding-composition，validation；效力/novelty UNKNOWN，未准入/入队/部署/全训练。
- 原46adb父mainf625/九additions及ref refs/pipeline/candidates/M233-NDE完整保留。原两自然TRAIN/common835/有限loss backward/整core更新两smoke已实际完成；candidate资源10.036472908G>原10G失败，champion资源未执行，normalizer只partial，不是完整准入。
- 本轮先于新实现01:23:19Z预注册revision1（默认最多2次，当前仅1次pending）。新0747f6acec1c61018ec99acf2efa5329c9b3523c父f625，独立ref refs/pipeline/candidates/M233-NDE-r1；仅distribution_embedding.py变，其他8文件字节保持，main未部署。
- 修订在三层共享analysis首affine做W[x,z]+b=Wx*x+b+gather(Wz*z)，parent项按唯一父节点计算；保留同参数/state_dict/RNG定义、逐child GELU/secondLinear及mean前路径、原raw bank/HCG/singleinst。不是新机制、调参或10G豁免。
- 源41和native软件57独审通过，workerb37fe5…；原resources函数AST保持，实际F.linear子项需真实同口径计数。revision1 Torch/数值反向等价/native/resources全部NOT_RUN，revision result保持pending。
- 原champion smoke复用30项独审通过，仍保留71旧owner/source46/原时间；新candidate须实测匹配完整common835和两自然批，不能改签旧raw。

## Closed Or Failed Directions
- NSD M232 crashed archive4c26231600b04e3ca7126aa32d869e02；PID2791609/start169787479自然退出，仅partial epoch1/1961 of4686；完整epoch/验证0、无pth、exactbest UNKNOWN，不自动重启。
- NSD在原loss主体前self.cuda→Module._apply→_python_dispatch.py401出现builtin_function_or_method无Tensor。根因UNKNOWN/implementation-inconclusive，非机制证伪；原native admission与四臂证据保持，不能外推长期健康。
- HVD M230 crashed archive656485273dd0482fb5ec08cef6a68df4，partial5/1449参数枚举MultiheadAttention非iterable；完整saved4/best.4264346659183502。PSC M231 archivecbed4ef333ad48aaa272ebd303e4ca13，partial2/984 worker Tensor.unique NoneType不可调用；完整saved1/best.3035579323768616。均不重启。
- 全部旧scope/numerical holds、M201/旧FCB、PCE2+extra1/RSTR2与已消费HAP授权保持，不改名重开bans；M206/M227独立人工暂停。

## Running And Queue
- 本轮无已登记项目训练或ready waiting；只两个人工暂停。无remote stage/新native lease/request/PID、无准入/部署/训练。
- 01:44Z只读GPU0 free32012MiB/compute contexts0、三锁dev66308/inodes92537152/53/54可用；初substring进程探针误匹配其自身，另存exact argv+cwd复核实际项目train0。两证据保持，不把旧快照当启动许可。
- mainHEADf6257de79148581334ee495e6e2d60ccb525457c/index6b26152bfa70b006a5b1292daf4b392eda2e6ac138718c2994b83661a7172ea2/原28用户文件及40ledger本轮核保持。
- SERVERS SHAfd465e93a88a0b92199e7b911575a5a50ac9be453356b5f8db4cf4e24420335e不变，仍NSD根及已消费过期生产shim；新诊断不得source旧shim。仅诊断immutable base server4_conda_4ca73fba.sh SHA6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0。

## Open Questions And Risks
- 原Torch失败根因未修复。此前CPU fresh import/6源RECORD一致仅provenance，不是异常复现或修复；有界异常frame元数据捕获原样re-raise在worker保留，未实际触发。
- 本轮native首版独审误把imported fingerprint视为worker本地函数；失败审保留，v2纠正并57软件PASS。实际Torch/GPU未运行。
- ops首版冻结pendingdigest过时且把prereg evidence=[]与新增源证据逐字比，独立抽取guard真实拒绝；错误disabled/active未release包及失败审保留，禁止调用。另存corrected DRAFT包，仅修正实际pendingdigest/immutable prereg与append-only evidence核验，7正负例通过，非候选revision2。
- native active只是runtime DRAFT单flag变更的本地软件副本；未创建adapter_release/实际native binding/lease/stage，不能称已启用运行。独立equivalence_diagnostic.py仅冻结GPU控制脚本，未授权绑定/执行，不插入原TRAIN2。
- SSH keys/StrictHostKeyChecking，仅songcl@192.168.1.115/hostname dl04-MS-7E06/GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c。不读密码/连旧.137/假设sudo。

## Last Tick
- 当前4fa1481eb5e14bd1a0637720635b6410 generated2026-11-08T01:13:04.022567Z/deadline02:13:04.022567Z；前71已FINALIZED/PASS/context_committed/released。
- 本轮保存真实预注册/新9源commit、软件检查与独审、ops拒绝及禁用修正、旧champion复用审和资源只读探针；全部tick_4fa1481e。原1020秒run门窗口于01:56:04Z结束，软件未及时完成可审执行链，因此没有GPU测试/远端stage；不是物理资源不足或模型失败。
- 不重跑旧46两smoke/资源或重制冻结包。下轮复用native/source与受审软件；另存真实新owner/deadline/root/runtime/UUID/producer绑定并独审，不续本轮lease/补旧NULL/盲重放。只做新candidate TRAIN2+candidate资源+缺champion资源；旧champion smoke按原provenance复用，并保留完整vs部分区别。
- 修订等价控制另受审绑定并实际执行，所有受影响原生/资源及独立实审完成后才可准入；不以57软件/7guard检查代签、不放宽10G或增加FP32/逐行非零/minimum-effect门。report/finish以实际收据为准，释放后不改记录。
"""
    assert len(memory.splitlines()) < 120
    (ROOT / "pipeline/codex_memory.md").write_text(memory, encoding="utf-8")
    notes = {
        "actions": [
            "核实际会话与Disabled调度；begin已观察，无项目运行/ready队列。只读GPU0实际free32012MiB/三锁可用；substring自匹配已另存exact argv纠正，真实train0。",
            "同稳定NDE先预注册revision1，保存仅首affine三层代数分解的独立0747九源版本；原46失败、原ref和全部负结果保持。源码41/native软件57独审通过，不是原生准入。",
            "ops初审真实拒绝stale pendingdigest和prereg evidence逐字比较，保留失败软件/审查；另存DRAFT修正版7个guard正负例。旧champion smoke复用审通过，保留71旧owner/source46/原时间。",
            "01:56:04Z原1020秒run门窗口已关闭；未创建远端stage/实际执行binding/lease/request/PID，无GPU/等价/native/resources/准入/训练。本轮实际成果仅软件准备与失败定位。",
        ],
        "decisions": [
            "revision1保持pending；原46实测10.036472908G>10G不被擦除或豁免，效力与novelty UNKNOWN。软件及修正审不能代签GPU或整体配对结果。",
            "下轮复用冻结源/native/受审软件，另存真实新owner执行绑定后只补受影响新candidate原生/资源与缺champion资源、独立等价控制。旧champion复用须common835/两自然批实测匹配，不改签、不盲重放。",
            "main/index/原28用户文件/40ledger/SERVERS与所有holds/bans/seed数据协议、仅GPU0/20k/max1/外部共享/三锁/1020门保持。不为额度新增变体；准备事项不通知用户。",
        ],
    }
    write_new(HERE / "tick_notes.json", notes)
    print(json.dumps({"status": "SOFTWARE_PREPARATION_ONLY_PERSISTED",
                      "revision_result": "pending", "new_GPU_executions": 0,
                      "new_admissions": 0, "memory_lines": len(memory.splitlines()),
                      "evidence_count_added": len(evidence), "notes": str(HERE / "tick_notes.json")}))


if __name__ == "__main__":
    main()
