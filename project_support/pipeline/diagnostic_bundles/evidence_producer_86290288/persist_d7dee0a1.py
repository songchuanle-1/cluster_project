"""Persist real CPU results and honest GPU blocks under the current lease."""
from datetime import datetime, timezone, timedelta
import os
from pathlib import Path
import sys

os.environ.update(PROJECT_ROOT="D:/project", PYTHONDONTWRITEBYTECODE="1")
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

ROOT = Path("D:/project/cluster_project")
OUT = Path(__file__).resolve().parent
TOKEN = "d7dee0a18225465284ff88f668cfc050"
PRIMARY = "m95-hierarchical-mask-feature-path-audit"
CID = "m202-paired-native-evidence-producer"
IDS = ["m95-native-relation-other-sign-conflict", "m95-native-main-role-weight-precedence",
       "m95-native-secondary-positive-mass", "m95-native-between-pair-support"]


def guard():
    owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    return owner


def ev(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": tick.digest(path)}


guard()
assert tick.digest(ROOT / "pipeline/goal.json") == "42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec"
plan = ROOT / "pipeline/designs/exp_design_20261016_hier_support_admitted.md"
assert tick.digest(plan) == "e03b138638da520f1a873e81e2ee501a2f3b18bc5545c98aed9fc9c4127f1fca"
cpu = tick.load(OUT / "cpu_controls.json")
preparation = tick.load(OUT / "preparation_result.json")
resources = tick.load(OUT / "resources_d7dee0a1.json")
assert cpu["passed"] and cpu["tests_run"] == 13 and preparation["static_compile_passed"]
assert preparation["native_forwards"] == 0 and not preparation["cuda_initialized"]
for value in resources.values():
    assert value["source_hashes_match"] and value["samples"][-1]["compute_processes"]
samples = resources["server-4"]["samples"]
first, last = samples[0], samples[-1]
def step(sample):
    phase, epoch, _, index, _ = sample["native_steps"][-1]
    return int(epoch), int(phase == "Val"), int(index)
assert first["training_alive"] and last["training_alive"] and step(last) > step(first)
assert not last["tail_crash_markers"] and len(last["training_lock_fds"]) == 3
assert all(row["pid"] == 1592337 for row in last["compute_processes"])
scalars = last["current_scalar_logs"][0]["miou"]
best = max(scalars)
continuity = {"observed_at": last["observed_at"], "samples_last": [sample["native_steps"][-1] for sample in samples],
              "native_progress_increased": True, "best_miou": best, "completed_val_records": len(scalars),
              "native_expression_counts": last["current_scalar_logs"][0]["expressions"],
              "source_hashes_match": True, "source_file_count": len(resources["server-4"]["source_hashes"]),
              "lifetime_locks": last["training_lock_fds"], "no_restart_or_model_changes": True,
              "scope": "Current SAME M202 continuation; scalar-only, no scene-paired trained efficacy"}
tick.save(OUT / "continuity_d7dee0a1.json", continuity)
work = tick.load(ROOT / "pipeline/research_work.json")
candidate = next(c for c in work["candidates"] if c["id"] == CID)
assert candidate["stage"] == "diagnosis" and candidate["candidate_type"] == "operational_diagnostic"
now = datetime.now(timezone.utc)
candidate.update({
    "stage": "blocked", "blocker_kind": "exclusive_gpu_slot", "required_server": "server-3",
    "blocker": "CPU producer and 13 controls/source-contract/manifest preparation completed. Preferred frozen server3 physicalGPU1 has NVML PID1453 using18687MiB, utilization100%, only5578MiB free at04:16:06Z. Alternative authorized server4 physicalGPU0 is running SAME M202 PID1592337 with all3lifetime locks held at04:16:13Z. No exclusive slot is currently safe; do not overlap, signal, reset or delete locks.",
    "retry_after": (now + timedelta(hours=1)).isoformat(),
    "unblock_condition": "Fresh authorized GPU1 UUID/hostname check shows no other compute context, utilization<10%, memory<1GiB used and all3lifetime locks acquired; then reverify frozen inputs and execute native_equivalence.py with fixed TRAIN groups before the current lease deadline. If server4 becomes free first, prepare a path/runtime-only manifest for that SAME diagnostic after its original3locks release; never interrupt M202 or alter scientific gates.",
    "next_action": "Resume SAME producer, not another schema review: upload the frozen exporter/native runner/manifest only after a live idle authorized slot is verified, execute four single-scene fixed-TRAIN native predicts without optimizer steps, compare all prediction payload hashes and exact float32 aggregate, then preserve JSON-roundtrip and full-identity paired controls. Native equivalence remains UNRUN, not PASS.",
    "attempted_alternatives": [
        "Implemented prediction-blind exporter; executed13CPUtests including shuffled alignment, object/scene/split/annotation conflicts, duplicate/missing/nonfinite/out-of-range rejection and exact float32 JSON aggregation.",
        "Verified original M95 and HDS predict methods have identical AST and native ScanRefer/res aggregation; compiled3files; current frozen checkpoint/config hash and Python/Torch CPU environment verified with CUDA uninitialized.",
        "Checked BOTH authorized slots after CPU controls: server3GPU1 is occupied by a non-managed compute context despite available project flocks; server4GPU0 is held by SAME training and3flocks. No GPU calculation or eviction attempted."],
    "execution_status": "CPU preparation passed; native GPU equivalence unrun due to actual occupation. No model revision/admission/launch.",
    "closure_compatibility_risk": "Existing closure exclusive_gpu_slot_available consults managed queue only. server3 has a queue opening despite live external GPU occupation; do not falsify required_server or change blocker_kind/checker to manufacture a PASS."})
for name in ("aligned_evidence.py", "test_aligned_evidence.py", "cpu_controls.json", "source_contract.json",
             "probe_attempt_1.json", "resources_d7dee0a1.json", "assets_d7dee0a1.json", "native_equivalence.py",
             "native_manifest.json", "preparation_result.json", "prepare_and_probe.py", "freeze_assets.py"):
    candidate["evidence"].append(ev(OUT / name))
primary = next(c for c in work["candidates"] if c["id"] == PRIMARY)
assert primary["stage"] == "training" and len(primary["revision_history"]) == 2
primary["evidence"].append(ev(OUT / "continuity_d7dee0a1.json"))
rows = []
for cid in IDS:
    c = next(c for c in work["candidates"] if c["id"] == cid)
    assert c["stage"] == "blocked" and c["blocker_kind"] == "human_authorization"
    rows.append({key: c.get(key) for key in ("id", "blocker", "blocker_kind", "unblock_condition", "next_action")})
scope = {"observed_at": now.isoformat(), "goal": ev(ROOT / "pipeline/goal.json"), "frozen_plan": ev(plan),
         "candidates": rows, "new_auxiliary_authorization": False,
         "attempted_alternatives": ["Latest goal/mainline and direct user messages reviewed; no scope restoration.",
                                   "Frozen admitted plan unchanged; no separately required auxiliary supervision test.",
                                   "Timer expiry and spare capacity do not satisfy any existing unblock condition."],
         "scope": "Human scope holds only, not scientific rejection or claimed GPU blockage of those four IDs"}
tick.save(OUT / "scope_d7dee0a1.json", scope)
for cid in IDS:
    c = next(c for c in work["candidates"] if c["id"] == cid)
    c["evidence"].append(ev(OUT / "scope_d7dee0a1.json"))
    c["retry_after"] = (now + timedelta(hours=4)).isoformat()
work["design_cycle"] = {"stop_reason": "external_resource_blocked", "attempted_ids": [CID, PRIMARY, *IDS],
    "evidence": [ev(OUT / name) for name in ("preparation_result.json", "resources_d7dee0a1.json", "scope_d7dee0a1.json")],
    "resume_condition": candidate["unblock_condition"],
    "scope": "Real native exclusive-slot block on BOTH authorized devices plus4unchanged human scope holds. No independent-route exhaustion claim; queue-only validator may reject the real external occupation."}
guard()
tick.save(ROOT / "pipeline/research_work.json", work)
notes = {"actions": [
    "本轮快照2026-10-17 12:08:48（上海时间），design；旧86290288轮被后续心跳中断、已超过原deadline。核对无遗留helper后用原令牌abort，原诊断/预注册保留且租约释放已核实；这不把旧轮补记为完成。本轮仅begin一次。",
    "续做原稳定ID m202-paired-native-evidence-producer，无新模型/结构修订。实现只读预测IoU导出器，13项CPU软件测试全部通过：乱序仍按完整split/scene/object/annotation对齐，重复/缺项/身份冲突/非有限/越界值被拒，JSON往返及原生float32均值保持；合成测试不证明真实模型收益。",
    "静态源码审计确认M95与HDS的predict/predict_by_feat完全相同，原生ScanRefer/res无nt_label重标记；predict只支持单场景batch，诊断使用batch1，不改训练batch2。3文件静态编译通过，冻结M95 checkpoint与配置在server3用CPU重新核验哈希，实际Python3.8/Torch1.12、CUDA未初始化。原生等价性runner/manifest已准备，仍UNRUN；不是native backward或训练效果PASS。",
    "12:16:06资源实测：server3物理GPU1正确UUID，非本轮管理的PID1453占18687MiB、利用率100%、空余5578MiB，三项目flock虽空闲却不代表GPU独占；12:16:13 server4物理GPU0为同一M202/PID1592337，三把原生命周期锁均持有。两授权槽均不可独占，无GPU计算、驱逐、reset、锁删除或重启。探针初次systemPython3.6不支持text参数的编排失败已保留，只改兼容API后通过，不算模型修订。",
    "同一M202两次7秒间隔原生Train步数" + str(continuity["samples_last"]) + "，确认增长，12个冻结源码/config/训练工具哈希相同，当前尾部无新异常。当前best=" + str(best) + "，累计20次VAL各9508表达；这是累计同一验证集观测，不是本轮20个独立实验。场景配对区间、噪声底限、最终效益及全程峰值仍未知。",
    "四个到期辅助ID各按ID复核一次，保留原human scope hold/失败/unblock条件并有界四小时复查，无晋升或M201恢复。储备已有5/目标2，本轮不扩储备、不为填槽变更主线。",
    "本轮实际产出：1个原诊断的可运行导出器、13项CPU测试结果、1份源码契约、冻结native输入与runner、双卡实时占用/同一训练连续性证据、4项scope复核及七段记忆/完整六段报告。新模型/修订/准入/训练启动/native GPU forward均0。收据用量仅begin至收据的本地窗口，早前读取/最终回复排除；最终用量暂未知，cache已在input内、reasoning已在output内，不重复相加，不当账单。"
    ], "decisions": [
    "科学状态：保持原M202训练与预注册评估/早停；best0.494656仅数值高于baseline0.4894、仍低于champion0.5020及target0.5100，不据此声称分层机制有效或被否定；原TypeError根因仍未知。",
    "执行状态：原生导出等价性因两授权卡实际占用而blocked；按真实server3冻结manifest记录required_server，不把外部占用伪装为本项目队列任务、不改阻塞类型或校验器来凑PASS。当前queue-only闭环校验可能拒绝此真实资源阻塞；必须以实际finish为准，失败则保留证据并abort、核实释放。",
    "不改goal、科学准入、两次修订上限、FLOPs特例、seed1999/epochs50/max_iters70、调度、其他项目或通知策略。空槽和到期不是放宽门槛的理由。"
    ]}
tick.save(OUT / "notes_d7dee0a1.json", notes)
memory = f"""# Codex Research Memory
## Goal And Phase
- USER20261015 mainline: scale-specific hierarchical interaction must really update point/superpoint inst_feats used with query features for masks. Efficiency is a Pareto constraint, not the sole contribution. Phase1 no tuning; target .5100.
- Goal SHA42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec,24constraints/11bans unchanged. SAME HDS revision2 has exact-source10.034588748G exception only; no revision3/global gate change.
- Authorized server3 physicalGPU1/sysu311-MS-7C59/192.168.1.120/UUIDGPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0 AND server4 physicalGPU0/dl04-MS-7E06/192.168.1.115/UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c,one task each/capacity2. No other GPU, eviction, reset, lock deletion, M201 recovery or scheduler change.
- SAME M202 currently uses native resume of its OWN epoch7 server4 checkpoint. Preserve source-bound revision2,seed1999/batch2/workers4/epochs50/max_iters70 and frozen evaluation boundaries.
## Champion And Baseline
- Historical M95=.5020, baseline=.4894, target=.5100, champion gap=.0080. Current M202 best={best!r}; numeric delta vs baseline={best-.4894!r}, vs champion={best-.5020!r}. Not scene-paired evidence or a mechanism-success conclusion.
- Current resumed run has{len(scalars)}completed VAL records, each9508expressions of SAME population; latest{scalars[-1]!r}. Not independent cohorts or this tick's experiment count. Noise floor/paired scene intervals remain UNKNOWN.
- Original standard FLOPs M95/HDS9.762532428G/10.034588748G; parameters157484090 each. User accepts only this source-bound .34588748% overrun; all relative memory/latency gates remain.
- Source limited-cohort memory4293406720/4499342848bytes did NOT guarantee training: server3 later OOMed. Target matched4scene train pair peaks M95/HDS6396853760/4492709888 and4131358720/2821511680bytes are diagnostic-only; whole-training peak unknown.
## Active Hypotheses
- Stable m95-hierarchical-mask-feature-path-audit / SAME M202-HDS uses disjoint fine/middle/coarse value support on the original point path; no new loss/routing/head/scale/seed/schedule. Exactly2passed implementation revisions.
- Model model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1,9Python+uniqueYAML,commit1400e0c3e580410e40e9b19634d321f0dc5e01b1. Native continuity confirms all12frozen source/config/train/utils hashes unchanged.
- Historical20native rematerialization controls passed exact output/input/parameter gradient identity at1e-6; four TRAIN scenes/16expressions baseline/HDS full native backward passed24finite nonzero point-path gradients each. Historical evidence, not repeated this tick.
- CURRENT continued operational diagnostic m202-paired-native-evidence-producer is BLOCKED/exclusive_gpu_slot,preferred required_server=server-3. It is NOT a new model, training experiment, structural revision or novelty claim.
- CURRENT implemented aligned_evidence.py;13CPUtests passed. Full split/scene/object/annotation identity handles annotation collisions, shuffled pairs, duplicate/missing/conflicting identities and bad IoUs; exact float32 aggregation/JSON roundtrip preserved on fixtures. Software controls are not native model efficacy.
- Source-contract audit: M95/HDS predict methods identical AST; actual ScanRefer/res uses empty nt_labels and native torch.stack(...).numpy().mean(). Native predict assumes ONE scene (scan_ids[0]); diagnostic batch1 only, original training batch2 unchanged. Optional metadata never fabricated.
- Native runner/native_manifest.json prepared and3files statically compiled. server3 CURRENT trusted M95 checkpoint SHAfe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e and baseline YAML SHAa18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a rehashed on CPU. Runtime /home/songcl/.conda/envs/3d-stmn/bin/python,Torch1.12+cu113,CUDA not initialized. Native equivalence UNRUN; not PASS or native backward.
## Closed Or Failed Directions
- Preserve original12prototype/4native compacted strict FAILs,25%cap OOMs,suffix-only incomplete attempts and original10GFAIL. They concern realizations, not falsification of the whole mechanism.
- Original ancestor support misses mean86.576%valid leaves and multiply covers2.035%; disjoint support exactly once16/16. Branch geometry only, not whole-model missing context or semantics/task harm.
- Original source PID40465 died OOM Train[1/50]1896/4686,21.20GiB allocated/22.48reserved,122MiB request,69.56MiB free; no M202 checkpoint existed. Preserve source failure log SHA28d727502bd3337e15648ff1d5de92f9b7a4d0a5c3ee3609ff77bd62b90c6fd0.
- User explicitly authorized SAME M202 fresh start on server4 after source OOM/no checkpoint; target native backward/resources verified before original launch. This was NOT resume. Original target PID216566 later died TypeError Parameter object not callable in native cuda_cast/Module.cuda atTrain[8/50]2998/4686,NOT OOM.
- Original TypeError log SHA7f895d3fc936b9be0e7b0bedede26cc1fe85207c3daae96e54a1f51d57000c25 preserved. Historical controlled recovery did NOT reproduce it:1163model entries/642optimizer states/scheduler matched;48cuda conversions kept parameter identities and4fixed TRAIN scenes completed backward,0optimizer steps. Root cause UNKNOWN,not repaired.
- Original3zero-step source startup failures and local GBK/serializer orchestration failures remain archived. No target Torch2.8 ctypes workaround. Initial checkpoint audit false missing flag for numpy.float32 corrected with real scalar evidence,not rewritten as a missing field.
- CURRENT read-only probe first failed because systemPython3.6 does not support subprocess text=True; probe_attempt_1.json preserved. universal_newlines compatibility repair passed; no model change or GPU initialization.
## Running And Queue
- CURRENT immutable snapshot2026-10-17T04:08:48.783026Z/design/deadline05:08:48.783026Z;active1/capacity2/budget1,waiting0,newterminal0,due5,reserve5/target2/budget0. begin monitor saw M20228/50,best.4947,no_improve8/10. No repeated preflight.
- CURRENT live observation{last['observed_at']}: SAME PID1592337/server4GPU0;7second samples native steps{continuity['samples_last']!r}; actual increase confirmed. Correct UUID,3original lifetime lockFDs,own-only GPU0 context,12source hashes unchanged,no new bounded-tail crash marker. Training continues; do not overlap diagnostics or blindly restart.
- CURRENT server4 instantaneous GPU0 used15103/free17007MiB/util37%; not full-run peak. Native log /data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1_20261017_003226.log is current; old20261016_173436 is archived crash.
- CURRENT server3GPU1 observation04:16:06Z: non-managed NVML PID1453 uses18687MiB,device18690used/5578freeMiB/util100%; project flocks available but slot NOT exclusive. No signal or GPU calculation. BOTH authorized slots have actual occupation evidence after CPU controls.
- Native resume source preserved in original20261016_173442/last.pth,936269892bytes,epoch7,best.47346487641334534,no_improve0,SHAfe4301ec2607f0ee0604173ea31422ae91df8e15b082657c557955c2c4d67e6c. Current process restarted epoch8 boundary,not lost-batch/RNG replay.
- Current admission pipeline/admissions/M202-HDS_resume_fded20f5.json; original pipeline/admissions/M202-HDS_server4_3c22e34d.json preserved. No duplicate queue entry,admission,recovery or automatic M201.
## Open Questions And Risks
- HDS trained mechanism benefit,full-run peak,scene-paired uncertainty,subgroup harm/noise floor and generalization remain UNKNOWN. One scalar high-water mark is not a paired efficacy result; no tuning from VAL.
- Historical TypeError root cause UNCONFIRMED; current continuation is observed,not proof of repair. Another failure requires exact native-state preservation and investigation,not blind relaunch/revision3.
- Native loop persists aggregates,not aligned per-expression evidence. Frozen original design SHA07bee904ae705a52547619de1a4cfb6fc89a7e168f7a79329584a01c0b4fca31 and admitted plan SHAe03b138638da520f1a873e81e2ee501a2f3b18bc5545c98aed9fc9c4127f1fca unchanged. Prepared exporter still needs fixed TRAIN native equivalence before actual matched trained evaluation.
- CURRENT13CPUcontrols/source audit/manifest/assets are complete; next test is native4single-scene TRAIN predict export with same M95 checkpoint/seed1999,0optimizer steps,payload hash/float32 aggregate equality and full-ID shuffled alignment. Recheck live UUID,occupation,3locks,exact assets and deadline first. Never run on busy GPU1 or overlapping server4 training.
- CURRENT4due auxiliary IDs retain human_authorization/auxiliary_scope_hold and original gates/failures; goal and admitted-plan hashes unchanged,no scope restoration or required mainline-matched auxiliary test. Four-hour retry recorded in ledger,not automation timing; spare GPU/timer never permits promotion/M201 recovery.
- Closure compatibility risk: exclusive_gpu_slot validator uses managed queue only,so preferred server3 has an apparent queue opening despite actual external PID1453. Preserve honest required_server/blocker; do not falsify queue or patch shared checker to obtain PASS. Actual finish may require abort with mismatch evidence.
## Last Tick
- Previous token862902880d824f63be9f0113367d1207 was interrupted,original deadline03:09:52Z passed. At04:08:12Z no previous Python/bash/helper writer remained; original-token abort saved INCOMPLETE receipt/discarded pending state/released lease,absent lock verified. Registered producer/prereg kept,unrun tests not backfilled as PASS.
- CURRENT tokend7dee0a18225465284ff88f668cfc050,verified owning thread01a04987-fdbe-7301-b2f0-f9b6ab60f74c. All current evidence under pipeline/diagnostic_bundles/evidence_producer_86290288; do not rerun registration or persist script.
- Actual current output: continued1existing operational ID,implemented exporter,13CPUcontrols,source-contract audit,3static compilations,frozen native runner+manifest,current CPUcheckpoint/runtime verification,dual-slot occupation and native continuity record,4real human scope checks. New candidates/models/revisions/admissions/launches/nativeGPUforwards/optimizer steps0.
- Scientific status: same training,best{best!r} below historical champion/target; native exporter equivalence unmeasured due to real resources. Execution recorded BEFORE postflight; require actual finish PASS and absent matching lease,otherwise preserve evidence/abort and report incomplete.
- Receipt usage window is begin-to-receipt local records only,earlier reads/final reply excluded;final usage currently unknown,cache already in input/reasoning in output,not billing. No post-release project writes.
"""
assert len(memory.splitlines()) < 120
guard()
(ROOT / "pipeline/codex_memory.md").write_text(memory, encoding="utf-8")
print("PERSISTED: CPU13 PASS; native UNRUN/real exclusive_gpu_slot block; training continuity verified; postflight NOT RUN")
