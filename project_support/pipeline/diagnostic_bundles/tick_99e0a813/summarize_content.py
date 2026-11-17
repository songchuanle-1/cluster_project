"""Scene-level uncertainty and resource postcheck; no new model execution."""
from datetime import datetime,timezone
import json
import math
import random
from ops import guard,save,tick,OUT,ssh,STAGE

guard();manifest=tick.load(OUT/"content_manifest.json");result=tick.load(OUT/"content_result.json")
assert result["passed_controls"] and result["independent_scenes"]==8
rows=result["rows"];scenes=sorted({r["scene_id"] for r in rows})
conditions=("native","true_zero","bias_retained_empty","permuted_norm_matched")
endpoints=("fixed_query_point","joint_fixed_selection","joint_own_selection")
def mean(values):
    assert values and all(math.isfinite(v) for v in values)
    return sum(values)/len(values)
scene_values={s:{e:{c:mean([r["conditions"][c][e]["point_iou"] for r in rows if r["scene_id"]==s]) for c in conditions} for e in endpoints} for s in scenes}
rng=random.Random(1999);draws=[[rng.randrange(8) for _ in range(8)] for _ in range(5000)]
def interval(values):
    samples=sorted(mean([values[i] for i in draw]) for draw in draws)
    return [samples[124],samples[4874]]
contrasts={}
for endpoint in endpoints:
    contrasts[endpoint]={}
    for control in conditions[1:]:
        values=[scene_values[s][endpoint]["native"]-scene_values[s][endpoint][control] for s in scenes]
        contrasts[endpoint]["native_minus_"+control]={"mean":mean(values),"scene_bootstrap_95":interval(values),"scene_values":dict(zip(scenes,values)),"positive_scenes":sum(v>0 for v in values),"negative_scenes":sum(v<0 for v in values),"zero_scenes":sum(v==0 for v in values)}
summary={"observed_at":datetime.now(timezone.utc).isoformat(),"native_observed_at":result["observed_at"],"expressions":len(rows),"independent_scenes":8,"scene_values":scene_values,"contrasts":contrasts,
    "max_native_match_error":max([v for c in result["controls"] for v in c["native_suffix_max_errors"].values()]+[c[k] for c in result["controls"] for k in ("injection_error","head_error")]),
    "max_relative_message_norm_error":max(c["norm_control"]["maximum_relative_norm_error"] for c in result["controls"]),
    "analysis_seed":1999,"bootstrap_draws":5000,"resampling_unit":"whole scene","scope":"8preselected TRAIN scenes32expressions; descriptive paired uncertainty,not population generalization or trained model improvement; no endpoint/mechanism selection from VAL"}
save("content_analysis.json",summary)
constants="FILES="+repr(manifest["source_hashes"])+"\nROOT="+repr(manifest["root"])+"\nCHECKPOINT="+repr(manifest["checkpoint"])+"\nSTAGE="+repr(STAGE)+"\n"
program=constants+r'''
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
    if (STAGE+"/native_content.py").encode() in args:own.append(int(proc.name))
hashes={name:sha(pathlib.Path(ROOT)/name) for name in FILES}
print(json.dumps({"observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"gpu":row,"contexts":contexts,"locks":locks,"own_diagnostic_pids":own,"source_hashes_match":hashes==FILES,"source_count":len(hashes),"checkpoint_sha256":sha(CHECKPOINT),"no_signals_or_resets":True}))
'''
post=ssh(program);save("content_postcheck.json",post)
assert not post["contexts"] and not post["own_diagnostic_pids"]
assert all(v=="acquired_and_released" for v in post["locks"].values()) and post["source_hashes_match"] and post["checkpoint_sha256"]==manifest["checkpoint_sha256"]
print(json.dumps({"contrasts":contrasts,"max_native_error":summary["max_native_match_error"],"max_relative_norm_error":summary["max_relative_message_norm_error"],"postcheck":post},indent=2))
