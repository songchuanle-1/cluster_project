"""Root-only exact-nine isolated LFT source save; default performs no operation."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, os, subprocess, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u

HERE = Path(__file__).resolve().parent
OUT = HERE / 'lft_version_prepare'
PREP = ROOT / 'pipeline/diagnostic_bundles/tick_34f4e385/lft_candidate_prepare'
REPO = ROOT / 'Cluster'
DEST = ROOT / 'pipeline/isolated_versions/lft_85772373'
BASE = '18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
CID = 'hierarchy-nonlinear-lifting-analysis-synthesis'
EXP = 'M227-LFT'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_lft'
CONFIG = 'configs/Quard/ctf_hcg_csort_lft/' + NAME + '.yaml'
PREP_SHA = '1210502d2454513983554dacf80293f7cd85fbdb55949b39f34e50b8fd01be92'
MANIFEST_SHA = '8cfb404d6291182a29d01f909295c6d3a782c436951ece71693e8fa1167bcf38'
BASELINE_SHA = '8bf6d685f58862e26ea18da484bab7166344e3bbc4b8087f5cb59249f64c86e9'
GIT = 'C:/Program Files (x86)/Git/cmd/git.exe'


def save(path, value):
    guard()
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())


def git(repo, *args):
    assert Path(repo).resolve() in (REPO.resolve(), DEST.resolve())
    guard()
    result = subprocess.run([GIT, '--no-optional-locks', '-c', 'core.autocrlf=false',
        '-c', 'core.eol=lf', '-c', 'core.fsmonitor=false', '-c', 'submodule.recurse=false',
        '-c', 'core.hooksPath=' + str(OUT / 'empty_hooks'), '-C', str(repo), *args],
        capture_output=True, timeout=120, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0',
        GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1', GIT_ALLOW_PROTOCOL='file'))
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-root', action='store_true')
    parser.add_argument('--preparation-sha256', default=PREP_SHA)
    parser.add_argument('--review-sha256')
    args = parser.parse_args()
    if not args.execute_root:
        print('DEFAULT_READ_ONLY_NO_GIT_NO_ARTIFACT'); return
    guard()
    assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS') == '0'
    assert args.preparation_sha256 == PREP_SHA == sha(PREP / 'preparation.json')
    assert args.review_sha256 and len(args.review_sha256) == 64
    peer = ROOT / 'pipeline/diagnostic_bundles/tick_34f4e385/lft_source_independent_review.json'
    assert sha(peer) == args.review_sha256
    prep, review = u.read(PREP / 'preparation.json'), u.read(peer)
    assert review['candidate_id'] == CID and review['experiment_id'] == EXP and review['material_concerns'] == []
    assert review['anchors']['preparation'] == u.ref(PREP / 'preparation.json')
    assert prep['candidate_id'] == CID and prep['experiment_id'] == EXP and prep['config'] == CONFIG
    assert all(prep[k] is None for k in ('code_commit', 'source_commit', 'source_parent_commit'))
    assert prep['base_reference_commit'] == BASE and prep['native'] == prep['resources'] == 'NOT_RUN'
    assert sha(PREP / 'source_manifest.json') == MANIFEST_SHA
    names = {'__init__.py', 'backbone.py', 'dec.py', 'hier_postprocess.py', 'loss.py', 'network.py', 'sample_model.py', 'nonlinear_lifting.py'}
    paths = {'framework/model/Quard_model/' + NAME + '/' + name for name in names} | {CONFIG}
    frozen = prep['source_files']
    assert len(frozen) == 9 and set(frozen) == paths and review['source_files_exact9'] == frozen
    assert frozen[CONFIG] == 'a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
    for name, value in prep['prepared_file_hashes'].items():
        path = (PREP / name).resolve()
        assert path.is_relative_to(PREP.resolve()) and sha(path) == value, name
    assert all(sha(PREP / 'staged_repository' / name) == value for name, value in frozen.items())
    assert not OUT.exists() and not DEST.exists(), 'Existing or partial attempt: read-only reconciliation only; never replay or clean'
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT)); assert lock is not None
    try:
        guard(); assert sha(HERE / 'protected_assets_before.json') == BASELINE_SHA
        baseline = u.read(HERE / 'protected_assets_before.json')
        assert baseline['head'] == BASE == u.SOURCE and len(baseline['files']) == 28 and len(baseline['protected_ledgers']) == 34
        def snapshot():
            guard()
            assert git(REPO, 'rev-parse', 'HEAD').decode().strip() == BASE
            assert git(REPO, 'status', '--porcelain=v1', '--untracked-files=all', '-z').hex() == baseline['status_hex']
            assert not git(REPO, 'diff', '--cached', '--name-only', '-z')
            assert all(sha(REPO / name) == value for name, value in baseline['files'].items())
            index = Path(git(REPO, 'rev-parse', '--git-path', 'index').decode().strip())
            if not index.is_absolute(): index = REPO / index
            assert sha(index) == baseline['index_sha256']
            ledgers = {name: sha(ROOT / 'pipeline' / name) for name in baseline['protected_ledgers']}
            assert ledgers == baseline['protected_ledgers']
            return {'primary_head': BASE, 'status_hex': baseline['status_hex'], 'index_sha256': sha(index),
                'protected_ledgers': ledgers, 'research_work_sha256': sha(ROOT / 'pipeline/research_work.json'),
                'memory_sha256': sha(ROOT / 'pipeline/codex_memory.md')}
        before = snapshot()
        def unchanged():
            guard(); assert snapshot() == before
            assert sha(PREP / 'preparation.json') == PREP_SHA and sha(peer) == args.review_sha256
            assert all(sha(PREP / 'staged_repository' / name) == value for name, value in frozen.items())
        result = subprocess.run([GIT, '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(REPO),
            'config', '--get-regexp', r'^(core\.hooksPath|filter\..*)$'], capture_output=True, timeout=20,
            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0'))
        allowed = {'filter.lfs.clean': 'git-lfs clean -- %f', 'filter.lfs.smudge': 'git-lfs smudge -- %f',
            'filter.lfs.process': 'git-lfs filter-process', 'filter.lfs.required': 'true'}
        assert result.returncode in (0, 1) and all(len(line.split(' ', 1)) == 2 and
            allowed.get(line.split(' ', 1)[0]) == line.split(' ', 1)[1] for line in result.stdout.decode().splitlines())
        for name in paths:
            assert name not in baseline['files'] and not (REPO / name).exists()
            assert not git(REPO, 'ls-tree', BASE, '--', name)
        unchanged(); OUT.mkdir(); (OUT / 'empty_hooks').mkdir()
        save(OUT / 'isolated_version_operation_intent.json', {'owner': EXPECTED,
            'recorded_at': datetime.now(timezone.utc).isoformat(), 'candidate_id': CID, 'experiment_id': EXP,
            'explicit_parent': BASE, 'source_preparation': u.ref(PREP / 'preparation.json'),
            'independent_source_review': u.ref(peer), 'source_files_exact9': frozen, 'protected_before': before,
            'scope': 'One local detached exact9A ordinary source commit only. No main/runtime ff, native, model revision, queue or launch. Partial attempt requires read-only reconciliation; no replay/cleanup.'})
        unchanged(); git(REPO, 'worktree', 'add', '--detach', str(DEST), BASE)
        assert git(DEST, 'rev-parse', 'HEAD').decode().strip() == BASE
        assert not git(DEST, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
        for name, value in frozen.items():
            unchanged(); path = (DEST / name).resolve(); assert path.is_relative_to(DEST.resolve()) and not path.exists()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as f:
                f.write((PREP / 'staged_repository' / name).read_bytes()); f.flush(); os.fsync(f.fileno())
            assert sha(path) == value
        ordered = tuple(sorted(paths)); assert not git(DEST, 'check-attr', '-a', '--', *ordered).strip()
        unchanged(); git(DEST, 'add', '--', *ordered)
        assert set(git(DEST, 'diff', '--cached', '--name-status').decode().splitlines()) == {'A\t' + name for name in paths}
        assert {name: hashlib.sha256(git(DEST, 'show', ':' + name)).hexdigest() for name in paths} == frozen
        unchanged(); output = git(DEST, 'commit', '-m', 'Save nonlinear lifting prototype on ELC parent (native pending)').decode('utf-8', errors='replace')
        code = git(DEST, 'rev-parse', 'HEAD').decode().strip()
        assert git(DEST, 'rev-list', '--parents', '-n', '1', code).decode().split() == [code, BASE]
        assert not git(DEST, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
        assert set(git(DEST, 'diff-tree', '--no-commit-id', '--name-status', '-r', code).decode().splitlines()) == {'A\t' + name for name in paths}
        blobs = {name: hashlib.sha256(git(DEST, 'show', code + ':' + name)).hexdigest() for name in paths}; assert blobs == frozen
        unchanged(); save(OUT / 'isolated_source_version.json', {'owner': EXPECTED,
            'recorded_at': datetime.now(timezone.utc).isoformat(), 'status': 'ISOLATED_LFT_SOURCE_COMMIT_ONLY_NATIVE_NOT_RUN',
            'candidate_id': CID, 'experiment_id': EXP, 'code_commit': code, 'parent_commit': BASE, 'worktree': str(DEST),
            'source_preparation': u.ref(PREP / 'preparation.json'), 'source_manifest': u.ref(PREP / 'source_manifest.json'),
            'native_protocol': u.ref(PREP / 'native_protocol.md'), 'independent_source_review': u.ref(peer),
            'frozen_source_files': frozen, 'committed_blob_sha256': blobs, 'source_file_count': 9, 'diff_exact9A': True,
            'isolated_worktree_and_index_clean': True, 'primary_HEAD_before': BASE, 'primary_HEAD_after': BASE,
            'runtime_expected_parent_commit': BASE, 'protected_before': before, 'protected_after': snapshot(),
            'primary_index_source28_and_all_current_lifecycle_bytes_unchanged': True,
            'original_null_source_metadata_unchanged': True, 'public_primary_or_runtime_promoted': False,
            'native_resources_remote_queue_launch': 'NOT_RUN', 'implementation_revision_created': False,
            'future_compatibility_scope': 'This source-only child is not tested or promoted. If actual main changes, preserve this proof and save/test a real compatible unchanged-nine version; no blind sibling fast-forward.',
            'commit_output': output})
        print(json.dumps({'code_commit': code, 'parent_commit': BASE, 'source_version': u.ref(OUT / 'isolated_source_version.json')}))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
