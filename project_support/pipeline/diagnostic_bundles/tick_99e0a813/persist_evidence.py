"""Persist measured outcomes,source controls and honest unfinished core work."""
from datetime import datetime,timezone,timedelta
import ast
import hashlib
import json
from ops import guard,save,evidence,tick,ROOT,OUT,STAGE,ssh,run
guard()
fine=tick.load(OUT/"fine_audit_result.json");ties=tick.load(OUT/"tie_audit_result.json")
assert fine["passed_controls"] and ties["passed_controls"]
rows=fine["rows"];total=sum(r["valid_superpoints"] for r in rows);mixed=sum(r["superpoints_in_mixed_leaves"] for r in rows)
fine_summary={"observed_at":datetime.now(timezone.utc).isoformat(),"expressions":128,"scenes":32,
    "expressions_with_mixed_fine_leaves":sum(r["mixed_leaves"]>0 for r in rows),"valid_superpoints":total,"superpoints_in_mixed_leaves":mixed,
    "pooled_mixed_member_fraction":mixed/total,"scene_mean_mixed_member_fraction":fine["mean_scene_mixed_member_fraction"],
    "native_errors_in_mixed_leaves":sum(r["native_mixed_leaf_errors"] for r in rows),"native_errors_elsewhere":sum(r["native_other_leaf_errors"] for r in rows),
    "mixed_error_rate":sum(r["native_mixed_leaf_errors"] for r in rows)/mixed,
    "other_error_rate":sum(r["native_other_leaf_errors"] for r in rows)/(total-mixed),
    "bank_only_minority_label_error_count":sum(r["bank_only_minority_error_count"] for r in rows),
    "scope":"Native TRAIN majority-target fine-leaf mixing proxy;not unique/relation/boundary annotations,not a whole-model error lower bound or proof of a causal bottleneck.",
    "real_geometry_stress":{"exact_cutoff_ties":sum(r["exact_cutoff_tie_rows"] for r in ties["rows"]),"adjacency_changes":sum(r["adjacency_membership_changed_rows_under_reversal"] for r in ties["rows"]),"max_duplicate_coordinates":max(r["max_equal_coordinate_multiplicity"] for r in ties["rows"])}}
save("fine_audit_analysis.json",fine_summary)
base="model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
def class_hash(path,name):
    tree=ast.parse(path.read_text(encoding="utf-8"));node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)
    return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()
base_path=ROOT/("Cluster/framework/model/Quard_model/"+base+"/hier_postprocess.py")
hds_path=ROOT/("Cluster/framework/model/Quard_model/"+base+"_hds_canon_r1/hier_postprocess.py")
classes={name:{"M95":class_hash(base_path,name),"HDS":class_hash(hds_path,name)} for name in ("PointCloudPartitioner","SharedClusterBank")}
save("geometry_source_control.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"classes":classes,
    "same_geometry_classes":all(v["M95"]==v["HDS"] for v in classes.values()),"scope":"AST implementation identity only,not trained M95 prediction or checkpoint equivalence."})
