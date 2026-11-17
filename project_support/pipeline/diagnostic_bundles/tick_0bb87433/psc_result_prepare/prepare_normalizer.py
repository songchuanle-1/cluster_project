"""Author a PSC-only local result normalizer from the reviewed HVD result schema."""
from pathlib import Path
import ast

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_0bb87433/psc_result_prepare"
source = (ROOT / "pipeline/diagnostic_bundles/tick_154767c2/hvd_actual_results/normalize_actual_results.py").read_text(encoding="utf8")
source = source.replace("HVD", "PSC").replace("hvd", "psc").replace("variance_decomposition", "position_feature_scatter")
replacements = {
    'HERE = Path(__file__).resolve().parent': '''HERE = Path(__file__).resolve().parent
OUTPUT = HERE / ("results_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ"))
OWNER_KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")''',
    'NATIVE = ROOT / "pipeline/diagnostic_bundles/tick_c7451cf1/psc_native_prepare/native"': 'NATIVE = ACTIVATION / "native"',
    'PROTOCOL = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare/native_protocol.md"': 'PROTOCOL = ROOT / "pipeline/diagnostic_bundles/tick_0f3c54ec/reserve_candidate_prepare/native_protocol.md"',
    'PROOF = ROOT / "pipeline/diagnostic_bundles/tick_1138a3fc/psc_compatible_source_version.json"': 'PROOF = ROOT / "pipeline/diagnostic_bundles/tick_12e364dc/psc_compatible_source/compatible_source_version.json"',
    'SOURCE_REVIEW = PROOF.with_name("psc_compatible_source_independent_review.json")': 'SOURCE_REVIEW = ROOT / "pipeline/diagnostic_bundles/tick_12e364dc/psc_compatible_source_independent_review.json"',
    'TOKEN = "154767c278664ba4a7b666c69f12abaa"': 'TOKEN = "0bb874337dde412e98bbbaac369f3370"',
    'CID = "hierarchy-native-variance-decomposition-composition"': 'CID = "hierarchy-native-position-feature-cross-scatter-composition"',
    'SOURCE = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"': 'SOURCE = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"',
    'PARENT = "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"': 'PARENT = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"',
    '    CHECKS.append({"name": name, "passed": bool(condition)})': '''    CHECKS.append({"name": name, "passed": bool(condition)})
    if not condition:
        raise ValueError("Actual result validation refused: " + name)''',
    '    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_154767c2/psc_actual_results"': '    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_0bb87433/psc_result_prepare"',
    '    assert os.environ.get("CODEX_THREAD_ID") != THREAD': '''    assert os.environ.get("CODEX_THREAD_ID") in (THREAD, "01a1b166-dcbf-7d01-b0cb-c85fff644605")
    assert OUTPUT.resolve().is_relative_to(HERE.resolve())''',
    '    path = HERE / name\n    assert path.parent == HERE and Path(name).name == name': '''    path = OUTPUT / name
    assert path.parent == OUTPUT and Path(name).name == name
    OUTPUT.mkdir(exist_ok=True)''',
    '        print(json.dumps({"status": "WAITING_ACTUAL_EXECUTION_FILES", "missing": missing, "PASS_artifacts_written": False}))': '''        partial = preserve_partial("WAITING_ACTUAL_EXECUTION_FILES", missing=missing)
        print(json.dumps({"status": "WAITING_ACTUAL_EXECUTION_FILES", "missing": missing, "partial": partial, "PASS_artifacts_written": False}))''',
    '"/data/songcl/Project/Cluster_project/Cluster_mic_20261105"': '"/data/songcl/Project/Cluster_project/Cluster_hvd_20261106"',
    'sha(ACTIVATION / "native_runtime.py")': 'sha(NATIVE / "native_runtime.py")',
    'ref(ACTIVATION / "native_runtime.py")': 'ref(NATIVE / "native_runtime.py")',
    'common_c["tensor_count"] == len(common_c["names"]) == len(common_c["shapes"]) == 835': '''common_c["tensor_count"] == len(common_c["names"]) == len(common_c["shapes"]) == 835
          and re.fullmatch(r"[0-9a-f]{64}", common_c["sha256"]) is not None) 
    check("original_common_initialization_exclusions_only", common_c["excluded_name_prefixes"] == [
          "dec.cluster_att.cluster_ffn.0.", "dec.cluster_att.cluster_ffn.1.",
          "dec.cluster_att.cluster_ffn.2.", "dec.cluster_att.position_feature_scatter."]''',
    'observation["actual_group_mean_calls"] == 8 * count': '''observation["actual_group_mean_calls"] == 11 * count
              and observation["actual_centered_cross_calls"] == 3 * count
              and observation["actual_within_between_add_calls"] == count''',
    'and observation["all_observed_internal_gradients_finite"] is True)': '''and ((observation["actual_internal_backward_callbacks"] > 0
                    and observation["all_observed_internal_gradients_finite"] is True)
                   or (observation["actual_internal_backward_callbacks"] == 0
                       and observation["all_observed_internal_gradients_finite"] is None)))
        validate_psc_path(observation)''',
    '    check("original_conditional15percent_memory_policy", not over_memory)': '''    check("original_conditional15percent_memory_policy", not over_memory)
    # An above15% result requires the existing measured +0.003mIoU retention
    # evidence. This normalizer never invents trained gain or rejects a mechanism.''',
    '    draft_ref = save("draft_receipt.json", draft)': '''    # This is only a local non-admitting draft, with no decision or root review.
    draft_ref = save("draft_receipt.json", draft)''',
    'Actual variance-decomposition hierarchy core replaces original three FFNs': 'Actual position-feature signed cross-scatter hierarchy core replaces original three FFNs',
    'if __name__ == "__main__":\n    main()': '''if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        partial = preserve_partial("ACTUAL_PARTIAL_FAILURE_OR_UNVERIFIED_NO_PASS", error=error)
        print(json.dumps({"status": "ACTUAL_PARTIAL_FAILURE_OR_UNVERIFIED_NO_PASS",
                          "error_type": type(error).__name__, "error": str(error),
                          "partial": partial, "PASS_artifacts_written": False}))
        raise SystemExit(2)''',
}
for old, new in replacements.items():
    assert source.count(old) == 1, old
    source = source.replace(old, new, 1)
