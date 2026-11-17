"""Bind actual independent BPS evidence without automatic git operations."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "pipeline/reports"
TOKEN = "1d59938f077948578e91e2cf34fc9d53"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def save(name, data):
    path = REPORTS / name
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    return path


def main():
    owner = load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    paths = list(REPORTS.glob("*" + TOKEN + "*.json"))
    paths = [p for p in paths if not p.name.startswith("summary")]
    native = load(REPORTS / ("bps_native_v2_" + TOKEN + ".json"))
    assert all(r["full_repeat_pass1e6"] for r in native["rows"])
    assert native["metadata_controls"]["changed_content_rejected"]
    assert native["metadata_controls"]["missing_catalog_prediction_exact"]
    primary = {name: load(REPORTS / (prefix + name + "_" + TOKEN + ".json"))
               for name, prefix in (("baseline", "bps_resources_"), ("champion", "bps_resources_"),
                                    ("candidate", "bps_resources_v2_"))}
    training = {name: load(REPORTS / (prefix + name + "_" + TOKEN + ".json"))
                for name, prefix in (("baseline", "bps_train_resources_"),
                                     ("champion", "bps_train_resources_"),
                                     ("candidate", "bps_train_resources_v2_"))}
    for name in ("baseline", "champion"):
        assert primary[name]["protocol"] == primary["candidate"]["protocol"]
        assert primary[name]["bound_identity"]["checkpoint_sha256"] == primary["candidate"]["bound_identity"]["checkpoint_sha256"]
        assert training[name]["protocol"] == training["candidate"]["protocol"]
        assert training[name]["checkpoint_sha256"] == training["candidate"]["checkpoint_sha256"]
    keys = ("flops_g", "params", "latency_ms_median", "latency_ms_p90", "peak_allocated_mib")
    increments = {}
    for name in ("baseline", "champion"):
        increments[name] = {key: primary["candidate"]["resources"][key] - primary[name]["resources"][key]
                            for key in keys}
        increments[name]["memory_relative"] = (
            primary["candidate"]["resources"]["peak_allocated_mib"] /
            primary[name]["resources"]["peak_allocated_mib"] - 1)
    assert primary["candidate"]["resources"]["flops_g"] <= 10
    summary = {
        "tick_token": TOKEN, "created_at": datetime.now(timezone.utc).isoformat(),
        "native_v2_repeat_cases": len(native["rows"]), "native_v2_metadata": native["metadata_controls"],
        "prediction_resources": {name: {k: row["resources"][k] for k in keys}
                                 for name, row in primary.items()},
        "prediction_increments": increments,
        "supplemental_training_resources": {name: row["metrics"] for name, row in training.items()},
        "population": load(REPORTS / ("bps_population_" + TOKEN + ".json"))["counts"],
        "teacher_proxy_slack": load(REPORTS / ("bps_teacher_witness_" + TOKEN + ".json"))["counts"],
        "evidence": [ref(p) for p in paths], "optimizer_steps": 0, "admissions": 0, "training_launches": 0,
        "independent_methods": 1, "physical_versions": 2,
        "next_action": "Run current V2 semantic matched-controls regression (prepared V3 runner, rebind next tick token), explain/optimize measured training-path overhead with exact non-event bypass/paired profiling, then final six-gate review, tested targeted commit, admission receipt and safe ff-only deployment before gated training.",
        "scope": "Execution and metadata/resource evidence, not trained efficacy/true witnesses/exhaustive novelty."
    }
    summary_path = save("bps_tick_summary_" + TOKEN + ".json", summary)
    record = {
        "stage": "validation", "execution_status": "Native V2 regression completed; actual tick postflight pending",
        "next_action": summary["next_action"], "blocker": "",
        "scientific_scope": summary["scope"],
        "gates": {
            "diagnosis": {"passed": False, "status": "Task-relevant native physical-support path observed; final scope review pending"},
            "controls": {"passed": False, "status": "V1 matched semantic controls complete; V2 semantic regression prepared, unrun"},
            "native_backward": {"passed": True, "evidence": [ref(REPORTS / ("bps_native_v2_" + TOKEN + ".json"))]},
            "resources": {"passed": False, "status": "Primary FLOPs/memory within budget; supplemental training-path latency increment needs review, not unilateral rejection", "evidence": [ref(summary_path)]},
            "independence": {"passed": True, "evidence": [ref(REPORTS / ("bps_source_manifest_v2_" + TOKEN + ".json"))]},
            "constraints": {"passed": False, "status": "Frozen numerical configuration preserved; final full18constraints/11bans review pending"}
        },
        "evidence": [ref(summary_path)] + [ref(p) for p in paths]
    }
    record_path = save("bps_work_update_" + TOKEN + ".json", record)
    subprocess.run([__import__("sys").executable, str(ROOT / "scripts/tick_ledger_20261012.py"),
                    "update", "--token", TOKEN, "--id", "m95-native-between-pair-support",
                    "--record", str(record_path)], check=True)
    support = {
        "stage": "validation",
        "next_action": "Preserve all native scalar-role source facts and failures; use the independent BPS V2 path and its pending matched semantic controls for structural information-path discrimination, not scalar normalization/priority variants. No old calibration rerun or automatic training.",
        "execution_status": "Resumed through distinct physically independent support path; source facts unchanged",
        "evidence": [ref(summary_path)]
    }
    support_path = save("bps_role_link_" + TOKEN + ".json", support)
    for candidate in ("m95-native-main-role-weight-precedence",
                      "m95-native-secondary-positive-mass",
                      "m95-native-relation-other-sign-conflict"):
        subprocess.run([__import__("sys").executable, str(ROOT / "scripts/tick_ledger_20261012.py"),
                        "update", "--token", TOKEN, "--id", candidate,
                        "--record", str(support_path)], check=True)
    cycle = {
        "stop_reason": "tick_deadline_near",
        "attempted_ids": ["m95-native-between-pair-support",
                          "m95-native-main-role-weight-precedence",
                          "m95-native-secondary-positive-mass",
                          "m95-native-relation-other-sign-conflict"],
        "evidence": [ref(summary_path)],
        "resume_condition": summary["next_action"]
    }
    cycle_path = save("bps_cycle_" + TOKEN + ".json", cycle)
    subprocess.run([__import__("sys").executable, str(ROOT / "scripts/tick_ledger_20261012.py"),
                    "cycle", "--token", TOKEN, "--record", str(cycle_path)], check=True)
    print(json.dumps({"summary": str(summary_path), "increments": increments,
                      "training_metrics": summary["supplemental_training_resources"]}))


if __name__ == "__main__":
    main()
