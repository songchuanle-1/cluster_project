"""Persist the paired baseline/champion resource-gate result for due candidates."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TICK = "2026-09-21T19:07:04.834125+00:00"
BASELINE = Path("pipeline/diagnostic_runs/baseline_resources_20260922.json")
CHAMPION = Path("pipeline/diagnostic_runs/champion_resources_20260922.json")
COMPARISON = Path(
    "pipeline/diagnostic_runs/baseline_champion_resource_gate_20260922.json")
EXPECTED_HASHES = {
    BASELINE: "0a6dac48891cbebd6b86930206e3d1ac1ea3a1faddf4f3fae06f91bc7ae80613",
    CHAMPION: "199cefd3b4857c58b52237692f1e94f4fc28b52385c9f3040ca69acb0e640bbc",
    COMPARISON: "163ae821954b45531280b3e9cecf4db2a50aaf8b155bf22430a701e245080c8c",
}
RESOURCE_GATE_BLOCKER = (
    "The calibrated paired gate failed the hard absolute FLOPs limit: baseline "
    "10.144194476 G and champion 10.20585054 G versus 10.0 G. This is not an "
    "external blocker; it is an unresolved goal constraint.")
NEXT = (
    "Do not admit, enqueue, or launch a variant while the inherited absolute "
    "fvcore total exceeds 10.0 G. Next bounded work is a goal-compliant resolution: "
    "derive and test a structurally motivated forward reduction of at least "
    "0.20585054 G, or obtain an explicit same-counter goal-policy recalibration; "
    "then rerun the paired real-validation gate. Independence and admission remain "
    "open and cannot pass this resource gate. M197 stays stopped_unknown with no "
    "restart or successor.")


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _write_new(path, value):
    output = ROOT / path
    if output.exists() or output.is_symlink():
        raise ValueError("Fresh output path required: %s" % path)
    with output.open("x", encoding="ascii") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    context = _read("pipeline/headless/.tick_context.json")
    if context["mode"] != "event":
        raise ValueError("Event tick required")
    if context["generated_at"] != EXPECTED_TICK:
        raise ValueError("Wrong tick")
    due_ids = list(context["research_work"]["due_ids"])
    if len(due_ids) != 8:
        raise ValueError("Unexpected due-candidate count")

    for path, expected in EXPECTED_HASHES.items():
        actual = _sha256(ROOT / path)
        if actual != expected:
            raise ValueError("Resource evidence hash changed: %s" % path)
    baseline = _read(BASELINE)
    champion = _read(CHAMPION)
    comparison = _read(COMPARISON)
    if baseline["target"] != "baseline" or champion["target"] != "champion":
        raise ValueError("Wrong resource targets")
    if comparison["gates"]["paired_real_validation"] is not True:
        raise ValueError("Resource comparison is not paired")
    if comparison["gates"]["absolute_flops_le_10g"] is not False:
        raise ValueError("This persistence script expects the measured gate to fail")
    if comparison["gates"]["resources_verified"] is not False:
        raise ValueError("Resource gate must remain failed")
    if comparison["gates"]["admission"] is not False:
        raise ValueError("Admission must not be granted")
    if comparison["protocol"]["sample_identity"] != (
            champion["protocol"]["sample_identity"]):
        raise ValueError("Comparison and champion samples differ")
    if comparison["protocol"]["sample_identity"] != (
            baseline["protocol"]["sample_identity"]):
        raise ValueError("Comparison and baseline samples differ")

    queue_hash = _sha256(ROOT / "pipeline/queue.json")
    work_hash = _sha256(ROOT / "pipeline/research_work.json")
    work = _read("pipeline/research_work.json")
    now = datetime.now().astimezone().isoformat()
    evidence_paths = [BASELINE, CHAMPION, COMPARISON]
    evidence = [
        {"path": path.as_posix(), "sha256": _sha256(ROOT / path)}
        for path in evidence_paths
    ]
    found = set()
    progress = {
        "timestamp": now,
        "sample_scan_id": baseline["protocol"]["sample_identity"]["scan_ids"],
        "sample_ann_id": baseline["protocol"]["sample_identity"]["ann_ids"],
        "baseline_flops_g": baseline["resources"]["flops_g"],
        "champion_flops_g": champion["resources"]["flops_g"],
        "champion_minus_baseline_flops_g": (
            comparison["comparison"]["champion_minus_baseline_flops_g"]),
        "champion_absolute_flop_overage_g": (
            comparison["comparison"]["champion_absolute_flop_overage_g"]),
        "baseline_latency_ms_median": (
            baseline["resources"]["latency_ms_median"]),
        "champion_latency_ms_median": (
            champion["resources"]["latency_ms_median"]),
        "baseline_peak_allocated_mib": (
            baseline["resources"]["peak_allocated_mib"]),
        "champion_peak_allocated_mib": (
            champion["resources"]["peak_allocated_mib"]),
        "paired_real_validation": True,
        "absolute_flops_le_10g": False,
        "resources_verified": False,
        "admission": False,
        "evidence": evidence,
    }
    for candidate in work["candidates"]:
        if candidate["id"] not in due_ids:
            continue
        found.add(candidate["id"])
        merged = {item["path"]: item for item in candidate.get("evidence", [])}
        merged.update({item["path"]: item for item in evidence})
        candidate["evidence"] = list(merged.values())
        candidate["resource_gate_progress"] = progress
        candidate["next_action"] = NEXT
        candidate["latest_progress"] = (
            "%s: Paired real-validation resource gate failed absolute limit; "
            "champion 10.20585054 G, baseline 10.144194476 G. No admission."
            % now)
    if found != set(due_ids):
        raise ValueError("Missing due record")
    work["last_event_tick"] = {
        "timestamp": now,
        "mode": "event",
        "due_ids": due_ids,
        "evidence": evidence,
        "next_action": NEXT,
        "result": (
            "Paired baseline/champion resource gate completed; hard 10.0 G "
            "FLOPs gate failed; no admission or queue mutation."),
    }
    work["next_action"] = NEXT
    if _sha256(ROOT / "pipeline/queue.json") != queue_hash:
        raise ValueError("Queue changed concurrently")
    if _sha256(ROOT / "pipeline/research_work.json") != work_hash:
        raise ValueError("Research work changed concurrently")

    temporary = ROOT / "pipeline/research_work.resource_gate_20260922.tmp"
    _write_new(temporary.relative_to(ROOT), work)
    os.replace(temporary, ROOT / "pipeline/research_work.json")
    print(json.dumps({
        "due_ids": due_ids,
        "evidence": evidence,
        "resources_verified": False,
        "admission": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
