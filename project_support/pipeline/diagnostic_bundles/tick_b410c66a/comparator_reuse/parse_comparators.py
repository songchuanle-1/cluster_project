"""Read-only comparison metadata. Prints JSON; never grants admission or runs a model."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path("D:/project/cluster_project")
HISTORICAL = {
    "smoke": (
        "pipeline/diagnostic_bundles/tick_71e15360/nde_execution/smoke_champion_execution.json",
        "adb5f2659a34b6c7622f20155fc4ff41fda08383df8c2b0c653ccb509b474a7b",
    ),
    "resources": (
        "pipeline/diagnostic_bundles/tick_5287cf71/nde_execution/resources_champion_execution.json",
        "ba47706b17f694cf868b75f83844aa314d5e1f2fe74e3ad4417e65d070b5c7f8",
    ),
    "resource_review": (
        "pipeline/diagnostic_bundles/tick_5287cf71/ordinary_resource_actual_result_independent_review.json",
        "3a9e3e912a110e09c9a1bf29faefcacd1459797592f9577e178189716d0d7c83",
    ),
}
RVE_EXCLUDED = [
    "dec.cluster_att.cluster_ffn.0.",
    "dec.cluster_att.cluster_ffn_norm.0.",
    "dec.cluster_att.fine_exchange.",
]
ORIGINAL_WORKER = ROOT / "pipeline/diagnostic_bundles/tick_801d029a/nde_resource_native_active/worker.py"
ORIGINAL_WORKER_SHA = "b37fe5cf29ce04b8110752c7321d34b8d1a26218a6d8e02940b5773d9e4d5f72"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, expected):
    if not expected or sha(path) != expected:
        raise ValueError("Required artifact hash differs: " + str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def unwrap(value):
    codes = []
    while isinstance(value, dict):
        if "returncode" in value:
            codes.append(value["returncode"])
        if "result" in value and isinstance(value["result"], dict):
            return value["result"], codes
        if "observation" in value and isinstance(value["observation"], dict):
            value = value["observation"]
        else:
            return value, codes
    raise ValueError("No result object")


def quantile90(values):
    values = sorted(values)
    position = (len(values) - 1) * 0.9
    lower = math.floor(position)
    upper = math.ceil(position)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def function_hash(path):
    module = ast.parse(path.read_text(encoding="utf-8"))
    function = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "resources")
    return hashlib.sha256(ast.dump(function, include_attributes=False).encode("utf-8")).hexdigest()


def owner(result):
    return result.get("owner") or {
        "token": result.get("current_token"),
        "generated_at": result.get("tick_generated_at"),
        "deadline_at": result.get("deadline_at"),
        "context_sha256": result.get("context_sha256"),
        "pending_sha256": result.get("pending_sha256"),
    }


def common_metadata(value):
    return {k: value.get(k) for k in (
        "tensor_count", "parameter_count", "sha256", "excluded_name_prefixes",
    )}


def context(result):
    return {
        "physical_gpu": result.get("physical_gpu"),
        "gpu_uuid": result.get("gpu_uuid"),
        "scope": result.get("measurement_scope"),
        "exclusive_measurement_claimed": result.get("exclusive_measurement_claimed"),
        "before": result.get("before"),
        "after": result.get("after"),
    }


def timings(result):
    values = result.get("measurements_ms", [])
    valid = len(values) == 100 and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0 for v in values
    )
    median = statistics.median(values) if valid else None
    p90 = quantile90(values) if valid else None
    return {
        "all100_positive_finite": valid,
        "median_recomputed_ms": median,
        "p90_recomputed_ms": p90,
        "stored_median_matches": valid and math.isclose(median, result.get("median_ms", math.nan), abs_tol=1e-9),
        "stored_p90_matches": valid and math.isclose(p90, result.get("p90_ms", math.nan), abs_tol=1e-9),
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("smoke", "resources"):
        parser.add_argument("--" + name, type=Path)
        parser.add_argument("--" + name + "-sha256")
    parser.add_argument("--resource-worker", type=Path)
    parser.add_argument("--resource-worker-sha256")
    args = parser.parse_args()
    historical = {}
    provenance = {}
    for name, (relative, digest) in HISTORICAL.items():
        path = ROOT / relative
        value = load(path, digest)
        result, codes = unwrap(value)
        historical[name] = result
        provenance[name] = {"path": relative, "sha256": digest, "original_owner": owner(result)}
        if name != "resource_review" and (codes != [0] or result.get("execution_completed") is not True):
            raise ValueError("Historical arm is not a terminal successful result")
    hs, hr = historical["smoke"], historical["resources"]
    if historical["resource_review"].get("passed") is not True:
        raise ValueError("Historical resource review did not pass")
    if not all(timings(hr).values()):
        raise ValueError("Historical timing metadata failed")
    historical_batches = [b["sha256"] for b in hs["batches"]]
    output = {
        "schema_version": 1,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "scope": "READ_ONLY_METADATA_COMPARISON_NOT_NATIVE_OR_RESOURCE_EXECUTION_OR_ADMISSION",
        "historical_provenance": provenance,
        "historical_smoke": {
            "batches_exact2": hs["batches"],
            "common": common_metadata(hs["common_initialized_parameters"]),
            "middle_coarse_FFN_initial_hashes": {
                k: hs["native_tracked_initial_hash"][k] for k in ("ffn_1", "ffn_2")
            },
            "source_hashes": hs["source_hashes"],
            "config_sha256": hs["config_sha256"],
            "initialization": hs["initialization"],
            "native_train_source_sha256": hs["native_train_source_sha256"],
            "context": context(hs),
        },
        "historical_resources": {
            **{k: hr[k] for k in (
                "profile", "input_sha256", "scan_ids", "ann_ids", "parameters", "batch_size",
                "lang_num_max", "warmup", "repeat", "native_predict_calls", "median_ms", "p90_ms",
                "peak_allocated_bytes", "peak_reserved_bytes", "source_hashes", "config_sha256",
                "initialization", "native_train_source_sha256",
            )},
            "timing_recomputation": timings(hr),
            "context": context(hr),
        },
        "current_r1_smoke": "NOT_SUPPLIED_NOT_ASSESSED",
        "current_r1_resources": "NOT_SUPPLIED_NOT_ASSESSED",
        "common_scope_warning": (
            "Historical hash835 excludes all three FFNs but retains fine norm0; RVE common841 "
            "retains middle/coarse FFNs but excludes fine norm0. The two full hashes are not "
            "directly comparable. A fresh in-process full841 M95/RVE gate is separate evidence. "
            "Exact historic-value continuity additionally needs a truthful reference projection "
            "under the old835 scope and middle/coarse FFN hashes; never relabel835 as841."
        ),
        "scientific_admission": False,
        "new_native_or_resource_PASS_claimed": False,
    }
    for mode in ("smoke", "resources"):
        path = getattr(args, mode)
        digest = getattr(args, mode + "_sha256")
        if path is None:
            if digest is not None:
                raise ValueError("Hash supplied without artifact")
            continue
        result, codes = unwrap(load(path, digest))
        old = hs if mode == "smoke" else hr
        assessment = {
            "path": str(path.resolve()), "sha256": digest, "recorded_owner": owner(result),
            "returncodes": codes, "execution_completed": result.get("execution_completed"),
            "declared_source_commit": result.get("code_commit"),
            "declared_target": result.get("target"),
            "declared_implementation_revision": result.get("implementation_revision"),
            "original_config_equal": result.get("original_config_sha256") == old["original_config_sha256"],
            "backbone_pretrain_descriptor_equal": result.get("initialization") == old["initialization"],
            "native_train_source_equal": result.get("native_train_source_sha256") == old["native_train_source_sha256"],
            "data_source_equal": result.get("data_source") == old["data_source"],
            "context": context(result),
            "source_and_current_owner_binding_review": "REQUIRED_EXTERNAL_TO_THIS_METADATA_PARSER",
        }
        if mode == "smoke":
            comparison = result.get("original_common_initialization_comparison", {})
            current_common = result.get("common_initialized_parameters", {})
            historical_names = set(hs["common_initialized_parameters"].get("names", []))
            current_names = set(current_common.get("names", []))
            assessment.update(
                raw_two_batch_fingerprints_equal=(
                    [b.get("sha256") for b in result.get("batches", [])] == historical_batches
                ),
                current_full_common=common_metadata(current_common),
                current_full_reference_gate=comparison,
                exact_RVE_exclusion_map=current_common.get("excluded_name_prefixes") == RVE_EXCLUDED,
                common_names_only_in_historical_scope=sorted(historical_names - current_names),
                common_names_only_in_current_scope=sorted(current_names - historical_names),
                historical835_hash_equals_current_full_hash_claimed=False,
                historical_scope_projection=result.get("historical_common_scope_reference", "NOT_RECORDED_GAP"),
                full_historical_common_continuity="NOT_PROVEN_BY_DIFFERENT_SCOPE_HASHES",
            )
        else:
            profile = result.get("profile", {})
            assessment.update(
                same_input_hash=result.get("input_sha256") == hr["input_sha256"],
                same_sample_ids=(result.get("scan_ids") == hr["scan_ids"] and result.get("ann_ids") == hr["ann_ids"]),
                same_fixed_protocol=all(result.get(k) == hr[k] for k in (
                    "batch_size", "lang_num_max", "warmup", "repeat", "native_predict_calls",
                )),
                same_counter_version=profile.get("fvcore_version") == hr["profile"]["fvcore_version"],
                same_three_counter_files=profile.get("profiler_file_sha256") == hr["profile"]["profiler_file_sha256"],
                reported_standard_FLOPs=profile.get("flops"),
                reported_standard_within10G=profile.get("within10G"),
                timing_recomputation=timings(result),
                new_unsupported_ops=profile.get("unsupported_ops"),
                same_resource_function_AST="NOT_SUPPLIED",
                exclusive_speedup_or_pure_training_peak_claimed=False,
            )
            for key in ("median_ms", "p90_ms", "peak_allocated_bytes", "peak_reserved_bytes"):
                value = result.get(key)
                assessment[key + "_ratio_to_historical_M95"] = value / hr[key] if isinstance(value, (int, float)) else None
            if args.resource_worker:
                load_digest = args.resource_worker_sha256
                if not load_digest or sha(args.resource_worker) != load_digest:
                    raise ValueError("Current resource worker hash differs")
                if load_digest != result.get("diagnostic_worker_sha256"):
                    raise ValueError("Worker is not the producer recorded by current result")
                if sha(ORIGINAL_WORKER) != ORIGINAL_WORKER_SHA:
                    raise ValueError("Authenticated original resource worker changed")
                assessment["same_resource_function_AST"] = function_hash(args.resource_worker) == function_hash(ORIGINAL_WORKER)
        output["current_r1_" + mode] = assessment
    print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