manifest=tick.load(OUT/"cooperation_manifest.json")
program="FILES="+repr(manifest["source_hashes"])+"\nROOT="+repr(manifest["root"])+"\nCHECKPOINT="+repr(manifest["checkpoint"])+"\nSTAGE="+repr(STAGE)+"\n"+r'''
import datetime,fcntl,hashlib,json,pathlib,socket,subprocess
assert socket.gethostname()=="dl04-MS-7E06"
def sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open("rb") as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b""):h.update(block)
    return h.hexdigest()
row=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
assert [v.strip() for v in row.split(",")][:2]==["0","GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
contexts=subprocess.check_output(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
locks={}
for kind in ("training","diagnostic","exclusive"):
    with open("/tmp/cluster_project_gpu0_"+kind+".lock","rb") as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:locks[kind]="held"
        else:locks[kind]="acquired_and_released";fcntl.flock(handle,fcntl.LOCK_UN)
own=[]
for proc in pathlib.Path("/proc").iterdir():
    if not proc.name.isdecimal():continue
    try:args=(proc/"cmdline").read_bytes().split(b"\0")
    except OSError:continue
    if any((STAGE+"/"+name).encode() in args for name in ("native_content.py","native_content_replication.py","native_cooperation.py","native_fine_audit.py","native_tie_audit.py")):own.append(int(proc.name))
hashes={name:sha(pathlib.Path(ROOT)/name) for name in FILES}
print(json.dumps({"observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"gpu":row,"contexts":contexts,"locks":locks,"own_diagnostic_pids":own,"source_count":len(hashes),"source_hashes_match":hashes==FILES,"checkpoint_sha256":sha(CHECKPOINT),"no_signals_resets_or_lock_deletion":True}))
'''
post=ssh(program);save("postverify_all.json",post)
assert not post["contexts"] and not post["own_diagnostic_pids"] and post["source_hashes_match"] and post["checkpoint_sha256"]==manifest["checkpoint_sha256"]
assert all(v=="acquired_and_released" for v in post["locks"].values())
other=ssh(r'''
import datetime,json,socket,subprocess
assert socket.gethostname()=="sysu311-MS-7C59"
row=subprocess.check_output(["nvidia-smi","-i","1","--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
assert [v.strip() for v in row.split(",")][:2]==["1","GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0"]
contexts=subprocess.check_output(["nvidia-smi","-i","1","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
print(json.dumps({"observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"gpu":row,"contexts":contexts,"no_signal_or_gpu_computation":True}))
''',host="192.168.1.120");save("server3_observation.json",other)
work=tick.load(ROOT/"pipeline/research_work.json")
content=next(c for c in work["candidates"] if c["id"]=="m202-train-content-bias-matched-audit")
content.update(stage="complete",failure_scope="inconclusive",gate_result="Native/controls PASS;positive means but both independent TRAIN scene intervals cross0,not confirmed efficacy or admission.",next_action="Retain8pilot/24independent replication separately,bias/zero/norm controls and uncertainty;do not tune/drop scales/restart HDS. Carry actual point-information premise into independently gated structural research.")
content["evidence"].extend(evidence(OUT/name) for name in ("native_execution.json","native_fetch.json","replication_result.json","replication_execution.json","replication_fetch.json","replication_analysis.json","postverify_all.json"))
coop=next(c for c in work["candidates"] if c["id"]=="m202-query-point-bilinear-cooperation")
coop.update(stage="complete",failure_scope="inconclusive",gate_result="Local point-energy dominance supported32/32scenes;native matching unchanged and algebra residual4.09e-14. Not an efficacy/novelty/admission claim.",next_action="Retain complete2x2readouts/inner products and TRAIN augmentation caveat;energy is not an additive share or population bottleneck. Distinct core structure still needs all original gates.")
coop["evidence"].extend(evidence(OUT/name) for name in ("cooperation_result.json","cooperation_execution.json","cooperation_fetch.json","cooperation_analysis.json","postverify_all.json"))
core=next(c for c in work["candidates"] if c["id"]=="fine-leaf-local-point-exchange")
core.update(stage="implementation",failure_scope="implementation",gate_result="Mixed-leaf prerequisite102/128measured;ordinary isolated controls PASS;original tied-neighbor FAIL preserved;independent prototype revision1retests PASS. Full native integration/backward/resources/novelty UNMEASURED,not admitted.",
    next_action="Build an independent M95candidate model/config integrating only recipient-specific fine readback;resolve orphan fine-FFN and geometry graph lifetime,then run matched native forward/backward,whole-model10G/latency/memory/independence and primary-source material novelty. No HDSrevision3,old-family reopening or queue until actual gates pass.")
