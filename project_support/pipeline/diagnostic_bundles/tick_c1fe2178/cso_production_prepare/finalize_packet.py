"""Default NOP. Root-only local freeze against a genuine canonical M236-CSO admission."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
SOURCE = '5413102c57b526035f3920b5e7a81f3b58ad764d'
CONFIG = 'configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    with Path(path).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root', action='store_true')
    parser.add_argument('--admission')
    parser.add_argument('--admission-sha256')
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({'status': 'DEFAULT_NOP_NO_FREEZE_OR_EXTERNAL_ACTION'}))
        return
    assert args.admission and args.admission_sha256
    assert sys.dont_write_bytecode and not sys.flags.optimize
    assert os.environ.get('GIT_OPTIONAL_LOCKS') == '0'
    manifest = read(HERE / 'SOURCE_MANIFEST.NOT_EXECUTABLE.json')
    owner = manifest['owner']
    assert os.environ.get('CODEX_THREAD_ID') == owner['thread_id']
    live = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert {key: live[key] for key in owner} == owner
    assert (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds() > 180
    mode = read(ROOT / 'pipeline/execution_mode.json')
    assert mode['mode'] == 'foreground' and mode['target_thread_id'] == owner['thread_id']
    for name, key in (('.tick_context.json', 'context_sha256'), ('.tick_context_state.next.json', 'pending_sha256')):
        assert sha(ROOT / 'pipeline/headless' / name) == owner[key]
    assert not (HERE / 'FROZEN.json').exists(), 'Never replace a frozen or uncertain packet'
    assert manifest['admission_not_yet_bound'] is True and manifest['source_commit'] == SOURCE
    assert all(sha(HERE / name) == expected for name, expected in manifest['files'].items())
    assert all(sha(ROOT / item['path']) == item['sha256'] for item in manifest['anchors'])
    admission_path = Path(args.admission).resolve()
    assert admission_path == (ROOT / 'pipeline/admissions/M236-CSO.json').resolve()
    assert sha(admission_path) == args.admission_sha256
    admission = read(admission_path)
    assert admission['id'] == 'M236-CSO' and admission['candidate_id'] == 'fine-leaf-full-covariance-shape-composition'
    assert admission['code_commit'] == SOURCE and admission['config'] == CONFIG
    assert admission['profile'] == 'experiment_first'
    assert all(admission['gates'][name]['passed'] is True for name in ('native_backward', 'resources', 'independence', 'constraints'))
    baseline = read(HERE / 'baseline.json')
    assert admission['goal_sha256'] == baseline['goal_sha256'] == sha(ROOT / 'pipeline/goal.json')
    assert sha(ROOT / 'SERVERS.yaml') == baseline['SERVERS_sha256']
    task = {'id': 'M236-CSO', 'candidate_id': admission['candidate_id'], 'config': CONFIG, 'code_commit': SOURCE,
            'profile': 'experiment_first', 'requires_exclusive_ownership': False,
            'admission_receipt': admission_path.relative_to(ROOT).as_posix()}
    sys.path.insert(0, str(SKILL))
    import closure
    closure.admission(ROOT, task)
    validation = {'owner': owner, 'recorded_at': datetime.now(timezone.utc).isoformat(),
        'kind': 'LOCAL_FINAL_PACKET_BINDING_TO_VALIDATED_CANONICAL_ADMISSION',
        'source_commit': SOURCE, 'admission_sha256': args.admission_sha256,
        'source_manifest_sha256': sha(HERE / 'SOURCE_MANIFEST.NOT_EXECUTABLE.json'),
        'canonical_closure_admission_validated': True, 'SSH_GPU_query_sync_render_queue_launch': False,
        'distinct_final_packet_review': 'PENDING', 'actual_production_path': 'NOT_OBSERVED_BY_FINALIZER'}
    save(HERE / 'finalization_validation.json', validation)
    files = dict(manifest['files'])
    files['SOURCE_MANIFEST.NOT_EXECUTABLE.json'] = sha(HERE / 'SOURCE_MANIFEST.NOT_EXECUTABLE.json')
    files['finalization_validation.json'] = sha(HERE / 'finalization_validation.json')
    anchors = list(manifest['anchors'])
    anchors.append({'path': admission_path.relative_to(ROOT).as_posix(), 'sha256': args.admission_sha256})
    frozen = {'owner': owner, 'recorded_at': validation['recorded_at'], 'author_thread_id': manifest['author_thread_id'],
        'source_commit': SOURCE, 'source_parent_commit': manifest['source_parent_commit'],
        'admission_sha256': args.admission_sha256, 'files': files, 'anchors': anchors,
        'status': 'FINAL_CURRENT_OWNER_PACKET_AWAITING_DISTINCT_REVIEW_REAL_SYNC_COLLECT_RENDER_AND_VERIFIED_LAUNCH',
        'author_executed': False, 'training_or_production_success_claimed': False}
    save(HERE / 'FROZEN.json', frozen)
    print(json.dumps({'FROZEN': str(HERE / 'FROZEN.json'), 'sha256': sha(HERE / 'FROZEN.json'),
                      'admission_sha256': args.admission_sha256, 'next': 'distinct current packet review'}))


if __name__ == '__main__':
    main()
