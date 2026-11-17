"""Persist this owned tick's observed resource block and byte-identical source save."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
REPO = ROOT / "Cluster"
TOKEN = "1138a3fc76ce46108e2bb511e1093826"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
MIC = "hierarchy-ancestry-mobius-interaction-composition"
HVD = "hierarchy-native-variance-decomposition-composition"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    owner = read(PIPE / "headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ.get("CODEX_THREAD_ID") == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(PIPE / "headless/.tick_context.json") == owner["context_sha256"]
    assert sha(PIPE / "headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256",
    )}


def save(path, value):
    guard()
    assert not path.exists()
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def replace(path, value):
    guard()
    temporary = path.with_name(path.name + ".1138a3fc.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    guard()
    os.replace(temporary, path)


owner = guard()
assert not (HERE / "persistence_result.json").exists()
version_path = HERE / "hvd_compatible_source_version.json"
peer_path = HERE / "hvd_compatible_source_independent_review.json"
version, peer = read(version_path), read(peer_path)
assert peer.get("passed") is True, "Independent actual source review must pass"
assert version["source_commit"] == "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
assert version["parent_commit"] == "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
assert version["same_source_bytes_as_independently_reviewed"] is True
assert version["protected_before"] == version["protected_after"]

observation_path = HERE / "gpu0_current_observation.json"
observation = read(observation_path)["observation"]
assert observation["physical_gpu"] == 0
assert observation["gpu_uuid"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
assert observation["memory_free_mib"] == 1150 < observation["required_free_mib"] == 20000
assert observation["external_overlay_authorized"] is True
original_files = [
    ROOT / "SERVERS.yaml", PIPE / "goal.json", PIPE / "queue.json",
    PIPE / "running.json", PIPE / "admissions/M229-MIC.json",
    PIPE / "execution_mode.json", PIPE / "closure_policy.json",
]
protected_before = {p.relative_to(ROOT).as_posix(): sha(p) for p in original_files}
work_path = PIPE / "research_work.json"
work = read(work_path)
other_before = digest([c for c in work["candidates"] if c["id"] not in (MIC, HVD)])
mic = next(c for c in work["candidates"] if c["id"] == MIC)
hvd = next(c for c in work["candidates"] if c["id"] == HVD)
assert mic["stage"] == "deployment" and mic["queued"] is True
assert hvd["stage"] == "validation" and hvd["source_commit"] == version["prior_source_commit"]
queue = read(PIPE / "queue.json")
task = next(t for t in queue["gpu_queues"]["server-4"] if t["id"] == "M229-MIC")
assert task["status"] == "waiting" and not task.get("pid") and not task.get("dispatch_hold")
assert not task.get("launch_verified") and not task.get("dispatch_phase")

resource_path = HERE / "gpu0_resource_budget_check.json"
native_command = "nvidia-smi -i 0 --query-gpu=index,uuid,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"
save(resource_path, {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
    "observed_at": observation["observed_at"], "candidate_id": MIC,
    "experiment_id": "M229-MIC", "result": "blocked",
    "actual_remote_native_command": native_command,
    "transport": "Key SSH BatchMode=yes StrictHostKeyChecking=yes ConnectTimeout=8 songcl@192.168.1.115; /usr/bin/python3 -B observer asserted pinned hostname and GPU0 UUID before querying.",
    "memory_free_mib": observation["memory_free_mib"], "required_free_mib": 20000,
    "compute_contexts_raw": observation["compute_contexts_raw"],
    "external_overlay_authorized": True,
    "source_observation": ref(observation_path),
    "canonical_begin_already_attempted_dispatch": True,
    "canonical_begin_found_no_native_training": True,
    "launch_requested": False, "training_Popen": False,
    "new_dispatch_hold": False, "signals_or_eviction": False,
    "interpretation": "Sharing permission remains valid; the original remaining-memory budget is not met. Keep the admitted deployed task waiting and recheck before any future launch.",
})
resource_evidence = [ref(observation_path), ref(resource_path)]
for entry in resource_evidence:
    if entry not in mic["evidence"]:
        mic["evidence"].append(entry)
retry = (datetime.fromisoformat(observation["observed_at"]) + timedelta(hours=1)).isoformat()
mic.update(
    implementation_status="ACTUAL_PAIRED_NATIVE_AND_COMPLETE_RESOURCES_PASSED_DEPLOYED_WAITING",
    source_version_status="EXACT07EF_SOURCE_DEPLOYED_AND_MAIN_HEAD_VERIFIED",
    remote_code_root="/data/songcl/Project/Cluster_project/Cluster_mic_20261105",
    latest_dispatch_resource_check=ref(resource_path),
    dispatch_resource_status="WAITING_ORIGINAL_FREE_MEMORY_BUDGET",
    retry_after=retry,
    unblock_condition="Physical server4 GPU0 free memory reaches the original20000MiB budget, current source/root/UUID/authorization and cooperative locks verify, with no other project task; external contexts may remain.",
    next_action="Keep the technically admitted exact07ef MIC waiting; canonical dispatch may run once fresh GPU0 free memory meets original20000MiB budget and all existing max1/three-lock/source gates pass. Verify increasing native steps after launch. No new sharing permission, empty-card requirement, budget reduction, eviction or blind launch replay.",
)
mic["execution_adapter"]["status"] = "ACTUAL_COMPLETE_GATES_RUNTIME_DEPLOYED_WAITING_RESOURCE_BUDGET"

hvd.setdefault("source_version_history", []).append({
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "prior_source_commit": hvd["source_commit"],
    "prior_code_commit": hvd["code_commit"],
    "prior_source_parent_commit": hvd["source_parent_commit"],
    "prior_source_version": hvd["source_version"],
    "prior_independent_source_version_review": hvd.get("independent_source_version_review"),
    "reason": "Preserve the same nine HVD blobs on actual current07ef parent; no model or protocol revision, no main promotion.",
    "saved_isolated_source_version": ref(version_path),
})
hvd.update(
    source_commit=version["source_commit"], code_commit=version["source_commit"],
    source_parent_commit=version["parent_commit"],
    future_version_parent=version["parent_commit"],
    source_version=ref(version_path), independent_source_version_review=ref(peer_path),
    source_version_status="SAME9_CURRENT07EF_COMPATIBLE_ISOLATED_SOURCE_SAVED_NOT_PROMOTED",
    future_version_parent_scope="Current actual07ef compatibility parent; main/runtime remain MIC07ef. Preserve originale38(parent6bc) and every frozen old packet. Future main changes need same-byte compatibility review, never sibling ff.",
    retry_after=retry,
    next_action="MIC M229 remains first for the sole GPU0 project slot. HVD same9 source is now saved/reviewed as isolatedd20eb221(parent07ef), without main promotion. Retain olde38/6bc/NEC-root frozen packets unchanged; after actual GPU0 memory>=20000MiB and slot/three-lock gates, separately bind the unchanged final worker to actual current owner/deadline/source/runtime/root/UUID/producer hashes. Run original YAML paired naturalTRAIN2/common-init/finite original-loss backward/wholecore updates and original resource checks before admission. Native/resources remain NOT_RUN; no GPU1 or paused route.",
)
hvd["current_source_compatibility"] = {
    "source_version": ref(version_path), "independent_review": ref(peer_path),
    "same_nine_blobs": True, "model_revision": False,
    "frozen_packets_rebound_or_executed": False,
    "native": "NOT_RUN", "resources": "NOT_RUN",
}
for entry in [ref(version_path), ref(peer_path)]:
    if entry not in hvd["evidence"]:
        hvd["evidence"].append(entry)
if work.get("tick_attempt"):
    work.setdefault("tick_attempt_history", []).append(work["tick_attempt"])
work["tick_attempt_history"].append({
    "tick_started_at": owner["generated_at"], "candidate_id": HVD,
    "kind": "implementation_test", "result": "passed",
    "command": "python -B -X utf8 " + str(HERE / "save_hvd_compatible_source.py"),
    "observation": "Independent-index Git save preserved exact nine reviewed HVD blobs on current07ef parent, compiled8Python sources without imports, and verified exact9A delta/main/index/user28/lifecycle preservation. No native/resource or model revision claim.",
    "evidence": [ref(version_path), ref(peer_path)],
})
work["tick_attempt"] = {
    "tick_started_at": owner["generated_at"], "candidate_id": MIC,
    "kind": "resource_check", "result": "blocked",
    "command": native_command,
    "observation": "Pinned server4 physicalGPU0 had1150MiB free versus original20000MiB budget; externalPID1900513/31408MiB preserved. Canonical begin found no training and left the fully admitted/deployed MIC waiting. No trainingPopen, new dispatch hold or permission request.",
    "evidence": resource_evidence,
}
work["updated_at"] = datetime.now(timezone.utc).isoformat()
work["next_action"] = "First recheck MIC original free-memory budget on authorized sharedGPU0 before canonical dispatch; preserve all old holds. HVD exact9-compatible isolated source prepared; fresh binding and native/resources still required."
assert other_before == digest([c for c in work["candidates"] if c["id"] not in (MIC, HVD)])
replace(work_path, work)

memory = """# Codex Research Memory

