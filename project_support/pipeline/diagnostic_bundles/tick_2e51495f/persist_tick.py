from pathlib import Path
from datetime import datetime, timezone, timedelta
import copy, hashlib, json, os, subprocess, sys

ROOT=Path("D:/project/cluster_project");P=ROOT/"pipeline";H=Path(__file__).resolve().parent
sys.path.insert(0,"C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import pipeline_monitor as mon
def read(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {"path":Path(p).relative_to(ROOT).as_posix(),"sha256":sha(p)}
def write(p,v):
    with Path(p).open("x",encoding="utf8",newline="\n") as f:
        json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
def guard():
    o=read(P/"headless/.foreground.lockdir/owner.json")
    assert o["token"]=="2e51495f07244023946fc53eec6e6d98" and o["thread_id"]==os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
    assert sha(P/"headless/.tick_context.json")==o["context_sha256"]
    assert sha(P/"headless/.tick_context_state.next.json")==o["pending_sha256"]
    return o
owner=guard();now=datetime.now(timezone.utc).isoformat()
assert not (H/"persist_result.json").exists()
archive=read(H/"hvd_crash_archive_result.json");assert archive["status"]=="crashed"
version=read(H/"nsd_isolated_source_version.json")
assert read(H/"reserve_candidate_independent_review.json")["passed"] is True
assert read(H/"psc_operational_prepare/static_validation.json")["passed"] is True
proposal=read(H/"reserve_candidate/candidate_proposal_final.json")
lock=mon.acquire_lock(str(ROOT));assert lock is not None
try:
    guard()
    work=read(P/"research_work.json")
    with (H/"research_work_before.json").open("xb") as f:f.write((P/"research_work.json").read_bytes())
    with (H/"codex_memory_before.md").open("xb") as f:f.write((P/"codex_memory.md").read_bytes())
    candidates=work["candidates"];assert isinstance(candidates,list)
    untouched={c["id"]:copy.deepcopy(c) for c in candidates if c["id"] not in (
        "hierarchy-native-variance-decomposition-composition","hierarchy-native-position-feature-cross-scatter-composition")}
    hvd=next(c for c in candidates if c["id"]=="hierarchy-native-variance-decomposition-composition")
    hvd.setdefault("training_observation_history",[]).append({
        "recorded_at":now,"previous_stage":hvd["stage"],"previous_training_status":hvd.get("training_status"),
        "previous_launch_protection":copy.deepcopy(hvd.get("launch_protection"))})
    hvd.update(stage="blocked",training_status="crashed_runtime_implementation_inconclusive",
        blocker="Actual HVD trainer exited at epoch5/1449 with TypeError during parameter enumeration. Root cause UNKNOWN. Saved complete epoch4 retained. Do not restart/resume; CPU diagnosis first. This is an implementation failure, not hypothesis rejection.",
        blocker_kind="runtime_implementation_failure",failure_scope="implementation",
        retry_after=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),
        updated_at=now,next_action="Inspect archived original traceback and exact installed-runtime method bindings/signatures with a CPU-only reproduction. Preserve last/best epoch4 and no automatic restart/resume. PSC remains the next native candidate; fresh owner/resources/bindings required.",
        exact_saved_best=0.4264346659183502,last_complete_epoch=4,failed_partial_epoch=5,
        failed_partial_step=1449,hypothesis_falsified=False,root_cause="UNKNOWN",
        archive_id=archive["archive_id"],automatic_restart_or_resume=False)
    hvd["launch_protection"].update(status="RELEASED_AFTER_EXACT_TRAINER_EXIT",
        released_at="2026-11-06T13:49:46.377575+00:00",current_kernel_locks=[])
    hvd_paths=["hvd_live_before.json","hvd_live_final.json","hvd_exit_observation.json",
        "hvd_death_confirmation_cpu_checkpoint.json","hvd_crash_archive_result.json","hvd_failure_diagnosis.json"]
    for name in hvd_paths:
        item=ref(H/name)
        if item not in hvd["evidence"]:hvd["evidence"].append(item)
    psc=next(c for c in candidates if c["id"]=="hierarchy-native-position-feature-cross-scatter-composition")
    psc.setdefault("implementation_test_history",[]).append(copy.deepcopy(psc.get("implementation_test")))
    psc_paths=["psc_preparation_gap_review.json","psc_native_prepare/FROZEN.json",
        "psc_native_prepare/native/preparation.json","psc_native_prepare/static_validation.json",
        "psc_operational_prepare/preparation.json","psc_operational_prepare/static_validation.json",
        "psc_operational_prepare/FROZEN.json","psc_operations_builder_pre_review.json"]
    # The producer's software result may use its own location; all paths are checked.
    for i,name in enumerate(psc_paths):
        if name=="psc_native_prepare/static_validation.json" and not (H/name).exists():
            psc_paths[i]="psc_native_prepare/software_validation.json"
    independent=H/"psc_native_operational_independent_review.json"
    independent_passed=independent.exists() and read(independent).get("passed") is True
    if independent.exists():psc_paths.append(independent.name)
    for name in psc_paths:
        item=ref(H/name)
        if item not in psc["evidence"]:psc["evidence"].append(item)
    psc.update(updated_at=now,worker_preparation=ref(H/"psc_native_prepare/native/preparation.json"),
        execution_adapter={"preparation":ref(H/"psc_operational_prepare/preparation.json"),
                           "release_template":ref(H/"psc_operational_prepare/release_template.json"),
                           "active_release_created":False},
        implementation_test={"result":"passed","command":"python -B -X utf8 psc_native_prepare/static_check.py; python -B -X utf8 psc_operational_prepare/local_software_check.py",
            "scope":"45 native-producer and27 operational actual CPU software checks only; native/resources/Torch/autograd NOT_RUN.",
            "evidence":[ref(H/name) for name in psc_paths]},
        independent_software_packet_review="PASSED" if independent_passed else "PENDING",
        native_status="NOT_RUN",resource_status="NOT_RUN",
        next_action="Reuse frozen disabled PSC producer/operations and isolated0ccc(parentd20); no rebuilding. HVD has crashed and been archived, but this owner's remaining deadline is below original1020sec run margin. Next tick first verify actual GPU0 free>=20000MiB/max1/three locks/UUID, separately review actual fresh owner/source/runtime/root/producer execution bindings, then original four-arm TRAIN2/resources and independent actual review. No old binding replay or native PASS from software checks.")
    assert not any(c["id"]==proposal["id"] for c in candidates)
    nsd=copy.deepcopy(proposal)
    nsd.update(stage="implementation",code_commit=version["source_commit"],source_commit=version["source_commit"],
        created_at=now,created_in_tick=owner["token"],created_tick=owner["generated_at"],updated_at=now,
        source_version=ref(H/"nsd_isolated_source_version.json"),
        source_preparation=ref(H/"reserve_candidate/source_preparation.json"),
        native_protocol=ref(H/"reserve_candidate/native_protocol.md"),
        goal_sha256=sha(P/"goal.json"),
        authorization=read(P/"closure_policy.json")["experiment_first"]["authorization"],
        resource_authorization={"path":"pipeline/authorizations/server4_gpu0_overlay_20261104.json",
            "sha256":sha(P/"authorizations/server4_gpu0_overlay_20261104.json")},
        native_status="NOT_RUN",resource_status="NOT_RUN",queued=False,scientific_admission=False,
        next_action="PSC remains first. Reuse exact isolated NSD1fa7 source parentd20 and actual CPU checks; full native/Torch/backward/resources NOT_RUN. If main advances after PSC, save/review same9 compatible source before any native activation; never blind sibling ff or resume HVD/LFT.")
    nsd["evidence"]=list(nsd.pop("preparation_evidence"))+[ref(H/"reserve_candidate/candidate_proposal_final.json"),
        ref(H/"reserve_candidate/FROZEN.json"),ref(H/"reserve_candidate_independent_review.json"),
        ref(H/"nsd_isolated_source_version.json")]
    candidates.append(nsd)
    if work.get("tick_attempt"):work.setdefault("tick_attempt_history",[]).append(copy.deepcopy(work["tick_attempt"]))
    work["tick_attempt"]={"tick_started_at":owner["generated_at"],"candidate_id":psc["id"],
        "kind":"implementation_test","result":"passed",
        "command":"python -B -X utf8 psc_operational_prepare/prepare_psc_operations.py; python -B -X utf8 psc_operational_prepare/local_software_check.py (native producer45 checks also recorded)",
        "observation":"PSC missing disabled native/operational software packets completed with actual45/27 CPU checks and exact current-source hashes; no Torch/native/resource execution. HVD concurrently crashed and was canonically archived; no GPU launch under remaining deadline.",
        "evidence":[ref(H/name) for name in psc_paths]}
    work["updated_at"]=now
    work["current_training_protection"]={"status":"RELEASED","experiment_id":"M230-HVD",
        "guardian_pid":3024669,"released_at":"2026-11-06T13:49:46.377575+00:00",
        "evidence":ref(H/"hvd_exit_observation.json")}
    assert all(c==untouched[c["id"]] for c in candidates if c["id"] in untouched)
    temp=P/"research_work.2e51495f.tmp";write(temp,work);os.replace(temp,P/"research_work.json")
    text=(H/"codex_memory_before.md").read_text(encoding="utf8")
    text=text.replace("已真实原生检查、完整资源、独立复核、技术准入、部署与单次启动；","已真实原生检查、完整资源、独立复核、技术准入、部署与单次启动，现因运行时TypeError崩溃归档；")
    active_add=(
        "- PSC禁用native/operational软件包已在tick_2e51495f完成45/27实际CPU检查；DRAFT=True/10NULL，无active release/binding/manifest/lease/request/远端stage；完整Torch/autograd/native/resources仍NOT_RUN。复用冻结包，独立软件包审查以该目录审查文件为准。\n"
        "- 新M232-NSD hierarchy-native-spatial-dirichlet-composition已登记implementation：原fine叶坐标链成对特征差能量→真祖先共享bottom-up analysis/top-down synthesis→原HCG单次inst_feats。41实际stdlib检查及独立200组有理数/源审通过；反例均值/方差/PSC scatter相同而能量8/7与24/7，仅证明信息差异。\n"
        "- NSD隔离源"+version["source_commit"]+"父d20，精确9文件，主线/index/用户文件保持；Torch/autograd/native/resources NOT_RUN，无准入/队列/部署。PSC优先；后续父版本变化须兼容保存同9字节，不盲ff兄弟提交。坐标链非一般旋转不变，效果/novelty UNKNOWN。\n")
    text=text.replace("\n## Closed Or Failed Directions", "\n"+active_add+"\n## Closed Or Failed Directions")
    start=text.index("## Running And Queue");end=text.index("## Open Questions And Risks")
    text=text[:start]+(
        "## Running And Queue\n"
        "- HVD于2026-11-06T13:49:46Z（上海21:49）在epoch5/1449退出，原日志TypeError: argument of type 'MultiheadAttention' is not iterable；根因UNKNOWN，不是自然早停或假设证伪。三次新鲜/proc死亡核验后canonical finalize_task已crashed归档"+archive["archive_id"]+"，未调用dispatch/crashfix或重启。\n"
        "- CPU CUDA_VISIBLE_DEVICES=''、map_location=cpu实际核saved best/last均epoch4/best0.4264346659183502/noimp0，未保存partial5；完整原日志已精确拉取。此best为中断训练已保存结果，非完整效力结论。\n"
        "- 原guardian3024669/start158549879已RELEASED，/proc/locks三锁空；无项目训练在跑。M206/LFT仍人工暂停/noPID/no resume，不算ready。\n"
        "- 当前main/runtime仍d20、live根Cluster_hvd_20261106、SERVERS SHA6a87d428190d77955500b34d58bff0310eecb13c8b233c7b3e4fd7ef253787a7；旧MIC/NEC/WFC/4457及用户/index保持。PSC最近可原生检查，但本轮剩余时间不足原1020秒run margin，不启动诊断；下轮重新核资源/三锁/UUID与实际当前owner绑定。\n\n"
    )+text[end:]
    text=text.replace("不重启当前HVD。","不自动重启或resume已崩溃HVD。")
    text=text.replace("既有conda_source shim保留缺陷证据；","既有conda_source shim保留缺陷证据；")
    text=text[:text.index("## Last Tick")]+(
        "## Last Tick\n"
        "- 前轮20c已FINALIZED/PASS/context_committed/released，启动后锁修复证据保持；更早12e INCOMPLETE保留，不重放旧owner/binding/NULL。\n"
        "- 本轮2e51495f07244023946fc53eec6e6d98 generated13:10:54Z/deadline14:10:54Z：完成PSC缺失软件producer/operations及NSD1个预算内独立源准备；0新准入/0训练或GPU检查启动。HVD故障与guardian释放真实记录并canonical归档，非科学拒绝，不自动恢复。\n"
        "- 审计目录pipeline/diagnostic_bundles/tick_2e51495f，含HVD原生退出/CPU检查点/归档/诊断、PSC双冻结包、NSD原源/独立审/隔离版本与persist_result。report/finish及释放以本轮实际tick_receipts收据为准，不预称成功。\n"
        "- 下一轮先核故障证据和当前资源，再优先PSC实际原生四臂缺项；不借软件PASS准入。HVD只做CPU根因调查，原last/best及所有人工暂停/bans/原seed协议保持。\n")
    assert text.count("\n## ")==7 and len(text.splitlines())<120
    (P/"codex_memory.md").write_text(text,encoding="utf8",newline="\n")
    guard()
    protected=read(H/"protected_assets_before.json")
    for name,digest in protected["protected_files"].items():
        if name not in ("pipeline/queue.json","pipeline/running.json"):assert sha(ROOT/name)==digest
    for name,digest in protected["user_modified_tracked_files"].items():assert sha(ROOT/"Cluster"/name)==digest
    notes={"actions":[
        "本轮先核HVD同PID与guardian/三锁，Train4步12→16健康；随后真实发现epoch5/1449因TypeError退出。三次新鲜/proc死亡核验，CPU检查点best/last均epoch4/best0.4264346659183502/noimp0，partial5未保存，guardian自然释放三锁。",
        "使用canonical finalize_task精确crashed归档HVD，保存完整原日志及检查点证据；未调用完整monitor、dispatch、crashfix、信号、重启或resume。根因UNKNOWN，运行实现失败不代表机制证伪。",
        "优先补齐PSC缺失的禁用native/operational软件包，实际45/27项CPU检查；原资源函数逐字保持，当前source0ccc/runtime d20与HVD根，DRAFT/10NULL/无active执行材料；完整Torch/native/resources仍NOT_RUN。",
        "预算允许1个独立储备，新增M232-NSD，41实际stdlib检查与独立源码/200组有理数案例通过，精确9文件另存隔离版本"+version["source_commit"]+"父d20，未晋升主线或部署。",
        "保存所有失败/历史冻结证据、七段记忆、原人工暂停/资源授权/bans/用户文件/index；本轮0新技术准入、0GPU检查、0训练启动。"],
        "decisions":[
        "HVD已crashed归档，只做CPU根因调查，保留epoch4完整状态；不得自动重启或resume，不将partial结果当完整效力/novelty结论。",
        "PSC优先于NSD。实际项目槽已释放，但本轮剩余时间不足原1020秒run margin，下一轮按实时GPU0原20GB/max1/三锁/UUID及新owner绑定才执行原生四臂检查。",
        "任意后续新训练必须先真实证明direct-Popen入口三锁继承；当前Bash-only shim缺陷证据保持。GPU1/其他服务器禁用及M206/LFT人工暂停保持。"]}
    write(H/"notes.json",notes)
    decision=mon.log_decision(str(ROOT),"other","HVD训练运行时崩溃，如何保护状态并推进已有候选？",
        "精确归档crashed、保留完整epoch4及原日志，不自动resume；PSC软件缺项完成，NSD隔离储备登记，下一轮优先PSC原生检查。",
        "实际死亡/CPU检查点/guardian释放已证；根因与效力未知，本轮不足原run margin不启动GPU诊断。",
        "pipeline/diagnostic_bundles/tick_2e51495f/hvd_crash_archive_result.json")
    write(H/"persist_result.json",{"recorded_at":now,"passed":True,"other_candidates_preserved":len(untouched),
        "new_candidates":1,"new_admissions":0,"GPU_diagnostics_or_training_launched":0,
        "HVD_archived_crashed":archive["archive_id"],"PSC_independent_software_review_passed":independent_passed,
        "NSD_source":version["source_commit"],"decision":ref(Path(decision))})
finally:lock.close()
print(json.dumps({"persisted":True,"HVD":"crashed","PSC":"software_only_native_NOT_RUN",
    "NSD_source":version["source_commit"],"new_candidates":1,"no_GPU_launch":True}))