core["evidence"].extend(evidence(OUT/name) for name in ("fine_audit_analysis.json","geometry_source_control.json","postverify_all.json","server3_observation.json"))
core["evidence"].extend(evidence(ROOT/name) for name in ("pipeline/reviews/motivation_review_20261017_99e0a813.md","pipeline/designs/exp_design_20261017_99e0a813.md"))
core["unmeasured_gates"]=["independent model/config","native integrated forward/backward","whole-model FLOPs/latency/memory","material original-paper novelty","complete constraints/admission/safe sync"]
holds=[c for c in work["candidates"] if c["stage"]=="blocked"]
assert len(holds)==4 and all(c.get("blocker_kind")=="human_authorization" for c in holds)
now=datetime.now(timezone.utc)
assert all(datetime.fromisoformat(c["retry_after"])<=now for c in holds)
scope={"observed_at":now.isoformat(),"ids":[c["id"] for c in holds],"goal_sha256":tick.digest(ROOT/"pipeline/goal.json"),"roadmap_sha256":tick.digest(ROOT/"docs/research_mainline_correction_20261015.md"),"decision":"Due auxiliary scope holds rechecked once;no new user priority authorization or independently required auxiliary test. Retain original failures/gates/unblock conditions;timer or free GPU is not authorization.","retry_after":(now+timedelta(hours=4)).isoformat(),"scientific_rejections":0,"admissions":0}
save("auxiliary_scope_recheck.json",scope)
for c in holds:c["retry_after"]=scope["retry_after"];c["evidence"].append(evidence(OUT/"auxiliary_scope_recheck.json"))
guard();tick.save(ROOT/"pipeline/research_work.json",work)
counts={stage:sum(c["stage"]==stage for c in work["candidates"]) for stage in ("complete","rejected","blocked","implementation","training")}
save("outcome_summary.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"counts":counts,"records":len(work["candidates"]),"actual_full_native_forwards":128,"actual_suffix_replays":192,"unique_TRAIN_scenes":32,"unique_expression_identities":128,"new_diagnostic_IDs":2,"new_provisional_structural_IDs":1,"independent_prototype_revision":1,"HDS_model_revisions_unchanged":2,"new_model_packages":0,"native_model_backwards":0,"isolated_CPU_autograd_checks":"executed;internal reverse-call count unknown","optimizer_steps":0,"VAL_forwards":0,"admissions":0,"training_launches":0,"postflight":"pending_actual_finish"})
decision=run(["C:/Program Files (x86)/Git/bin/bash.exe","C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh","cluster_project","other",
    "32TRAIN场景的内容对照与Q/F归因后，能否开始新的点云分层结构训练？",
    "完成8pilot+24独立内容复核及32场景Q/F诊断；正均值区间跨0，不宣称提升。细簇混合102/128支持继续点级信息研究，建立独立细层点交换草案；保留等距反例及一次原型修订，不改HDS或启动未准入模型。",
    "独立24场景native-minus等幅置换+.008502/95%[-.003567,.020718]；point/query能量3.1853/.09139，非收益份额。旧attnpool池化与逐点输出已作源/控制区分；材料新颖性、完整模型接入/原生反向/资源仍缺，必须续做，不能把内部缺测试说成资源阻塞。",
    "pipeline/designs/exp_design_20261017_99e0a813.md;pipeline/reviews/motivation_review_20261017_99e0a813.md;pipeline/diagnostic_bundles/tick_99e0a813/replication_analysis.json;pipeline/diagnostic_bundles/tick_99e0a813/cooperation_analysis.json;pipeline/diagnostic_bundles/tick_99e0a813/tie_stress_result.json"],45)
save("decision_log_result.json",{"returncode":decision.returncode,"stdout":decision.stdout,"stderr":decision.stderr});assert decision.returncode==0,decision.stderr
print(json.dumps({"fine":fine_summary,"counts":counts,"postcheck":post,"server3":other,"decision":decision.stdout,"remaining_seconds":(datetime.fromisoformat(guard()["deadline_at"])-datetime.now(timezone.utc)).total_seconds()},ensure_ascii=False,indent=2))
