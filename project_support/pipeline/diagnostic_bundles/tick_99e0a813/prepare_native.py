"""Run non-GPU controls and freeze outcome-blind native TRAIN identities."""
from datetime import datetime,timezone
import hashlib
import json
from ops import guard,save,evidence,tick,ROOT,OUT,PRIOR,CID,ssh
from matched_control import cpu_controls

guard();save("cpu_controls.json",cpu_controls())
program=r'''
import datetime,fcntl,hashlib,json,pathlib,socket,subprocess
assert socket.gethostname()=="dl04-MS-7E06"
row=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
assert [c.strip() for c in row.split(",")][:2]==["0","GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
contexts=subprocess.check_output(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
locks={}
for kind in ("training","diagnostic","exclusive"):
    with open("/tmp/cluster_project_gpu0_"+kind+".lock","rb") as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:locks[kind]="held"
        else:
            locks[kind]="acquired_and_released";fcntl.flock(handle,fcntl.LOCK_UN)
path=pathlib.Path("/home/songcl/data/data/scanrefer/ScanRefer_train_new.json")
raw=path.read_bytes();annotations=json.loads(raw)
annotations.sort(key=lambda r:r["scene_id"])
groups=[];current=[];scene=None
for item in annotations:
    if scene!=item["scene_id"] or len(current)>=4:
        if current:groups.append(current)
        current=[];scene=item["scene_id"]
    current.append(item)
if current:groups.append(current)
first={}
for index,group in enumerate(groups):first.setdefault(group[0]["scene_id"],index)
excluded={"scene0000_00","scene0002_00","scene0003_00","scene0004_00"}
ordered=sorted((s for s in first if s not in excluded),key=lambda s:hashlib.sha256(("cluster-content-1999:"+s).encode()).hexdigest())
selected=[]
for scene in ordered[:8]:
    index=first[scene]
    identities=[{"split":"train","scene_id":r["scene_id"],"object_ids":[int(r["object_id"])],"ann_id":int(r["ann_id"])} for r in groups[index]]
    selected.append({"scene_id":scene,"group":index,"identities":identities})
assert len(selected)==8
dataset=pathlib.Path("/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/framework/dataset/scannetv2.py")
print(json.dumps({"observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"gpu":row,"contexts":contexts,"locks":locks,
    "annotation_path":str(path),"annotation_sha256":hashlib.sha256(raw).hexdigest(),"dataset_source_sha256":hashlib.sha256(dataset.read_bytes()).hexdigest(),
    "native_group_size":4,"groups_total":len(groups),"train_scenes_total":len(first),"selected":selected,"excluded":sorted(excluded),"native_forwards":0,"cuda_initialized":False}))
'''
cohort=ssh(program)
save("cohort_resource_precheck.json",cohort)
assert len(cohort["selected"])==8 and not set(cohort["excluded"]).intersection(s["scene_id"] for s in cohort["selected"])
manifest=tick.load(PRIOR/"scale_manifest.json")
manifest={key:manifest[key] for key in ("root","model","config","checkpoint","checkpoint_sha256","source_hashes")}
manifest.update(deadline_at=guard()["deadline_at"],selected=cohort["selected"],annotation_path=cohort["annotation_path"],
    annotation_sha256=cohort["annotation_sha256"],dataset_source_sha256=cohort["dataset_source_sha256"],
    producer_hashes={name:tick.digest(OUT/name) for name in ("native_content.py","matched_control.py")})
save("content_manifest.json",manifest)
work=tick.load(ROOT/"pipeline/research_work.json")
candidate=next(c for c in work["candidates"] if c["id"]==CID)
assert candidate["stage"]=="diagnosis"
candidate.update(stage="validation",next_action="Execute frozen8scene/32expression TRAIN native matched message controls on live idle pinned GPU0 under3lifetime locks; no training or source changes.")
candidate["evidence"].extend(evidence(OUT/name) for name in ("cpu_controls.json","matched_control.py","prepare_native.py","cohort_resource_precheck.json","content_manifest.json","native_content.py"))
guard();tick.save(ROOT/"pipeline/research_work.json",work)
print(json.dumps({"cpu_controls":4,"selected_scenes":[s["scene_id"] for s in cohort["selected"]],"groups":[s["group"] for s in cohort["selected"]],"expressions":sum(len(s["identities"]) for s in cohort["selected"]),"gpu":cohort["gpu"],"contexts":cohort["contexts"],"locks":cohort["locks"]},indent=2))