## Goal And Phase
- 最新直接用户2026-11-04授权server4物理GPU0、启动、继续，明确“可叠加在他们的任务上  显存够用”。共享授权pipeline/authorizations/server4_gpu0_overlay_20261104.json保持；allowed_gpus=[0]/dispatch_enabled=true/allow_external_overlay=true/项目max1/原task_memory_mb=20000，保留training/diagnostic/exclusive三协作锁。
- Phase1目标mIoU .5100，冠军M95 .5020/baseline .4894。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50/max_iters70/patience10、10G与原conditional15%显存规则/bans不变；不增FP32、逐参数非零或minimum-effect门，Phase2人工。
- GPU1和其他服务器禁用，M227-LFT、M206独立人工暂停保持；不驱逐、发信号、重启或迁移已有/外部任务，Pipeline-cluster_project保持Disabled，不改目标或调度。

## Champion And Baseline
- 冠军M95 .5020保持。WFC(M226)原生epoch30/noimp10自然早停，精确完整best .49711745977401733；归档ead6b5a9edf2466ea96e2587c931c865及精确校正保留，不重启，不称last为epoch30。
- NEC(M228)原生epoch23/noimp10自然早停，23完整val，精确best .49454113841056824@epoch13；归档35d448b2c70544049fa18e199081d30d，best checkpoint13/noimp0，last22/noimp9（break先于save）。低于冠军，仅本实现本seed结果，不重启。

