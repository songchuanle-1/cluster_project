"""Candidate-first preregistration and exact toy bilinear controls."""
from datetime import datetime,timezone
from ops import guard,save,evidence,tick,ROOT,OUT

guard()
cid="m202-query-point-bilinear-cooperation"
work=tick.load(ROOT/"pipeline/research_work.json")
assert not any(c["id"]==cid for c in work["candidates"])
candidate={"id":cid,"stage":"diagnosis","kind":"TRAIN_mechanistic_diagnostic",
    "hypothesis":"On all32already-fixed TRAIN scenes, point-only bilinear logit-change squared energy exceeds query-only energy under a magnitude-matched spatial-message intervention. This premise is local sensitivity, not efficacy or a population bottleneck.",
    "matched_control":"Same captured native prefix,normal selected query,original/permuted point message;2x2Q/F readouts and exact detached CPU float64 algebra. Native model float32 and1e-6 unchanged.",
    "next_action":"Run4bilinear CPU controls,freeze all32previously selected TRAIN scenes,then32native captures+64suffixes with strict native and algebra checks on authorized idle GPU0; preserve every scene and failure.",
    "evidence":[evidence(OUT/"cooperation_prereg.md"),evidence(OUT/"content_analysis.json")],
    "preregistered_at":datetime.now(timezone.utc).isoformat(),"failure_scope":"inconclusive"}
work["candidates"].append(candidate);guard();tick.save(ROOT/"pipeline/research_work.json",work)
controls=[]
for name,q0,f0,q1,f1 in (("identity",[1,2],[3,4],[1,2],[3,4]),("point_only",[1,2],[3,4],[1,2],[5,8]),("query_only",[1,2],[3,4],[5,7],[3,4]),("mixed",[1,2],[3,4],[5,7],[5,8])):
    dot=lambda q,f:sum(x*y for x,y in zip(q,f))
    dq=[b-a for a,b in zip(q0,q1)];df=[b-a for a,b in zip(f0,f1)]
    terms=[dot(q0,df),dot(dq,f0),dot(dq,df)]
    assert sum(terms)==dot(q1,f1)-dot(q0,f0)
    controls.append({"name":name,"terms":terms,"exact_residual":0})
save("cooperation_cpu_controls.json",{"passed":True,"controls":controls,"native_forwards":0})
pilot=tick.load(OUT/"content_manifest.json");replication=tick.load(OUT/"replication_manifest.json")
manifest=dict(pilot);manifest["selected"]=pilot["selected"]+replication["selected"]
assert len(manifest["selected"])==32 and len({s["scene_id"] for s in manifest["selected"]})==32
manifest["producer_hashes"]={name:tick.digest(OUT/name) for name in ("native_cooperation.py","matched_control.py")}
save("cooperation_manifest.json",manifest)
candidate.update(stage="validation",next_action="Execute32native TRAIN captures+64same-prefix suffixes and2x2mask readouts;report energies/inner products without treating them as additive shares. No new structure/admission.")
candidate["evidence"].extend(evidence(OUT/name) for name in ("cooperation_cpu_controls.json","cooperation_manifest.json","native_cooperation.py","prepare_cooperation.py"))
guard();tick.save(ROOT/"pipeline/research_work.json",work)
print("Registered independent cooperation diagnosis;4CPUcontrols PASS;32fixed scenes;model unchanged.")
