"""Fix candidate-only graph check in the M95 resource harness, retaining failure."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import repair

c = repair.c
BASE = repair.OUT
c.OUT = BASE / 'm95_reference'
c.STAGE += '/m95_reference'


def main():
    owner, _ = c.guard(1200)
    failed = c.tick.load(BASE / 'resources_champion_result.json')
    assert failed['error_type'] == 'ModuleNotFoundError'
    c.OUT.mkdir(exist_ok=False)
    protocol = c.save('harness_repair.json', {
        'preregistered_at': c.now(), 'candidate_id': c.CID, 'model_implementation_changed': False,
        'failure_evidence': c.evidence(BASE / 'resources_champion_result.json'),
        'change': 'The R2 worker unconditionally imports the staged PCE package during a candidate-only graph check, even for champion setup. Skip ONLY that graph check for target=champion; original parent construction, checkpoint, input, predict calls, counter, precision and20/100 timing loop remain unchanged.',
        'candidate_retest': False, 'training': 0})
    worker = (BASE / 'worker.py').read_text(encoding='utf-8')
    marker = '    check_graph(sample, result)'
    assert worker.count(marker) == 1
    worker = worker.replace(marker, "    if result['target'] == 'candidate':\n        check_graph(sample, result)")
    payload = {'worker.py': worker.encode('utf-8'),
        'native_runtime.py': (BASE / 'native_runtime.py').read_bytes() if (BASE / 'native_runtime.py').exists() else
            (repair.ROOT / 'pipeline/diagnostic_bundles/tick_658721c0/native_runtime.py').read_text(encoding='utf-8').replace('658721c071ae487ea47224e55d51abde', c.TOKEN).replace('01a04987-fdbe-7301-b2f0-f9b6ab60f74c', c.THREAD).encode('utf-8'),
        'candidate.yaml': (repair.ROOT / 'Cluster/configs/Quard/ctf_hcg_csort_pce' / (c.NAME + '_pce.yaml')).read_bytes()}
    manifest = copy.deepcopy(c.tick.load(BASE / 'native_manifest.json'))
    manifest.update(stage=c.STAGE, resource_harness_repair=c.evidence(protocol))
    manifest['diagnostic_files'] = {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()}
    c.save('native_manifest.json', manifest)
    payload['native_manifest.json'] = (c.OUT / 'native_manifest.json').read_bytes()
    c.save('execution_lease.json', {'token': c.TOKEN, 'thread_id': c.THREAD, 'project': 'cluster_project',
        'deadline_at': owner['deadline_at'], 'native_manifest_sha256': c.tick.digest(c.OUT / 'native_manifest.json')})
    payload['execution_lease.json'] = (c.OUT / 'execution_lease.json').read_bytes()
    encoded = {name: base64.b64encode(value).decode('ascii') for name, value in payload.items()}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()}
    code = '''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE)
stage.mkdir(exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'staged':str(stage),'files':len(PAYLOAD)}))
'''
    staged = c.save('staging.json', c.remote('STAGE=' + repr(c.STAGE) + '\nPAYLOAD=' + repr(encoded) + '\nHASHES=' + repr(hashes) + '\n' + code))
    assert c.tick.load(staged)['returncode'] == 0
    c.advance([protocol, staged, c.OUT / 'native_manifest.json', Path(__file__)],
        'Complete matched M95 resource measurement after preserving candidate-import harness failure. No model changes or candidate rerun.')
    c.run('resources', 'champion')


if __name__ == '__main__':
    main()