source = source.replace("import os\n", "import os\nimport re\n", 1)
source = source.replace("variance-decomposition", "position-feature cross-scatter")
source = source.replace('M230-PSC', 'M231-PSC')
extra = '''

def preserve_partial(status, missing=None, error=None):
    guard()
    entries = {}
    for mode, target in PAIRS:
        path = EXECUTION / (mode + "_" + target + "_execution.json")
        if path.is_file():
            try:
                value = read(path)
                entries[mode + "_" + target] = {"evidence": ref(path), "actual_raw_wrapper": value}
            except Exception as malformed:
                entries[mode + "_" + target] = {"evidence": ref(path), "parse_error": str(malformed)}
    return save("partial_actual_results.json", {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": status, "candidate_id": CID, "source_commit": SOURCE,
        "runtime_code_commit": PARENT, "owner_provenance_only": {
            key: read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")[key] for key in OWNER_KEYS},
        "missing": missing or [], "error_type": type(error).__name__ if error else None,
        "error": str(error) if error else None, "checks_before_refusal": CHECKS,
        "actual_results_preserved": entries, "PASS_artifacts_written": False,
        "native_pass_claimed": False, "resources_pass_claimed": False,
        "shared_or_raw_files_written": False, "GPU_SSH_model_execution": False,
        "failure_scope": "Observed implementation/data/resource evidence only; no whole-mechanism rejection.",
        "conditional_memory_rule": "Above15% requires actual trained +0.003mIoU retention evidence; never synthesized.",
        "unrelated_HVD_root_cause": "UNKNOWN; not a PSC scientific gate.",
    })


def validate_psc_path(observation):
    step = str(observation["forward"])
    check("PSC_original_coordinate_and_encoder_references_step" + step,
          observation["exact_original_decoder_padded_positions_reference"] is True
          and observation["exact_original_encoder_feature_and_mask_references"] is True
          and observation["actual_three_LN_calls"] == [1, 1, 1]
          and observation["native_positions"]["finite"] is True
          and observation["native_positions"]["shape"][-1] == 3)
    scenes = observation["scene_observations"]
    active = [scene for scene in scenes if scene["true_supported_nodes_by_scale"][0] > 0]
    check("PSC_supported_scene_counts_step" + step, len(active) == observation["actual_supported_scene_count"])
    for index, scene in enumerate(active):
        suffix = step + "_scene" + str(index)
        counts = scene["true_supported_nodes_by_scale"]
        check("PSC_original_call_counts_" + suffix,
              all(scene[key] == 1 for key in ("actual_original_builder_calls", "actual_stats_calls",
                  "actual_pack_calls", "actual_factor_concat_calls", "actual_factor_calls",
                  "actual_GELU_calls", "actual_split_calls", "actual_within_between_add_calls"))
              and scene["actual_group_mean_calls"] == 11 and scene["actual_centered_cross_calls"] == 3
              and scene["actual_linear_calls"] == 2 and scene["actual_final_index_copy_calls"] == 3)
        stats, pack = scene["stats_observations"], scene["pack_observations"]
        check("PSC_original_stats_pack_single_calls_" + suffix, len(stats) == len(pack) == 1)
        stats, pack = stats[0], pack[0]
        channels = pack["semantic_inputs"][0]["shape"][-1]
        check("PSC_native_coordinates_and_original_five_moments_" + suffix,
              all(stats[key] is True for key in ("actual_native_mask_selection_observed",
                  "native_coordinate_dtype_cast_observed", "equal_supported_child_center_and_covariance_objects_verified",
                  "coarse_within_input_is_actual_middle_within_plus_between", "returned_original_tuple_unchanged"))
              and stats["moment_arithmetic_replayed"] is False and stats["statistic_nonzero_or_minimum_effect_gate"] is False
              and stats["moment_names"] == ["fine_cross_scatter", "middle_within", "middle_between",
                                           "coarse_within", "coarse_between"]
              and stats["native_coordinate_input"]["finite"] is True
              and stats["native_coordinate_input"]["shape"] == [scene["point_count"], 3]
              and stats["native_coordinate_input"]["dtype"] == stats["point_input"]["dtype"]
              and [value["shape"] for value in stats["outputs"]] == [
                  [counts[0], 3 * channels], [counts[1], 3 * channels], [counts[1], 3 * channels],
                  [counts[2], 3 * channels], [counts[2], 3 * channels]]
              and all(value["finite"] is True for value in stats["outputs"]))
        means, crosses = scene["group_mean_observations"], scene["centered_cross_observations"]
        check("PSC_eleven_actual_means_and_three_signed3xC_crosses_" + suffix,
              len(means) == 11 and [item["ordinal"] for item in means] == list(range(1, 12))
              and len(crosses) == 3 and [item["level"] for item in crosses] == [0, 1, 2]
              and all(item["original_calls"] == 1 and item["input"]["finite"] is True
                      and item["output"]["finite"] is True for item in means)
              and all(item["original_calls"] == 1 and item["arithmetic_replayed"] is False
                      and item["signed_outer_product_width"] == 3 * channels
                      and item["output"]["shape"] == [counts[level], 3 * channels]
                      and all(item[key]["finite"] is True for key in ("positions", "features", "position_center", "feature_center", "output"))
                      for level, item in enumerate(crosses)))
        check("PSC_actual_C_3C_3C_3C_to10C_pack_" + suffix,
              all(pack[key] is True for key in ("moment_inputs_are_actual_returned_objects",
                  "packing_blocks_C_3C_3C_3C", "returned_original_list_unchanged"))
              and pack["packing_replayed"] is False and pack["actual_ancestor_index_select_calls"] == 3
              and [value["shape"] for value in pack["outputs"]] == [[count, 10 * channels] for count in counts]
              and all(value["finite"] is True for value in pack["outputs"]))
        factor, restore = scene["factor_observations"], scene["restoration_observations"]
        check("PSC_original_shared_factor_and_restoration_" + suffix,
              [item["kind"] for item in factor] == ["first_linear", "original_GELU", "second_linear"]
              and factor[0]["input"]["shape"] == [sum(counts), 10 * channels]
              and all(item["input"]["finite"] is True and item["output"]["finite"] is True for item in factor)
              and len(restore) == 3 and [item["level"] for item in restore] == [0, 1, 2]
              and all(item["source_is_actual_factor_split"] is True and item["zero_initialized_destination"] is True
                      and item["returned_original_object_unchanged"] is True and item["output"]["finite"] is True for item in restore))
    for level in range(3):
        for key in ("native_normalized_level" + str(level) + "_gradients", "native_output_level" + str(level) + "_gradients"):
            check("PSC_original_finite_observed_backward_" + step + "_" + key,
                  bool(observation[key]) and all(item["finite"] is True for item in observation[key]))

'''
source = source.replace("\ndef main():\n", extra + "\ndef main():\n", 1)
source = source.replace('    input_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in input_paths}', '''
    check("manifest_exact_activation_template_projection", manifest == {
        **read(NATIVE / "manifest_template.json"),
        "current_token": TOKEN, "stage": "/data/songcl/Project/Cluster_project/pipeline/psc_" + TOKEN[:8] + "_gpu0",
        "tick_generated_at": owner["generated_at"], "deadline_at": owner["deadline_at"],
        "physical_gpu": 0, "gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c", "allowed_gpus": [0],
        "context_sha256": owner["context_sha256"], "pending_sha256": owner["pending_sha256"], "runtime_code_commit": PARENT})
    check("PSC_source_proof_and_review_hashes", sha(PROOF) == "9c6308fe6d166216123ef23e871eeacec5e8e3b2b3b9c02fb448364a44d13083"
          and sha(SOURCE_REVIEW) == "7098b020bc414f34eab9013f6f3b94a72ad0d842249ceff7c30a1310cd2bf6d8"
          and sha(PROTOCOL) == "98b12c011260550efd1a87a10dc834d80468ee3523cb3301ddb18c2a4671976a")
    check("exact_reviewed_worker_and_runtime", sha(NATIVE / "worker.py") == "530a5230021fad8d880c37a34c18973b4c556e7dc1536b6c4faaffdd6d6f93d8"
          and sha(NATIVE / "native_runtime.py") == "2468966c25ef12b0c1d06907b39c9f341daa07e2771c026c8920899f8acb72a7")
    for (mode, target), actual in raw.items():
        for boundary in ("before", "after"):
            observed = actual[boundary]
            row = [value.strip() for value in observed["gpu"].split(",")]
            check(mode + "_" + target + "_" + boundary + "_actual_authorized_boundary",
                  row[:2] == ["0", binding["gpu_uuid"]]
                  and observed["resource_authorization"] == manifest["resource_authorization"]
                  and observed["resource_memory_policy"] == manifest["resource_memory_policy"]
                  and observed["measurement_scope"] == manifest["resource_memory_policy"]["measurement_scope"]
                  and observed["exclusive_measurement_claimed"] is False
                  and observed["cooperative_project_locks_held"] == (0 if boundary == "before" else 3)
                  and datetime.fromisoformat(owner["generated_at"]) <= datetime.fromisoformat(observed["observed_at"]) < datetime.fromisoformat(owner["deadline_at"]))
        check(mode + "_" + target + "_before_original20000MiB_budget",
              actual["before"]["memory_free_mib"] >= 20000
              and actual["before"]["usable_under_current_overlay_policy"] is True)
        if mode == "resources":
            check(target + "_original121_predict_calls_no_optimizer_or_loss",
                  actual["native_predict_calls"] == 121 and actual["optimizer_steps"] == actual["native_loss_forwards"] == actual["native_criterion_backwards"] == 0)
    input_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in input_paths}''', 1)
ast.parse(source)
compile(source, "normalize_psc_actual_results.py", "exec")
with (HERE / "normalize_psc_actual_results.py").open("x", encoding="utf8", newline="\n") as stream:
    stream.write(source)
print("PSC normalizer authored; no actual result normalization or PASS output performed.")
