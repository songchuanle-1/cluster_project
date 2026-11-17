"""Final bounded PCE revision: exact geometry join, original attention."""
import argparse
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
import control as c

BASE = Path(__file__).resolve().parent
REMOTE = '/data/songcl/Project/Cluster_project/pipeline/pce_fefdcc2a/implementation_r2'


def preregister():
    c.guard(600)
    assert c.tick.load(BASE / 'implementation_r1/operator_candidate_result.json')['operator_equivalence_passed'] is False
    archived = BASE / 'contact_exchange_degree_batched_r1.py'
    shutil.copyfile(c.ROOT / 'Cluster/framework/model/Quard_model' / (c.NAME + '_pce') / 'contact_exchange.py', archived)
    protocol = c.save('implementation_revision2.json', {
        'preregistered_at': c.now(), 'candidate_id': c.CID, 'revision': 2,
        'failure_scope': 'implementation',
        'reason': 'Measured CPU contact construction724-921ms dominates833.84ms full predict; revision1 strict input-gradient equivalence failed at6.7353e-6 although outputs were identical.',
        'change': 'Restore exact original exchange/backward, replace ONLY Python per-voxel graph joins with NumPy exact coordinate-key joins and full Cartesian membership joins. All co-occupied/six-face contacts retained; no donor pruning or numeric-ID ownership.',
        'prediction': 'Original attention output/gradient is exact, original/new graph edge sets are exact on native geometry and co-occupancy controls, total median latency decreases without memory gate violation.',
        'tests': 'Native resource-sample graph equality plus batched/co-occupied synthetic graph controls; original8-expression operator controls; full model original20/100 resources; full-source controls/native backward.',
        'tolerance': 1e-6, 'maximum_revisions': 2,
        'nonclaims': 'This is an implementation repair, not a second architecture or a waiver of failed full-source numeric gates.',
        'failure_evidence': [c.evidence(BASE / 'section_profile_result.json'),
            c.evidence(BASE / 'implementation_r1/operator_candidate_result.json'),
            c.evidence(BASE / 'gradient_repeatability_result.json'),
            c.evidence(BASE / 'implementation_r1/resources_candidate_result.json')],
        'original_source': c.evidence(BASE / 'contact_exchange_original.py'), 'revision1_source': c.evidence(archived)})
    work = c.tick.load(c.ROOT / 'pipeline/research_work.json')
    candidate = next(item for item in work['candidates'] if item['id'] == c.CID)
    assert len(candidate['revision_history']) == 1
    candidate['revision_history'][0].update(result='failed', evidence=[
        c.evidence(BASE / 'implementation_revision1.json'),
        c.evidence(BASE / 'implementation_r1/operator_candidate_result.json'),
        c.evidence(BASE / 'implementation_r1/resources_candidate_result.json'),
        c.evidence(BASE / 'implementation_r1/controls_candidate_result.json')])
    p = c.tick.load(protocol)
    candidate['revision_history'].append({key: p[key] for key in
        ('revision', 'failure_scope', 'reason', 'change', 'prediction', 'preregistered_at', 'failure_evidence')})
    candidate['revision_history'][-1].update(result='pending', evidence=[c.evidence(protocol), c.evidence(archived)])
    candidate['evidence'].extend([c.evidence(protocol), c.evidence(archived)])
    candidate['stage'] = 'implementation'
    candidate['next_action'] = 'Execute final preregistered geometry-only revision2 with exact original attention; no revision3 or numerical waiver is authorized.'
    c.tick.save(c.ROOT / 'pipeline/research_work.json', work)
    print({'preregistered_revision': 2, 'scientific_admission': False})


def configure():
    c.OUT = BASE / 'implementation_r2'
    c.STAGE = REMOTE


