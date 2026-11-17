"""Persist genuine partial PSC results and CPU evidence without admission."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import copy, hashlib, json, os, subprocess, sys

ROOT=Path("D:/project/cluster_project");P=ROOT/"pipeline";H=Path(__file__).resolve().parent
sys.path.insert(0,"C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import pipeline_monitor as mon
def read(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {"path":Path(p).relative_to(ROOT).as_posix(),"sha256":sha(p)}
def save(p,v):
    with Path(p).open("x",encoding="utf8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
def guard():
    o=read(P/"headless/.foreground.lockdir/owner.json")
    assert o["token"]=="0bb874337dde412e98bbbaac369f3370" and o["thread_id"]==os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
    assert sha(P/"headless/.tick_context.json")==o["context_sha256"]
    assert sha(P/"headless/.tick_context_state.next.json")==o["pending_sha256"]
    return o
o=guard();now=datetime.now(timezone.utc).isoformat()
assert not (H/"persist_partial_result.json").exists()
actual_review=H/"psc_partial_actual_independent_review.json"
assert read(actual_review).get("passed") is True
raws=[H/"psc_execution"/(name+"_execution.json") for name in ("smoke_champion","smoke_candidate","resources_champion")]
for path in raws:
    raw=read(path);assert raw["certainty"]=="terminal" and raw["returncode"]==0 and raw["result"]["execution_completed"] is True
assert not (H/"psc_execution/resources_candidate_request.json").exists()
assert not (H/"psc_root_run_resources_candidate_intent.json").exists()
assert read(H/"psc_run_resources_candidate_capture.json")["returncode"]==1
candidate=read(raws[1])["result"]
assert len(candidate["steps"])==2 and candidate["backward_finite"] and candidate["intended_path_observed"]
proof_path=H/"psc_cpu_path_proof_actual.json";proof=read(proof_path)
assert proof["returncode"]==0 and proof["observation"]["returncode"]==0
assert proof["observation"]["result"]["passed"] is True
proof_review=H/"psc_cpu_path_proof_actual_independent_review.json"
proof_review_passed=proof_review.exists() and read(proof_review).get("passed") is True
base=read(H/"protected_assets_before.json")
git=["git","--no-optional-locks","-C",str(ROOT/"Cluster")]
def q(*args):return subprocess.check_output(git+list(args),env=dict(os.environ,GIT_OPTIONAL_LOCKS="0"))
assert q("rev-parse","HEAD").decode().strip()==base["head"]
index=Path(q("rev-parse","--git-path","index").decode().strip());index=index if index.is_absolute() else ROOT/"Cluster"/index
assert sha(index)==base["index_sha256"] and q("status","--porcelain=v1","--untracked-files=all","-z").hex()==base["status_hex"]
for name,digest in base["files"].items():assert sha(ROOT/"Cluster"/name)==digest
for name,digest in base["fixed_configs"].items():assert sha(ROOT/name)==digest
queue=read(P/"queue.json")
assert not any(t.get("status") in ("running","claiming") for tasks in queue["gpu_queues"].values() for t in tasks)
queue_sha,running_sha=sha(P/"queue.json"),sha(P/"running.json")
lock=mon.acquire_lock(str(ROOT));assert lock is not None
try:
    guard()
    work_path=P/"research_work.json";work=read(work_path)
    with (H/"research_work_before_final.json").open("xb") as f:f.write(work_path.read_bytes())
    with (H/"codex_memory_before.md").open("xb") as f:f.write((P/"codex_memory.md").read_bytes())
    psc=next(c for c in work["candidates"] if c["id"]=="hierarchy-native-position-feature-cross-scatter-composition")
    hvd=next(c for c in work["candidates"] if c["id"]=="hierarchy-native-variance-decomposition-composition")
    unchanged={c["id"]:copy.deepcopy(c) for c in work["candidates"] if c["id"] not in (psc["id"],hvd["id"])}
    paths=[H/"resources_initial.json",H/"resources_before_stage.json",H/"psc_root_activation_anchors.json",
           H/"psc_current_activation_independent_review.json",*raws,
           H/"psc_run_resources_candidate_capture.json",actual_review,
           H/"psc_result_prepare/results_20261106T155125_654697Z/partial_actual_results.json",
           H/"psc_path_lock_independent_review.json",H/"psc_path_lock_prepare/v2/FROZEN.json",proof_path]
    if proof_review.exists():paths.append(proof_review)
    refs=[ref(path) for path in paths]
    psc.setdefault("native_resource_check_history",[]).append({
        "recorded_at":now,"previous_native_status":psc.get("native_status"),
        "previous_resource_status":psc.get("resource_status"),"evidence":refs})
    psc.update(stage="validation",native_status="ACTUAL_ORIGINAL_PAIRED_TRAIN2_BACKWARD_PATH_WHOLECORE_UPDATES_PASSED",
        full_forward="ACTUAL_ORIGINAL_TRAIN2_PASSED",
        resource_status="PARTIAL_CHAMPION_MEASURED_CANDIDATE_NOT_RUN_DEADLINE",
        resources="PARTIAL_CHAMPION_ONLY_NOT_COMPLETE",technical_admission=False,
        scientific_admission=False,queued=False,updated_at=now,
        actual_native_smoke_pair={"champion":ref(raws[0]),"candidate":ref(raws[1]),"independent_review":ref(actual_review)},
        actual_resource_partial={"champion":ref(raws[2]),"candidate":"NOT_RUN",
            "candidate_refusal":ref(H/"psc_run_resources_candidate_capture.json"),
            "reason":"Original1020second remaining-owner run margin refused before root intent/request/SSH/Popen; deadline unchanged."},
        next_action="Reuse actual paired smoke/common835init/two naturalTRAIN batches/whole-core update evidence and independently reviewed frozen PSC source/worker. Complete original matched resource comparison under a separately reviewed fresh-owner binding; retain real provenance and same-fixture/measurement protocol, do not copy old requests or renew old lease. Candidate resources NOT_RUN and no admission/deployment/queue/training yet. CPU PATH proof passed only isolated fixtures; actual production PSC source/runtime/YAML/interpreter/existing3inodes still need separate render/review before any new full trainer launch.")
    for item in refs:
        if item not in psc["evidence"]:psc["evidence"].append(item)
    psc["launch_protection_preparation"]={"CPU_proof_actual":ref(proof_path),
        "CPU_proof_independent_review":ref(proof_review) if proof_review.exists() else None,
        "CPU_review_passed":proof_review_passed,"production_enabled":False,
        "scope":"Actual isolated direct-Popen/condaPATH/three proof FD+kernelFLOCK/contention/natural-release test, not actual production binding."}
    diagnosis=H/"hvd_cpu_failure_diagnosis/diagnosis.json"
    assert read(diagnosis)["root_cause"]=="UNKNOWN"
    for path in (diagnosis,H/"hvd_cpu_failure_diagnosis/cpu_observation.json"):
        item=ref(path)
        if item not in hvd["evidence"]:hvd["evidence"].append(item)
    hvd.update(root_cause="UNKNOWN",updated_at=now,
        latest_CPU_diagnosis=ref(diagnosis),
        retry_after=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),
        next_action="Preserve crashed run and complete epoch4 best/last; no automatic restart/resume. Full traceback confirms train.py129 clip_grad_norm parameter enumeration. Installed Torch/custom-MHA bound methods and128 CPU traversal/clipnorm cases passed without reproducing the original failure. Root cause remains UNKNOWN; any next diagnostic must address actual missing runtime history rather than repeating the same CPU check.")
    if work.get("tick_attempt"):work.setdefault("tick_attempt_history",[]).append(copy.deepcopy(work["tick_attempt"]))
    work["tick_attempt"]={"tick_started_at":o["generated_at"],"candidate_id":psc["id"],"kind":"native_smoke","result":"passed",
        "command":"run_psc_operation_once.py run smoke champion; run_psc_operation_once.py run smoke candidate (original native YAML pairedTRAIN2)",
        "observation":"Actual paired two naturalTRAIN batches/common835 initialization, original finite loss/backward, native coordinate-feature path and whole-core real updates independently passed. Resource champion measured; resource candidate NOT_RUN due unchanged1020second owner margin. No complete resource/admission/queue/training PASS.",
        "evidence":[ref(raws[0]),ref(raws[1]),ref(actual_review)]}
    work["updated_at"]=now
    assert all(c==unchanged[c["id"]] for c in work["candidates"] if c["id"] in unchanged)
    temp=P/"research_work.0bb87433.final.tmp";save(temp,work);os.replace(temp,work_path)
    text=(H/"codex_memory_before.md").read_text(encoding="utf8")
    text=text.replace("完整Torch/autograd/native/resources仍NOT_RUN，无新准入/部署/队列。",
        "本轮成对原生TRAIN2/有限backward/实际路径及整core更新已通过；完整资源未齐，无准入/部署/队列。",1)
    text=text.replace("完整Torch/autograd/native/resources仍NOT_RUN。复用冻结包，独立软件包审查以该目录审查文件为准。",
        "原冻结包保持；本轮新owner激活与原生实测见Last Tick，不能把原冻结软件检查代签native。")
    text=text.replace("PSC最近可原生检查，但本轮剩余时间不足原1020秒run margin，不启动诊断；下轮重新核资源/三锁/UUID与实际当前owner绑定。",
        "本轮PSC成对TRAIN2已实测通过；资源冠军臂实测、候选臂在原1020秒余量检查前拒绝，未准入/部署/训练。下一轮另存新owner执行绑定，不能续写本轮lease。")
    marker="\n## Closed Or Failed Directions"
    added=(
        "- PSC在tick_0bb87433用新owner/source0ccc/runtimeD20/HVDroot/UUID/producer绑定真实stage，原worker530a…不变；成对原自然TRAIN2、835共同init、有限原loss backward、coords/cross11means/3cross/10C/整core更新独立181项核对通过。候选loss9.213239669799805/13.907380104064941，不代表效力。\n"
        "- PSC资源champion已terminal实测，resources_candidate尚NOT_RUN：原1020秒owner剩余门在request/intent/SSH/Popen前拒绝。3臂部分结果全部保留，不能准入/入队或混签完整资源PASS；不延长旧owner，不盲重放。\n"
        "- 真实PATH锁方案v2已在隔离CPU fixture通过真实conda/PATH/directPopen/3可继承FD及kernelFLOCK/竞争拒绝/自然释放；代码core字节共用，生产配置未启用，实际PSC部署/source/YAML/interpreter/原3inode须另审。证据psc_cpu_path_proof_actual.json，独立实测审以目录文件为准。\n")
    text=text.replace(marker,"\n"+added+marker)
    text=text.replace("根因UNKNOWN，不是自然早停或假设证伪。","根因UNKNOWN，不是自然早停或假设证伪；完整原栈已确认train.py129参数枚举调用点。",1)
    risk="\n## Last Tick"
    text=text.replace(risk,
        "\n- HVD已实际CPU核安装Torch2.8.0+cu128/Module方法签名和自定义MHA绑定，6层嵌套含共享MHA的128次参数/模块遍历与无梯度clip_norm未复现。没有forward/backward/GPU/旧对象历史，根因仍UNKNOWN，非修复或恢复许可；不重复同一无信息增益CPU检查。\n"+risk)
    text=text[:text.index("## Last Tick")]+(
        "## Last Tick\n"
        "- 前轮2e51495f已FINALIZED/PASS/context_committed/released；HVDcrashed归档、checkpoint4与guardian释放保持。当前0bb874337dde412e98bbbaac369f3370 generated2026-11-06T15:05:46Z/deadline16:05:46Z，不延期。\n"
        "- 本轮实际3个PSC GPU检查臂完成：smoke champion/candidate和resources champion；资源candidate仅本地时限门拒绝，未执行。0新候选/0技术准入/0入队/0完整训练启动，NSD源与所有暂停/hold不变。\n"
        "- 目录tick_0bb87433保存当前激活、3实测raw/独立partial审/正规化partial、CPU PATH proof及HVD CPU诊断。当前main/runtime仍d20、PSC隔离源0ccc，不晋升；全部旧NULL/owner/失败证据保持。\n"
        "- 下一轮优先PSC剩余完整资源比较，复用有效成对smoke证据；若原资源同owner/fixture协议要求重测对照，按实际协议处理而非拼装旧lease。新owner/source/runtime/root/UUID/producer重新审绑定，不能直接执行已过期0bb请求。production PATH尚需实际配置另审。\n"
        "- report/finish及lease释放以本轮实际tick_receipts收据为准，不预称成功。HVD保持故障归档不自动resume，NSD等待PSC之后及真实预算。\n")
    assert text.count("\n## ")==7 and len(text.splitlines())<120
    (P/"codex_memory.md").write_text(text,encoding="utf8",newline="\n")
    assert sha(P/"queue.json")==queue_sha and sha(P/"running.json")==running_sha
    notes={"actions":[
        "核当前GPU0实际free32514MiB/真实UUID/空项目槽与三锁；仅本项目server4 GPU0，新owner绑定独立274项复核后原guard prepare/stage成功，原冻结NULL包保持。",
        "实际完成PSC与champion两个原生自然TRAIN批成对smoke，835共同init/批指纹一致、原loss有限backward、实际coords-crossstats-10C路径及整core更新通过独立181项审；候选loss9.213239669799805/13.907380104064941。",
        "实际resources_champion已terminal/rc0；resources_candidate在root guard的原1020秒余量检查前拒绝，无request/intent/SSH/Popen。保存3臂partial，不生成完整资源PASS或准入，不延长期限/重放旧意图。",
        "实际隔离CPU PATH证明完成：真实conda/PATH与direct Popen、三可继承FD/三kernelFLOCK、竞争拒绝和自然释放；仅proof fixture，未绑定或启用真实PSC生产配置。",
        "HVD完整原栈确认train.py129 clip_grad_norm参数枚举；实际安装Torch/自定义MHA绑定与128次CPU遍历检查未复现持续故障，根因UNKNOWN；故障归档与epoch4 checkpoint保持。",
        "更新七段记忆与实际部分结果；主线/index/28用户文件/原资源与所有hold/暂停/NSD保持，0新候选/0准入/0训练启动。"],
        "decisions":[
        "PSC原生smoke通过不等于完整资源或效力/novelty结论；候选资源未执行，保持validation。下一轮另存新owner执行绑定补齐原协议资源缺项，复用可验证的既有实测，不续写旧lease或补签NULL。",
        "CPU PATH证明不是生产放行；未来实际source/runtime/YAML/解释器/原三inode绑定须单独审。HVD不自动恢复，M206/LFT独立人工暂停与GPU1/其他服务器禁用保持。",
        "本轮剩余时间不足原run margin即停止新GPU检查，不降门槛，不为预算额外创建变体。"]}
    save(H/"notes.json",notes)
    decision=mon.log_decision(str(ROOT),"other","PSC原生两步已通过但本轮资源检查不完整，是否准入？",
        "保留validation与3臂部分实测，不准入/入队/启动；下轮新owner补资源。CPU PATH隔离实证与生产绑定分开。",
        "候选资源在原1020秒余量门前拒绝，native/资源完整性与deadline不改；HVD根因未定、原暂停保持。",
        "pipeline/diagnostic_bundles/tick_0bb87433/psc_partial_actual_independent_review.json")
    guard()
    save(H/"persist_partial_result.json",{"recorded_at":now,"passed":True,"PSC_native_smoke":"ACTUAL_PASSED",
        "resource_arms_completed":1,"candidate_resources":"NOT_RUN","new_candidates":0,"admissions":0,
        "full_training_launches":0,"CPU_PATH_actual":True,"CPU_PATH_actual_review_passed":proof_review_passed,
        "other_candidate_records_preserved":len(unchanged),"queue_running_unchanged":True,"decision":ref(Path(decision))})
finally:lock.close()
print(json.dumps({"persisted":True,"PSC":"paired_native_smoke_passed_resources_partial_no_admission",
    "CPU_PATH_proof":True,"no_full_training_launch":True}))
