"""Bind preserved failure and preregistered measurement-only axis repair."""
from datetime import datetime, timezone
from tick_ops import guard, save, evidence, tick, ROOT, OUT, CID

guard()
for name in ("scale_native.py", "scale_terms.py"):
    compile((OUT/name).read_text(encoding="utf-8"),name,"exec")
manifest=tick.load(OUT/"scale_manifest.json")
manifest["producer_hashes"]={name:tick.digest(OUT/name) for name in ("scale_native.py","scale_terms.py")}
save("scale_manifest.json",manifest)
work=tick.load(ROOT/"pipeline/research_work.json")
candidate=next(c for c in work["candidates"] if c["id"]==CID)
assert candidate["stage"]=="validation"
failed=tick.load(OUT/"attempt1_scale_result.json")
assert not failed["passed_controls"] and failed["native_forwards"]==1 and failed["native_suffix_replays"]==0
candidate["evidence"]=[e for e in candidate["evidence"] if e["path"] not in {
    (OUT/name).relative_to(ROOT).as_posix() for name in ("scale_native.py","scale_manifest.json")}]
candidate["evidence"].extend(evidence(OUT/name) for name in (
    "attempt1_scale_native.py","attempt1_scale_manifest.json","attempt1_scale_result.json",
    "attempt1_scale_execution.json","attempt1_scale_fetch.json","attempt1_live_resource_precheck.json",
    "scale_protocol_revision1.md","scale_native.py","scale_manifest.json"))
candidate["measurement_protocol_history"]=[{"revision":1,"preregistered_at":datetime.now(timezone.utc).isoformat(),
    "scope":"instrumentation_only_expression_axis","reason":"Native canonical loops over expressions after scene expansion, not once per input scene.",
    "failure_evidence":[evidence(OUT/"attempt1_scale_result.json")],
    "prediction":"Per-expression stacked scale terms reproduce all normal native messages/suffixes within unchanged1e-6.",
    "result":"pending"}]
candidate["next_action"]="Execute same8subset protocol with native expression-axis terms; preserve first1forward/0suffix failure and unchanged1e-6 controls. No model revision/admission."
guard();tick.save(ROOT/"pipeline/research_work.json",work)
print("Measurement revision1 preregistered; original failure retained; model revision count unchanged.")
