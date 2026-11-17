"""Register one trained-path diagnosis and execute its bilinear CPU controls."""
from datetime import datetime, timezone
import numpy as np
from audit_terminal import guard, save, ROOT, OUT, tick

guard()
cid = "m202-trained-mask-feature-contribution"
path = ROOT/"pipeline/research_work.json"
work = tick.load(path)
assert not any(c["id"] == cid for c in work["candidates"])
prereg = OUT/"trained_feature_prereg.md"
work["candidates"].append({"id":cid,"stage":"diagnosis","candidate_type":"mechanistic_diagnostic",
    "parent_candidate_id":"m95-hierarchical-mask-feature-path-audit","parent_experiment_id":"M202-HDS",
    "created_at":datetime.now(timezone.utc).isoformat(),
    "hypothesis":"On the four pre-fixed TRAIN scenes, the already-trained HDS point message yields positive mean native point IoU contribution at the SAME normal-pass final query/selection compared with point features from a zero-message counterfactual. Nonpositive mean refutes only this local cohort hypothesis.",
    "matched_control":"Same ended HDSepoch19 weights/data/seed: original identity-hook predict, exact seeded repeat, temporary zero point-message hook; cross-read Qon/Fon,Qon/Foff,Qoff/Fon,Qoff/Foff with selection fixed to original on index.",
    "next_action":"First execute float64 identity/feature-only/query-only/joint bilinear controls, then fixed4TRAINscene native trained-path intervention under exclusive authorized GPU0 locks. Preserve failures and1e-6 native head/repeat tolerance; no optimizer/model revision.",
    "evidence":[{"path":prereg.relative_to(ROOT).as_posix(),"sha256":tick.digest(prereg)}],
    "scope":"TRAIN-only causal diagnostic on existing trained realization, not a new model/training admission or VAL-selected mechanism."})
tick.save(path,work)
q0=np.asarray([[1.,2.,-1.],[0.5,-2.,3.]])
f0=np.asarray([[1.,0.,2.],[0.,3.,-1.],[-2.,1.,0.5],[4.,-1.,2.]])
dq=np.asarray([[0.5,-1.,0.],[1.,0.,-0.5]])
df=np.asarray([[1.,-0.5,0.],[0.,1.,2.],[0.5,0.,1.],[-1.,2.,0.]])
rows=[]
for condition,query_delta,feature_delta in (("identity",dq*0,df*0),("feature_only",dq*0,df),("query_only",dq,df*0),("joint",dq,df)):
    q1,f1=q0+query_delta,f0+feature_delta
    l00=q0@f0.T;l10=q1@f0.T;l01=q0@f1.T;l11=q1@f1.T
    residual=l11-l10-l01+l00
    expected=query_delta@feature_delta.T
    error=float(np.max(np.abs(residual-expected)))
    assert error<=1e-12
    if condition=="identity":assert np.array_equal(l00,l11)
    if condition=="feature_only":assert np.array_equal(l11,l01) and np.array_equal(l10,l00) and not np.array_equal(l11,l00)
    if condition=="query_only":assert np.array_equal(l11,l10) and np.array_equal(l01,l00) and not np.array_equal(l11,l00)
    if condition=="joint":assert np.linalg.norm(expected)>0
    rows.append({"condition":condition,"passed":True,"interaction_max_error":error})
save("trained_feature_cpu_controls.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"passed":True,"controls":rows,
     "scope":"4toy float64 bilinear controls only; no trained-network efficacy, gradient or admission claim"})
work=tick.load(path)
candidate=next(c for c in work["candidates"] if c["id"]==cid)
candidate["evidence"].append({"path":(OUT/"trained_feature_cpu_controls.json").relative_to(ROOT).as_posix(),"sha256":tick.digest(OUT/"trained_feature_cpu_controls.json")})
guard();tick.save(path,work)
print("Registered SAME-trained-model diagnostic;4bilinear CPU controls PASS;native test pending.")
