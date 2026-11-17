"""Normalize only complete actual NDE results; never admit, enqueue or execute."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys
import yaml

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / ("results_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ"))
OWNER_KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
TICK = ROOT / 'pipeline/diagnostic_bundles/tick_f6536795'
EXECUTION = TICK / "nde_execution"
BASE_NATIVE = Path('D:\\project\\cluster_project\\pipeline\\diagnostic_bundles\\tick_4fa1481e\\nde_revision_native_prepare')
NATIVE = None  # Actual reviewed execution copy is passed explicitly by root.
PROTOCOL = ROOT / "pipeline/diagnostic_bundles/tick_2e51495f/reserve_candidate/native_protocol.md"
PROOF = ROOT / 'pipeline/diagnostic_bundles/tick_4fa1481e/nde_revision1_source/source_version.json'
SOURCE_REVIEW = ROOT / 'pipeline/diagnostic_bundles/tick_4fa1481e/nde_revision_source_independent_review.json'
TOKEN = 'f653679598744de7ac2fafb23a96c1ea'
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CID = "hierarchy-native-distribution-embedding-composition"
SOURCE = '0747f6acec1c61018ec99acf2efa5329c9b3523c'
PARENT = "f6257de79148581334ee495e6e2d60ccb525457c"
GOAL = "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
PAIRS = (("smoke", "champion"), ("smoke", "candidate"), ("resources", "champion"), ("resources", "candidate"))
DRAFT_NORMALIZATION_DISABLED = False
EXPECTED_WORKER_SHA256 = 'b37fe5cf29ce04b8110752c7321d34b8d1a26218a6d8e02940b5773d9e4d5f72'
EXPECTED_RUNTIME_SHA256 = '348024f11e6a106788840c1359ad8c65363914d1f1882cfe4a5f8d319d5ea1a4'
HISTORICAL_PROVENANCE = ROOT / 'pipeline/diagnostic_bundles/tick_4fa1481e/nde_revision_result_prepare/historical_champion_smoke_provenance.json'
HISTORICAL_PROVENANCE_SHA256 = 'cbad63e6da551b6024572c47d0df6b6c147af5aaad890d8eb05dd14eea58d170'
REUSE_REVIEW = ROOT / 'pipeline/diagnostic_bundles/tick_4fa1481e/nde_historical_champion_smoke_reuse_review.json'
REUSE_REVIEW_SHA256 = '1c2913321b0bf0b9681043104096cad0100939f8fc1acc5ca52dd9b67a9ad756'
EXPECTED_NATIVE = Path('D:\\project\\cluster_project\\pipeline\\diagnostic_bundles\\tick_4fa1481e\\nde_revision_native_active')
EXPECTED_OPERATIONAL_REFS = {'FROZEN.json': {'path': 'pipeline/diagnostic_bundles/tick_f6536795/nde_operational_active/FROZEN.json', 'sha256': '19171f4e3094bcd5a11a911c7a7d135a65bb6bf9e3710921e937f84ad77dfd4f'}, 'adapter.py': {'path': 'pipeline/diagnostic_bundles/tick_f6536795/nde_operational_active/adapter.py', 'sha256': '8c2613e18c51b2c03e603028ec123b26c16057d930c04587a3c9309e92e25364'}, 'remote_ops.py': {'path': 'pipeline/diagnostic_bundles/tick_f6536795/nde_operational_active/remote_ops.py', 'sha256': 'db82eab9dd05fd90e30194119b0e1df559ed11a4178a2015923b11e16a48779e'}, 'run_nde_operation.py': {'path': 'pipeline/diagnostic_bundles/tick_f6536795/nde_operational_active/run_nde_operation.py', 'sha256': '1a43c01799c9b6fba00fb9a9e31ed6824c0034237399f8733e4aa16c3b7dab9f'}, 'current_binding.json': {'path': 'pipeline/diagnostic_bundles/tick_f6536795/nde_operational_active/current_binding.json', 'sha256': '6dac90238cb877863d9ed22237ee9119f9230ba05da116cbb52ce3d7e4daa160'}, 'release_template.json': {'path': 'pipeline/diagnostic_bundles/tick_f6536795/nde_operational_active/release_template.json', 'sha256': 'aaf4b8734321fe6ff5dff33e7f5419e0c48230a8d44bb724143ed9bfdaa8cc18'}, 'preparation.json': {'path': 'pipeline/diagnostic_bundles/tick_f6536795/nde_operational_active/preparation.json', 'sha256': '48cd8101c6999fad6a7c1cf2dfd7b85bda35b6f21fac9f922289e7c4faf0bd78'}, 'software_validation.json': {'path': 'pipeline/diagnostic_bundles/tick_f6536795/nde_operational_active/software_validation.json', 'sha256': '141c48cba979292485f6b4e1deba37f8e29823785629c34ca8842009543e6c2d'}}
CHECKS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def check(name, condition):
    CHECKS.append({"name": name, "passed": bool(condition)})
    if not condition:
        raise ValueError("Actual result validation refused: " + name)


def guard():
    assert not DRAFT_NORMALIZATION_DISABLED, "DRAFT normalizer is disabled; no normalization or output"
    assert HERE.resolve().is_relative_to(TICK.resolve())
    assert sha(HISTORICAL_PROVENANCE) == HISTORICAL_PROVENANCE_SHA256
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert os.environ.get("CODEX_THREAD_ID") == THREAD
    assert sys.dont_write_bytecode and os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert OUTPUT.resolve().is_relative_to(HERE.resolve())
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return owner


def save(name, value):
    guard()
    path = OUTPUT / name
    assert path.parent == OUTPUT and Path(name).name == name
    OUTPUT.mkdir(exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return ref(path)


def finite(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def percentile90(values):
    ordered = sorted(values)
    index = (len(ordered) - 1) * 0.9
    lo = math.floor(index)
    return ordered[lo] + (ordered[math.ceil(index)] - ordered[lo]) * (index - lo)


def source_function(path, name):
    text = path.read_text(encoding="utf-8")
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(text, node)



def preserve_partial(status, missing=None, error=None):
    guard()
    entries = {}
    for mode, target in PAIRS:
        path = arm_path(mode, target, "execution")
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
        "actual_results_preserved": entries,
        "PASS_artifacts_written": any((OUTPUT / name).exists() for name in
            ('native_smoke.json', 'resources.json', 'constraints_independence.json', 'draft_receipt.json')),
        "native_pass_claimed": (OUTPUT / 'native_smoke.json').exists(),
        "resources_pass_claimed": (OUTPUT / 'resources.json').exists(),
        "shared_or_raw_files_written": False, "GPU_SSH_model_execution": False,
        "failure_scope": "Observed implementation/data/resource evidence only; no whole-mechanism rejection.",
        "conditional_memory_rule": "Above15% requires actual trained +0.003mIoU retention evidence; never synthesized.",
        "unrelated_parent_runtime_root_causes": "UNKNOWN; not a NDE scientific gate.",
    })


def arm_path(mode, target, suffix):
    directory = ROOT / read(HISTORICAL_PROVENANCE)['execution_dir'] if (mode,target)==('smoke','champion') else EXECUTION
    return directory / (mode + '_' + target + '_' + suffix + '.json')


def arm_context(mode, target, owner, manifest, binding, lease):
    if (mode,target)!=('smoke','champion'):
        return {'manifest':manifest,'binding':binding,'lease':lease,'owner':owner,
                'native':NATIVE,'source':SOURCE,'execution':EXECUTION,'evidence_paths':[]}
    check('historical_champion_provenance_hash', sha(HISTORICAL_PROVENANCE)==HISTORICAL_PROVENANCE_SHA256)
    check('historical_champion_reuse_independent_review', REUSE_REVIEW is not None
          and sha(REUSE_REVIEW)==REUSE_REVIEW_SHA256 and read(REUSE_REVIEW).get('passed') is True)
    provenance=read(HISTORICAL_PROVENANCE)
    evidence_paths=[]
    for name,digest in provenance['files'].items():
        path=(ROOT/name).resolve()
        check('historical_champion_immutable_'+name, path.is_relative_to(ROOT.resolve()) and sha(path)==digest)
        evidence_paths.append(path)
    directory=ROOT/provenance['execution_dir'];native=ROOT/provenance['native_dir']
    old_manifest=read(directory/'native_manifest.json');old_binding=read(directory/'execution_binding.json')
    old_lease=read(directory/'execution_lease.json');old_owner=provenance['original_owner']
    check('historical_champion_original_binding_manifest_lease', old_binding['owner']==old_owner
          and old_binding['code_commit']==old_manifest['code_commit']==provenance['source_commit']
          and old_binding['runtime_code_commit']==old_manifest['runtime_code_commit']==PARENT
          and old_binding['native_manifest_sha256']==old_lease['native_manifest_sha256']==sha(directory/'native_manifest.json')
          and old_binding['execution_lease_sha256']==sha(directory/'execution_lease.json')
          and old_manifest['current_token']==old_lease['token']==old_owner['token'])
    check('historical_champion_exact_original_activation_projection',old_manifest=={
        **read(native/'manifest_template.json'),'current_token':old_owner['token'],'stage':old_binding['stage'],
        'tick_generated_at':old_owner['generated_at'],'deadline_at':old_owner['deadline_at'],
        'physical_gpu':0,'gpu_uuid':old_binding['gpu_uuid'],'allowed_gpus':[0],
        'context_sha256':old_owner['context_sha256'],'pending_sha256':old_owner['pending_sha256'],'runtime_code_commit':PARENT})
    check('historical_champion_unchanged_M95_YAML_data_runtime_protocol',old_manifest['candidate_id']==CID
          and old_manifest['goal_sha256']==GOAL and old_manifest['root']==manifest['root']
          and old_manifest['config']==manifest['config'] and old_manifest['assets']==manifest['assets']
          and old_manifest['candidate_config_sha256']==manifest['candidate_config_sha256']
          and sha(native/'candidate.yaml')==sha(NATIVE/'candidate.yaml'))
    return {'manifest':old_manifest,'binding':old_binding,'lease':old_lease,'owner':old_owner,
            'native':native,'source':provenance['source_commit'],'execution':directory,
            'evidence_paths':evidence_paths}


def validate_external_arm_identity(result, mode, target, expected_source):
    package = "framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort" + ("_nde" if target == "candidate" else "")
    expected = {"candidate_id": "hierarchy-native-distribution-embedding-composition", "code_commit": expected_source,
                "experiment_id": "M233-NDE", "goal_sha256": GOAL,
                "config": "configs/Quard/ctf_hcg_csort_nde/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde.yaml",
                "mode": mode, "target": target, "model_package": package}
    check("external_literal_NDE_arm_identity_" + mode + "_" + target,
          mode in ("smoke", "resources") and target in ("champion", "candidate")
          and isinstance(result, dict) and all(result.get(k) == v for k, v in expected.items()))


def validate_nde_path(observation):
    step = str(observation['forward'])
    check('NDE_original_native_feature_encoder_refs_' + step,
          observation['exact_original_encoder_feature_and_mask_references'] is True
          and observation['actual_three_LN_calls'] == [1, 1, 1]
          and observation['native_point_analysis_precedes_first_private_mean'] is True
          and observation['per_parameter_nonzero_FP32_minimum_effect_gate_added'] is False
          and observation['actual_revision1_affine_factoring_observed'] is True
          and observation['implementation_revision'] == 1)
    active = [scene for scene in observation['scene_observations'] if scene['true_supported_nodes_by_scale'][0] > 0]
    check('NDE_original_supported_scene_count_' + step, len(active) == observation['actual_supported_scene_count'])
    mappings = ['point_to_fine', 'fine_to_middle', 'middle_to_coarse']
    for index, scene in enumerate(active):
        suffix = step + '_scene' + str(index)
        counts = scene['true_supported_nodes_by_scale']
        check('NDE_original_single_call_topology_' + suffix,
              scene['actual_original_support_builder_calls'] == 1
              and scene['actual_original_valid_feature_mask_reference'] is True
              and all(scene[k] == 3 for k in ('actual_group_mean_calls', 'actual_parent_context_broadcast_calls',
                  'actual_analysis_calls', 'actual_synthesis_calls', 'actual_final_index_copy_calls')))
        contexts = scene['parent_context_observations']
        check('NDE_original_three_parent_contexts_' + suffix,
              len(contexts) == 3 and [x['level'] for x in contexts] == [0, 1, 2]
              and all(x['mapping'] == mappings[x['level']]
                      and x['actual_original_normalized_parent_token_ref'] is True
                      and x['actual_original_ancestry_mapping'] is True
                       and x['projected_unique_parent_before_gather'] is True
                       and x['unique_parent_rows'] == counts[x['level']]
                       and x['child_rows'] == (scene['point_count'] if x['level'] == 0
                                              else counts[x['level'] - 1])
                       and x['output']['shape'][0] == x['child_rows']
                      and x['original_calls'] == 1 and x['output']['finite'] is True for x in contexts))
        means = scene['mean_observations']
        check('NDE_original_three_transformed_value_means_' + suffix,
              len(means) == 3 and [x['level'] for x in means] == [0, 1, 2]
              and all(x['mapping'] == mappings[x['level']] and x['groups'] == counts[x['level']]
                      and x['actual_shared_analysis_precedes_private_mean'] is True
                      and x['actual_original_parent_ids'] is True
                      and x['original_calls'] == 1 and x['returned_original_object_unchanged'] is True
                      and x['input']['finite'] is True and x['output']['finite'] is True
                      and x['output']['shape'][0] == counts[x['level']] for x in means))
        for kind, order in (('analysis', [0, 1, 2]), ('synthesis', [2, 1, 0])):
            stages = scene[kind + '_observations']
            check('NDE_original_shared_' + kind + '_' + suffix,
                  len(stages) == 3 and [x['level'] for x in stages] == order
                  and all(x['original_calls'] == 1 and x['actual_original_shared_module'] is True
                          and x['no_replay_or_replacement'] is True
                          and x['input']['finite'] is True and x['output']['finite'] is True
                          and x['input']['shape'] == [x['output']['shape'][0], (1 if kind == 'analysis' else 2) * x['output']['shape'][-1]] for x in stages))
            if kind == 'analysis':
                check('NDE_native_points_before_first_mean_then_actual_child_states_' + suffix,
                      all(x['before_private_mean'] is True and x['analysis_source'] ==
                          ('actual_native_points' if x['level'] == 0 else 'actual_child_state')
                          and x['parent_input']['shape'] == [counts[x['level']], x['output']['shape'][-1]]
                           and x['parent_input']['finite'] is True
                          and x['actual_three_argument_analysis'] is True
                           and x['actual_child_and_unique_parent_first_affine_halves'] is True
                           and x['actual_original_first_affine_bias_applied_once'] is True
                          and x['actual_parent_projection_before_gather'] is True
                          and x['original_per_child_GELU_and_second_Linear'] is True
                           and x['analysis_first_affine_source_rows'] == x['input']['shape'][0]
                           and x['analysis_first_affine_unique_parent_rows'] == counts[x['level']]
                          and x['original_parameter_topology_and_precision'] is True for x in stages)
                      and stages[0]['output']['shape'][0] == scene['point_count']
                      and all(stages[level]['output']['shape'][0] == counts[level - 1] for level in (1, 2))
                      and all(means[level]['input']['shape'] == stages[level]['output']['shape'] for level in range(3)))
                for stage in stages:
                    level = stage['level']
                    channels = stage['output']['shape'][-1]
                    child_rows = stage['input']['shape'][0]
                    linear = stage['affine_factorization_observations']
                    check('NDE_revision1_actual_original_weight_linear_operations_' + suffix + '_level' + str(level),
                          len(linear) == 3
                          and [entry['role'] for entry in linear] == [
                              'actual_child_first_affine_half',
                              'actual_unique_parent_first_affine_half',
                              'actual_original_second_linear']
                          and all(entry['original_calls'] == 1
                                  and entry['actual_original_parameter_or_slice_reference'] is True
                                  and entry['returned_original_object_unchanged'] is True
                                  and entry['FP32_cast_added'] is False
                                  and entry['input']['finite'] is True
                                  and entry['weight']['finite'] is True
                                  and entry['output']['finite'] is True
                                  and entry['weight']['shape'] == [channels, channels]
                                  and entry['input']['shape'] == [
                                      counts[level] if ordinal == 1 else child_rows, channels]
                                  and entry['output']['shape'] == entry['input']['shape']
                                  for ordinal, entry in enumerate(linear))
                          and [entry['first_affine_original_bias_applied_here'] for entry in linear]
                              == [True, False, None]
                          and contexts[level]['output']['shape'] == [child_rows, channels])
            else:
                check('NDE_original_synthesis_supported_counts_' + suffix,
                      all(x['output']['shape'][0] == counts[x['level']] for x in stages))
        restored = scene['restoration_observations']
        check('NDE_original_supported_id_restoration_' + suffix,
              len(restored) == 3 and [x['level'] for x in restored] == [0, 1, 2]
              and all(x['original_calls'] == 1 and x['actual_synthesis_delta_ref'] is True
                      and x['zero_initialized_destination'] is True and x['returned_original_object_unchanged'] is True
                      and x['original_node_ids'] == scene['nodes'][x['level']] and x['output']['finite'] is True for x in restored))
    for level in range(3):
        for key in ('native_normalized_level' + str(level) + '_gradients', 'native_output_level' + str(level) + '_gradients'):
            check('NDE_original_finite_observed_backward_' + step + '_' + key,
                  bool(observation[key]) and all(x['finite'] is True for x in observation[key]))



def main():
    global NATIVE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-reviewed', action='store_true')
    parser.add_argument('--native-dir', required=False,
                        help='Actual separately reviewed current-owner execution payload directory; never the disabled mother packet')
    args = parser.parse_args()
    if not args.execute_reviewed:
        print(json.dumps({'status':'DEFAULT_NOP_NO_NORMALIZATION','draft_disabled':DRAFT_NORMALIZATION_DISABLED}));return
    assert not DRAFT_NORMALIZATION_DISABLED and args.native_dir, 'Reviewed activation and explicit actual native directory required'
    NATIVE = Path(args.native_dir).resolve()
    assert NATIVE == EXPECTED_NATIVE.resolve() and NATIVE != BASE_NATIVE.resolve()
    owner = guard()
    check('fresh_operational_payload_refs_bound', isinstance(EXPECTED_OPERATIONAL_REFS, dict)
          and bool(EXPECTED_OPERATIONAL_REFS))
    for name, entry in EXPECTED_OPERATIONAL_REFS.items():
        artifact = (ROOT / entry['path']).resolve()
        check('fresh_operational_immutable_' + name,
              artifact.is_relative_to(TICK.resolve()) and sha(artifact) == entry['sha256'])
    missing = [mode + "_" + target + "_execution.json" for mode, target in PAIRS
               if not arm_path(mode, target, "execution").is_file()]
    if missing:
        partial = preserve_partial("WAITING_ACTUAL_EXECUTION_FILES", missing=missing)
        print(json.dumps({"status": "WAITING_ACTUAL_EXECUTION_FILES", "missing": missing, "partial": partial, "PASS_artifacts_written": False}))
        return
    manifest = read(EXECUTION / "native_manifest.json")
    binding = read(EXECUTION / "execution_binding.json")
    lease = read(EXECUTION / "execution_lease.json")
    proof = read(PROOF)
    config = manifest["config"]
    proof_files = proof.get("files", proof.get("source_files"))
    base = {"id": "M233-NDE", "candidate_id": CID, "config": config, "code_commit": SOURCE,
            "goal_sha256": GOAL, "recorded_at": datetime.now(timezone.utc).isoformat()}
    input_paths = [EXECUTION / name for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    raw = {}
    arm_contexts = {}
    check("manifest_exact_identity_source_runtime_goal", manifest["candidate_id"] == CID and manifest["code_commit"] == SOURCE
          and manifest["runtime_code_commit"] == PARENT and manifest["goal_sha256"] == GOAL
          and manifest["root"] == "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107")
    check("goal_unchanged", sha(ROOT / "pipeline/goal.json") == GOAL)
    check("binding_manifest_lease_match", binding["native_manifest_sha256"] == sha(EXECUTION / "native_manifest.json")
          == lease["native_manifest_sha256"] and binding["execution_lease_sha256"] == sha(EXECUTION / "execution_lease.json")
          and binding["code_commit"] == SOURCE and binding["runtime_code_commit"] == PARENT)
    owner_keys = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
    check("execution_actual_current_owner", binding["owner"] == {k: owner[k] for k in owner_keys}
          and manifest["current_token"] == lease["token"] == TOKEN)
    check("source_compatible_proof_and_review", proof["source_commit"] == SOURCE and proof["source_parent_commit"] == PARENT
          and read(SOURCE_REVIEW)["passed"] is True and proof["exact_nine_additions"] is True
          and isinstance(proof_files, dict) and len(proof_files) == 9)
    for mode, target in PAIRS:
        name = mode + "_" + target
        path, request_path = arm_path(mode, target, "execution"), arm_path(mode, target, "request")
        arm = arm_context(mode, target, owner, manifest, binding, lease)
        arm_contexts[mode, target] = arm
        am, ab, ao, an, ac = (arm[k] for k in ('manifest','binding','owner','native','source'))
        input_paths.extend(arm['evidence_paths'])
        entry, request = read(path), read(request_path)
        result = entry.get("result") or {}
        validate_external_arm_identity(result, mode, target, ac)
        raw[(mode, target)] = result
        input_paths.extend((path, request_path))
        expected = {"project": "cluster_project", "candidate_id": CID, "code_commit": ac,
                    "stage": ab["stage"], "token": ao["token"], "request_id": request["request_id"],
                    "operation": "run", "physical_gpu": 0, "gpu_uuid": ab["gpu_uuid"],
                    "native_manifest_sha256": ab["native_manifest_sha256"]}
        check(name + "_wrapper_identity", entry["identity"] == expected and request == {**expected, "mode": mode, "target": target})
        check(name + "_actual_terminal_success", entry.get("certainty") == "terminal"
              and entry.get("returncode") == 0 and result.get("execution_completed") is True)
        check(name + "_original_command", entry["command"] == [
            "/home/songcl/.conda/envs/project_cluster/bin/python", "-B", ab["stage"] + "/worker.py",
            "--lease", ab["stage"] + "/execution_lease.json", "--mode", mode, "--target", target])
        identity = {"candidate_id": CID, "experiment_id": "M233-NDE", "code_commit": ac,
                    "goal_sha256": GOAL, "config": config, "mode": mode, "target": target,
                    "stage": ab["stage"], "physical_gpu": 0, "gpu_uuid": ab["gpu_uuid"],
                    "current_token": ao["token"], "native_manifest_sha256": ab["native_manifest_sha256"],
                    "diagnostic_worker_sha256": sha(an / "worker.py"),
                    "runtime_sha256": sha(an / "native_runtime.py"),
                    "context_sha256": ao["context_sha256"], "pending_sha256": ao["pending_sha256"],
                    "tick_generated_at": ao["generated_at"], "deadline_at": ao["deadline_at"]}
        check(name + "_raw_identity", all(result.get(k) == v for k, v in identity.items()))
        expected_sources = am["candidate_source_hashes"] if target == "candidate" else am["assets"]["source_hashes"]
        check(name + "_source_and_YAML_exact", result.get("source_hashes") == expected_sources
              and result.get("config_sha256") == result.get("original_config_sha256") == am["candidate_config_sha256"]
              and result.get("native_train_source_sha256") == am["assets"]["native_train_source_sha256"]
              and result.get("native_model_and_yaml_unchanged") is True)
        check(name + "_native_pretrain_seed", result.get("initialization", {}).get("kind") == "native_train_pretrain"
              and result["initialization"]["seed"] == 1999 and result["initialization"]["trained_m95_checkpoint_loaded"] is False
              and result["initialization"]["sha256"] == am["assets"]["pretrain_sha256"])

    check("manifest_exact_activation_template_projection", manifest == {
        **read(NATIVE / "manifest_template.json"),
        "current_token": TOKEN, "stage": "/data/songcl/Project/Cluster_project/pipeline/nde_" + TOKEN[:8] + "_gpu0",
        "tick_generated_at": owner["generated_at"], "deadline_at": owner["deadline_at"],
        "physical_gpu": 0, "gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c", "allowed_gpus": [0],
        "context_sha256": owner["context_sha256"], "pending_sha256": owner["pending_sha256"], "runtime_code_commit": PARENT})
    check("NDE_source_proof_and_review_hashes", sha(PROOF) == '0afd1b6c7f9d7582cfe42e1f382d125132a9d787fdac66ae33f7f19f30a4f1d0'
          and sha(SOURCE_REVIEW) == '1c5ae5b77ed256462097c433ec4c2233fb567ed1bedc5dc3d03e10588d2bee53'
          and sha(PROTOCOL) == "ab5675efd2d72432c827d60095d3bddbd6fef53fa3b0a2764af5a9f9ba61dee4")
    check("exact_reviewed_worker_and_runtime", sha(NATIVE / "worker.py") == EXPECTED_WORKER_SHA256
          and sha(NATIVE / "native_runtime.py") == EXPECTED_RUNTIME_SHA256)
    check('actual_enabled_runtime_is_only_reviewed_DRAFT_flag_change',
          (NATIVE / 'native_runtime.py').read_bytes() ==
          (BASE_NATIVE / 'native_runtime.py').read_bytes().replace(
              b'DRAFT_EXECUTION_DISABLED = True', b'DRAFT_EXECUTION_DISABLED = False', 1))
    check('actual_worker_same_as_reviewed_NDE_mother', sha(NATIVE / 'worker.py') == sha(BASE_NATIVE / 'worker.py'))
    version = read(NATIVE / 'source_version_binding.json')
    check('actual_source_binding_matches_frozen_NDE_and_manifest',
          version['source_commit'] == version['code_commit'] == SOURCE and version['parent_commit'] == PARENT
          and version['source_files'] == proof_files and version['candidate_source_hashes'] == manifest['candidate_source_hashes']
          and sha(NATIVE / 'source_version_binding.json') == manifest['source_version_binding_sha256'])
    for (mode, target), actual in raw.items():
        arm = arm_contexts[mode,target]
        am, ab, ao = (arm[k] for k in ('manifest','binding','owner'))
        for boundary in ("before", "after"):
            observed = actual[boundary]
            row = [value.strip() for value in observed["gpu"].split(",")]
            check(mode + "_" + target + "_" + boundary + "_actual_authorized_boundary",
                  row[:2] == ["0", ab["gpu_uuid"]]
                  and observed["resource_authorization"] == am["resource_authorization"]
                  and observed["resource_memory_policy"] == am["resource_memory_policy"]
                  and observed["measurement_scope"] == am["resource_memory_policy"]["measurement_scope"]
                  and observed["exclusive_measurement_claimed"] is False
                  and observed["cooperative_project_locks_held"] == (0 if boundary == "before" else 3)
                  and datetime.fromisoformat(ao["generated_at"]) <= datetime.fromisoformat(observed["observed_at"]) < datetime.fromisoformat(ao["deadline_at"]))
        check(mode + "_" + target + "_before_original20000MiB_budget",
              actual["before"]["memory_free_mib"] >= 20000
              and actual["before"]["usable_under_current_overlay_policy"] is True)
        if mode == "resources":
            check(target + "_original121_predict_calls_no_optimizer_or_loss",
                  actual["native_predict_calls"] == 121 and actual["optimizer_steps"] == actual["native_loss_forwards"] == actual["native_criterion_backwards"] == 0)
    input_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in input_paths}
    champion, candidate = raw["smoke", "champion"], raw["smoke", "candidate"]
    for target, result in (("champion", champion), ("candidate", candidate)):
        check(target + "_two_natural_original_loss_steps", result.get("optimizer_steps") == result.get("native_loss_forwards")
              == result.get("native_criterion_backwards") == 2
              and len(result.get("losses", [])) == len(result.get("batches", [])) == len(result.get("steps", [])) == 2
              and all(finite(x) for x in result["losses"]) and result.get("native_data_loaded") is True
              and result.get("native_train_function_executed") is True and result.get("backward_finite") is True
              and result.get("native_smoke_checks_passed") is True and result.get("intended_path_observed") is True)
        check(target + "_no_extra_backward_or_training", result.get("auxiliary_autograd_grad_or_backward_used") is False
              and result.get("training_checkpoint_saved") is False and result.get("new_training") == 0)
        check(target + "_finite_original_backward", all(s.get("all_observed_gradients_finite") is True
              and not s.get("nonfinite_parameter_names") and s.get("optimizer_step_completed") is True for s in result["steps"]))
        check(target + "_single_inst_mask_path", len(result.get("inst_to_mask_path_observations", [])) == 2
              and all(x.get("single_native_inst_update_exact") is True and x.get("new_extra_injection") is False
                      for x in result["inst_to_mask_path_observations"]))
    common_c, common_b = candidate["common_initialized_parameters"], champion["common_initialized_parameters"]
    check("paired835_common_named_tensors_shapes_and_values", common_c == common_b
          and common_c["tensor_count"] == len(common_c["names"]) == len(common_c["shapes"]) == 835
          and re.fullmatch(r"[0-9a-f]{64}", common_c["sha256"]) is not None) 
    check("original_common_initialization_exclusions_only", common_c["excluded_name_prefixes"] == [
          "dec.cluster_att.cluster_ffn.0.", "dec.cluster_att.cluster_ffn.1.",
          "dec.cluster_att.cluster_ffn.2.", "dec.cluster_att.distribution_embedding."])
    check("paired_two_complete_natural_batch_fingerprints", candidate["batches"] == champion["batches"])
    check("paired_native_initialization_data_optimizer_schedule", candidate["initialization"] == champion["initialization"]
          and candidate["data_source"] == champion["data_source"]
          and candidate["native_dataloader_config"] == champion["native_dataloader_config"]
          and candidate["optimizer_type"] == champion["optimizer_type"] == "AdamW"
          and candidate["scheduler_type"] == champion["scheduler_type"] == "PolyLR")
    gradient_summary = []
    for step in candidate["steps"]:
        gradient = step["whole_distribution_embedding_weight_gradient"]
        weight_changed = step["weight_before_step_hash"]["distribution_embedding"] != step["weight_after_step_hash"]["distribution_embedding"]
        module_changed = step["module_before_step_hash"]["distribution_embedding"] != step["module_after_step_hash"]["distribution_embedding"]
        check("whole_core_gradient_and_update_step" + str(step["forward"]),
              gradient["finite"] is True and finite(gradient["abs_max"]) and gradient["abs_max"] > 0
              and step["whole_distribution_embedding_weight_updated"] is weight_changed and weight_changed
              and step["whole_distribution_embedding_module_updated"] is module_changed and module_changed)
        gradient_summary.append({"forward": step["forward"], "aggregate_weight_gradient": gradient,
                                 "aggregate_weight_updated": weight_changed, "aggregate_module_updated": module_changed})
    observations = candidate["NDE_distribution_embedding_observations"]
    check("two_actual_NDE_path_observations", len(observations) == 2)
    check("original_three_raw_skips_and_exact_HCG_inputs",
          len(candidate["hcg_readbacks"]) == 2
          and all(x["NDE_original_three_skips_and_exact_HCG_inputs"] == [True, True, True]
                  for x in candidate["hcg_readbacks"]))
    path_summary = []
    for observation in observations:
        count = observation["actual_supported_scene_count"]
        check("actual_production_NDE_path_step" + str(observation["forward"]),
              observation["actual_true_fine_paths"] > 0 and count > 0
              and all(observation[k] == 3 * count for k in ("actual_group_mean_calls", "actual_parent_context_broadcast_calls",
                  "actual_analysis_calls", "actual_synthesis_calls", "actual_final_index_copy_calls"))
              and observation["actual_production_NDEmbedding_path_observed"] is True
              and observation["no_feature_or_model_replay"] is True
              and ((observation["actual_internal_backward_callbacks"] > 0
                    and observation["all_observed_internal_gradients_finite"] is True)
                   or (observation["actual_internal_backward_callbacks"] == 0
                       and observation["all_observed_internal_gradients_finite"] is None)))
        validate_nde_path(observation)
        path_summary.append({key: value for key, value in observation.items() if isinstance(value, (str, int, float, bool))})
    values = yaml.safe_load((NATIVE / "candidate.yaml").read_text(encoding="utf-8"))
    check("original_data_seed_schedule_saved_YAML", values["train"]["seed"] == 1999 and values["train"]["epochs"] == 50
          and values["lr_scheduler"]["max_iters"] == 70 and values["dataloader"]["train"]["batch_size"] == 2
          and values["dataloader"]["train"]["num_workers"] == 4 and values["dataloader"]["train"]["persistent_workers"] is True)
    rb, rc = raw["resources", "champion"], raw["resources", "candidate"]
    check("matched_resource_fixture", all(rb[k] == rc[k] for k in (
        "input_sha256", "scan_ids", "ann_ids", "batch_size", "lang_num_max", "warmup", "repeat", "initialization", "data_source"))
        and rc["batch_size"] == rc["lang_num_max"] == 1 and rc["warmup"] == 20 and rc["repeat"] == 100)
    check("same_original_profiler_handlers", rb["profile"]["profiler_file_sha256"] == rc["profile"]["profiler_file_sha256"]
          == {"flop_count": "b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba",
              "jit_analysis": "110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31",
              "jit_handles": "ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129"})
    producer = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native/worker.py"
    check("complete_original_resource_function_byte_exact", source_function(NATIVE / "worker.py", "resources") == source_function(producer, "resources"))
    for target, result in (("champion", rb), ("candidate", rc)):
        times = result["measurements_ms"]
        check(target + "_all100_resource_measurements_recomputed", len(times) == 100 and all(finite(x) and x > 0 for x in times)
              and math.isclose(statistics.median(times), result["median_ms"], rel_tol=1e-12)
              and math.isclose(percentile90(times), result["p90_ms"], rel_tol=1e-12)
              and result["parameter_flags_preserved"] is True and result["source_body_executed_without_replacement"] is True
              and result["validation_accuracy_evaluated_for_selection"] is False
              and isinstance(result["profile"]["unsupported_ops"], dict) and bool(result["profile"]["by_operator"]))
    over_memory = rc["peak_allocated_bytes"] > rb["peak_allocated_bytes"] * 1.15
    check("original_whole_model10G_gate", finite(rc["profile"]["flops_g"]) and rc["profile"]["flops_g"] <= 10
          and rc["profile"]["within10G"] is True)
    check("original_conditional15percent_memory_policy", not over_memory)
    # An above15% result requires the existing measured +0.003mIoU retention
    # evidence. This normalizer never invents trained gain or rejects a mechanism.
    check("raw_input_files_preserved", all(sha(ROOT / name) == digest for name, digest in input_hashes.items()))
    failures = [item["name"] for item in CHECKS if not item["passed"]]
    evidence = [ref(arm_path(mode, target, "execution")) for mode, target in PAIRS]
    evidence += [ref(EXECUTION / name) for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    evidence += [ref(PROOF), ref(SOURCE_REVIEW), ref(PROTOCOL), ref(NATIVE / "worker.py"), ref(NATIVE / "native_runtime.py")]
    per_arm_provenance = {mode + '_' + target: {
        'source_commit': arm['source'], 'owner': arm['owner'],
        'historical_reuse': (mode,target)==('smoke','champion'),
        'current_owner_execution_claimed': (mode,target)!=('smoke','champion'),
        'execution': ref(arm_path(mode,target,'execution')),
        'request': ref(arm_path(mode,target,'request')),
        'worker': ref(arm['native']/'worker.py'), 'runtime': ref(arm['native']/'native_runtime.py'),
        'binding': ref(arm['execution']/'execution_binding.json'),
        'manifest': ref(arm['execution']/'native_manifest.json'),
        'lease': ref(arm['execution']/'execution_lease.json')}
        for (mode,target),arm in arm_contexts.items()}
    evidence += [ref(HISTORICAL_PROVENANCE), ref(REUSE_REVIEW)]
    evidence += [ref(p) for p in arm_contexts['smoke','champion']['evidence_paths']]
    audit = {**base, "per_arm_provenance": per_arm_provenance, "passed": not failures, "checks": CHECKS, "check_count": len(CHECKS), "failed_checks": failures,
             "actual_input_files": input_hashes, "original_thresholds_only": True,
             "per_row_map_bias_positivity_or_FP32_minimum_effect_gates_added": False,
             "root_or_independent_actual_review_completed_by_this_author": False,
             "shared_state_or_raw_result_written": False, "GPU_model_execution_by_normalizer": False}
    if failures:
        audit["status"] = "ACTUAL_FAILURE_OR_UNVERIFIED_GATE_PRESERVED_NO_ADMISSION_DRAFT"
        result_ref = save("normalization_audit.json", audit)
        print(json.dumps({"status": audit["status"], "failed_checks": failures, "evidence": result_ref}))
        return
    smoke = {**base, "per_arm_provenance": per_arm_provenance, "passed": True, "steps": 2, "losses": candidate["losses"], "champion_losses": champion["losses"],
             "native_data_loaded": True, "backward_finite": True, "intended_path_observed": True,
             "split": "train", "command": candidate["actual_train_command"], "data_source": candidate["data_source"],
             "paired_TRAIN_batches": {"shared_initialization_verified": True, "two_natural_train_batches": True,
                 "common_tensor_count": 835, "common_parameter_count": common_c["parameter_count"],
                 "common_sha256": common_c["sha256"], "excluded_name_prefixes": common_c["excluded_name_prefixes"],
                 "batches": candidate["batches"]},
             "whole_NDE_core_original_loss_gradient_and_update": gradient_summary,
             "actual_NDE_path_observations": path_summary, "evidence": evidence,
             "limitations": ["Two natural TRAIN steps establish technical execution only, not trained efficacy or novelty.",
                 "Smoke memory includes observer hooks and snapshots; it is not pure optimizer TRAIN memory.",
                 "Individual rows/maps/biases/statistic components may be zero; no additional coverage or positivity gate was added."]}
    smoke_ref = save("native_smoke.json", smoke)
    metrics = {"flops_g": (rb["profile"]["flops_g"], rc["profile"]["flops_g"])}
    metrics.update({key: (rb[key], rc[key]) for key in ("median_ms", "p90_ms", "peak_allocated_bytes", "peak_reserved_bytes", "parameters")})
    resources = {**base, "schema_version": 1, "experiment_id": "M233-NDE", "passed": True,
                 "decision": "ORIGINAL_RESOURCE_GATE_PASSED_ACTUAL_MATCHED_SAME_OWNER_FIXTURE",
                 "champion_actual": evidence[2], "candidate_actual": evidence[3],
                 "pairing": {key: rc[key] for key in ("input_sha256", "scan_ids", "ann_ids", "batch_size", "lang_num_max", "warmup", "repeat")},
                 "runtime_code_commit": PARENT, "runtime_root": manifest["root"], "physical_gpu": 0, "gpu_uuid": binding["gpu_uuid"],
                 "measured": {key: {"champion": pair[0], "candidate": pair[1]} for key, pair in metrics.items()},
                 "delta": {key: {"absolute": pair[1] - pair[0], "percent": (pair[1] / pair[0] - 1) * 100} for key, pair in metrics.items()},
                 "full_profile": {"champion": rb["profile"], "candidate": rc["profile"]},
                 "all100_times_each_and_statistics_recomputed": True,
                 "original_gates": {"whole_model_counted_FLOPs_at_most10G": True,
                     "peak_prediction_allocated_memory_increase_above15percent": over_memory,
                     "conditional_retention_gain_requirement_triggered": over_memory,
                     "trained_mIoU_gain_measured": False, "new_latency_cutoff_added": False},
                 "resource_boundary_observations": {target: {key: result[key] for key in ("before", "after", "measurement_scope", "exclusive_measurement_claimed")}
                                                    for target, result in (("champion", rb), ("candidate", rc))},
                 "evidence": evidence, "limitations": [
                     "Sequential authorized-overlay measurements; not exclusive timing or a causal speed claim.",
                     "Complete original profiler unsupported-op counts are retained; counted FLOPs use the original standard.",
                     "Full optimizer TRAIN peak and no-cluster baseline delta remain UNKNOWN.",
                     "Memory increase is below15%; no trained +0.003 mIoU condition is triggered. Efficacy/novelty remain UNKNOWN."]}
    resource_ref = save("resources.json", resources)
    constraints = {**base, "experiment_id": "M233-NDE", "parent_commit": PARENT, "passed": True,
                   "actual_git_source_hashes": proof_files, "exact_nine_paths_only": True,
                   "source_version": ref(PROOF), "independent_source_review": ref(SOURCE_REVIEW),
                   "native_smoke": smoke_ref, "resources": resource_ref, "protocol": ref(PROTOCOL),
                   "source_unchanged_from_tested_bytes": True, "config_is_independent_native_YAML": True,
                   "fixed_original_data_seed_schedule_loss_precision": True,
                   "native_yaml_record": {"seed": 1999, "epochs": 50, "max_iters": 70,
                                          "precision_intervention": False, "optimizer": candidate["optimizer_type"],
                                          "scheduler": candidate["scheduler_type"], "data_source": candidate["data_source"]},
                   "mainline": "Actual original native point conditional vector embedding BEFORE private means/true-ancestry shared analysis/synthesis replaces original three FFNs and reaches original rawskip/HCG/single inst_feats/ILA/mask path.",
                   "no_goal_server_bans_holds_or_protocol_changes": True,
                   "efficacy": "UNKNOWN", "novelty": "UNKNOWN", "scientific_admission": False,
                   "review_status": "PENDING_ROOT_AND_INDEPENDENT_ACTUAL_GATE_REVIEW", "evidence": evidence}
    constraints_ref = save("constraints_independence.json", constraints)
    authorization = {"path": "pipeline/authorizations/experiment_first_20261021.json",
                     "sha256": "2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8"}
    draft = {**base, "profile": "experiment_first", "authorization": authorization,
             "native_smoke": smoke_ref, "decision": None, "draft": True, "canonical_receipt": False,
             "admission_granted": False, "requires_root_and_independent_actual_review": True,
             "independent_reviews": [], "gates": {
                 "native_backward": {"passed": True, "evidence": [smoke_ref]},
                 "resources": {"passed": True, "evidence": [resource_ref]},
                 "independence": {"passed": True, "evidence": [constraints_ref]},
                 "constraints": {"passed": True, "evidence": [constraints_ref]}},
             "efficacy": "UNKNOWN; technical checks do not establish training gain or novelty."}
    # Validate only the existing read-only canonical smoke interface, not admission.
    sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
    import experiment_first
    experiment_first.validate_smoke(ROOT, draft)
    audit["canonical_validate_smoke_actual_passed"] = True
    audit["status"] = "ACTUAL_RESULTS_NORMALIZED_PENDING_ROOT_AND_INDEPENDENT_REVIEW"
    audit_ref = save("normalization_audit.json", audit)
    draft["normalization_audit"] = audit_ref
    # This is only a local non-admitting draft, with no decision or root review.
    draft_ref = save("draft_receipt.json", draft)
    print(json.dumps({"status": audit["status"], "check_count": len(CHECKS), "native_smoke": smoke_ref,
                      "resources": resource_ref, "constraints_independence": constraints_ref,
                      "draft_receipt": draft_ref, "normalization_audit": audit_ref,
                      "candidate_losses": candidate["losses"], "resource_measured": resources["measured"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        partial = preserve_partial("ACTUAL_PARTIAL_FAILURE_OR_UNVERIFIED_NO_PASS", error=error)
        print(json.dumps({"status": "ACTUAL_PARTIAL_FAILURE_OR_UNVERIFIED_NO_PASS",
                          "error_type": type(error).__name__, "error": str(error),
                          "partial": partial,
                          "PASS_artifacts_written": any((OUTPUT / n).exists() for n in ('native_smoke.json', 'resources.json', 'constraints_independence.json'))}))
        raise SystemExit(2)
