"""Fresh token-bound native diagnostic; synchronous, no training launch."""
import ast
import base64
import copy
import json
from pathlib import Path
from ops import ROOT, OUT, ID, TOKEN, THREAD, guard, evidence, remote, save, tick, now

owner, _ = guard(900)
old = ROOT / 'pipeline/diagnostic_bundles/tick_c121c67d/native_relabel'
manifest = copy.deepcopy(tick.load(old / 'native_manifest.json'))
stage = '/data/songcl/Project/Cluster_project/pipeline/contact_658721c0'
runtime = (old / 'native_runtime.py').read_text(encoding='utf-8')
marker = "    lease = json.loads(Path(lease_path).read_text())\n"
assert runtime.count(marker) == 1
runtime = runtime.replace(marker, marker + '    assert lease["token"] == ' + repr(TOKEN) + '\n')
runtime = runtime.replace('signal.alarm(min(1200,', 'signal.alarm(min(600,')
(OUT / 'native_runtime.py').write_text(runtime, encoding='utf-8')
archive = OUT / 'cpu_contact_operator_v0.py'
initial = tick.load(OUT / 'initial_resources.json')['data']
if archive.exists() and tick.digest(archive) != initial['source_hashes']['contact_exchange.py']:
    bad = OUT / 'cpu_archive_normalization_failure.py'
    bad.write_bytes(archive.read_bytes())
    save('pre_native_local_failure.json', {'observed_at': now(),
        'reason': 'Text reconstruction did not reproduce the tested CPU operator bytes; stopped before staging or GPU launch.',
        'failed_archive': evidence(bad), 'expected_sha256': initial['source_hashes']['contact_exchange.py'],
        'repair': 'Retrieve the unchanged, hash-verified original diagnostic source bytes from its existing remote stage. No scientific source or gate changed.',
        'native_forwards': 0, 'gpu_computation': False})
if not archive.exists() or tick.digest(archive) != initial['source_hashes']['contact_exchange.py']:
    original_observation = remote("import base64,hashlib,json\nfrom pathlib import Path\np=Path(" + repr(stage + '/contact_exchange.py')
        + ")\nvalue=p.read_bytes()\nprint(json.dumps({'sha256':hashlib.sha256(value).hexdigest(),'bytes_base64':base64.b64encode(value).decode()}))")
    save('cpu_source_archive_observation.json', original_observation)
    assert original_observation['returncode'] == 0
    assert original_observation['data']['sha256'] == initial['source_hashes']['contact_exchange.py']
    archive.write_bytes(base64.b64decode(original_observation['data']['bytes_base64']))
assert tick.digest(archive) == initial['source_hashes']['contact_exchange.py']
files = ('native_runtime.py', 'native_contact_task.py', 'contact_exchange.py')
for name in files:
    ast.parse((OUT / name).read_text(encoding='utf-8'), filename=name)
manifest.update(stage=stage, candidate_id=ID, cohort=tick.load(OUT / 'contact_protocol.json')['cohort'],
    protocol=evidence(OUT / 'contact_protocol.json'),
    diagnostic_files={name: tick.digest(OUT / name) for name in files})
manifest_path = OUT / 'native_manifest.json'
if manifest_path.exists():
    assert tick.load(manifest_path) == manifest
    save('pre_native_transport_failure.json', {'observed_at': now(),
        'failure': 'WinError206 before SSH process creation: encoded staging payload exceeded Windows command-line length.',
        'repair': 'Send the identical Python staging payload via SSH standard input, not the command line. Existing frozen manifest/protocol/lease retained.',
        'native_forwards': 0, 'gpu_computation': False})
else:
    save('native_manifest.json', manifest)
lease = OUT / 'native_lease.json'
if lease.exists():
    saved_lease = tick.load(lease)
    assert saved_lease['token'] == TOKEN and saved_lease['deadline_at'] == owner['deadline_at']
    assert saved_lease['native_manifest_sha256'] == tick.digest(manifest_path)