## Active Hypotheses
- M229-MIC hierarchy-ancestry-mobius-interaction-composition：已完成实际原生两自然TRAIN批/common-init/有限原loss backward/整core更新及路径执行、完整原口径资源与独立复核，已技术准入并部署/入队，当前stage deployment/waiting，无PID或训练启动。效力/novelty UNKNOWN。
- MIC receipt pipeline/admissions/M229-MIC.json SHA b7cb59e0b78ae81f4b3dec9dd5b40a19b1797cb4a0902e704918eb6ff7f3ff40；完整证据tick_3b2b394d/mic_native_smoke.json、mic_resource_comparison.json、mic_constraints_independence.json、mic_actual_independent_review.json，不重跑旧smoke或重制冻结包。
- MIC835共同参数tensor/155907386参数初始化一致；champion losses9.52912425994873/13.909585952758789，MIC8.9503173828125/13.903985023498535。FLOPs9.724783692G对9.762532428G；峰显存−0.645%，原15%条件未触发；median36.88871465ms对35.38573999ms，+4.247%，异时共享观察，不称独占性能。
- M230-HVD hierarchy-native-variance-decomposition-composition仍validation/native/resources NOT_RUN。真实祖先within/between方差分解→共享4C→C→C→原HCG单次inst_feats写回；原29软件项与后续21/26禁用包软件审保持，不代表forward/Torch/autograd/效力/novelty。
- HVD本轮以独立index保存同九blob兼容源d20eb221eff6584b67d4e9b5673559d0e1cb735b，父当前MIC07ef；实际8Python语法/九新增路径/原字节及独立源审通过，未晋升主线、未部署、非模型修订。原e38d92db(parent6bc)和全部NULL母包/冻结worker保持。
- HVD冻结native/operational包仍在tick_c7451cf1，最终worker f91bddf7；旧绑定e38/6bc/NEC根不可执行或补签NULL。未来真实显存/槽位许可后另存受审owner/source/runtime/root/UUID/producer绑定，先原TRAIN2及完整资源实际通过再准入。

## Closed Or Failed Directions
- M206-CGCA、M227-LFT保持原waiting/user_paused/dispatch_hold/noPID/resume_authorized=false；M201、旧FCB及历史scope/numerical holds不恢复，不借空卡重开。
- 全部旧失败/negative/unknown、PCE2+extra1/RSTR2预算及已消费HAP授权保持；不借MIC/HVD改名重开禁用路线，未测结果不代签。

## Running And Queue
- 本轮canonical begin监控无训练；M229是唯一可派发waiting，M206/LFT为暂停项。未生成MIC dispatch request，未Popen或启动，未发生未知claim。
- 当前本地主线Cluster实际HEAD07ef534a6e44f22bd7b2d083550ebd7823d1d3d3，live SERVERS根/data/songcl/Project/Cluster_project/Cluster_mic_20261105；SERVERS SHA84730b8f91db3022d2e1819362d803b20293ea6224cfa9d607b8d4e45e8f43c0。原用户28文件/index保持。
- 已验证部署证据tick_3b2b394d/mic_runtime_deployment.json SHA6f526352e2d9c356d3a3142398705813208bbcf1cb3cb8a99550bfa15e076ff8；旧NEC6bc、WFC94及4457目录/源均保留，不全局替换历史版本。
- 2026-11-05T15:26:17Z严格key/hostname/GPU0UUID只读核验：总32607MiB、已用31457MiB、余1150MiB，外部PID1900513占31408MiB；不满足原20000MiB余量门，MIC保持waiting。共享许可仍有效，不要求空卡/无context/低利用率。

