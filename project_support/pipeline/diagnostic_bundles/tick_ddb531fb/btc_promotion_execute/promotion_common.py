"""Private disabled promotion draft. No effect on import; no authority is created."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/project/cluster_project')
PRIVATE = Path(__file__).resolve().parent
TICK = PRIVATE.parent
CODE = ROOT / 'Cluster'
BASE = '43dce016c1a1713c2a5dab7061810dc2efde8954'
TESTED = '00e2b18c6b8d568a64edb496e6979d766440883c'
EXP = 'M211-BTC'
CID = 'hierarchy-parent-binary-tree-complement-composition'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc'
CONFIG = 'configs/Quard/ctf_hcg_csort_btc/' + NAME + '.yaml'
TOKEN = 'ddb531fb89824389b3b2e2df5779a5ef'
EXPECTED_OWNER = {
    'token': TOKEN, 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253',
    'generated_at': '2026-10-24T16:06:44.679939+00:00',
    'deadline_at': '2026-10-24T17:06:44.679939+00:00',
    'context_sha256': 'e3eeb6a2ab5a8f7f840e6224e4fecc29bcc4c2ee81b7c6e0377e286c0e8f6ad4',
    'pending_sha256': '43e0cce243f02e398f89c66a27122cb746cdc3b0e2bdcb720c8be8c04d367c84',
}
# Root must review this draft and bind actual reviewed evidence; never invent hashes.
DRAFT_EXECUTION_ENABLED = True
SEMANTIC_REVIEW_PATH = 'pipeline/diagnostic_bundles/tick_ddb531fb/btc_execution_review_preparation/actual_four_result_review.json'
SEMANTIC_REVIEW_SHA = '15e19fbfd01268b8142ea50073d5e3046066e178d072a38c0abb19a2ba68d9a6'
INDEPENDENT_REVIEW_PATH = 'pipeline/diagnostic_bundles/tick_ddb531fb/btc_native_resource_independent_review.json'
INDEPENDENT_REVIEW_SHA = 'dc03f6cd308f598baab970e06483ad333d963b1f1efbfc4944e1f7cef8204bbd'
INDEPENDENT_STATUS = 'FOUR_ACTUAL_BTC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
PAIRS = [('smoke', 'champion'), ('smoke', 'candidate'),
         ('resources', 'champion'), ('resources', 'candidate')]
PROTECTED_BASELINE = ROOT / 'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json'
PROTECTED_BASELINE_SHA = 'deb2f6e1093be710fbbae886b4008c187b2e6b63d63276bfb47706b36b4be142'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text('utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'Evidence outside project')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def execution_enabled(execute_root):
    require(execute_root and DRAFT_EXECUTION_ENABLED is True,
            'DRAFT_DISABLED: no ff/dispatch or shared/remote action is enabled')
    for path, expected in [(SEMANTIC_REVIEW_PATH, SEMANTIC_REVIEW_SHA),
                           (INDEPENDENT_REVIEW_PATH, INDEPENDENT_REVIEW_SHA)]:
        require(path is not None and isinstance(expected, str) and
                re.fullmatch(r'[0-9a-f]{64}', expected), 'Actual review path/SHA must be bound by root')


def owner_guard():
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    require({k: owner.get(k) for k in EXPECTED_OWNER} == EXPECTED_OWNER,
            'Original six-field owner binding changed; never extend this draft')
    mode = read(ROOT / 'pipeline/execution_mode.json')
    require(mode.get('mode') == 'foreground' and
            owner['thread_id'] == mode.get('target_thread_id') == os.environ.get('CODEX_THREAD_ID'),
            'Actual root/environment/mode mismatch; do not override identity')
    require(datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at']), 'Original deadline expired')
    require(sha(ROOT / 'pipeline/headless/.tick_context.json') == owner['context_sha256'] and
            sha(ROOT / 'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256'],
            'Original context/pending changed')
    require(sha(ROOT / 'pipeline/goal.json') == GOAL, 'Goal changed')
    return owner


def git_bytes(*args):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(CODE), *args],
                                   env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))


def git(*args):
    return git_bytes(*args).decode('utf-8').strip()


def protected():
    require(sha(PROTECTED_BASELINE) == PROTECTED_BASELINE_SHA, 'Protected baseline changed')
    rows = read(PROTECTED_BASELINE)['protected_existing_worktree']
    require(len(rows) == 28, 'Wrong protected inventory')
    status = [x for x in git_bytes('status', '--porcelain=v1', '-z', '-uall').split(b'\0') if x]
    actual = {(x[:2].decode(), x[3:].decode()) for x in status}
    require(actual == {(r['status'], r['path']) for r in rows}, 'Protected28 status set changed')
    require(all(sha(CODE / r['path']) == r['sha256'] for r in rows), 'Protected28 bytes changed')
    require(not git_bytes('diff', '--cached', '--name-only', '-z'), 'Index is not empty')
    return rows


def reviewed_four_raw():
    execution_enabled(True)
    owner_guard()
    local_path = (ROOT / SEMANTIC_REVIEW_PATH).resolve()
    independent_path = (ROOT / INDEPENDENT_REVIEW_PATH).resolve()
    require(local_path.is_relative_to(ROOT) and independent_path.is_relative_to(ROOT), 'Review path escapes project')
    require(sha(local_path) == SEMANTIC_REVIEW_SHA and sha(independent_path) == INDEPENDENT_REVIEW_SHA,
            'Actual frozen review changed')
    local, independent = read(local_path), read(independent_path)
    observations = local.get('observations') or {}
    require(local.get('review_status') == 'RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' and
            observations.get('native_semantics_and_pairing_checked') is True and
            observations.get('resource_protocol_checked') is True and
            local.get('standard_PASS_receipt_queue_written') is False,
            'Actual local raw semantic review did not pass its recorded schema')
    require(independent.get('status') == INDEPENDENT_STATUS and
            independent.get('material_concerns') == [], 'Actual independent semantic review did not pass')
    for review in (local, independent):
        require((review.get('candidate_id'), review.get('code_commit'), review.get('goal_sha256')) ==
                (CID, TESTED, GOAL), 'Review candidate/version/goal mismatch')
    require(local.get('id') == EXP, 'Local review experiment mismatch')
    raw_refs = independent.get('raw_results', [])
    require(len(raw_refs) == 4, 'Independent review must bind all four original results')
    hashes = {}
    for mode, target in PAIRS:
        path = TICK / 'btc_execution' / (mode + '_' + target + '_execution.json')
        matches = [r for r in raw_refs if r.get('mode') == mode and r.get('target') == target]
        require(len(matches) == 1, 'Missing/ambiguous independently reviewed pair')
        item = matches[0]
        require((ROOT / item['execution_path']).resolve() == path.resolve() and
                sha(path) == item['execution_sha256'], 'Original independently reviewed raw artifact drift')
        envelope = read(path)
        require(envelope.get('certainty') == 'terminal' and envelope.get('returncode') == 0,
                'A real original execution is not complete/rc0')
        result = envelope.get('result') or {}
        package = 'framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
        if target == 'candidate':
            package += '_btc'
        require(result.get('execution_completed') is True and
                (result.get('candidate_id'), result.get('code_commit'), result.get('goal_sha256'),
                 result.get('mode'), result.get('target'), result.get('model_package')) ==
                (CID, TESTED, GOAL, mode, target, package), 'Raw result identity/completion mismatch')
        require(item['result_sha256'] == envelope.get('result_sha256') and
                item['request_id'] == envelope['identity']['request_id'], 'Original request/result proof mismatch')
        hashes[mode + '_' + target] = sha(path)
    manifest = read(TICK / 'btc_execution/native_manifest.json')
    require(manifest['candidate_id'] == CID and manifest['code_commit'] == TESTED and
            manifest['goal_sha256'] == GOAL and manifest['current_token'] == TOKEN,
            'Actual manifest candidate/version/original token mismatch')
    binding = read(TICK / 'btc_execution/execution_binding.json')
    require(binding['owner'] == EXPECTED_OWNER and binding['physical_gpu'] == 0 and
            binding['native_manifest_sha256'] == sha(TICK / 'btc_execution/native_manifest.json'),
            'Original fresh binding/GPU/manifest mismatch')
    require(read(ROOT / 'pipeline/experiments/M210-PSNC.json')['status'] == 'done_earlystop',
            'Original PSNC has not been canonically archived')
    return manifest, hashes, [ref(local_path), ref(independent_path)]


def source_paths(manifest):
    require(manifest['candidate_name'] == NAME and manifest['config'] == CONFIG, 'Wrong tested package/config')
    names = {'__init__.py', 'backbone.py', 'dec.py', 'hier_postprocess.py', 'loss.py',
             'middle_tree.py', 'network.py', 'sample_model.py'}
    require(set(manifest['candidate_source_hashes']) == names, 'Expected exact eight independent sources')
    paths = {'framework/model/Quard_model/' + NAME + '/' + n: h
             for n, h in manifest['candidate_source_hashes'].items()}
    paths[CONFIG] = manifest['candidate_config_sha256']
    require(all(isinstance(h, str) and re.fullmatch(r'[0-9a-f]{64}', h) for h in paths.values()),
            'Unknown tested source hash')
    return paths