def prepare():
    c.guard(330)
    configure()
    c.OUT.mkdir(exist_ok=False)
    worker = (BASE / 'implementation_r1/worker.py').read_text(encoding='utf-8')
    helper = (BASE / 'graph_function.py').read_text(encoding='utf-8')
    original = c.tick.load(BASE / 'implementation_revision2.json')['original_source']['sha256']
    helper = helper.replace('ORIGINAL_OPERATOR_SHA', repr(original))
    worker = worker.replace('def main():', helper + '\n\ndef main():')
    marker = "    signature = fingerprint(torch, sample)"
    assert worker.count(marker) == 1
    worker = worker.replace(marker, '    check_graph(sample, result)\n' + marker)
    worker = worker.replace("choices=('resources', 'controls', 'operator')", "choices=('resources', 'controls', 'operator', 'combined')")
    old = "        if args.mode == 'operator':\n            operator_equivalence(torch, result)"
    new = "        if args.mode == 'combined':\n            resources(torch, gorilla, cfg, model, result)\n            result['resources_execution_completed'] = True\n            result['execution_completed'] = False\n            operator_equivalence(torch, result)\n            result['execution_completed'] = False\n            controls(torch, gorilla, cfg, model, qualified, result)\n        elif args.mode == 'operator':\n            operator_equivalence(torch, result)"
    assert worker.count(old) == 1
    worker = worker.replace(old, new)
    ast.parse(worker)
    with (c.OUT / 'worker.py').open('x', encoding='utf-8') as stream:
        stream.write(worker)
    manifest = copy.deepcopy(c.tick.load(c.OLD / 'native_manifest.json'))
    manifest.update(stage=REMOTE, current_token=c.TOKEN, revision=2,
        resource_protocol=c.evidence(BASE / 'implementation_revision2.json'))
    owner, _ = c.guard(330)
    runtime = (c.OLD / 'native_runtime.py').read_text(encoding='utf-8').replace('658721c071ae487ea47224e55d51abde', c.TOKEN)
    payload = {'native_runtime.py': runtime.encode('utf-8'), 'worker.py': worker.encode('utf-8')}
    package = c.ROOT / 'Cluster/framework/model/Quard_model' / (c.NAME + '_pce')
    for path in sorted(package.glob('*.py')):
        payload['candidate_model/' + path.name] = path.read_bytes()
    config = c.ROOT / 'Cluster/configs/Quard/ctf_hcg_csort_pce' / (c.NAME + '_pce.yaml')
    payload['candidate.yaml'] = config.read_bytes()
    manifest['candidate_source_hashes'] = {Path(name).name: hashlib.sha256(value).hexdigest()
        for name, value in payload.items() if name.startswith('candidate_model/')}
    manifest['diagnostic_files'] = {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()}
    c.save('native_manifest.json', manifest)
    payload['native_manifest.json'] = (c.OUT / 'native_manifest.json').read_bytes()
    c.save('execution_lease.json', {'token': c.TOKEN, 'thread_id': c.THREAD, 'project': 'cluster_project',
        'deadline_at': owner['deadline_at'], 'native_manifest_sha256': c.tick.digest(c.OUT / 'native_manifest.json')})
    payload['execution_lease.json'] = (c.OUT / 'execution_lease.json').read_bytes()
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()}
    encoded = {name: base64.b64encode(value).decode('ascii') for name, value in payload.items()}
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
print(json.dumps({'stage':str(stage),'files':len(PAYLOAD)}))
'''
    observation = c.remote('STAGE=' + repr(REMOTE) + '\nPAYLOAD=' + repr(encoded) + '\nHASHES=' + repr(hashes) + '\n' + code)
    path = c.save('staging.json', observation)
    assert observation['returncode'] == 0
    c.advance([BASE / 'implementation_revision2.json', c.OUT / 'native_manifest.json', c.OUT / 'worker.py', path, Path(__file__)],
        'Run final geometry revision2 exact graph/operator controls, paired same-standard resources and full-source controls. No scientific waiver or extra revision.')
    print({'staged': REMOTE, 'files': len(payload)})


def run(mode):
    c.guard(330)
    configure()
    code = '''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
p=subprocess.run([sys.executable,'-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json'),'--mode',MODE,'--target','candidate'],capture_output=True,text=True,timeout=200)
path=stage/(MODE+'_candidate_result.json')
r={'returncode':p.returncode,'stdout':p.stdout[-6000:],'stderr':p.stderr[-12000:]}
if path.exists():r['result']=json.loads(path.read_text())
print(json.dumps(r))
'''
    observation = c.remote('STAGE=' + repr(REMOTE) + '\nMODE=' + repr(mode) + '\n' + code, timeout=230, conda=True)
    opath = c.save(mode + '_candidate_execution.json', observation)
    assert observation['returncode'] == 0
    result = observation['data'].get('result', {})
    path = c.save(mode + '_candidate_result.json', result)
    c.advance([opath, path], 'Review final revision2 outcomes without changing original numeric gates; no automatic revision3/commit/launch.')
    keys = ('execution_completed', 'error_type', 'error', 'median_ms', 'p90_ms', 'peak_allocated_bytes',
        'graph_controls_passed', 'maximum_operator_error', 'operator_equivalence_passed',
        'controls', 'all_full_source_controls_passed', 'gradient_tensor_count')
    print(json.dumps({'returncode': observation['data']['returncode'], 'result': {key: result.get(key) for key in keys}}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('preregister', 'prepare', 'operator', 'resources', 'controls', 'combined'))
    args = parser.parse_args()
    if args.operation == 'preregister':
        preregister()
    elif args.operation == 'prepare':
        prepare()
    else:
        run(args.operation)
