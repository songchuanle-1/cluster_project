"""Commit only the nine independently reviewed, static-checked PSBR additions."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/project/cluster_project')
P = ROOT / 'pipeline'
B = P / 'diagnostic_bundles/tick_8fafa3d4/psbr_prepare'
REPO = ROOT / 'Cluster'
TOKEN = '8fafa3d4ebcb48e7ba3436e084f6ee9f'
PARENT = '9e543af623acd7fa9bd4a3f81ce79c932e98774a'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True, encoding='utf-8').strip()


def current_status():
    output = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=REPO, text=True, encoding='utf-8')
    return {(line[:2], line[3:]) for line in output.splitlines()}


owner = load(P / 'headless/.foreground.lockdir/owner.json')
assert owner['token'] == TOKEN and owner['thread_id'] == os.environ['CODEX_THREAD_ID']
assert load(P / 'execution_mode.json')['target_thread_id'] == owner['thread_id']
assert dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(owner['deadline_at'])
assert sha(P / 'headless/.tick_context.json') == owner['context_sha256']
assert sha(P / 'authorizations/experiment_first_20261021.json') == '2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'
assert not (B / 'version.json').exists()
assert git('rev-parse', 'HEAD') == PARENT and not git('diff', '--cached', '--name-only')

static = load(B / 'static_validation.json')
assert static['status'] == 'STATIC_CHECKS_PASS_NATIVE_NOT_RUN' and static['check_count'] == 50
assert len(static['checks']) == 50 and all(v is True for v in static['checks'].values())
source_hashes = static['source_hashes']
assert len(source_hashes) == 9
assert sum(name.endswith('.py') for name in source_hashes) == 8
assert sum(name.endswith('.yaml') for name in source_hashes) == 1
for name, expected in source_hashes.items():
    assert 'ctf_hcg_csort_psbr/' in name and sha(REPO / name) == expected, name
    assert not git('ls-files', '--', name), name
for name in ['preparation.json', 'independent_review.json', 'constraints_review.json']:
    assert (B / name).is_file(), name
assert sha(B / 'preparation.json') == 'f1973052931bb76bb8a4087e1d1aff5d6e5051f2859227d4fbc74a7827020128'
assert sha(B / 'independent_review.json') == '2c1edad5579d13aeb36fcd0ccf78efffeb64731c9a2d98ec9a54652b560fd834'
assert sha(B / 'constraints_review.json') == '8202697d1a8113ac714e3245c3850fe8873839fc28d396762abb46e3c66ff917'
for name in ['preparation.json', 'independent_review.json', 'constraints_review.json']:
    review = load(B / name)
    assert review['source_hashes'] == source_hashes, name
    assert not review.get('blocking_findings', []), name

protected = load(P / 'diagnostic_bundles/tick_16b87793/protected_worktree_before.json')['protected_existing_worktree']
protected_status = {(x['status'], x['path']) for x in protected}
assert len(protected_status) == 28
for x in protected:
    assert sha(REPO / x['path']) == x['sha256'], x['path']
assert current_status() == protected_status | {('??', name) for name in source_hashes}

subprocess.run(['git', 'add', '--', *source_hashes], cwd=REPO, check=True, capture_output=True)
staged = git('diff', '--cached', '--name-status').splitlines()
assert {tuple(line.split('\t')) for line in staged} == {('A', name) for name in source_hashes}
subprocess.run(['git', 'commit', '-m', 'Add parent-segmented bidirectional middle-token recurrence'], cwd=REPO, check=True, capture_output=True)
commit = git('rev-parse', 'HEAD')
assert git('rev-parse', 'HEAD^') == PARENT
actual = git('diff-tree', '--no-commit-id', '--name-status', '-r', 'HEAD').splitlines()
assert {tuple(line.split('\t')) for line in actual} == {('A', name) for name in source_hashes}
for name, expected in source_hashes.items():
    committed = subprocess.check_output(['git', 'show', f'{commit}:{name}'], cwd=REPO)
    assert hashlib.sha256(committed).hexdigest() == expected == sha(REPO / name)
for x in protected:
    assert sha(REPO / x['path']) == x['sha256']
assert current_status() == protected_status
assert not git('diff', '--cached', '--name-only')

record = {
    'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'candidate_id': 'hierarchy-parent-segmented-bidirectional-token-state',
    'experiment_id': 'M209-PSBR', 'code_commit': commit, 'parent_commit': PARENT,
    'operation': 'LOCAL_ONLY_NINE_ADDED_SOURCE_YAML_FILES',
    'authorization': ref(P / 'authorizations/experiment_first_20261021.json'),
    'tested_scope': '50 CPU static checks and independent source/constraint review only; no torch/model/native/GPU/resource execution',
    'static_validation': ref(B / 'static_validation.json'),
    'independent_review': ref(B / 'independent_review.json'),
    'constraints_review': ref(B / 'constraints_review.json'),
    'preparation': ref(B / 'preparation.json'), 'source_hashes': source_hashes,
    'all_nine_committed_bytes_match_reviewed_sources': True,
    'all_28_existing_worktree_files_and_status_unchanged': True,
    'git_index_empty': True, 'push': False, 'sync': False, 'train': False,
    'native_smoke': 'NOT_RUN', 'resources': 'NOT_RUN', 'efficacy': 'UNKNOWN',
}
(B / 'version.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'code_commit': commit, 'files_added': 9, 'protected_existing': 28, 'version': ref(B / 'version.json'), 'native': 'NOT_RUN'}, ensure_ascii=False))
