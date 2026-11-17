"""Small source-save guard checks; never run Git or the complete helper entry."""
from pathlib import Path
import argparse
import ast
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json

HERE = Path(__file__).resolve().parent
HELPER = HERE / 'prepare_isolated_aef_version.py'


def main():
    raw = HELPER.read_bytes()
    tree = ast.parse(raw)
    compile(raw, str(HELPER), 'exec')
    checks = [{'name': 'AST+compile actual helper', 'passed': True}]
    definitions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    literals = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                literals[node.targets[0].id] = ast.literal_eval(node.value)
            except (TypeError, ValueError):
                pass
    def need(name, condition):
        assert condition, name
        checks.append({'name': name, 'passed': True})
    need('default flag disabled', literals['DRAFT_EXECUTION_ENABLED'] is False)
    need('actual parent026c separate from immutable source reference4e8', literals['BASE'] == '026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563' and literals['SOURCE_REFERENCE_ONLY'] == '4e80006047d5cb3dcdfb9c1102e02c33f354a07d')
    need('owner exactly6/originaldeadline', set(literals['EXPECTED_OWNER']) == {'token', 'thread_id', 'generated_at', 'deadline_at', 'context_sha256', 'pending_sha256'} and literals['EXPECTED_OWNER']['deadline_at'] == '2026-10-26T17:09:41.027895+00:00')
    ns = {'argparse': argparse, 'DRAFT_EXECUTION_ENABLED': False}
    def no_execute():
        raise AssertionError('execute() must never be reached')
    ns['execute'] = no_execute
    subset = ast.Module(body=[definitions['require'], definitions['main']], type_ignores=[])
    exec(compile(subset, 'actual_main_AST_guard_only', 'exec'), ns)
    with contextlib.redirect_stdout(io.StringIO()) as output:
        assert ns['main']([]) == 0
    need('actual default main AST returns before execute', 'DRAFT_DISABLED_NO_GIT_OR_SOURCE_WRITE' in output.getvalue())
    try:
        ns['main'](['--execute-root'])
    except RuntimeError as error:
        need('execute-root still refuses while disabled', 'Draft disabled' in str(error))
    else:
        raise AssertionError('Disabled execute-root accepted')
    source = raw.decode('utf8')
    need('canonical project lock', 'monitor.acquire_lock(str(ROOT))' in source and 'lock.close()' in source)
    need('once intent and no blind replay', 'isolated_version_operation_intent.json' in source and 'Existing attempt requires read-only reconciliation; no replay' in source)
    need('hook/filter protection plus isolated hooks', 'git_hooks_filters_guard()' in source and "'core.hooksPath=' + str(HERE / 'empty_hooks')" in source)
    calls = [n for n in ast.walk(definitions['execute']) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'git']
    mutations = [n for n in calls if len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value in ('worktree', 'add', 'commit')]
    need('exact three Git mutations only worktree-add/stage/commit', len(mutations) == 3)
    need('no remote/reset/clean/stash/push operations', not any(isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in ('reset', 'clean', 'stash', 'push', 'fetch', 'pull', 'ssh', 'scp') for n in ast.walk(tree)))
    need('single parent/exact9A/blob/clean postconditions', all(t in source for t in ['[commit, BASE]', "{'A\\t' + n for n in frozen}", 'blobs == frozen', 'Isolated committed worktree/index must be clean']))
    need('original model/seed/config not executed', not any(isinstance(n, ast.Import) and any(a.name.startswith(('torch', 'framework')) for a in n.names) for n in ast.walk(tree)))
    report = {'status': 'DEFAULT_DISABLED_SOURCE_SAVE_GUARD_SOFTWARE_CHECKS_PASSED', 'recorded_at': datetime.now(timezone.utc).isoformat(), 'helper_sha256': hashlib.sha256(raw).hexdigest(), 'checks': checks, 'check_count': len(checks), 'complete_helper_entry_executed': False, 'Git_subprocess_network_Torch_shared_mutation': False, 'old_136_and_46_scientific_suites_rerun': False}
    path = HERE / 'static_validation.json'
    with path.open('x', encoding='utf8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'checks': len(checks), 'helper_sha256': report['helper_sha256'], 'validation_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
