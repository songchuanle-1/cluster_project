"""Bind three uniform predict measurements and the current prototype."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "pipeline/reports"
TOKEN = "612af628c2f046f4acf6414e49f6f18a"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ref(path):
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    owner = load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    paths = {
        "baseline": REPORTS / "root_role_resources_baseline_20261012_0810.json",
        "champion": REPORTS / "root_role_resources_champion_20261012_0810.json",
        "candidate": REPORTS / "root_role_resources_v2_target_role_20261012_0810.json",
    }
    rows = {name: load(path) for name, path in paths.items()}
    candidate = rows["candidate"]
    for row in rows.values():
        assert row["protocol"] == candidate["protocol"]
        for key in ("checkpoint_sha256", "seed"):
            assert row["bound_identity"][key] == candidate["bound_identity"][key]
    assert candidate["protocol"]["forward_mode"] == "predict"
    assert candidate["protocol"]["batch_size"] == 1
    assert candidate["protocol"]["warmup"] == 20 and candidate["protocol"]["repeat"] == 100
    metrics = ("flops_g", "params", "latency_ms_median", "latency_ms_p90",
               "peak_allocated_mib")
    differences = {}
    for name in ("baseline", "champion"):
        differences[name] = {
            key: candidate["resources"][key] - rows[name]["resources"][key]
            for key in metrics}
        differences[name]["memory_relative"] = (
            candidate["resources"]["peak_allocated_mib"] /
            rows[name]["resources"]["peak_allocated_mib"] - 1)
    assert candidate["resources"]["flops_g"] <= 10
    assert all(value["memory_relative"] < 0.15 for value in differences.values())
    full = load(REPORTS / "root_role_full_native_v2_20261012_0810.json")
    prediction = load(REPORTS / "root_role_predict_controls_20261012_0810.json")
    static = load(REPORTS / "root_role_static_v2_20261012_0810.json")
    assert full["source_manifest"] == static == prediction["source_manifest"]
    for row in full["rows"]:
        assert row["all_gradients_finite"] and row["nonzero_gradient_tensors"] > 0
        if row["repeat"]:
            assert row["repeat"]["input_equal"]
            assert max(value for key, value in row["repeat"].items()
                       if key != "input_equal") <= 1e-6
    assert prediction["prediction_rebind_calls"] == 0
    assert prediction["prediction_max_delta"] == 0
    result = {
        "contract": "tmr_uniform_resource_review_v2",
        "evidence": [ref(path) for path in paths.values()],
        "protocol": candidate["protocol"],
        "metrics": {name: {key: row["resources"][key] for key in metrics}
                    for name, row in rows.items()},
        "increments": differences, "uniform_resource_gate_passed": True,
        "native_repeat_gate_passed": True, "prediction_catalog_control_passed": True,
        "limitations": "Execution gates only; no trained efficacy, novelty, train memory or speed claim. Uniform unsupported ops retained.",
    }
    output = REPORTS / "root_role_resource_compare_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
