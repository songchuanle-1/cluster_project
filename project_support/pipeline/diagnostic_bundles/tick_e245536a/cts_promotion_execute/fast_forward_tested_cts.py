"""Disabled private root draft; never run before actual four-result reviews."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import promotion_common as common


def save(path, data):
    common.execution_enabled(True)
    common.owner_guard()
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root', action='store_true')
    parser.add_argument('--bec-native-round-settled',action='store_true',help='Operational settlement, not BEC scientific approval')
    args = parser.parse_args()
    if not args.execute_root:
        print('DRAFT_DISABLED: no Git, shared or remote operation invoked')
        return
    common.execution_enabled(args.execute_root)
    import sys
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(common.ROOT));common.require(lock is not None,'Canonical pipeline lock busy')
    try:
        common.owner_guard()
        settlement=common.require_bec_runtime_settled(args.bec_native_round_settled)
        manifest, execution_hashes, reviews = common.reviewed_four_raw()
        require = common.require
        require(common.git('rev-parse', 'HEAD') == common.BASE, 'Primary is not original common48fc')
        require(common.git('show', '-s', '--format=%P', common.TESTED) == common.BASE, 'CTS is not exact single child of48fc')
        rows = common.protected()
        lifecycle_before = common.protected_lifecycle()
        ledger_names=('queue.json','running.json','research_work.json','experiments/M213-BFC.json','experiments/M212-BCR.json','experiments/M206-CGCA.json','admissions/M213-BFC.json','admissions/M212-BCR.json')
        ledger_hashes={name:common.sha(common.ROOT/'pipeline'/name) for name in ledger_names}
        paths = common.source_paths(manifest)
        diff = common.git('diff-tree', '--no-commit-id', '--name-status', '-r', common.TESTED).splitlines()
        require(len(diff) == 9 and set(diff) == {'A\t' + p for p in paths}, 'Commit is not exactly tested nine additions')
        for path, expected in paths.items():
            require(not (common.CODE / path).exists(), 'Destination already exists: ' + path)
            require(not any(path == r['path'] or path.startswith(r['path'] + '/') or
                            r['path'].startswith(path + '/') for r in rows), 'Protected path overlap')
            require(hashlib.sha256(common.git_bytes('show', common.TESTED + ':' + path)).hexdigest() == expected,
                    'Git blob is not tested source: ' + path)
            require(common.git('ls-tree', common.TESTED, '--', path).split()[0] == '100644', 'Unexpected source mode')
        before = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'owner': common.EXPECTED_OWNER,
                  'before_commit': common.BASE, 'tested_commit': common.TESTED, 'changed_paths': paths,
                  'protected_rows': rows, 'actual_execution_hashes': execution_hashes,
                  'actual_review_refs': reviews, 'index_empty': True, 'new_commit_created': False}
        common.begin_phase('ff',{'before':before,'BEC_runtime_settlement':settlement,'protected_lifecycle':lifecycle_before})
        save(common.TICK / 'cts_primary_ff_before.json', before)
        hooks = common.TICK / 'cts_empty_hooks'
        hooks.mkdir(exist_ok=False)
        command = ['git', '--no-optional-locks', '-C', str(common.CODE), '-c', 'merge.autoStash=false',
                   '-c', 'core.autocrlf=false', '-c', 'core.eol=lf', '-c', 'core.hooksPath=' + str(hooks),
                   'merge', '--ff-only', common.TESTED]
        env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_LFS_SKIP_SMUDGE='1')
        # Immediately revalidate owner/context/deadline and original protected state.
        common.owner_guard()
        require(common.protected() == rows and common.git('rev-parse', 'HEAD') == common.BASE,
                'Primary/protected state changed before ff-only')
        common.owner_guard()
        run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', env=env, timeout=120)
        save(common.TICK / 'cts_primary_ff_command.json', {'command': command, 'returncode': run.returncode,
                                                        'stdout': run.stdout, 'stderr': run.stderr})
        require(run.returncode == 0, 'ff-only failed; inspect exact HEAD/status, never reset/stash/clean')
        require(common.git('rev-parse', 'HEAD') == common.TESTED, 'Exact tested HEAD was not reached')
        require(common.protected() == rows, 'Protected28 changed after ff-only')
        require(all(common.sha(common.CODE / p) == h for p, h in paths.items()), 'Worktree differs from tested bytes')
        require(common.protected_lifecycle()==lifecycle_before and all(common.sha(common.ROOT/'pipeline'/name)==digest for name,digest in ledger_hashes.items()),'Protected lifecycle or ledgers changed during local ff; no rollback or retry')
        result = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'token': common.TOKEN,
                  'HEAD': common.TESTED, 'only_nine_tested_additions': True,
                  'protected_28_status_and_bytes_unchanged': True, 'index_empty': True,
                  'source_hashes': paths, 'remote_sync_performed': False,
                  'admission_or_launch_performed': False, 'new_commit_created': False,
                  'reset_clean_stash_force_used': False, 'protected_lifecycle_and_ledger_bytes_unchanged': True}
        save(common.TICK / 'cts_primary_ff_result.json', result)
        common.phase_result('ff',result)
        print(json.dumps(result, ensure_ascii=False))


    finally:
        lock.close()
if __name__ == '__main__':
    main()
