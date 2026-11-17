"""Static independence and one synchronous native standalone integration test."""
import ast
import base64
import copy
import json
import sys
from pathlib import Path
from ops import ROOT, OUT, ID, NAME, TOKEN, THREAD, guard, evidence, remote, save, tick, now

owner, _ = guard(360)
repair = sys.argv[1:] == ['--fresh-import-repair']
assert repair or not sys.argv[1:]
suffix = '_r1' if repair else ''
new_name = NAME + '_pce'
directory = ROOT / 'Cluster/framework/model/Quard_model' / new_name
config = ROOT / 'Cluster/configs/Quard/ctf_hcg_csort_pce' / (new_name + '.yaml')
sources = sorted(directory.glob('*.py'))
for path in sources:
    tree = ast.parse(path.read_bytes(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not ('Quard_model.model_' in node.module), 'Cross-variant import'
assert len(list((ROOT / 'Cluster/configs').rglob(new_name + '.yaml'))) == 1
assert tick.digest(config) == tick.load(OUT / 'independent_draft_initial.json')['parent_config_sha256']
network = ast.parse((directory / 'network.py').read_bytes())
cls = next(n for n in network.body if isinstance(n, ast.ClassDef) and n.name == 'Network')
for method in ('loss', 'predict'):
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method)
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'contacts' for n in ast.walk(node))
static = save('independence_and_wiring' + suffix + '.json', {'observed_at': now(), 'model_name': new_name,
    'model_sources': {p.name: tick.digest(p) for p in sources}, 'config': evidence(config),
    'physical_package_independent': True, 'cross_variant_imports': 0, 'syntax_files': len(sources),
    'config_basename_unique': True, 'configuration_numeric_changes': 0,
    'training_and_inference_graph_wiring_static': True,
    'status': 'Static pass only; native standalone test not yet run at this record.'})
local = OUT / ('standalone_runtime' + suffix)
local.mkdir()
for name in ('native_runtime.py', 'native_standalone_task.py'):
    (local / name).write_bytes((OUT / name).read_bytes())
protocol = save('standalone_preregistration' + suffix + '.json', {'preregistered_at': now(), 'candidate_id': ID,
    'test': 'Hash-bound independent package, no forward replacement hooks, frozen M95 state/seed1999/two TRAIN scenes. Original native criterion forward/backward; zero optimizer steps.',
    'expected': 'Finite native loss/gradients, same parameter keys/count as parent, contact generation active in independent Network/DEC/readback. Missing formal efficiency and full-source controls are not granted PASS.',
    'harness_revision': 1 if repair else 0,
    'failure_evidence': evidence(OUT / 'native_standalone_result.json') if repair else None,
    'local_correction': 'Fresh process loads only the independent package; do not first instantiate the parent and do not force/reset the global Criterion registry. No candidate model arithmetic changed.' if repair else None})
manifest = copy.deepcopy(tick.load(OUT / 'native_manifest.json'))
stage = '/data/songcl/Project/Cluster_project/pipeline/contact_standalone_658721c0' + suffix
manifest.update(stage=stage, protocol=evidence(protocol), candidate_source_hashes={p.name: tick.digest(p) for p in sources},
    diagnostic_files={name: tick.digest(local / name) for name in ('native_runtime.py', 'native_standalone_task.py')})
tick.save(local / 'native_manifest.json', manifest)
tick.save(local / 'native_lease.json', {'project': 'cluster_project', 'thread_id': THREAD, 'token': TOKEN,
    'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
files = {name: local / name for name in ('native_runtime.py', 'native_standalone_task.py', 'native_manifest.json', 'native_lease.json')}
files.update({'candidate_model/' + p.name: p for p in sources})
payload = {name: base64.b64encode(path.read_bytes()).decode() for name, path in files.items()}
hashes = {name: tick.digest(path) for name, path in files.items()}
code = '''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE)
stage.mkdir(exist_ok=False)
(stage/'candidate_model').mkdir()
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 path.write_bytes(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'stage':str(stage),'source_files':len(PAYLOAD)}))
'''
staged = remote('STAGE=' + repr(stage) + '\nPAYLOAD=' + repr(payload) + '\nHASHES=' + repr(hashes) + '\n' + code)
save('standalone_stage_observation' + suffix + '.json', staged)
assert staged['returncode'] == 0
code = '''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
process=subprocess.run([sys.executable,'-B',str(stage/'native_standalone_task.py'),'--lease',str(stage/'native_lease.json')],capture_output=True,text=True,timeout=420)
value={'returncode':process.returncode,'stdout':process.stdout[-7000:],'stderr':process.stderr[-10000:]}
result=stage/'native_standalone_result.json'
if result.exists():value['native_result']=json.loads(result.read_text())
print(json.dumps(value))
'''
observed = remote('STAGE=' + repr(stage) + '\n' + code, timeout=450, conda=True)
observation = save('native_standalone_observation' + suffix + '.json', observed)
assert observed['returncode'] == 0
native = observed['data'].get('native_result', {})
native_path = save('native_standalone_result' + suffix + '.json', native)
guard()
work = tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(c for c in work['candidates'] if c['id'] == ID)
candidate['evidence'].extend([evidence(static), evidence(protocol), evidence(native_path), evidence(observation)])
candidate['stage'] = 'validation' if native.get('execution_completed') else 'implementation'
candidate['next_action'] = 'Complete uniform total efficiency/full-source numerical controls and prediction-blind broader scene task evidence for the independent PCE model; preserve all original failures and novelty limits. No queue or training until all admission gates pass.'
tick.save(ROOT / 'pipeline/research_work.json', work)
print(json.dumps({'candidate_id': ID, 'returncode': observed['data']['returncode'], 'static': evidence(static), 'native': native, 'evidence': evidence(native_path)}, ensure_ascii=False))
