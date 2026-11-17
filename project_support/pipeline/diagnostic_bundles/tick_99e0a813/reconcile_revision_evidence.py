"""Preserve the record;separate frozen protocol from post-registration results."""
from datetime import datetime,timezone
import copy
from ops import guard,save,evidence,tick,ROOT,OUT
guard();work=tick.load(ROOT/"pipeline/research_work.json")
candidate=next(c for c in work["candidates"] if c["id"]=="fine-leaf-local-point-exchange")
revision=candidate["revision_history"][0]
assert revision["result"]=="passed"
before=copy.deepcopy(revision)
save("revision_record_before_evidence_partition.json",before)
registered=datetime.fromisoformat(revision["preregistered_at"]).timestamp()
protocol=[];results=[]
for entry in revision["evidence"]:
    path=ROOT/entry["path"]
    assert tick.digest(path)==entry["sha256"]
    (protocol if path.stat().st_mtime<registered else results).append(entry)
assert len(protocol)==2 and len(results)==2
assert all(entry["path"].endswith(("operator_revision1_prereg.md","fine_exchange_operator_v1.py")) for entry in protocol)
revision["protocol_evidence"]=protocol
revision["evidence"]=results
for entry in protocol:
    if entry not in candidate["evidence"]:candidate["evidence"].append(entry)
proof={"observed_at":datetime.now(timezone.utc).isoformat(),"reason":"Closure result evidence must be post-registration. Frozen plan/source are protocol evidence,not test results;retain every original hash and the whole prior record without changing timestamps,tests,results or the scientific hypothesis.",
    "before_record":evidence(OUT/"revision_record_before_evidence_partition.json"),"protocol":protocol,"post_registration_results":results,
    "unchanged_protocol_fields":["revision","failure_scope","reason","change","prediction","failure_evidence","preregistered_at","result"]}
assert all(revision[k]==before[k] for k in proof["unchanged_protocol_fields"])
save("revision_evidence_partition.json",proof)
candidate["evidence"].extend([evidence(OUT/"revision_record_before_evidence_partition.json"),evidence(OUT/"revision_evidence_partition.json")])
guard();tick.save(ROOT/"pipeline/research_work.json",work)
notes=tick.load(OUT/"report_notes.json")
notes["actions"].append("收尾前按实际时序核对独立原型修订收据：冻结计划/源码归入protocol evidence，预注册后的实测结果归入result evidence；原记录整体及全部哈希另行保留，时间戳、假设、协议、结果和失败证据均未改，不修改校验器或门槛。")
save("report_notes.json",notes)
import closure
closure.validate_revisions(ROOT,candidate)
print("Independent revision evidence chronology PASS;all original artifacts/record preserved,not retimestamped.")
