"""Summarize bounded, source-bound diagnostic artifacts under the owned lease."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "c9de23ffb1804f1eaa81cf54b94b9d6a"
REPORTS = ROOT / "pipeline/reports"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    owner = load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    refs = []
    def evidence(name):
        path = REPORTS / (name + "_" + TOKEN + ".json")
        value = load(path)
        refs.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                     "sha256": sha(path)})
        return value
    manifest = evidence("bps_source_manifest")
    comparison = evidence("bps_compare")
    native = evidence("bps_native_current")
    controls = evidence("bps_controls_opt")
    old_controls = evidence("bps_controls_current")
    geometry = evidence("bps_geometry")
    primary = {target: evidence("bps_resources_v3_" + target)
               for target in ("baseline", "champion", "candidate")}
    train = {case: {target: evidence("bps_train_cost_" + case + "_" + target)
                    for target in primary} for case in ("stress", "nonevent", "single")}
    assert all(row["pass1e6"] for row in comparison["rows"])
    assert all(row["pass1e6"] and row["input_equal"] for row in native["rows"])
    assert native["source_manifest"]["package"] == manifest["package"]
    assert controls["source_manifest"]["package"] == manifest["package"]
    assert primary["candidate"]["resources"]["flops_g"] <= 10.
    reference_protocol = primary["champion"]["protocol"]
    assert all(value["protocol"] == reference_protocol for value in primary.values())
    checkpoints = {value["bound_identity"]["checkpoint_sha256"] for value in primary.values()}
    assert len(checkpoints) == 1
    assert all(value["gpu"]["visible_devices"] == ["7"] for value in primary.values())
    train_deltas = {}
    for case, targets in train.items():
        assert all(value["protocol"] == targets["champion"]["protocol"] for value in targets.values())
        assert len({value["checkpoint_sha256"] for value in targets.values()}) == 1
        assert all(value["all_losses_gradients_finite"] and value["optimizer_steps"] == 0
                   for value in targets.values())
        assert targets["candidate"]["source_identity"] == manifest["package"]
        train_deltas[case] = {}
        for reference in ("baseline", "champion"):
            current, base = targets["candidate"]["metrics"], targets[reference]["metrics"]
            train_deltas[case][reference] = {
                "median_ms_delta": current["latency_ms_median"] - base["latency_ms_median"],
                "median_percent": (current["latency_ms_median"] / base["latency_ms_median"] - 1) * 100,
                "allocated_mib_delta": current["peak_allocated_mib"] - base["peak_allocated_mib"],
                "allocated_percent": (current["peak_allocated_mib"] / base["peak_allocated_mib"] - 1) * 100}
    primary_deltas = {}
    for reference in ("baseline", "champion"):
        current, base = primary["candidate"]["resources"], primary[reference]["resources"]
        primary_deltas[reference] = {
            "flops_g_delta": current["flops_g"] - base["flops_g"],
            "params_delta": current["params"] - base["params"],
            "median_ms_delta": current["latency_ms_median"] - base["latency_ms_median"],
            "allocated_mib_delta": current["peak_allocated_mib"] - base["peak_allocated_mib"],
            "allocated_percent": (current["peak_allocated_mib"] / base["peak_allocated_mib"] - 1) * 100}
    geometry_pass = all(row["implementation_pass1e6"] and row["invariance_pass1e6"]
                        and row["readout_exact"] and row["restoration_exact"]
                        for row in geometry["rows"])
    assert controls["prediction_catalog_free_exact"]
    assert controls["rows"] == old_controls["rows"]
    assert controls["prediction_fingerprint"] == old_controls["prediction_fingerprint"]
    assert all(row["conditions"]["coherent"] == row["conditions"]["identity"]
               == row["conditions"]["reversed_pair_order"]
               and row["conditions"]["no_event_bypass"]["loss"] == 0
               and row["conditions"]["no_event_bypass"]["gradient_l2"] == 0
               and row["gt_self_operator_loss"] == 0 and row["wrong_target_bypass_loss"] == 0
               for row in controls["rows"])
    active = [row for row in native["rows"] if row["trials"][0]["component_nonzero_original_tensors"] > 0]
    assert active and native["optimizer_steps"] == 0
    memory_under15 = all(value["allocated_percent"] <= 15 for value in primary_deltas.values())
    assert memory_under15
    summary = {"tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
               "evidence": refs, "source_package": manifest["package"],
               "native_rows": len(native["rows"]), "native_forward_count": native["native_forward_count"],
               "native_backward_count": native["native_backward_count"],
               "native_active_cases": len(active),
               "component_nonzero_original_tensors": sorted({
                   row["trials"][0]["component_nonzero_original_tensors"] for row in active}),
               "equivalence_rows": len(comparison["rows"]), "equivalence_all_pass": True,
               "controls_groups": len(controls["rows"]), "geometry_rows": len(geometry["rows"]),
               "all_semantic_controls_v2_v3_exact": True,
               "geometry_all_pass": geometry_pass,
               "primary_metrics": {key: value["resources"] for key, value in primary.items()},
               "primary_protocol": reference_protocol, "primary_deltas": primary_deltas,
               "train_metrics": {case: {key: value["metrics"] for key, value in targets.items()}
                                 for case, targets in train.items()},
               "train_deltas": train_deltas, "resource_measured_forward_count": 3 * 120 + 9 * 120,
               "flops_trace_forward_count": None,
               "resource_test_backward_count": 9 * 120, "primary_memory_under15_percent": memory_under15,
               "optimizer_steps": 0, "admissions": 0, "training_launches": 0,
               "scientific_status": "validation", "postflight_status": "pending",
               "scope": "Execution/resource evidence; no trained efficacy, true witness identity or exhaustive novelty certificate."}
    output = REPORTS / ("bps_tick_evidence_" + TOKEN + ".json")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"summary": str(output), "sha256": sha(output),
                      "geometry_all_pass": geometry_pass, "primary_deltas": primary_deltas,
                      "train_deltas": train_deltas}))


if __name__ == "__main__":
    main()
