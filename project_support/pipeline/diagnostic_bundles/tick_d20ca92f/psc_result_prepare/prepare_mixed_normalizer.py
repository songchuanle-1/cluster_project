"""Adapt the reviewed normalizer to historical validated smoke and fresh resources."""
from pathlib import Path
import ast
import hashlib

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OLD = ROOT / "pipeline/diagnostic_bundles/tick_0bb87433/psc_result_prepare"
assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_d20ca92f/psc_result_prepare"
assert hashlib.sha256((OLD / "normalize_psc_actual_results.py").read_bytes()).hexdigest() == "1998df4ddc60acc307b05bc4eb70d0ef8e10bc006a18111884a6b3f8f07f6ba7"
source = (OLD / "normalize_psc_actual_results.py").read_text(encoding="utf8")
source = source.replace("tick_0bb87433/psc_result_prepare", "tick_d20ca92f/psc_result_prepare")
source = source.replace('TOKEN = "0bb874337dde412e98bbbaac369f3370"', 'TOKEN = "d20ca92f1b654e24ba9cf29f634307b7"')
source = source.replace('CHECKS = []', '''CHECKS = []
HISTORICAL_TICK = ROOT / "pipeline/diagnostic_bundles/tick_0bb87433"
HISTORICAL_EXECUTION = HISTORICAL_TICK / "psc_execution"
HISTORICAL_ACTIVATION = HISTORICAL_TICK / "psc_current_activation"
HISTORICAL_REVIEW = HISTORICAL_TICK / "psc_partial_actual_independent_review.json"
OWNER_PROVENANCE = {}''', 1)
extra = '''

def arm_execution(mode):
    if mode not in ("smoke", "resources"):
        raise ValueError("Unknown original PSC mode")
    return HISTORICAL_EXECUTION if mode == "smoke" else EXECUTION


def historical_smoke_provenance():
    check("historical_actual_smoke_review181_hash",
          sha(HISTORICAL_REVIEW) == "371d6354e24c8db8806b518e279b293341f36ee457fcdf8d92b4b9400088168c")
    review = read(HISTORICAL_REVIEW)
    check("historical_actual_smoke_pair_independently_validated",
          review["passed"] is True and review["actual_check_count"] == 181
          and review["paired_smoke"]["status"] == "ACTUAL_PAIRED_NATIVE_SMOKE_CHECKS_PASSED")
    for target in ("champion", "candidate"):
        entry = review["actual_arm_evidence"]["smoke_" + target]
        check("historical_smoke_" + target + "_exact_reviewed_wrapper",
              (ROOT / entry["path"]).resolve() == (HISTORICAL_EXECUTION / ("smoke_" + target + "_execution.json")).resolve()
              and sha(ROOT / entry["path"]) == entry["sha256"])
    needed = ("native_manifest.json", "execution_binding.json", "execution_lease.json",
              "smoke_champion_request.json", "smoke_candidate_request.json")
    for name in needed:
        path = HISTORICAL_EXECUTION / name
        original_hash = next(digest for name_, digest in review["inputs_unchanged_after_review"].items()
                             if (ROOT / name_).resolve() == path.resolve())
        check("historical_provenance_file_unchanged:" + name, sha(path) == original_hash)
    manifest, binding, lease = (read(HISTORICAL_EXECUTION / name) for name in needed[:3])
    owner = review["owner_provenance_only"]
    check("historical_smoke_exact_historical_owner_binding",
          binding["owner"] == owner and owner["token"] == "0bb874337dde412e98bbbaac369f3370"
          and binding["native_manifest_sha256"] == lease["native_manifest_sha256"] == sha(HISTORICAL_EXECUTION / "native_manifest.json")
          and binding["execution_lease_sha256"] == sha(HISTORICAL_EXECUTION / "execution_lease.json")
          and lease["token"] == manifest["current_token"] == owner["token"]
          and manifest["code_commit"] == SOURCE and manifest["runtime_code_commit"] == PARENT
          and manifest["goal_sha256"] == GOAL and manifest["candidate_id"] == CID)
    expected = read(HISTORICAL_ACTIVATION / "native/manifest_template.json")
    expected.update(current_token=owner["token"], stage=binding["stage"],
                    tick_generated_at=owner["generated_at"], deadline_at=owner["deadline_at"],
                    physical_gpu=0, gpu_uuid=binding["gpu_uuid"], allowed_gpus=[0],
                    context_sha256=owner["context_sha256"], pending_sha256=owner["pending_sha256"], runtime_code_commit=PARENT)
    check("historical_smoke_original_manifest_projection", manifest == expected)
    OWNER_PROVENANCE["smoke"] = {
        "owner": owner, "execution_directory": HISTORICAL_EXECUTION.relative_to(ROOT).as_posix(),
        "independent_actual_review": ref(HISTORICAL_REVIEW), "reuse": "Immutable validated actual smoke only",
        "historical_expired_lease_used_for_new_execution": False, "copied_raw_into_current_execution": False}
    return {"owner": owner, "manifest": manifest, "binding": binding, "lease": lease}

'''
source = source.replace("\ndef main():\n", extra + "\ndef main():\n", 1)
source = source.replace('    owner = guard()\n    missing =', '''    owner = guard()
    historical = historical_smoke_provenance()
    OWNER_PROVENANCE["resources"] = {"owner": {key: owner[key] for key in OWNER_KEYS},
        "execution_directory": EXECUTION.relative_to(ROOT).as_posix(),
        "reuse": "Fresh same-current-owner resource pair required"}
    missing =''', 1)
