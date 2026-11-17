"""Local-only correction of two final interpreter argv lists in an unfrozen draft."""
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import sys

AUDIT = Path(__file__).resolve().parent
TICK = AUDIT.parent
ROOT = TICK.parents[2]
HERE = TICK / 'cso_production_prepare'
assert sys.dont_write_bytecode and not (HERE / 'FROZEN.json').exists()
names = ('lock_core.py', 'production_controller.py', 'SOURCE_MANIFEST.NOT_EXECUTABLE.json',
         'lock_core.py.diff', 'production_controller.py.diff', 'collect_request.draft.json',
         'render_request.draft.json', 'independent_review_contract.json', 'draft_validation.json', 'README.md')
before = {name: (HERE / name).read_bytes() for name in names}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save_json(path, value):
    with Path(path).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def update_json(name, value):
    assert not (HERE / 'FROZEN.json').exists()
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf8', newline='\n')


for name, data in before.items():
    with (AUDIT / (name + '.before')).open('xb') as stream:
        stream.write(data)
save_json(AUDIT / 'before.sha256.json', {name: sha(data) for name, data in before.items()})
entry_hash = sha((HERE / 'entry_factory.py').read_bytes())
core = before['lock_core.py']
old = b'os.execve(BINDING["python"], [BINDING["python"], *args], os.environ.copy())'
new = b'os.execve(BINDING["python"], [BINDING["python"], "-B", *args], os.environ.copy())'
assert core.count(old) == 2
new_core = core.replace(old, new)
old_core_sha, new_core_sha = sha(core), sha(new_core)
assert old_core_sha == '4d0faba09745ce86a70484658e2b972f3eba451f9db15900eeba0ece3fad4c2c'
controller = before['production_controller.py']
assert controller.count(old_core_sha.encode()) == 1
new_controller = controller.replace(old_core_sha.encode(), new_core_sha.encode())
old_controller_sha, new_controller_sha = sha(controller), sha(new_controller)
assert not (HERE / 'FROZEN.json').exists()
(HERE / 'lock_core.py').write_bytes(new_core)
(HERE / 'production_controller.py').write_bytes(new_controller)
for name in ('collect_request.draft.json', 'render_request.draft.json', 'independent_review_contract.json'):
    data = before[name]
    assert old_core_sha.encode() in data and old_controller_sha.encode() in data
    data = data.replace(old_core_sha.encode(), new_core_sha.encode()).replace(old_controller_sha.encode(), new_controller_sha.encode())
    (HERE / name).write_bytes(data)
for name in ('lock_core.py', 'production_controller.py'):
    historical = ROOT / 'pipeline/diagnostic_bundles/tick_9573f1fc/m235_production_prepare' / name
    delta = ''.join(difflib.unified_diff(historical.read_text(encoding='utf8').splitlines(keepends=True),
                                      (HERE / name).read_text(encoding='utf8').splitlines(keepends=True),
                                      fromfile='tick9573/' + name, tofile='tickc1fe/' + name))
    (HERE / (name + '.diff')).write_text(delta, encoding='utf8', newline='\n')
for name, data, changed in (('lock_core.py', core, new_core), ('production_controller.py', controller, new_controller)):
    delta = ''.join(difflib.unified_diff(data.decode().splitlines(keepends=True), changed.decode().splitlines(keepends=True),
                                      fromfile='draft_before/' + name, tofile='draft_after/' + name))
    with (AUDIT / (name + '.correction.diff')).open('x', encoding='utf8', newline='\n') as stream:
        stream.write(delta)
before_ast, after_ast = ast.parse(core), ast.parse(new_core)
def definition(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
assert ast.dump(definition(before_ast, 'validate_training')) == ast.dump(definition(after_ast, 'validate_training'))
execs = [n for n in ast.walk(after_ast) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'os' and n.func.attr == 'execve']
assert len(execs) == 2
assert all(isinstance(n.args[1], ast.List) and isinstance(n.args[1].elts[1], ast.Constant) and n.args[1].elts[1].value == '-B' for n in execs)
for node in before_ast.body:
    if isinstance(node, ast.FunctionDef) and node.name not in ('locked_exec', 'main'):
        assert ast.dump(node) == ast.dump(definition(after_ast, node.name)), node.name
assert sha((HERE / 'entry_factory.py').read_bytes()) == entry_hash == '0a8ed26bd62327314de89f4228b53c8c633fdd73e4e1867d674df94b24d073dd'
ast.parse(new_controller)
validation = json.loads(before['draft_validation.json'])
validation['python_B_final_exec_correction'] = {
    'author_thread_id': '/root/cso_readiness', 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'both_final_training_and_nontraining_exec_argv_explicit_B': True,
    'validate_training_exact_six_args_function_AST_unchanged': True,
    'entry_factory_raw_bytes_unchanged': True, 'scope': 'STATIC_AST_ONLY_NO_PREPARED_MODULE_IMPORT_EXECUTION_OR_QUERY'}
update_json('draft_validation.json', validation)
readme = before['README.md'].decode()
readme += '\nBoth final original-interpreter exec paths now explicitly insert `-B` before the already validated arguments; the training six-argument contract and entry_factory bytes remain unchanged. The original draft and exact correction diff are preserved in sibling `cso_production_pythonB_audit`.\n'
(HERE / 'README.md').write_text(readme, encoding='utf8', newline='\n')
record = {'owner': json.loads(before['SOURCE_MANIFEST.NOT_EXECUTABLE.json'])['owner'],
          'recorded_at': datetime.now(timezone.utc).isoformat(), 'author_thread_id': '/root/cso_readiness',
          'kind': 'UNFROZEN_DRAFT_TWO_FINAL_EXEC_ARGV_PYTHON_B_CORRECTION',
          'before': {name: sha(data) for name, data in before.items()},
          'after': {name: sha((HERE / name).read_bytes()) for name in names if name != 'SOURCE_MANIFEST.NOT_EXECUTABLE.json'},
          'entry_factory_sha256_preserved': entry_hash,
          'static_validation': {'two_execve_explicit_B': True, 'validate_training_sixargs_AST_unchanged': True,
                                'other_guard_functions_AST_unchanged': True, 'AST_parse': True},
          'final_FROZEN_existed_or_modified': False, 'SSH_Torch_GPU_training_or_shared_state_mutation': False,
          'actual_production_path': 'NOT_EXECUTED', 'scientific_admission': False}
save_json(AUDIT / 'correction.actual.json', record)
manifest = json.loads(before['SOURCE_MANIFEST.NOT_EXECUTABLE.json'])
manifest['files'] = {name: sha((HERE / name).read_bytes()) for name in manifest['files']}
manifest['anchors'].append({'path': (AUDIT / 'correction.actual.json').relative_to(ROOT).as_posix(),
                            'sha256': sha((AUDIT / 'correction.actual.json').read_bytes())})
update_json('SOURCE_MANIFEST.NOT_EXECUTABLE.json', manifest)
assert all(sha((HERE / name).read_bytes()) == digest for name, digest in manifest['files'].items())
assert not (HERE / 'FROZEN.json').exists()
print(json.dumps({'lock_core_sha256': new_core_sha, 'controller_sha256': new_controller_sha,
                  'SOURCE_MANIFEST_sha256': sha((HERE / 'SOURCE_MANIFEST.NOT_EXECUTABLE.json').read_bytes()),
                  'audit_sha256': sha((AUDIT / 'correction.actual.json').read_bytes()), 'entry_factory_unchanged': True,
                  'validate_training_unchanged': True, 'final_FROZEN_exists': False}))
