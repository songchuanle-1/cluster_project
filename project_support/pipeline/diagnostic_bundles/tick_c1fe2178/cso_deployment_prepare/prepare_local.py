"""Default NOP. Local-only adaptation of retained6b canonical safe_sync preparation."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/project/cluster_project').resolve()
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_6b23467a/m235_deployment_prepare'
MAIN = ROOT / 'Cluster'
DETACHED = ROOT / 'pipeline/isolated_versions/m236_cso_integrated_7caf419d'
SOURCE = '5413102c57b526035f3920b5e7a81f3b58ad764d'
PARENT = 'b1e639b3ceb14bb5c65d9f81a084d41c834b951c'
NATIVE = 'af45707d7b6089f764843337c5f88af285383f88'
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def save(name, value):
    with (HERE / name).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def git(code, *args, expected_rc=0):
    command = ['git', '--no-optional-locks', '-c', 'safe.directory=' + Path(code).resolve().as_posix(),
               '-c', 'core.fsmonitor=false', '-C', str(code), *args]
    run = subprocess.run(command, capture_output=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), timeout=30)
    assert run.returncode == expected_rc, run.stderr.decode('utf8', 'replace')
    return run.stdout


NATIVE_GUARD = '''
def current_native_gate_binding(receipt):
    """Future real gates only; no prospective template may authorize safe_sync."""
    version_path = TICK / "cso_version_binding/version_bound_evidence.json"
    normalized_path = TICK / "cso_version_binding/native_smoke.version_bound.json"
    version, normalized = read(version_path), read(normalized_path)
    assert receipt.get("normalization_owner", receipt.get("owner")) == OWNER
    for field, path in (("version_association", version_path), ("native_smoke", normalized_path)):
        item = receipt[field]
        assert (ROOT / item["path"]).resolve() == path.resolve() and sha(path) == item["sha256"]
    assert version["owner"] == normalized["normalization_owner"] == OWNER
    assert version["passed"] is True and version["material_concerns"] == []
    assert version["kind"] == "DERIVED_EXACT_BYTE_VERSION_ASSOCIATION_NOT_NEW_EXECUTION"
    assert version["associated_code_commit"] == normalized["code_commit"] == SOURCE
    assert version["actual_execution_code_commit"] == normalized["original_execution_code_commit"] == "af45707d7b6089f764843337c5f88af285383f88"
    assert version["actual_source_parent_commit"] == "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
    assert version["actual_runtime_HEAD"] == normalized["runtime_original_parent_commit"] == PARENT
    assert version["files_exact9_sha256"] == read(HERE / "baseline.json")["source_files_exact9"]
    assert version["new_execution_claimed"] is False and version["raw_actual_source_owner_or_metadata_modified"] is False
    inputs = {}
    for item in version["inputs"]:
        path = (ROOT / item["path"]).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha(path) == item["sha256"]
        inputs[path] = item["sha256"]
    assert sha(Path(version["producer"]["path"]) if Path(version["producer"]["path"]).is_absolute() else ROOT / version["producer"]["path"]) == version["producer"]["sha256"]
    for mode, flag in (("smoke", "native_smoke_passed"), ("resources", "resource_gate_passed")):
        actual_path = TICK / ("cso_native_execution/run_" + mode + "_candidate_actual.json")
        assert inputs[actual_path.resolve()] == sha(actual_path)
        record = read(actual_path)
        assert record["owner"] == OWNER and record["certainty"] == "terminal" and record["returncode"] == 0
        observation = record["observation"]
        assert json.loads(record["stdout"]) == observation
        assert observation["certainty"] == "terminal" and observation["returncode"] == 0
        result = observation["result"]
        assert result["execution_completed"] is True and result["owner"] == OWNER
        assert result["mode"] == mode and result["target"] == "candidate"
        assert result["code_commit"] == "af45707d7b6089f764843337c5f88af285383f88"
        assert result["physical_gpu"] == 0 and result["gpu_uuid"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
        if mode == "smoke":
            assert result["optimizer_steps"] == result["native_criterion_backwards"] == result["native_loss_forwards"] == 2
            assert result["native_smoke_checks_passed"] is True and result["backward_finite"] is True
            assert result["original_common_initialization_comparison"]["passed"] is True
            assert result["original_common_initialization_comparison"]["candidate_tensor_count"] == 841
            assert len(result["native_tracked_after_hash"]) == 9 and result["native_tracked_each_parameter_updated"] is True
        else:
            assert (result["batch_size"], result["lang_num_max"], result["warmup"], result["repeat"]) == (1, 1, 20, 100)
            assert result["profile"]["within10G"] is True and result["source_body_executed_without_replacement"] is True
        reviews = []
        for path in inputs:
            if path.is_relative_to(TICK.resolve()) and path.suffix == ".json":
                value = read(path)
                if value.get("actual_sha256") == sha(actual_path) and value.get(flag) is True:
                    reviews.append(value)
        assert len(reviews) == 1
        peer = reviews[0]
        assert peer["owner"] == OWNER and peer["passed"] is True and peer["material_concerns"] == []
        assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/cso_readiness", "/root/cso_native_ops")
    review_item = receipt["version_association_review"]
    review_path = (ROOT / review_item["path"]).resolve()
    assert review_path.is_relative_to(TICK.resolve()) and sha(review_path) == review_item["sha256"]
    peer = read(review_path)
    assert peer["owner"] == OWNER and peer["passed"] is True and peer["material_concerns"] == []
    assert peer["reviewer_thread_id"] not in (OWNER["thread_id"], "/root", "/root/cso_readiness", "/root/cso_native_ops")
    assert peer["version_bound_evidence_sha256"] == sha(version_path) and peer["normalized_smoke_sha256"] == sha(normalized_path)
    assert peer["associated_commit"] == SOURCE and peer["commit_parent"] == PARENT
    assert peer["exact_nine_added_blobs_verified"] is True and peer["commit_worktree_clean"] is True


def scoped_safe_sync(closure, server, strict_ssh):
    """Keep canonical safe_sync untouched; add only process-local exact worktree trust."""
    previous_count = os.environ.get("GIT_CONFIG_COUNT")
    count = int(previous_count or "0")
    key, value = "GIT_CONFIG_KEY_" + str(count), "GIT_CONFIG_VALUE_" + str(count)
    previous_key, previous_value = os.environ.get(key), os.environ.get(value)
    try:
        os.environ["GIT_CONFIG_COUNT"] = str(count + 1)
        os.environ[key] = "safe.directory"
        os.environ[value] = DETACHED.resolve().as_posix()
        return closure.safe_sync(ROOT, DETACHED, server, strict_ssh)
    finally:
        for name, old in (("GIT_CONFIG_COUNT", previous_count), (key, previous_key), (value, previous_value)):
            if old is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old


'''


def prepare():
    assert sys.dont_write_bytecode and not sys.flags.optimize
    owner = read(TICK / 'current_owner_binding.json')
    assert owner['token'] == 'c1fe217800894083b65baac45f79aa83'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    before = read(TICK / 'integrity_before.json')
    assert before['owner'] == owner
    old_baseline = read(OLD / 'baseline.json')
    old_frozen = read(OLD / 'FROZEN.json')
    old_helper = OLD / 'deploy_m235_once.py'
    assert sha(old_helper) == old_frozen['files']['deploy_m235_once.py']
    proof_path = ROOT / 'pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json'
    proof = read(proof_path)
    assert sha(proof_path) == '41dd72acfb62ff4fc7ff690f751c820fca80536dc3b5b552a62c704ea5a99c7a'
    assert proof['commit'] == SOURCE and proof['parent_commit'] == PARENT and proof['native_source_commit'] == NATIVE
    files = proof['files_exact9_sha256']
    assert len(files) == 9
    assert git(MAIN, 'rev-parse', 'HEAD').decode().strip() == before['local_main_HEAD']
    index = Path(git(MAIN, 'rev-parse', '--git-path', 'index').decode().strip())
    if not index.is_absolute():
        index = MAIN / index
    assert sha(index) == before['index_sha256']
    protected = {name: sha(MAIN / name) for name in before['dirty_sha256']}
    assert len(protected) == 37 and protected == before['dirty_sha256']
    assert protected == {**old_baseline['dirty_files_exact28'], **old_baseline['working_tree_r0_files_exact9']}
    index_entries = hashlib.sha256(git(MAIN, 'ls-files', '--stage', '-z')).hexdigest()
    porcelain = hashlib.sha256(git(MAIN, 'status', '--porcelain=v1', '--untracked-files=all', '-z')).hexdigest()
    checkout = []
    for location, commit, parent in ((DETACHED, SOURCE, PARENT), (Path(proof['native_source_worktree']), NATIVE, proof['native_source_parent_commit'])):
        assert git(location, 'rev-parse', 'HEAD').decode().strip() == commit
        git(location, 'symbolic-ref', '-q', 'HEAD', expected_rc=1)
        assert git(location, 'status', '--porcelain=v1', '--untracked-files=all', '-z') == b''
        assert git(location, 'rev-list', '--parents', '-n', '1', commit).decode().split() == [commit, parent]
        changes = git(location, 'diff-tree', '--no-commit-id', '--name-status', '-r', commit).decode().splitlines()
        assert len(changes) == 9 and set(changes) == {'A\t' + name for name in files}
        observed_blobs = {}
        for name, expected in files.items():
            assert sha(location / name) == hashlib.sha256(git(location, 'cat-file', 'blob', commit + ':' + name)).hexdigest() == expected
            blob = git(location, 'rev-parse', commit + ':' + name).decode().strip()
            assert blob == proof['blob_ids'][name]
            observed_blobs[name] = blob
        checkout.append({'worktree': str(location), 'commit': commit, 'parent': parent, 'clean': True,
                         'only_nine_additions': True, 'blob_ids': observed_blobs})
    assert sha(ROOT / 'SERVERS.yaml') == before['servers_sha256']
    baseline = dict(old_baseline, owner=owner, main_HEAD=before['local_main_HEAD'], real_index_sha256=sha(index),
                    real_index_entries_sha256=index_entries, main_porcelain_sha256=porcelain,
                    dirty_files_exact28={k: protected[k] for k in old_baseline['dirty_files_exact28']},
                    working_tree_r0_files_exact9={k: protected[k] for k in old_baseline['working_tree_r0_files_exact9']},
                    source_files_exact9=files, source_commit=SOURCE, source_parent_commit=PARENT,
                    runtime_original_parent_commit=PARENT, detached_checkout=str(DETACHED),
                    SERVERS_sha256=sha(ROOT / 'SERVERS.yaml'), captured_at=datetime.now(timezone.utc).isoformat(),
                    current_integrity_before=ref(TICK / 'integrity_before.json'), legacy_baseline=ref(OLD / 'baseline.json'),
                    source_integrated_exact_bytes_equal_native_source=NATIVE)
    save('baseline.json', baseline)
    checkout_proof = {'owner': owner, 'recorded_at': datetime.now(timezone.utc).isoformat(), 'source_commit': SOURCE,
                      'source_parent_commit': PARENT, 'detached_checkout': str(DETACHED), 'existing_checkout_reused': True,
                      'new_checkout_performed': False, 'clean': True, 'files_exact9': files, 'current_git_observations': checkout,
                      'original_commit_proof': ref(proof_path), 'native_source_commit_preserved': NATIVE,
                      'source9_rebuilt_or_recommitted': False, 'native_gate_claimed': False}
    save('existing_checkout_proof.json', checkout_proof)
    helper = old_helper.read_text(encoding='utf8')
    replacements = {
        'm235_deployment_execution': 'cso_deployment_execution',
        'pipeline/isolated_versions/m235_sinc_79656807': 'pipeline/isolated_versions/m236_cso_integrated_7caf419d',
        'SOURCE = "b1e639b3ceb14bb5c65d9f81a084d41c834b951c"': 'SOURCE = "' + SOURCE + '"',
        'PARENT = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"': 'PARENT = "' + PARENT + '"',
        'ctf_hcg_csort_sinc': 'ctf_hcg_csort_cso', 'M235-SINC': 'M236-CSO',
        'fine-leaf-geometric-simplex-incidence-composition': 'fine-leaf-full-covariance-shape-composition',
        '"6b23467adea64dd3b75c4a2b6535c5da"': json.dumps(owner['token']),
        '"2026-11-10T09:13:21.378843+00:00"': json.dumps(owner['generated_at']),
        '"2026-11-10T10:13:21.378843+00:00"': json.dumps(owner['deadline_at']),
        '"6aa1ba65decf72579d62b1f0ad19f097241ba1728706fe28706287b6729ab2b9"': json.dumps(owner['context_sha256']),
        '"d27b1af1f62754d25a631dddc5fefd5a23612eaae1a61fc8148ae3389b3c2697"': json.dumps(owner['pending_sha256']),
        '[GIT, "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(code), *args]': '[GIT, "--no-optional-locks", "-c", "safe.directory=" + Path(code).resolve().as_posix(), "-c", "core.fsmonitor=false", "-C", str(code), *args]',
        '[GIT, "--no-optional-locks", "-C", str(DETACHED), "symbolic-ref"': '[GIT, "--no-optional-locks", "-c", "safe.directory=" + DETACHED.resolve().as_posix(), "-C", str(DETACHED), "symbolic-ref"',
        'assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"': 'assert sys.dont_write_bytecode and not sys.flags.optimize and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"',
        '    assert receipt["profile"] == "experiment_first"\n': '    assert receipt["profile"] == "experiment_first"\n    current_native_gate_binding(receipt)\n',
        '"/root/fresh_ops", "01a1ba7b-e7ea-7e33-8551-b1fdfce9cdf5")': '"/root/fresh_ops", "/root/cso_readiness", "/root/cso_native_ops")',
        'assert closure.safe_sync(ROOT, DETACHED, server, strict_ssh) is True': 'assert scoped_safe_sync(closure, server, strict_ssh) is True',
    }
    for old, new in replacements.items():
        assert old in helper, old
        helper = helper.replace(old, new)
    helper = helper.replace('\nREMOTE_OBSERVE = r', '\n' + NATIVE_GUARD + '\nREMOTE_OBSERVE = r', 1)
    assert 'm235_' not in helper and 'M235-SINC' not in helper and 'ctf_hcg_csort_sinc' not in helper
    ast.parse(helper)
    (HERE / 'deploy_cso_once.py').write_text(helper, encoding='utf8', newline='\n')
    contract = read(OLD / 'sync_output_contract.json')
    contract.update(owner=owner, actual_path=str(TICK / 'cso_deployment_execution/sync.actual.json'),
                    canonical_result_path=str(TICK / 'cso_deployment_execution/sync_result.json'),
                    intent_path=str(TICK / 'cso_deployment_execution/sync_intent.json'), source_commit=SOURCE,
                    expected_runtime_before=PARENT, source_files_exact9=files)
    save('sync_output_contract.json', contract)
    save('independent_review_contract.json', {'owner': owner, 'status': 'NOT_REVIEWED_NOT_AUTHORIZED_TO_EXECUTE',
        'required_fields': ['passed=true', 'owner6', 'material_concerns=[]', 'distinct reviewer_thread_id', 'FROZEN_sha256',
                            'helper_sha256', 'baseline_sha256', 'source_commit', 'admission_sha256 (real CLI SHA)',
                            'source_review_passed=true', 'canonical_sync_review_passed=true'],
        'source_only_review_may_prepare': True, 'source_only_review_grants_execution': False,
        'actual_admission_and_version_reviews_required_at_execution': True})
    validation = {'owner': owner, 'scope': 'LOCAL_STATIC_PREPARATION_ONLY_NOT_NATIVE_SYNC_OR_ADMISSION',
                  'AST_parse': True, 'actual_source9_git_objects_and_worktrees_read': True,
                  'main_HEAD_index_indexentries_porcelain_protected37_verified': True,
                  'canonical_safe_sync_called_only_inside_future_execute_guard': True,
                  'native_TRAIN2': 'NOT_RUN_BY_PREPARATION_AUTHOR', 'resources': 'NOT_RUN_BY_PREPARATION_AUTHOR',
                  'sync': 'NOT_RUN', 'Torch_imported': False, 'SSH_performed': False,
                  'training_started': False, 'scientific_admission': False}
    save('software_validation.json', validation)
    static_files = [path for path in HERE.iterdir() if path.is_file() and path.name != 'FROZEN.json']
    anchors = {'historical_deployment_source': ref(old_helper), 'historical_deployment_freeze': ref(OLD / 'FROZEN.json'),
               'source_commit_proof': ref(proof_path),
               'source_commit_review': ref(ROOT / 'pipeline/diagnostic_bundles/tick_7caf419d/peer_review/cso_integration_independent_review.json'),
               'current_integrity_before': ref(TICK / 'integrity_before.json'),
               'closure': ref(SKILL / 'closure.py'), 'source_integrity': ref(SKILL / 'source_integrity.py'),
               'monitor': ref(SKILL / 'pipeline_monitor.py'), 'policy': ref(ROOT / 'pipeline/closure_policy.json'),
               'goal': ref(ROOT / 'pipeline/goal.json'), 'servers': ref(ROOT / 'SERVERS.yaml'),
               'base_conda': ref(ROOT / 'pipeline/runtime/server4_conda_4ca73fba.sh')}
    frozen = {'schema_version': 1, 'owner': owner, 'author_thread_id': '/root/cso_readiness',
              'recorded_at': datetime.now(timezone.utc).isoformat(), 'source_commit': SOURCE, 'source_parent_commit': PARENT,
              'runtime_base': PARENT, 'detached_checkout': str(DETACHED), 'phase': 'sync_only_existing_checkout',
              'helper_sha256': sha(HERE / 'deploy_cso_once.py'), 'baseline_sha256': sha(HERE / 'baseline.json'),
              'files': {p.name: sha(p) for p in static_files}, 'anchors': anchors,
              'admission_binding': 'DYNAMIC_REAL_CLI_PATH_AND_SHA_REQUIRED_NOT_FROZEN_AS_PLACEHOLDER',
              'status': 'SOURCE_ONLY_FROZEN_NOT_RUN_REQUIRES_REAL_NATIVE_RESOURCE_VERSION_REVIEWS_RECEIPT_AND_DISTINCT_SYNC_REVIEW',
              'author_executed_SSH_Torch_GPU': False, 'shared_ledger_or_SERVERS_modified': False, 'historical_freezes_modified': False}
    save('FROZEN.json', frozen)
    print(json.dumps({'status': frozen['status'], 'helper_sha256': frozen['helper_sha256'], 'FROZEN_sha256': sha(HERE / 'FROZEN.json')}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-local', action='store_true')
    args = parser.parse_args()
    if not args.prepare_local:
        print(json.dumps({'status': 'DEFAULT_NOP_LOCAL_PREPARATION_NOT_EXECUTED'}))
        return
    prepare()


if __name__ == '__main__':
    main()
