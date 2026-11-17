"""Persist the corrected predict-mode resource-gate result for due candidates."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(
    "pipeline/diagnostic_runs/baseline_predict_resources_20260922.json")
CHAMPION = Path(
    "pipeline/diagnostic_runs/champion_predict_resources_20260922.json")
COMPARISON = Path(
    "pipeline/diagnostic_runs/"
    "baseline_champion_predict_resource_gate_20260922.json")
MEASUREMENT_SCRIPT = Path(
    "scripts/champion_baseline_resource_gate_20260922.py")
EXPECTED_HASHES = {
    BASELINE: "a824b2c88d76b396befedb2fb7268814a992a94e6bda387bdf6e938b5d0be1c5",
    CHAMPION: "23a9b06c89f77034e1faa38792d6f6a91f35857fbdbcc6bf681e14e393aa92dd",
    COMPARISON: "79771dcf3a65680aa7b6979679641da30bed3828e841ce022e3d3286673cc530",
}
NEXT = (
    "The corrected historical predict-mode resource gate is verified: baseline "
    "9.700876364 G and champion 9.762532428 G, below the 10.0 G limit. Continue "
    "each due candidate's existing diagnosis/design work and next executable "
    "independent implementation or native control. Do not enqueue or launch until "
    "diagnosis, derivation, literature, controls, native_backward, resources, "
    "independence and constraints gates all pass. M197 remains stopped_unknown "
    "with no restart or successor.")


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
    for result in (baseline, champion):
        if result["protocol"]["forward_mode"] != "predict":
            raise ValueError("The probe did not use predict mode")
    if comparison["protocol"]["sample_identity"] != (
            baseline["protocol"]["sample_identity"]):
        raise ValueError("Comparison and baseline samples differ")
    if comparison["protocol"]["sample_identity"] != (
            champion["protocol"]["sample_identity"]):
        raise ValueError("Comparison and champion samples differ")
    gates = comparison["gates"]
    if gates["paired_real_validation"] is not True:
        raise ValueError("Resource comparison is not paired")
    if gates["absolute_flops_le_10g"] is not True:
        raise ValueError("Corrected resource gate did not pass")
    if gates["resources_verified"] is not True:
        raise ValueError("Resources must be verified")
    if gates["admission"] is not False:
        raise ValueError("Admission must not be granted")

    queue_hash = _sha256(ROOT / "pipeline/queue.json")
    work_hash = _sha256(ROOT / "pipeline/research_work.json")
    work = _read("pipeline/research_work.json")
    now = datetime.now().astimezone().isoformat()
    evidence_paths = [
        BASELINE, CHAMPION, COMPARISON, MEASUREMENT_SCRIPT,
    ]
    evidence = [
        {"path": path.as_posix(), "sha256": _sha256(ROOT / path)}
        for path in evidence_paths
    ]
    progress = {
        "timestamp": now,
        "protocol": "historical predict-mode fvcore",
        "sample_scan_id": baseline["protocol"]["sample_identity"]["scan_ids"],
        "sample_ann_id": baseline["protocol"]["sample_identity"]["ann_ids"],
        "baseline_flops_g": baseline["resources"]["flops_g"],
        "champion_flops_g": champion["resources"]["flops_g"],
        "champion_minus_baseline_flops_g": (
            comparison["comparison"]["champion_minus_baseline_flops_g"]),
        "champion_margin_to_limit_g": -(
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
        "absolute_flops_le_10g": True,
        "resources_verified": True,
        "admission": False,
        "evidence": evidence,
    }

    found = set()
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
            "%s: Corrected predict-mode resource gate passed; champion "
            "9.762532428 G versus 10.0 G limit. Resources verified; admission "
            "remains open." % now)
    if found != set(due_ids):
        raise ValueError("Missing due record")

    work["last_event_tick"] = {
        "timestamp": now,
        "mode": "event",
        "due_ids": due_ids,
        "evidence": evidence,
        "next_action": NEXT,
        "result": (
            "Corrected the resource probe to the historical predict-mode "
            "forward; resources now pass with 0.237467572 G champion margin. "
            "No admission or queue mutation occurred."),
    }
    work["next_action"] = NEXT
    if _sha256(ROOT / "pipeline/queue.json") != queue_hash:
        raise ValueError("Queue changed concurrently")
    if _sha256(ROOT / "pipeline/research_work.json") != work_hash:
        raise ValueError("Research work changed concurrently")

    temporary = ROOT / (
        "pipeline/research_work.predict_resource_gate_20260922.tmp")
    _write_new(temporary.relative_to(ROOT), work)
    os.replace(temporary, ROOT / "pipeline/research_work.json")
    print(json.dumps({
        "due_ids": due_ids,
        "evidence": evidence,
        "resources_verified": True,
        "admission": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
