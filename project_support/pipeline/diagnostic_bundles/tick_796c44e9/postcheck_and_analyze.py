"""Verify released native resources and describe the fixed TRAIN factorial."""
from datetime import datetime, timezone
import math
from tick_ops import guard, save, tick, OUT, ssh, REMOTE_STAGE

guard()
manifest=tick.load(OUT/"scale_manifest.json")
program="EXPECTED="+repr(manifest["source_hashes"])+"\nROOT="+repr(manifest["root"])+"\nCHECKPOINT="+repr(manifest["checkpoint"])+"\nSTAGE="+repr(REMOTE_STAGE)+"\n"+r'''
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
        else:
            locks[kind]="acquired_and_released";fcntl.flock(handle,fcntl.LOCK_UN)
own=[]
for proc in pathlib.Path("/proc").iterdir():
    if not proc.name.isdecimal():continue
    try:args=(proc/"cmdline").read_bytes().split(b"\0")
    except OSError:continue
    if (STAGE+"/scale_native.py").encode() in args:own.append(int(proc.name))
hashes={name:sha(pathlib.Path(ROOT)/name) for name in EXPECTED}
print(json.dumps({"observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"hostname":socket.gethostname(),"gpu":row,"contexts":contexts,"locks":locks,"own_diagnostic_pids":own,"source_count":len(hashes),"source_hashes_match":hashes==EXPECTED,"checkpoint_sha256":sha(CHECKPOINT),"no_signals_resets_or_lock_deletion":True}))
'''
post=ssh(program)
save("postcheck_resources.json",post)
assert not post["contexts"] and not post["own_diagnostic_pids"]
assert all(value=="acquired_and_released" for value in post["locks"].values())
assert post["source_hashes_match"] and post["source_count"]==12
assert post["checkpoint_sha256"]==manifest["checkpoint_sha256"]
program3=r'''
import datetime,json,socket,subprocess
assert socket.gethostname()=="sysu311-MS-7C59"
row=subprocess.check_output(["nvidia-smi","-i","1","--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
assert [v.strip() for v in row.split(",")][:2]==["1","GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0"]
contexts=subprocess.check_output(["nvidia-smi","-i","1","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
print(json.dumps({"observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"gpu":row,"contexts":contexts,"no_gpu_computation_or_signals":True}))
'''
server3=ssh(program3,host="192.168.1.120")
save("server3_resource_observation.json",server3)
result=tick.load(OUT/"scale_result.json")
assert result["passed_controls"] and len(result["rows"])==16
rows=result["rows"]
def average(values):
    assert values and all(math.isfinite(v) for v in values)
    return sum(values)/len(values)
def describe(group):
    full=average([r["subsets"]["7"]["fixed_q_point"]["point_iou"] for r in group])
    empty=average([r["subsets"]["0"]["fixed_q_point"]["point_iou"] for r in group])
    zero=average([r["zero_message_fixed_q_point"]["point_iou"] for r in group])
    contribution=[average([r["fixed_q_point_point_iou_shapley"][i] for r in group]) for i in range(3)]
    assert abs(sum(contribution)-(full-empty))<=1e-12
    return {"expressions":len(group),"full_scale_fixed_q_iou":full,"empty_scale_bias_retained_fixed_q_iou":empty,
        "true_zero_message_fixed_q_iou":zero,"full_minus_empty":full-empty,"full_minus_true_zero":full-zero,
        "empty_bias_retained_minus_true_zero":empty-zero,"point_iou_shapley_fine_middle_coarse":contribution,
        "joint_fixed_selection_full_minus_empty":average([r["subsets"]["7"]["joint_fixed_selection"]["point_iou"]-r["subsets"]["0"]["joint_fixed_selection"]["point_iou"] for r in group]),
        "joint_own_selection_full_minus_empty":average([r["subsets"]["7"]["joint_own_selection"]["point_iou"]-r["subsets"]["0"]["joint_own_selection"]["point_iou"] for r in group])}
scenes={scene:describe([r for r in rows if r["scene_id"]==scene]) for scene in sorted({r["scene_id"] for r in rows})}
efficiency=max(abs(v) for r in rows for key,v in r.items() if key.endswith("_efficiency_residual"))
controls=result["controls"]
native_error=max([c[k] for c in controls for k in ("component_sum_max_error","message_max_error","injection_max_error","head_max_error")]+[v for c in controls for v in c["all_scales_suffix_max_errors"].values()])
assert efficiency<=1e-12 and native_error<=1e-6
analysis={"observed_at":datetime.now(timezone.utc).isoformat(),"native_result_observed_at":result["observed_at"],
    "scope":"TRAIN only,4fixed scenes16expressions,off-distribution omissions,descriptive exact Shapley; no mechanism tuning or population proof",
    "summary":describe(rows),"scenes":scenes,"maximum_native_matching_error":native_error,
    "maximum_scalar_efficiency_residual":efficiency,"canonical_calls_by_scene":[c["canonical_calls"] for c in controls],
    "empty_subset_message_norm_by_scene":[c["empty_subset_message_norm"] for c in controls],
    "local_all_scales_nonnegative":result["local_all_scales_nonnegative"],
    "actual_work":{"cpu_control_families":4,"full_native_forwards":5,"successful_full_native_forwards":4,
        "native_suffix_replays":36,"first_failed_full_native_forwards":1,"backwards":0,"optimizer_steps":0,
        "val_forwards":0,"training_launches":0,"model_revisions":0},
    "unknowns":["independent full-network reproducibility","population scale harms","cause of VAL deficit",
        "retrained omission ablations","subgroup labels","generalization","whole-training peak memory"],
    "interpretation":"All-scale-beneficial local premise refuted. Empty subset retains learned bias and differs from true zero; Shapley signs depend on that preregistered reference. Never conclude coarse/middle globally harmful or select a new model from this cohort."}
save("scale_analysis.json",analysis)
print(__import__("json").dumps({"summary":analysis["summary"],"scenes":scenes,"max_native_error":native_error,
    "efficiency_residual":efficiency,"calls":analysis["canonical_calls_by_scene"],"postcheck":post,"server3":server3},indent=2))
