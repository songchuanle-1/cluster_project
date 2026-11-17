"""Keep pilot/replication separate and verify bilinear-energy accounting."""
from datetime import datetime,timezone
import json
import math
import random
from ops import guard,save,tick,OUT,ssh,STAGE
guard()
rep=tick.load(OUT/"replication_result.json");coop=tick.load(OUT/"cooperation_result.json")
assert rep["passed_controls"] and coop["passed_controls"]
def mean(values):
    assert values and all(math.isfinite(v) for v in values)
    return sum(values)/len(values)
def paired_summary(rows,endpoints,controls):
    scenes=sorted({r["scene_id"] for r in rows});n=len(scenes)
    rng=random.Random(1999);draws=[[rng.randrange(n) for _ in range(n)] for _ in range(5000)]
    output={}
    for endpoint in endpoints:
        output[endpoint]={}
        for control in controls:
            values=[mean([r["conditions"]["native"][endpoint]["point_iou"]-r["conditions"][control][endpoint]["point_iou"] for r in rows if r["scene_id"]==s]) for s in scenes]
            samples=sorted(mean([values[i] for i in draw]) for draw in draws)
            output[endpoint]["native_minus_"+control]={"mean":mean(values),"scene_bootstrap_95":[samples[124],samples[4874]],"scene_values":dict(zip(scenes,values)),"positive_scenes":sum(v>0 for v in values),"negative_scenes":sum(v<0 for v in values),"zero_scenes":sum(v==0 for v in values)}
    return output
endpoints=("fixed_query_point","joint_fixed_selection","joint_own_selection")
rep_summary={"observed_at":datetime.now(timezone.utc).isoformat(),"native_observed_at":rep["observed_at"],"expressions":96,"independent_scenes":24,
    "contrasts":paired_summary(rep["rows"],endpoints,("true_zero","bias_retained_empty","permuted_norm_matched")),
    "scope":"Independent fixed-size24scene TRAIN replication of8pilot;not VAL,generalization,trained ablation or optional-stopped confirmatory test."}
save("replication_analysis.json",rep_summary)
energy_keys=("point_energy","query_energy","interaction_energy","total_energy","point_query_inner_product","point_interaction_inner_product","query_interaction_inner_product")
energies={k:mean([r["bilinear"][k] for r in coop["rows"]]) for k in energy_keys}
reconstructed=sum(energies[k] for k in energy_keys[:3])+2*sum(energies[k] for k in energy_keys[4:])
assert abs(reconstructed-energies["total_energy"])<=1e-10
scene_energies={s:{k:mean([r["bilinear"][k] for r in coop["rows"] if r["scene_id"]==s]) for k in energy_keys} for s in sorted({r["scene_id"] for r in coop["rows"]})}
task={}
for metric in ("point_iou","point_bce"):
    v11=[r["conditions"]["native"]["fixed_query_point"][metric] for r in coop["rows"]]
    v10=[r["conditions"]["permuted_norm_matched"]["fixed_query_point"][metric] for r in coop["rows"]]
    v01=[r["query_only_fixed_original_feature"][metric] for r in coop["rows"]]
    v00=[r["conditions"]["permuted_norm_matched"]["joint_fixed_selection"][metric] for r in coop["rows"]]
    task[metric]={"native_Q_native_F":mean(v11),"native_Q_permuted_F":mean(v10),"permuted_Q_native_F":mean(v01),"permuted_Q_permuted_F":mean(v00),"nonlinear_interaction":mean([a-b-c+d for a,b,c,d in zip(v11,v10,v01,v00)])}
cooperation_summary={"observed_at":datetime.now(timezone.utc).isoformat(),"native_observed_at":coop["observed_at"],"expressions":128,"independent_scenes":32,
    "mean_energies":energies,"scene_energies":scene_energies,"energy_reconstruction_residual":reconstructed-energies["total_energy"],
    "maximum_algebra_residual":max(r["bilinear"]["algebra_max_residual"] for r in coop["rows"]),
    "local_point_energy_dominates":energies["point_energy"]>energies["query_energy"],
    "scenes_with_point_energy_greater":sum(v["point_energy"]>v["query_energy"] for v in scene_energies.values()),
    "crossed_task_readouts":task,"fixed_query_contrast":paired_summary(coop["rows"],endpoints,("permuted_norm_matched",)),
    "scope":"Same32scene/expression identities,not32new independent scenes. Native TRAIN augmentation pipeline unchanged; input tensor identity across separate diagnostic processes was not hashed,so no between-process numerical reproducibility/noise claim. Energies are not additive shares or task efficacy."}
save("cooperation_analysis.json",cooperation_summary)
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
    if any((STAGE+"/"+name).encode() in args for name in ("native_content.py","native_content_replication.py","native_cooperation.py")):own.append(int(proc.name))
hashes={name:sha(pathlib.Path(ROOT)/name) for name in FILES}
print(json.dumps({"observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"gpu":row,"contexts":contexts,"locks":locks,"own_diagnostic_pids":own,"source_count":len(hashes),"source_hashes_match":hashes==FILES,"checkpoint_sha256":sha(CHECKPOINT),"no_signals_resets_or_lock_deletion":True}))
'''
post=ssh(program);save("final_native_postcheck.json",post)
assert not post["contexts"] and not post["own_diagnostic_pids"] and post["source_hashes_match"] and post["checkpoint_sha256"]==manifest["checkpoint_sha256"]
assert all(v=="acquired_and_released" for v in post["locks"].values())
print(json.dumps({"replication_primary":rep_summary["contrasts"]["fixed_query_point"],"cooperation_mean_energies":energies,"point_dominant_scenes":cooperation_summary["scenes_with_point_energy_greater"],"algebra_error":cooperation_summary["maximum_algebra_residual"],"crossed_task_readouts":task,"postcheck":post},indent=2))
