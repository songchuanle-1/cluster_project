"""Default NOP; generate tick-local reporting drafts only, never shared ledger/memory."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,re
ROOT=Path("D:/project/cluster_project");HERE=Path(__file__).resolve().parent;TICK=HERE.parent
CANDIDATE="fine-leaf-receiver-conditioned-vector-exchange";REVISION="daaf3041ebd3a9beacf487c60346d214374fd81a9a9411379801232e4450377f"
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument("--write-drafts",action="store_true");a.add_argument("--label");args=a.parse_args()
 if not args.write_drafts:print("DEFAULT_NOP: only explicit tick-local draft generation supported");return
 assert args.label and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}",args.label)
 now=datetime.now(timezone.utc).isoformat();owner=read(TICK/"launch_observe_prepare/owner_binding.json")["owner"]
 work=read(ROOT/"pipeline/research_work.json");c=next(x for x in work["candidates"] if x.get("id")==CANDIDATE);revision=next(x for x in c["revision_history"] if x["revision"]==1);assert canonical(revision)==REVISION
 queue=read(ROOT/"pipeline/queue.json");tasks=[t for ts in queue["gpu_queues"].values() for t in ts if t.get("id")=="M234-RVE"];assert len(tasks)==1;task=tasks[0]
 names=["source_verify_execution/verify_actual.json","operational_review/source_verifier_packet_independent_review.json","rvec_setup_execution/stage_actual.json","rvec_setup_execution/collect_actual.json","rvec_setup_execution/collect_result.json","operational_review/rvec_collect_actual_independent_review.json","rvec_setup_execution/production_activation.json","rvec_setup_execution/render_actual.json","rvec_setup_execution/render_result.json","operational_review/rvec_production_actual_independent_review.json","rvec_pointer_execution/switch_result.json","rvec_dispatch_execution/rvec_prelaunch_actual_resources.json","rvec_dispatch_execution/rvec_dispatch_intent.json","rvec_dispatch_execution/rvec_dispatch_result.json","dispatch_proof_execution/capture_actual.json","dispatch_proof_execution/dispatch_proof.json"]
 names+= [str(q.relative_to(TICK)).replace("\\","/") for q in sorted((TICK/"launch_observe_prepare").glob("*.actual.json"))]
 names += ["rvec_dispatch_execution/prelaunch_failure_reconciliation.json","clear_hold_actual.json","operational_review/rvec_render_actual_independent_review.json"]
 names=list(dict.fromkeys(names+[str(q.relative_to(TICK)).replace("\\","/") for q in sorted((TICK/"operational_review").glob("*.json"))]))
 evidence=[];values={}
 for name in names:
  q=TICK/name
  if q.exists():
   v=read(q);values[name]=v;evidence.append({"path":q.relative_to(ROOT).as_posix(),"sha256":sha(q)})
 verify=values["source_verify_execution/verify_actual.json"];render=values.get("rvec_setup_execution/render_result.json");dispatch=values.get("rvec_dispatch_execution/rvec_dispatch_result.json");proof=values.get("dispatch_proof_execution/dispatch_proof.json")
 assert verify["passed"] is True and verify["owner"]==owner and verify["kind"]=="CURRENT_READONLY_VERIFICATION_REUSE_OLD_SYNC_NOT_NEW_SYNC"
 if render:assert render["owner"]==owner and render["kind"]=="PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED"
 if dispatch:assert dispatch["owner_token"]==owner["token"]
 if proof:assert proof["owner"]==owner and proof["pid"]==int(task["pid"])
 verified=bool(dispatch and dispatch.get("launch_verified") is True and task.get("launch_verified") is True and task["status"]=="running")
 started=bool(verified or proof);observations=[v for k,v in values.items() if k.startswith("launch_observe_prepare/") and k.endswith(".actual.json")];growth=any(v.get("native_step_growth_observed") is True for v in observations)
 live=[v["observation"] for v in observations if v.get("returncode")==0 and "observation" in v and not v.get("parse_or_identity_error")]
 resource_reconciliation=values.get("rvec_dispatch_execution/prelaunch_failure_reconciliation.json");resource_block=bool(resource_reconciliation and resource_reconciliation["observation"]["free_memory_mib"]<resource_reconciliation["observation"]["required_free_mib"] and not dispatch)
 if resource_block:
  assert resource_reconciliation["owner"]==owner and not resource_reconciliation["dispatch_intent_exists"] and resource_reconciliation["observation"]["project_trainers"]==[] and resource_reconciliation["observation"]["marker_exists"] is False
 stage="training" if verified else "deployment"
 if verified:next_action="Protect the existing M234 process; collect bounded native progress/validation through canonical monitoring. Do not relaunch or replay consumed entry."
 elif resource_block:next_action="Wait for authorized GPU0 live free memory to reach at least20000MiB; preserve external tasks and all completed production evidence. No empty-GPU or low-utilization requirement. On a future valid owner, revalidate expiring owner/deadline guards and one-shot state before canonical dispatch; do not weaken resource policy or replay expired shim/lease."
 elif dispatch:next_action="Reconcile the existing dispatch PID/log/marker/start identity and native progress; do not issue another launch."
 else:next_action="Require actual rendered-production peer PASS, conda_source-only switch, clear only M234 setup hold, canonical one-shot dispatch and factual PID/marker/lock/native step growth before any training claim."
 servers=(ROOT/"SERVERS.yaml").read_text(encoding="utf-8");block=re.search(r"(?ms)^  server-4:.*?(?=^  [A-Za-z0-9_-]+:|\Z)",servers);pointer_match=re.search(r"(?m)^\s+conda_source:\s*(.+)$",block.group(0)) if block else None;pointer=pointer_match.group(1).strip() if pointer_match else "SEE_ACTUAL_SERVERS_BYTES"
 summary={"draft_only":True,"as_of":now,"owner":owner,"candidate_id":CANDIDATE,"experiment_id":"M234-RVE","stage_proposal":stage,"source_commit":verify["source_commit"],"current_source_verification_kind":verify["kind"],"historical_sync_retained_original_owner":verify["historical_sync"],"new_sync_performed":False,"current_queue":{k:task.get(k) for k in ("id","status","pid","log","gpu","claimed_gpu","dispatch_hold","launch_verified","launch_verification")},"SERVERS_sha256":sha(ROOT/"SERVERS.yaml"),"current_conda_source":pointer,"actual_production_rendered":bool(render),"production_artifact":render.get("artifact") if render else None,"canonical_dispatch_artifact_exists":bool(dispatch),"launch_verified":verified,"training_started_supported_by_actual_identity_or_canonical_progress":started,"native_step_growth_observed":growth,"latest_actual_observations":[{k:x.get(k) for k in ("pid","start_ticks","latest_native_step","log_bytes","error_markers","all_three_original_lock_inodes_inherited")} for x in live[-3:]],"next_action":next_action,"scientific_efficacy":"UNKNOWN","novelty":"UNKNOWN","long_term_stability":"UNKNOWN","immutable_passed_revision_digest":REVISION,"evidence":evidence,"shared_memory_or_ledger_modified":False,"refresh_before_apply_if_launch_or_queue_changes":True}
 summary["actual_resource_block"]=resource_reconciliation if resource_block else None
 summary["production_pointer_switched"]=bool(values.get("rvec_pointer_execution/switch_result.json"));summary["M234_setup_hold_cleared"]=bool(values.get("clear_hold_actual.json"))
 patch={"draft_only":True,"as_of":now,"candidate_id":CANDIDATE,"base_research_work_sha256":sha(ROOT/"pipeline/research_work.json"),"immutable_revision1_sha256_before_and_required_after":REVISION,"append_only_candidate_outer_evidence":evidence,"candidate_outer_fields_proposed":{"stage":stage,"queued":task["status"] in ("waiting","claiming","running"),"deployed":True,"source_synced":True,"runtime_code_commit":verify["runtime_code_commit"],"training_started":started,"dispatch_hold":task.get("dispatch_hold"),"blocker":task.get("dispatch_hold") or (None if verified else "Actual canonical progress/launch reconciliation pending"),"next_action":next_action,"current_owner_operational_readiness":{"owner":owner,"as_of":now,"current_verification_sha256":sha(TICK/"source_verify_execution/verify_actual.json"),"actual_render_result_sha256":sha(TICK/"rvec_setup_execution/render_result.json") if render else None,"launch_verified":verified,"native_step_growth_observed":growth}},"forbidden_targets":["revision_history[*]","revision_history[revision=1].evidence","revision_history[revision=1].result_evidence","other_candidates","queue","SERVERS","shared_memory"],"application":"Root must recheck current facts/base hash and append only missing outer evidence; no automatic application is provided."}
 if resource_block:
  patch["candidate_outer_fields_proposed"]["blocker"]="Actual GPU0 free6503MiB below required20000MiB; no project trainer, marker or dispatch intent; waiting production_ready. External workload remains untouched."
  patch["candidate_outer_fields_proposed"]["runtime_resource_block"]=resource_reconciliation
 baseline=(ROOT/"pipeline/codex_memory.md").read_text(encoding="utf-8");head=baseline.split("## Active Hypotheses",1)[0]
 active=baseline.split("## Active Hypotheses",1)[1].split("## Closed Or Failed Directions",1)[0]
 active=re.sub(r"(?m)^- M234-RVE[^\n]*", "- M234-RVE稳定ID fine-leaf-receiver-conditioned-vector-exchange，当前source d21477b0、已canonical准入/原owner真实同步保留；本轮另存新owner ee6f5eda只读验证和CPU生产render通过。部署/启动状态见Running And Queue；效力/novelty UNKNOWN。",active,count=1)
 closed=baseline.split("## Closed Or Failed Directions",1)[1].split("## Running And Queue",1)[0]
 risks=baseline.split("## Open Questions And Risks",1)[1].split("## Last Tick",1)[0]
 risks+="- 本轮read-only验证复用旧sync，不是新sync；CPU stage/collect/render及identity-only UUID不能冒充GPU occupancy/resource PASS、长训练或步数增长。所有新声明必须取实际dispatch/proof/observer artifact。\n"
 launch_line=("- 实际canonical launch/progress已验证；现有PID"+str(task.get("pid"))+"；实际log"+str(task.get("log"))+"。禁止重放已消费入口。\n") if verified else ("- 截至本草稿时间，canonical dispatch记录"+("已存在，实际进度/身份待协调；不得再次派发。" if dispatch else "不存在；不声称训练已启动。")+"\n")
 running="\n- M234 queue实际status="+str(task.get("status"))+"；dispatch_hold="+str(task.get("dispatch_hold"))+"；launch_verified="+str(verified)+"。\n"+launch_line+"- runtime根/data/songcl/Project/Cluster_project/Cluster_nsd_20261107，实际HEAD d21477b0；main0747/index/user28/r0九文件保持。558旧sync22fb0e59保留原owner，不重放；ee6当前验证951e2e93是只读复核。\n- SERVERS实际conda_source="+pointer+"，SHA="+sha(ROOT/"SERVERS.yaml")+"；只以真实switch结果/当前bytes为准。M206/M227独立人工暂停授权保持。\n- 新生产stage /data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prod_ee6f5eda；CPU render时marker未消费/未启动训练。之后是否消费仅以实际marker/PID proof为准。\n- 实际observer增长="+str(growth)+"；早期步数不证明完整epoch/验证、最终效力或长期稳定性。\n"
 last="\n- ee6f5eda，快照2026-11-09T07:10:46.030397Z，原deadline08:10:46.030397Z；本草稿as-of "+now+"，仅tick-local，shared memory/work未由作者修改。\n- 当前只读source验证951e2e93通过，kind CURRENT_READONLY_VERIFICATION_REUSE_OLD_SYNC_NOT_NEW_SYNC，保留旧sync22fb0e59原owner。\n- 新stage c7a13282 / CPU collect0250ea6a、resultf6b321a3、独审39bef064通过；root activation4906c93a仅授权render，training_launch_authorized=false。\n- 实际render38519c30/result735fd2e8通过，固定bindingb9a56ca3、entrybc455767、corec0857d0b；真实PATH/conda CPU验证，render本身未训练/未消费marker。实际生产独审/切换/hold-clear/dispatch仅按本快照已有artifact及Running And Queue事实为准；render本身不证明这些阶段已完成。\n- 已passed RVE revision1 canonical digest daaf3041ebd3a9beacf487c60346d214374fd81a9a9411379801232e4450377f保持；新证据仅加candidate外层，不改revision evidence/result_evidence。native841 exact/common 与历史835不同scope；不重测有效门槛。\n- 下一步："+next_action+"\n"
 if resource_block:
  resource_note="- 2026-11-09T08:05:48Z实际resource block：GPU0 used26104/total32607/free6503MiB、util93%，free<原required20000；项目trainers=[]，marker=false，dispatch_intent=false，M234waiting/production_ready/无setup hold，无PID/log，无长训练、无步数增长。原生产实际独审/指针切换/仅M234 hold-clear已完成，不驱逐外部任务、不降低门槛、不误称机制失败。reconciliation SHA6adfb07d7e85cf9b27cd561c7ee56d2d89bc3820e9df95edc0afcccec6bd7640。\n"
  running+=resource_note;last+=resource_note
 memory=head+"## Active Hypotheses"+active+"## Closed Or Failed Directions"+closed+"## Running And Queue"+running+"\n## Open Questions And Risks"+risks+"\n## Last Tick"+last
 assert len(re.findall(r"(?m)^## ",memory))==7
 out=HERE/args.label;out.mkdir(exist_ok=False)
 for name,value in (("report_notes.draft.json",summary),("candidate_outer_patch.draft.json",patch)):
  with (out/name).open("x",encoding="utf-8",newline="\n") as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write("\n")
 (out/"codex_memory.successor.draft.md").write_text(memory,encoding="utf-8",newline="\n")
 assert canonical(next(x for x in read(ROOT/"pipeline/research_work.json")["candidates"] if x.get("id")==CANDIDATE)["revision_history"][0])==REVISION
 print(json.dumps({"draft_directory":str(out),"as_of":now,"stage_proposal":stage,"launch_verified":verified,"native_step_growth_observed":growth,"files":{q.name:sha(q) for q in out.iterdir()}}))
if __name__=="__main__":main()