else:
    save('native_lease.json', {'project': 'cluster_project', 'thread_id': THREAD, 'token': TOKEN,
        'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(manifest_path), 'created_at': now()})
scope = OUT / 'native_readout_preregistration.json'
if not scope.exists():
    save('native_readout_preregistration.json', {'preregistered_at': now(), 'token': TOKEN,
    'candidate_id': ID, 'frozen_manifest': evidence(manifest_path),
    'first_run': 'One unchanged M95 native TRAIN loss-forward, 2 fixed scenes/8 expressions; then exact captured banks and fixed deployed-query point-feature counterfactuals.',
    'controls': 'Replicated readback, native mask head identity, captured-bank encoder identity, deleted-contact mask identity, and native-feature operator row reversal all retain 1e-6. Stop task interpretation if any control fails.',
    'arms': 'Original/deleted contacts, physical cross-leaf contact attention, fixed one-position donor-value rotation. Same original head, query identities, middle/coarse banks and targets.',
    'readout': 'Selected deployed query from original indication logits (not GT matching); probability MAE versus native gt_spmasks, cross-leaf receiver subset, and target-boundary incidence. Aggregate by actual scene; 8 expressions are not 8 independent scenes.',
    'backward': 'One cut-path derivative on native captured features proves a direct off-leaf donor dependency only. It is not full native criterion backward or admission.',
    'limitations': 'Frozen-bank operator tests do not pass prior full-source recomputation/permutation failures. New mechanism task benefit/efficacy/novelty remain unproved.'})
payload = {name: base64.b64encode((OUT / name).read_bytes()).decode()
           for name in (*files, 'native_manifest.json', 'native_lease.json')}
hashes = {name: tick.digest(OUT / name) for name in payload}
code = '''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE)
assert stage.is_dir()
current=stage/'contact_exchange.py'
assert hashlib.sha256(current.read_bytes()).hexdigest()==OLD
(stage/'cpu_contact_operator_v0.py').write_bytes(current.read_bytes())
for name,value in PAYLOAD.items():
 assert Path(name).name==name
 path=stage/name
 if name!='contact_exchange.py':assert not path.exists()
 path.write_bytes(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'staged':str(stage),'hashes':HASHES}))
'''
staged = remote('STAGE=' + repr(stage) + '\nOLD=' + repr(tick.digest(archive)) + '\nPAYLOAD=' + repr(payload)
    + '\nHASHES=' + repr(hashes) + '\n' + code)
save('native_stage_observation.json', staged)
assert staged['returncode'] == 0, 'Staging failed; preserve evidence, do not launch'
guard(750)
code = '''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
process=subprocess.run([sys.executable,'-B',str(stage/'native_contact_task.py'),'--lease',str(stage/'native_lease.json')],capture_output=True,text=True,timeout=660)
result={'returncode':process.returncode,'stdout':process.stdout[-12000:],'stderr':process.stderr[-10000:]}
path=stage/'native_contact_result.json'
if path.exists():result['native_result']=json.loads(path.read_text())
print(json.dumps(result))
'''
observed = remote('STAGE=' + repr(stage) + '\n' + code, timeout=720, conda=True)
observation_path = save('native_contact_observation.json', observed)
assert observed['returncode'] == 0, 'Native observer failed; inspect saved evidence'
data = observed['data']
native = data.get('native_result', {})
native_path = save('native_contact_result.json', native)
guard()
work = tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(c for c in work['candidates'] if c['id'] == ID)
candidate['evidence'].extend([evidence(scope), evidence(native_path), evidence(observation_path)])
candidate['next_action'] = ('Evaluate scene-level matched readouts and freeze the next discriminating native/full-backward/resource step; no scientific gate or training PASS inferred.'
    if native.get('execution_completed') else 'Classify and repair only the observed diagnostic implementation failure under this stable ID; preserve failed controls and original gates.')
if not native.get('execution_completed'):
    candidate['failure_scope'] = 'implementation'
tick.save(ROOT / 'pipeline/research_work.json', work)
print(json.dumps({'candidate_id': ID, 'returncode': data['returncode'], 'result': native, 'evidence': evidence(native_path)}, ensure_ascii=False))
