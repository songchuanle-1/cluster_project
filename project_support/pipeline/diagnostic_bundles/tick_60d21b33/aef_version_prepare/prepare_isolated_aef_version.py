"""Default-disabled root-only local AEF source save; no promotion or execution."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
REPO = ROOT / 'Cluster'
HERE = Path(__file__).resolve().parent
DEST = ROOT / 'pipeline/isolated_versions/aef_60d21b33'
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_150c2902/new_candidate_prepare'
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
CID = 'hierarchy-parent-antisymmetric-edge-flux'
EXP = 'M216-AEF'
MODEL = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aef'
CONFIG = 'configs/Quard/ctf_hcg_csort_aef/' + MODEL + '.yaml'
BASE = '026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
SOURCE_REFERENCE_ONLY = '4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
SOURCE_PREP_SHA = '9d6a03ba72c37b518d54f072400a4ecb3b042783b9e74e1d32a5169cfc50d990'
RECORD_SHA = '3898be398097d819ce8029112d6cd361bc97f462c57eadf9c7aacf4b161794f0'
PROTOCOL_SHA = '2db56f395f93ace93cf10c9ee79885fc53f661e14d2f95525317e95bb7deddde'
REVIEW_PATH = ROOT / 'pipeline/diagnostic_bundles/tick_150c2902/aef_source_topology_independent_review.json'
REVIEW_SHA = '27d6266fd98dcafd64b8351f7bc8143dad44d5c9a6a15d86f19fb408b6786aca'
BASELINE = ROOT / 'pipeline/diagnostic_bundles/tick_60d21b33/protected_assets_before.json'
BASELINE_SHA = '360ef79a37979fa44131b96c9c45611d08e156396bd1299f1d3675cecb7fd41d'
AUTH = {'path': 'pipeline/authorizations/experiment_first_20261021.json', 'sha256': '2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'}
EXPECTED_OWNER = {'token': '60d21b3324c94445b26d2ecb24a3ba65', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-26T16:09:41.027895+00:00', 'deadline_at': '2026-10-26T17:09:41.027895+00:00', 'context_sha256': '062a6fc0ddeba051336890fe88f3d2d0382d2036f7afc139f368da2568334c23', 'pending_sha256': 'c3ef64975c4c76f8c4febbcdc09867e2c133dbd465aab18a834238cafcf98cb4'}
DRAFT_EXECUTION_ENABLED = False


def require(value, message):
    if not value:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT.resolve()), 'Artifact outside this project')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def save(name, value):
    with (HERE / name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def owner_guard():
    require(set(EXPECTED_OWNER) == {'token', 'thread_id', 'generated_at', 'deadline_at', 'context_sha256', 'pending_sha256'}, 'Owner must have exactly six canonical fields')
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    mode = read(ROOT / 'pipeline/execution_mode.json')
    require({k: owner.get(k) for k in EXPECTED_OWNER} == EXPECTED_OWNER, 'Actual foreground owner changed')
    require(mode['mode'] == 'foreground' and mode['target_thread_id'] == os.environ.get('CODEX_THREAD_ID') == EXPECTED_OWNER['thread_id'], 'Actual root environment required; do not spoof identity')
    require(datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED_OWNER['deadline_at']), 'Original deadline expired')
    require(sha(ROOT / 'pipeline/headless/.tick_context.json') == EXPECTED_OWNER['context_sha256'] and sha(ROOT / 'pipeline/headless/.tick_context_state.next.json') == EXPECTED_OWNER['pending_sha256'], 'Current snapshot changed')
    require(sha(ROOT / 'pipeline/goal.json') == GOAL, 'Goal changed')
    policy = read(ROOT / 'pipeline/closure_policy.json')
    require(policy['enabled'] is True and policy['experiment_first']['enabled'] is True and policy['experiment_first']['authorization'] == AUTH and sha(ROOT / AUTH['path']) == AUTH['sha256'], 'Standing experiment-first source-save authorization changed')


def git(repo, *args):
    require(Path(repo).resolve() in (REPO.resolve(), DEST.resolve()), 'Git scope outside primary or exact isolated destination')
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1', GIT_ALLOW_PROTOCOL='file')
    command = ['git', '--no-optional-locks', '-c', 'core.autocrlf=false', '-c', 'core.eol=lf', '-c', 'core.fsmonitor=false', '-c', 'submodule.recurse=false', '-c', 'core.hooksPath=' + str(HERE / 'empty_hooks'), '-C', str(repo), *args]
    result = subprocess.run(command, capture_output=True, timeout=120, env=env)
    require(result.returncode == 0, result.stderr.decode('utf8', errors='replace'))
    return result.stdout


def source_details():
    require(sha(OLD / 'preparation.json') == SOURCE_PREP_SHA and sha(OLD / 'candidate_record.json') == RECORD_SHA and sha(OLD / 'native_protocol.md') == PROTOCOL_SHA, 'Frozen AEF source/record/protocol drift')
    source = read(OLD / 'preparation.json')
    require((source['candidate_id'], source['experiment_id'], source['source_file_count'], source['model_file_count']) == (CID, EXP, 9, 8), 'Original AEF identity/count differs')
    require(source['code_commit'] is None and source['source_commit'] is None and source['future_version_parent'] == source['base_reference_commit'] == SOURCE_REFERENCE_ONLY, 'Original null version/reference declarations must stay unchanged')
    require(len(source['prepared_file_hashes']) == 16, 'Original frozen16 map differs')
    for name, expected in source['prepared_file_hashes'].items():
        p = (OLD / name).resolve()
        require(p.is_relative_to(OLD.resolve()) and sha(p) == expected, 'Frozen prepared artifact differs')
    require(sha(REVIEW_PATH) == REVIEW_SHA, 'Original independent source review changed')
    review = read(REVIEW_PATH)
    require(review['candidate_id'] == CID and review['material_concerns'] == [] and review['anchors']['preparation'] == ref(OLD / 'preparation.json') and review['anchors']['native_protocol'] == ref(OLD / 'native_protocol.md'), 'Independent source-review binding differs')
    names = {'__init__.py', 'backbone.py', 'dec.py', 'hier_postprocess.py', 'loss.py', 'middle_flux.py', 'network.py', 'sample_model.py'}
    expected_paths = {'framework/model/Quard_model/' + MODEL + '/' + n for n in names} | {CONFIG}
    frozen = {name.removeprefix('staged_repository/'): h for name, h in source['prepared_file_hashes'].items() if name.startswith('staged_repository/')}
    require(set(frozen) == expected_paths and frozen == read(OLD / 'source_manifest.json')['source_files'], 'Only original exact8+YAML allowed')
    require(frozen[CONFIG] == 'a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a', 'Original native YAML changed')
    return frozen


def git_hooks_filters_guard():
    result = subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(REPO), 'config', '--get-regexp', r'^(core\.hooksPath|filter\..*)$'], capture_output=True, timeout=20, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0'))
    require(result.returncode in (0, 1), 'Cannot inspect Git hook/filter configuration')
    rows = [row.split(' ', 1) for row in result.stdout.decode().splitlines()]
    require(all(len(row) == 2 for row in rows), 'Malformed hook/filter configuration')
    configured = dict(rows)
    allowed = {'filter.lfs.clean': 'git-lfs clean -- %f', 'filter.lfs.smudge': 'git-lfs smudge -- %f', 'filter.lfs.process': 'git-lfs filter-process', 'filter.lfs.required': 'true'}
    require(all(k in allowed and allowed[k] == v for k, v in configured.items()), 'Nonstandard Git hooks/filters require review')
    hooks = Path(git(REPO, 'rev-parse', '--git-path', 'hooks').decode().strip())
    if not hooks.is_absolute():
        hooks = REPO / hooks
    require(not hooks.exists() or not any(p.is_file() and not p.name.endswith('.sample') for p in hooks.iterdir()), 'Active original hooks require review')


def primary_snapshot():
    require(sha(BASELINE) == BASELINE_SHA, 'Fresh protection baseline changed')
    baseline = read(BASELINE)
    require(baseline['head'] == BASE and baseline['index_empty'] is True and len(baseline['files']) == 28, 'Fresh primary/protected inventory differs')
    head = git(REPO, 'rev-parse', 'HEAD').decode().strip()
    require(head == BASE, 'Actual primary changed; refuse to guess or replace parent')
    status = git(REPO, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    require(status.hex() == baseline['status_hex'], 'Primary protected28 status changed')
    files = {n: sha(REPO / n) for n in baseline['files']}
    require(files == baseline['files'], 'Primary protected28 bytes changed')
    require(not git(REPO, 'diff', '--cached', '--name-only', '-z'), 'Primary index must remain empty')
    index = Path(git(REPO, 'rev-parse', '--git-path', 'index').decode().strip())
    if not index.is_absolute():
        index = REPO / index
    return {'HEAD': head, 'status_hex': status.hex(), 'index_sha256': sha(index), 'protected_files': files}


def lifecycle_snapshot():
    baseline = read(BASELINE)
    expected = baseline['protected_ledgers']
    require(len(expected) == 14, 'Fresh fourteen lifecycle ledgers required')
    require({n: sha(ROOT / 'pipeline' / n) for n in expected} == expected, 'Fresh protected lifecycle bytes changed')
    paths = list('pipeline/' + n for n in expected) + ['pipeline/research_work.json', 'pipeline/codex_memory.md', 'pipeline/closure_policy.json', 'pipeline/execution_mode.json', 'SERVERS.yaml']
    result = {n: sha(ROOT / n) for n in paths}
    queue = read(ROOT / 'pipeline/queue.json')
    target = [t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id') == 'M215-BEC']
    require(len(target) == 1 and target[0].get('status') == 'running' and target[0].get('code_commit') == BASE and target[0].get('pid') == 1558071 and target[0].get('gpu') in (0, '0') and target[0].get('launch_verified') is True, 'Preserve exact original BEC0 job; no lifecycle repair by source-save helper')
    work = read(ROOT / 'pipeline/research_work.json')
    matches = [c for c in work['candidates'] if c['id'] == CID]
    require(len(matches) == 1 and matches[0].get('code_commit') is None, 'AEF already versioned or missing; reconcile instead of replay')
    return result


def execute():
    owner_guard()
    frozen = source_details()
    require(DEST.resolve().is_relative_to((ROOT / 'pipeline/isolated_versions').resolve()) and not DEST.exists(), 'Exact isolated destination exists or escaped scope')
    require(not (HERE / 'isolated_version_operation_intent.json').exists() and not (HERE / 'isolated_source_version.json').exists(), 'Existing attempt requires read-only reconciliation; no replay')
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    require(lock is not None, 'Canonical project lock busy')
    try:
        owner_guard()
        git_hooks_filters_guard()
        before = primary_snapshot()
        ledgers = lifecycle_snapshot()
        require(not (set(frozen) & set(before['protected_files'])), 'Target paths overlap user files')
        for name in frozen:
            require(not git(REPO, 'ls-tree', BASE, '--', name) and not (REPO / name).exists(), 'AEF target already tracked or present; never overwrite')
        def mutation_guard():
            owner_guard()
            git_hooks_filters_guard()
            require(primary_snapshot() == before and lifecycle_snapshot() == ledgers and source_details() == frozen, 'Protected primary/lifecycle/source changed before mutation')
        save('isolated_version_before.json', {'recorded_at': datetime.now(timezone.utc).isoformat(), 'owner': EXPECTED_OWNER, 'primary': before, 'protected_ledgers': ledgers, 'fresh_protection_baseline': ref(BASELINE)})
        mutation_guard()
        save('isolated_version_operation_intent.json', {'recorded_at': datetime.now(timezone.utc).isoformat(), 'owner': EXPECTED_OWNER, 'operation': 'local detached worktree add; exact frozen9 copy/add; ordinary local commit', 'worktree': str(DEST), 'actual_parent_required': BASE, 'historical_source_reference_only': SOURCE_REFERENCE_ONLY, 'source_preparation': ref(OLD / 'preparation.json'), 'source_files': frozen, 'remote_or_primary_promotion': False, 'partial_policy': 'preserve original attempt and reconcile read-only; never reset/stash/clean/replay'})
        (HERE / 'empty_hooks').mkdir(exist_ok=False)
        DEST.parent.mkdir(exist_ok=True)
        mutation_guard()
        git(REPO, 'worktree', 'add', '--detach', str(DEST), BASE)
        require(git(DEST, 'rev-parse', 'HEAD').decode().strip() == BASE and not git(DEST, 'status', '--porcelain=v1', '-z', '--untracked-files=all'), 'Fresh isolated worktree is not clean exact parent')
        for name, expected in frozen.items():
            p = (DEST / name).resolve()
            require(p.is_relative_to(DEST.resolve()) and not p.exists(), 'Unsafe/existing isolated copy destination')
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open('xb') as stream:
                stream.write((OLD / 'staged_repository' / name).read_bytes())
            require(sha(p) == expected, 'Frozen copied bytes differ')
        require(not git(DEST, 'check-attr', '-a', '--', *sorted(frozen)).strip(), 'Target attributes/filter semantics require review')
        mutation_guard()
        git(DEST, 'add', '--', *sorted(frozen))
        require(set(git(DEST, 'diff', '--cached', '--name-status').decode().splitlines()) == {'A\t' + n for n in frozen}, 'Staged diff must be exact9A')
        require({n: hashlib.sha256(git(DEST, 'show', ':' + n)).hexdigest() for n in frozen} == frozen, 'Staged bytes differ from original frozen9')
        mutation_guard()
        output = git(DEST, 'commit', '-m', 'Add AEF antisymmetric middle-token edge flux (native pending)').decode('utf8', errors='replace')
        commit = git(DEST, 'rev-parse', 'HEAD').decode().strip()
        require(re.fullmatch('[0-9a-f]{40}', commit), 'New source commit has invalid SHA')
        require(git(DEST, 'rev-list', '--parents', '-n', '1', commit).decode().split() == [commit, BASE], 'New source must be exact single child of actual026c')
        require(not git(DEST, 'status', '--porcelain=v1', '-z', '--untracked-files=all') and not git(DEST, 'diff', '--cached', '--name-only', '-z'), 'Isolated committed worktree/index must be clean')
        blobs = {n: hashlib.sha256(git(DEST, 'show', commit + ':' + n)).hexdigest() for n in frozen}
        require(blobs == frozen and set(git(DEST, 'diff-tree', '--no-commit-id', '--name-status', '-r', commit).decode().splitlines()) == {'A\t' + n for n in frozen}, 'New commit is not exact frozen9 additions')
        owner_guard()
        after = primary_snapshot()
        require(after == before and lifecycle_snapshot() == ledgers and source_details() == frozen, 'Protected primary/lifecycle/old source changed; no rollback or retry')
        result = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'status': 'ISOLATED_AEF_SOURCE_COMMIT_ONLY_NATIVE_UNEXECUTED', 'candidate_id': CID, 'experiment_id': EXP, 'code_commit': commit, 'parent_commit': BASE, 'worktree': str(DEST), 'source_preparation': ref(OLD / 'preparation.json'), 'candidate_record': ref(OLD / 'candidate_record.json'), 'independent_source_review': ref(REVIEW_PATH), 'native_protocol': ref(OLD / 'native_protocol.md'), 'frozen_source_files': frozen, 'committed_blob_sha256': blobs, 'source_file_count': 9, 'diff_exact9A': True, 'isolated_worktree_and_index_clean': True, 'primary_HEAD_before': before['HEAD'], 'primary_HEAD_after': after['HEAD'], 'primary_HEAD_index_status_28_protected_bytes_unchanged': True, 'protected_ledgers_before': ledgers, 'protected_ledgers_after': lifecycle_snapshot(), 'old_source_code_commit': None, 'old_source_source_commit': None, 'old_source_future_parent_reference_unchanged': SOURCE_REFERENCE_ONLY, 'actual_new_parent_separately_recorded': BASE, 'native_resources_transport_queue_or_launch': 'NOT_RUN', 'remote_operations': False, 'primary_promotion_or_checkout': False, 'new_native_binding_or_lease': False, 'current_BEC_job_unchanged': True, 'commit_output': output, 'future_boundary': 'This is an isolated source version only. Do not promote primary/runtime or treat this save as native/admission permission. If actual primary changes, create and test a separately compatible version; never relabel earlier raw results. Old source9d6 null/reference4e8 declarations remain immutable.', 'material_concerns': []}
        save('isolated_source_version.json', result)
        print(json.dumps({'status': result['status'], 'code_commit': commit, 'parent': BASE, 'native': 'NOT_RUN'}))
    finally:
        lock.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root', action='store_true')
    args = parser.parse_args(argv)
    if not args.execute_root:
        print('DRAFT_DISABLED_NO_GIT_OR_SOURCE_WRITE')
        return 0
    require(DRAFT_EXECUTION_ENABLED is True, 'Draft disabled: root must review and materialize a separate single-flag execution copy')
    execute()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
