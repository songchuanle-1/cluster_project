"""Preserve source history, render six-section audit and record real disposition."""
from datetime import datetime,timezone
import json
from ops import ROOT,OUT,CODE,CID,TOKEN,guard,save,evidence,run,tick
import closure

owner=guard()
remaining=(datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()
assert 0<remaining<=180,"Only the actual final180seconds permit this disposition"
work=tick.load(ROOT/"pipeline/research_work.json")
candidate=next(c for c in work["candidates"] if c["id"]==CID)
assert candidate["stage"]=="training" and candidate["experiment_id"]=="M203-FLE"
archive=OUT/"source_before_guard/__init__.py"
relocations=[]
for entry in candidate["evidence"]:
    path=ROOT/entry["path"]
    if path.name=="__init__.py" and "_fle_r1/" in entry["path"] and tick.digest(path)!=entry["sha256"]:
        assert tick.digest(archive)==entry["sha256"]
        old=dict(entry);entry["path"]=archive.relative_to(ROOT).as_posix()
        relocations.append({"original":old,"archived":dict(entry),"current_path_sha256":tick.digest(path),"reason":"Original hash-identical M95 init archived before guard-only import update;tested mathematical sources unchanged. Not a retimestamped test or rewritten result."})
assert len(relocations)==1
save("source_evidence_relocation.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"entries":relocations,"archive_copied_from":"unchanged hash-identical M95 __init__.py","negative_evidence_removed":False})
candidate["evidence"].append(evidence(OUT/"source_evidence_relocation.json"))
for entry in candidate["evidence"]:closure.artifact(ROOT,entry)
queue=tick.load(ROOT/"pipeline/queue.json")
task=next(t for t in queue["gpu_queues"]["server-4"] if t["id"]=="M203-FLE")
assert task["launch_verified"] and task["status"]=="running"
closure.admission(ROOT,task)
live=tick.load(OUT/"live_training_postcheck.json")
summary={"observed_at":datetime.now(timezone.utc).isoformat(),"immutable_snapshot_at":"2026-10-17T14:12:50.697689+00:00",
    "latest_training_observation_at":live["observed_at"],"latest_native_step":live["latest_native_step"],"unique_TRAIN_scenes":4,"unique_TRAIN_expression_identities":16,
    "full_native_diagnostic_forwards":10,"full_native_diagnostic_backwards":10,"native_suffix_replays":4,"complete_resource_receipts":2,"predict_calls_per_complete_receipt":121,
    "additional_serialization_failed_resource_calls":121,"setup_failed_resource_calls":0,"diagnostic_optimizer_steps":0,"new_models":1,"new_admissions":1,"verified_training_launches":1,
    "new_validation_efficacy_results":0,"material_novelty":"unestablished_known_operators","full_training_peak":None,"original_baseline_resource_delta":None,
    "stop_reason":"tick_deadline_near","seconds_remaining_at_disposition":remaining,"execution_status":"pending_actual_finish_not_preclaimed"}
save("progress_summary.json",summary)
candidate["evidence"].extend([evidence(OUT/"live_training_postcheck.json"),evidence(OUT/"server3_live_observation.json"),evidence(OUT/"progress_summary.json")])
work["design_cycle"]={"stop_reason":"tick_deadline_near","attempted_ids":[CID],"evidence":[evidence(OUT/n) for n in ("progress_summary.json","dispatch_result.json","live_training_postcheck.json","resource_comparison.json")],
    "resume_condition":"Next tick monitor the SAME M203-FLE native run and first VAL/terminal/resource evidence. Preserve frozen evaluation and auxiliary holds;never duplicate launch or fabricate another variant for the remaining logical slot."}
guard();tick.save(ROOT/"pipeline/research_work.json",work)
notes={"actions":[
    "本轮冻结快照为2026-10-17 22:12:50上海时间（design）；0-3段保留脚本当时事实，不把后来启动混入旧快照。科学状态：尚无新验证提升或已确立新颖性；本轮执行收尾仍待真实finish。",
    "完成一个物理独立的细层逐点交换模型：移除孤立细层FFN，保留M95中粗层上下文与原训练数值。CPU契约、同前缀匹配对照、两批完整原生反向、18个有效点路径参数梯度、原配置四worker及原生backbone新初始化全部有实测证据；10次完整前后向调用仅覆盖重复测量的4个TRAIN场景/16条表达，不是10项独立实验。",
    "同输入同口径资源：候选9.627987020G，M95 9.762532428G；中位延迟43.73ms对36.82ms，约慢18.77%；推理峰值934659072对936763392字节。两种worker设置下配对训练样本峰值增加3.48%-7.92%，不是全程训练峰值。原始无cluster baseline资源参照未知；补充未计数算子工作单列，不改变10G门槛。",
    "仅新增准入及启动M203-FLE一个实验，提交587cccf，现有门控入口安全快进同步，原生步数增长已核实。23:05:27上海时间实际第1轮第599步，server4 GPU0三把锁均属同一PID1995443；首次验证指标未知。server3 GPU1仍有外部占用，未驱逐或叠加。没有M201恢复、HDS第三次修订、旧辅助路线重开或其他项目/调度修改。",
    "直接核对Point Transformer和RefMask3D原文：逐点局部注意力及query-点mask不是已证明的新发明；这里只做结构假设首筛。保留原等距失败、资源脚本同名故障、测量后JSON序列化失败及派发前字段故障，未将失败改为PASS。完整资源收据两份各121次调用，另一次121次调用后写出失败单独保留；诊断优化器更新0，实际新训练已有步增长。用量仅统计本轮begin至收据的本地日志窗口，早期读取/迟到记录/最终回复不含；收据最终数值在finish前未知，缓存属于输入、推理属于输出，不重复相加也不当账单。"
 ],"decisions":[
    "仅以执行性门槛准入一个FLE结构首筛，不宣称已提升或核心创新成立。冻结完整VAL、历史baseline/champion与可用M95权重参照、场景区间、细层混合代理子组及伤害/Pareto规则，效果留待训练结果；原始baseline资源未知和当前延迟代价明确留档。",
    "真实截止已进入180秒内，按tick_deadline_near收尾；保留同一M203-FLE监控和首个VAL/终态为下一动作，不硬撑截止、不凑第二变体、不将server3外部占用或旧授权保留伪装为科学否定。下一次准确调度时间未核实。"
 ]}
save("report_notes.json",notes)
result=run(["python","-B","C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/foreground_tick.py","cluster_project","report","--token",TOKEN,"--notes",str(OUT/"report_notes.json")],90)
assert result.returncode==0,result.stderr
assert len((ROOT/"pipeline/codex_memory.md").read_text(encoding="utf-8").splitlines())<120
print(json.dumps({"report_rendered":True,"native_step":live["latest_native_step"],"remaining_seconds":remaining,"ready_for_actual_finish":True}))
