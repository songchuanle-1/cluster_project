"""Review real source-bound gates, then admit exactly one independent FLE task."""
from datetime import datetime,timezone
import json
import subprocess
from ops import CODE,ROOT,OUT,NAME,CID,guard,save,evidence,run,tick
import closure
import pipeline_monitor as monitor

guard()
EID="M203-FLE"
config="configs/Quard/ctf_hcg_csort_fle_r1/"+NAME+".yaml"
final=tick.load(OUT/"final_source.json")
for name,expected in final["source_hashes"].items():
    path="framework/model/Quard_model/"+NAME+"/"+name
    assert tick.digest(CODE/path)==expected
    raw=subprocess.check_output(["git","-C",str(CODE),"show","HEAD:"+path])
    import hashlib
    assert hashlib.sha256(raw).hexdigest()==expected,"Committed bytes differ from tested source"
assert tick.digest(CODE/config)==final["config_sha256"]
commit=closure.git(CODE,"rev-parse","HEAD")
assert commit=="587cccfbe2bc9867ece4b67d0785d8a5f5dc3e01"
results={name:tick.load(OUT/(name+"_result.json")) for name in ("contracts","native","native_m95","native_loader_candidate","native_loader_champion","native_fresh_candidate","guard_probe","resource_champion_retry1","resource_candidate_retry1")}
for name,r in results.items():assert r.get("passed",r.get("passed_measurement")) is True,name
c=results["resource_candidate_retry1"];m=results["resource_champion_retry1"]
assert c["input_sha256"]==m["input_sha256"] and c["profile"]["profiler_file_sha256"]==m["profile"]["profiler_file_sha256"]
assert c["profile"]["flops"]<=10e9
pairs=[]
for left,right,label in (("native","native_m95","workers0"),("native_loader_candidate","native_loader_champion","workers4")):
    for a,b in zip(results[left]["pairs"],results[right]["pairs"]):
        assert a["input_sha256"]==b["input_sha256"]
        ratio=a["native_training_peak_bytes"]/b["native_training_peak_bytes"]-1
        assert ratio<.15
        pairs.append({"protocol":label,"input_sha256":a["input_sha256"],"candidate_peak_bytes":a["native_training_peak_bytes"],"M95_peak_bytes":b["native_training_peak_bytes"],"fraction_increase":ratio})
save("resource_comparison.json",{"passed_existing_budget":True,"candidate_flops":c["profile"]["flops"],"M95_flops":m["profile"]["flops"],"delta_flops":c["profile"]["flops"]-m["profile"]["flops"],
    "candidate_median_ms":c["median_ms"],"M95_median_ms":m["median_ms"],"median_fraction_increase":c["median_ms"]/m["median_ms"]-1,
    "inference_peak_fraction_increase":c["peak_allocated_bytes"]/m["peak_allocated_bytes"]-1,"matched_training_pairs":pairs,
    "original_no_cluster_baseline_resource_delta":None,"original_baseline_note":"Historical configs/model_base1.yaml unavailable in current local/git/server3/server4 project archives; unknown,not fabricated. Verified M95 current/historical standard resource reference reproduces9.762532428G exactly.",
    "supplemental_attention_work":c["supplemental_fine_qk_av_fma_work"],"new_threshold_or_handler":False,"full_training_peak":None,"trained_efficacy":None})
prior=ROOT/"pipeline/diagnostic_bundles/tick_99e0a813"
review=ROOT/"pipeline/reviews/motivation_review_20261017_0571f421.md"
design=ROOT/"pipeline/designs/exp_design_20261017_0571f421.md"
gates={
 "diagnosis":{"passed":True,"status":"Fixed32TRAINscene128expression fine-leaf mixing prerequisite;branch-scoped causal hypothesis,not population bottleneck.","evidence":[evidence(prior/"fine_audit_analysis.json"),evidence(review)]},
 "controls":{"passed":True,"status":"Same-prefix candidate/uniform support control changes final masks;native/repeat/suffix errors0;CPUequivalence/tie/padding/isolation/gradcheck pass. No untrained effect threshold.","evidence":[evidence(OUT/"contracts_result.json"),evidence(OUT/"native_result.json")]},
 "native_backward":{"passed":True,"status":"Actual full native loss/backward on both batch2 pairs,18used point-path tensors and fine/message/input gradients;configuredworkers4 and genuine backbone-only new initialization also pass,zero diagnostic optimizer steps.","evidence":[evidence(OUT/"native_result.json"),evidence(OUT/"native_loader_candidate_result.json"),evidence(OUT/"native_fresh_candidate_result.json")]},
 "resources":{"passed":True,"status":"Same-input unchanged FVCore handlers,9.627987020G<=10G;M95reference9.762532428G reproduced. Inference memory nearlyequal,pairedtraining+3.48to7.92%<15%;medianlatency+18.77%disclosed,not speedup. Original no-cluster resource delta/full-run peak unknown;no borrowed HDSexception.","evidence":[evidence(OUT/"resource_comparison.json"),evidence(OUT/"resource_candidate_retry1_result.json"),evidence(OUT/"resource_champion_retry1_result.json"),evidence(OUT/"native_m95_result.json"),evidence(OUT/"native_loader_champion_result.json")]},
 "independence":{"passed":True,"status":"9physical independent source files,unique matching config,no cross-variant imports. Seven mathematical sources unchanged from actual tests;training-only guard separately passes identity/lock/release checks.","evidence":[evidence(OUT/"final_source.json"),evidence(OUT/"static_independence.json"),evidence(OUT/"guard_probe_result.json")]},
 "constraints":{"passed":True,"status":"Frozen24constraints/11bans reviewed in source-bound review/design;structural point-information flow,all numeric protocol unchanged,originallosses,no new gate/routing/pooling/repeated injection,default10G,permittedGPU0three locks. No HDSrevision3/M201recovery/auxiliary-hold reopening. Known prior art/material novelty limitation explicitly retained;no novelty PASS asserted.","evidence":[evidence(review),evidence(design),evidence(OUT/"primary_source_comparison.md"),evidence(OUT/"guard_probe_result.json")]}}