source = source.replace('if not (EXECUTION / (mode + "_" + target + "_execution.json")).is_file()]',
                        'if not (arm_execution(mode) / (mode + "_" + target + "_execution.json")).is_file()]')
source = source.replace('        path = EXECUTION / (mode + "_" + target + "_execution.json")',
                        '        path = arm_execution(mode) / (mode + "_" + target + "_execution.json")', 1)
source = source.replace('        "missing": missing or [],', '        "evidence_owner_provenance_by_mode": OWNER_PROVENANCE,\n        "missing": missing or [],', 1)
tree = ast.parse(source)
main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
loop = next(node for node in main.body if isinstance(node, ast.For) and ast.get_source_segment(source, node.target) == "mode, target")
text = ast.get_source_segment(source, loop)
adapted = text.replace("EXECUTION /", "arm_directory /").replace('manifest[', 'arm_manifest[').replace('binding[', 'arm_binding[').replace('owner[', 'arm_owner[').replace("TOKEN", 'arm_owner["token"]')
first = 'for mode, target in PAIRS:'
adapted = adapted.replace(first, first + '''
        arm_directory = arm_execution(mode)
        arm_owner = historical["owner"] if mode == "smoke" else owner
        arm_manifest = historical["manifest"] if mode == "smoke" else manifest
        arm_binding = historical["binding"] if mode == "smoke" else binding''', 1)
source = source[:loop.col_offset + sum(len(line) for line in source.splitlines(keepends=True)[:loop.lineno - 1])] + adapted + "\n" + source[sum(len(line) for line in source.splitlines(keepends=True)[:loop.end_lineno]):]
# AST text replacement above includes the leading indentation already present before the node.
source = source.replace('    input_paths = [EXECUTION / name for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]',
    '''    input_paths = [EXECUTION / name for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    input_paths += [HISTORICAL_EXECUTION / name for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    input_paths.append(HISTORICAL_REVIEW)''', 1)
source = source.replace('    for (mode, target), actual in raw.items():\n', '''    for (mode, target), actual in raw.items():
        boundary_owner = historical["owner"] if mode == "smoke" else owner
''', 1)
source = source.replace('datetime.fromisoformat(owner["generated_at"]) <= datetime.fromisoformat(observed["observed_at"]) < datetime.fromisoformat(owner["deadline_at"])',
                        'datetime.fromisoformat(boundary_owner["generated_at"]) <= datetime.fromisoformat(observed["observed_at"]) < datetime.fromisoformat(boundary_owner["deadline_at"])')
source = source.replace('evidence = [ref(EXECUTION / (mode + "_" + target + "_execution.json")) for mode, target in PAIRS]',
                        'evidence = [ref(arm_execution(mode) / (mode + "_" + target + "_execution.json")) for mode, target in PAIRS]', 1)
source = source.replace('    evidence += [ref(PROOF),', '''    evidence += [ref(HISTORICAL_EXECUTION / name) for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    evidence.append(ref(HISTORICAL_REVIEW))
    evidence += [ref(PROOF),''', 1)
source = source.replace('"passed": not failures, "checks": CHECKS,', '"passed": not failures, "evidence_owner_provenance_by_mode": OWNER_PROVENANCE, "checks": CHECKS,', 1)
source = source.replace('"split": "train", "command": candidate["actual_train_command"]',
                        '"owner_provenance": OWNER_PROVENANCE["smoke"], "validated_historical_smoke_reused": True,\n              "split": "train", "command": candidate["actual_train_command"]', 1)
source = source.replace('"runtime_code_commit": PARENT, "runtime_root": manifest["root"],',
                        '"owner_provenance": OWNER_PROVENANCE["resources"],\n                  "runtime_code_commit": PARENT, "runtime_root": manifest["root"],', 1)
source = source.replace('"parent_commit": PARENT, "passed": True,',
                        '"parent_commit": PARENT, "passed": True, "evidence_owner_provenance_by_mode": OWNER_PROVENANCE,', 1)
source = source.replace('"ACTUAL_RESULTS_NORMALIZED_PENDING_ROOT_AND_INDEPENDENT_REVIEW"',
                        '"ACTUAL_HISTORICAL_SMOKE_AND_FRESH_RESOURCES_NORMALIZED_PENDING_ROOT_AND_INDEPENDENT_REVIEW"')
source = source.replace('    values = yaml.safe_load((NATIVE / "candidate.yaml").read_text(encoding="utf-8"))', '''
    new_version = read(NATIVE / "source_version_binding.json")
    old_version = read(HISTORICAL_ACTIVATION / "native/source_version_binding.json")
    check("identical_exact9_source_versions_across_evidence_owners",
          new_version["source_files"] == old_version["source_files"] == proof["source_files_exact9"]
          and new_version["code_commit"] == old_version["code_commit"] == SOURCE
          and new_version["parent_commit"] == old_version["parent_commit"] == PARENT)
    check("historical_and_current_same_native_YAML_bytes",
          sha(NATIVE / "candidate.yaml") == sha(HISTORICAL_ACTIVATION / "native/candidate.yaml") == manifest["candidate_config_sha256"])
    values = yaml.safe_load((NATIVE / "candidate.yaml").read_text(encoding="utf-8"))''', 1)
source = source.replace('"""Normalize only complete actual PSC results; never admit, enqueue or execute."""',
                        '"""Normalize historical validated PSC smoke plus fresh current-owner resources; never execute."""', 1)
compile(source, "normalize_psc_actual_results.py", "exec")
with (HERE / "normalize_psc_actual_results.py").open("x", encoding="utf8", newline="\n") as stream:
    stream.write(source)
print("Mixed-owner normalizer authored; no normalization or PASS result performed.")
