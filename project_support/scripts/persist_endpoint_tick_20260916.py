"""Persist shared executed diagnostics without mutating training state."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "pipeline/research_work.json"
work = json.loads(path.read_text(encoding="utf-8"))
context = json.loads((root / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
names = [
    "scripts/physical_mask_endpoints_20260916.py",
    "scripts/test_physical_mask_endpoints_20260916.py",
    "scripts/endpoint_audit_20260916.py",
    "pipeline/reports/endpoint_audit_20260916-1715.json",
    "pipeline/decisions/20260916-171447_other.md",
]
for candidate in work["candidates"]:
    if candidate["id"] not in context["research_work"]["due_ids"]:
        continue
    for name in names:
        entry = dict(path=name, sha256=hashlib.sha256((root / name).read_bytes()).hexdigest())
        if entry not in candidate["evidence"]:
            candidate["evidence"].append(entry)
    candidate["endpoint_adapter_progress"] = dict(
        stage_completed="Shared static endpoint adapter and archive availability/sensitivity audit",
        tests_passed=12, native_execution_completed=False,
        finding="All16rows lack selected mask/semantic endpoints; leave-one-scene-out success .4167-.5833.",
        limitations="No expanded capture, seven-control binding, same-class population estimate or PIRS comparison.",
        next_action="Integrate versioned adapter with native semantic support; preserve candidate-specific capture/control actions.")
    if candidate["id"] in {
        "modality-identity-preservation", "instance-identity-representation",
        "input-modality-distinguishability"
    }:
        candidate["next_action"] = (
            "Integrate tested physical_mask_endpoints_20260916 adapter into a new versioned native "
            "capture; bind semantic labels to exact support and execute predefined TRAIN sample. "
            "Apply frozen recoverable same-class stratum before paired feature-stage contrasts. "
            "Do not infer language grounding from instance retrieval.")
path.write_text(json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
print("Persisted shared static progress; eight diagnosis stages retained.")