save("gate_review.json",{"gates":gates,"commit":commit,"goal_sha256":tick.digest(ROOT/"pipeline/goal.json"),"training_not_yet_launched":True,"material_novelty":"unestablished_known_operators","post_training_evaluation":evidence(design)})
before=set((ROOT/"pipeline/decisions").glob("*_next_batch.md"))
decision=run(["C:/Program Files (x86)/Git/bin/bash.exe","C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh","cluster_project","next_batch",
    "细层逐点交换是否达到一次结构首筛的执行准入？","仅准入一个新实验 M203-FLE，先安全同步再由现有门控入口派发；不称已训练成功。",
    "独立源码、原生对照及完整反向、新初始化、四worker和同口径资源已测通过；计算9.628G，延迟增加约19%，训练样本显存增加不足8%；新颖性和训练收益未知，保留旧失败及原始baseline资源未知。",
    "pipeline/diagnostic_bundles/tick_0571f421/gate_review.json;pipeline/designs/exp_design_20261017_0571f421.md"],90)
assert decision.returncode==0,decision.stderr
created=set((ROOT/"pipeline/decisions").glob("*_next_batch.md"))-before
assert len(created)==1
decision_path=created.pop()
lock=monitor.acquire_lock(str(ROOT));assert lock is not None,"Project queue lock busy"
try:
    guard();queue=monitor.load_queue(str(ROOT));work=tick.load(ROOT/"pipeline/research_work.json")
    assert not any(t.get("id")==EID for ts in queue["gpu_queues"].values() for t in ts)
    assert not (ROOT/("pipeline/experiments/"+EID+".json")).exists()
    candidate=next(x for x in work["candidates"] if x["id"]==CID)
    assert len(candidate["revision_history"])==1 and candidate["revision_history"][-1]["result"]=="passed"
    receipt={"id":EID,"candidate_id":CID,"config":config,"code_commit":commit,"goal_sha256":tick.digest(ROOT/"pipeline/goal.json"),
        "decision":evidence(decision_path),"gates":gates,"implementation_revision_sha256":closure.revision_digest(candidate["revision_history"][-1]),
        "post_training_evaluation":evidence(design),"source_binding":evidence(OUT/"final_source.json"),"recorded_at":datetime.now(timezone.utc).isoformat(),
        "limitations":"Executability only;no trained gain,material novelty,speedup,full-run memory guarantee or recovered original baseline resource identity."}
    task={"id":EID,"config":config,"status":"waiting","label":"M203 FLE fine-recipient point exchange with M95 larger-scale context","gpu":0,"code_commit":commit,
        "admission_receipt":"pipeline/admissions/"+EID+".json","requires_exclusive_ownership":True}
    candidate.update(stage="deployment",experiment_id=EID,config=config,admission_receipt=task["admission_receipt"],
        next_action="Use existing gated dispatcher once on server4GPU0;verify lifetime guard,exactconfig/source and increasing native steps. No relaunch if uncertain.",
        gate_result="Six executability gates source-bound PASS;trained efficacy/material novelty UNKNOWN;not launched yet.",unmeasured_gates=["trained efficacy","material novelty","full-training peak","original no-cluster resource delta"])
    candidate["evidence"].extend(evidence(OUT/n) for n in ("native_result.json","contracts_result.json","native_m95_result.json","native_loader_candidate_result.json","native_loader_champion_result.json","native_fresh_candidate_result.json","resource_comparison.json","final_source.json","guard_probe_result.json","gate_review.json","primary_source_comparison.md"))
    candidate["evidence"].extend([evidence(review),evidence(design),evidence(decision_path)])
    guard();tick.save(ROOT/task["admission_receipt"],receipt);tick.save(ROOT/"pipeline/research_work.json",work)
    closure.admission(ROOT,task)
    queue["gpu_queues"]["server-4"].append(task);monitor.save_queue(str(ROOT),queue)
    save("admission_result.json",{"admitted":EID,"candidate_id":CID,"receipt":task["admission_receipt"],"commit":commit,"decision":evidence(decision_path),"launches":0})
finally:lock.close()
print(json.dumps({"admitted":EID,"queued":True,"launched":False,"commit":commit}))
