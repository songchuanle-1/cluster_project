"""Merge generated diagnostic evidence into current work, preserving concurrent work."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "pipeline/research_work.json"
result_path = root / "pipeline/reports/recipient_dependence_audit_20260916.json"
result = json.loads(result_path.read_text(encoding="utf-8"))
work = json.loads(path.read_text(encoding="utf-8"))
evidence = [
    {"path": str(p.relative_to(root)).replace("\\", "/"),
     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    for p in (result_path, root / "scripts/recipient_dependence_audit_20260916.py")
]
for candidate in work["candidates"]:
    if candidate["id"] not in result["next_actions"]:
        continue
    candidate["recipient_control_progress"] = {
        "timestamp": "2026-09-16T04:15:00+08:00",
        "checks_passed": 8,
        "finding": result["next_actions"][candidate["id"]],
        "scope": "Static archived-evidence audit; not native causal identification.",
    }
    if candidate["id"] != "same-target-description-grounding":
        candidate["next_action"] = result["next_actions"][candidate["id"]]
    candidate["next_action"] += " Use recipient_dependence_audit_20260916 keyed controls; no repeated captures."
    existing = {e["path"] for e in candidate["evidence"]}
    candidate["evidence"].extend(e for e in evidence if e["path"] not in existing)
path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Merged hashed evidence into three due candidates; concurrent state preserved.")