## Open Questions And Risks
- 当前阻塞是实测剩余显存，不是缺共享授权；不重复询问、不削减预算、不挤占外部任务。下轮先重新核真实显存、项目max1与三锁后派发MIC，成功须原生步数增长，PID不够。
- MIC完整技术准入不证明效力/新颖性；HVD兼容源保存不证明原生训练或资源通过，主线仍MIC07ef。源再变化时先兼容复核同9字节，不盲ff兄弟提交。
- 旧3b2 dispatch v1/v2为schema/depth本地拒绝，v3在过期owner前拒绝；无request/无Popen，保留负证据，不用过期token重放。未知启动须先reconcile。
- SSH只用key/StrictHostKeyChecking及固定dl04-MS-7E06/192.168.1.115/GPU0UUID958e；不读密码文件、不连旧.137、不假设sudo。授权内SERVERS_after_sha为历史指纹，不要求回退。

## Last Tick
- 当前owner1138a3fc76ce46108e2bb511e1093826，generated2026-11-05T15:16:11.501598+00:00/deadline2026-11-05T16:16:11.501598+00:00；按真实收据report/finish核验，不预称postflight成功。
- 前轮3b2b394d已INCOMPLETE/context_committed=false/lease released；实际MIC准入、部署、ff与waiting仍有效。此前memory的abb partial资源/NEC根缓存已按实际文件更正。
- 本轮真实resource_check blocked证据tick_1138a3fc/gpu0_current_observation.json及gpu0_resource_budget_check.json；未启动训练、未新增候选/准入/hold。
- 本轮HVD同9字节兼容源及独立审见tick_1138a3fc/hvd_compatible_source_version.json、hvd_compatible_source_independent_review.json；所有其他候选、队列/运行账、授权/禁用项/源及index保持。
- 后续优先MIC满足原余量门后的canonical dispatch；HVD仅等待新绑定及原生/资源真实缺项。不重复制作冻结包、不为配额新增。
"""
assert len(memory.splitlines()) < 120
replace(PIPE / "codex_memory.md", memory)
notes = {
    "actions": [
        "本轮canonical begin先观察并尝试已有队列；实际无训练，M229已准入部署waiting，M206/LFT维持用户暂停。",
        "只读核验server4身份与物理GPU0 UUID，15:26:17Z真实余量1150MiB，低于原20000MiB预算；外部PID1900513保留。未启动、未生成dispatch请求，GPU0共享授权有效。",
        "独立复核既有MIC receipt/四门/部署proof/实际main07ef与live MIC根，复用完整实测证据，未重跑smoke或重制包。",
        "使用独立Git index保存原HVD同9blob为d20eb221(parent07ef)，8Python语法与实际9新增路径/其他条目/用户28文件/index保持均核真，另有独立源审。未修改模型、冻结包、主线或远端。",
        "更新七节memory以纠正前轮partial资源/旧NEC根缓存，保存本轮resource_check和HVD兼容源证据；前轮3b2明确INCOMPLETE且已释放。",
    ],
    "decisions": [
        "MIC保持deployment/waiting，不新增dispatch_hold或人工许可要求；下次只在真实余量达到原20000MiB且max1/三锁/版本核验通过后canonical派发，并核原生步数增长。",
        "HVD保留validation/native/resources NOT_RUN；同9兼容保存仅软件/版本证据，原e38与冻结NULL包保持，后续另存受审当前绑定。不因准备工作或例行资源阻塞发送通知。",
        "0新增候选、0新准入、0启动；不削减预算、不要求空卡、不挤占外部任务、不使用GPU1/其他服务器，不恢复M227/M206或历史禁用路线，不改目标/调度。",
    ],
}
save(HERE / "report_notes.json", notes)
protected_after = {p.relative_to(ROOT).as_posix(): sha(p) for p in original_files}
assert protected_before == protected_after
actual_work = read(work_path)
assert other_before == digest([c for c in actual_work["candidates"] if c["id"] not in (MIC, HVD)])
result = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
    "resource_check": ref(resource_path), "compatible_source": ref(version_path),
    "independent_source_review": ref(peer_path),
    "other_candidates_unchanged": True,
    "protected_files_before": protected_before, "protected_files_after": protected_after,
    "queue_and_running_unchanged": True, "training_launches": 0,
    "new_candidates": 0, "new_admissions": 0,
    "memory_lines": len(memory.splitlines()),
    "notes": ref(HERE / "report_notes.json"),
}
save(HERE / "persistence_result.json", result)
print(json.dumps({
    "persisted": True, "MIC": "deployment/waiting/resource_budget_blocked",
    "HVD": "validation/same9_compatible_source_saved/native_resources_NOT_RUN",
    "new_candidates": 0, "new_admissions": 0, "training_launches": 0,
    "memory_lines": len(memory.splitlines()), "result": ref(HERE / "persistence_result.json"),
}, ensure_ascii=False))
