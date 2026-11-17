"""Execute one frozen PCE revision under the recovered foreground owner."""
import argparse
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import repair

c = repair.c
OUT = repair.OUT
ROOT = repair.ROOT


def prepare():
    owner, _ = c.guard(1200)
    work = c.tick.load(ROOT / 'pipeline/research_work.json')
    candidate = next(item for item in work['candidates'] if item['id'] == c.CID)
    assert candidate['revision_history'][-1]['revision'] == 3
    assert candidate['revision_history'][-1]['result'] == 'pending'
    repair.closure.validate_revisions(ROOT, candidate)
    package = ROOT / 'Cluster/framework/model/Quard_model' / (c.NAME + '_pce')
    changed = []
    for path in package.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
        if path.read_bytes() != (OUT / 'source_r2' / path.name).read_bytes():
            changed.append(path.name)
    assert set(changed) == {'contact_geometry.py', 'contact_exchange.py', 'hier_postprocess.py', 'dec.py'}
    def syntax(path, name):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        return ast.dump(next(node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name))
    assert syntax(package / 'hier_postprocess.py', 'PointCloudPartitioner') == syntax(OUT / 'source_r2/hier_postprocess.py', 'PointCloudPartitioner')
    assert syntax(package / 'contact_exchange.py', 'exchange') == syntax(OUT / 'source_r2/contact_exchange.py', 'exchange')
    for name in ('SelfAttentionLayer', 'CrossAttentionLayer', 'FFN'):
        assert syntax(package / 'dec.py', name) == syntax(OUT / 'source_r2/dec.py', name)
    worker = (ROOT / 'pipeline/diagnostic_bundles/tick_3259705f/worker.py').read_bytes()
    with (OUT / 'worker.py').open('xb') as stream:
        stream.write(worker)
    runtime = (ROOT / 'pipeline/diagnostic_bundles/tick_658721c0/native_runtime.py').read_text(encoding='utf-8')
    runtime = runtime.replace('658721c071ae487ea47224e55d51abde', c.TOKEN)
    runtime = runtime.replace('01a04987-fdbe-7301-b2f0-f9b6ab60f74c', c.THREAD)
    manifest = copy.deepcopy(c.tick.load(ROOT / 'pipeline/diagnostic_bundles/tick_3259705f/native_manifest.json'))
    manifest.update(stage=c.STAGE, current_token=c.TOKEN, revision=3,
        resource_protocol=c.evidence(OUT / 'implementation_revision3.json'))
    payload = {'native_runtime.py': runtime.encode('utf-8'), 'worker.py': worker}
    for path in sorted(package.glob('*.py')):
        payload['candidate_model/' + path.name] = path.read_bytes()
    config = ROOT / 'Cluster/configs/Quard/ctf_hcg_csort_pce' / (c.NAME + '_pce.yaml')
    payload['candidate.yaml'] = config.read_bytes()
    manifest['candidate_source_hashes'] = {Path(name).name: hashlib.sha256(value).hexdigest()
        for name, value in payload.items() if name.startswith('candidate_model/')}
    manifest['diagnostic_files'] = {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()}
    c.save('native_manifest.json', manifest)
    payload['native_manifest.json'] = (OUT / 'native_manifest.json').read_bytes()
    c.save('execution_lease.json', {'token': c.TOKEN, 'thread_id': c.THREAD, 'project': 'cluster_project',
        'deadline_at': owner['deadline_at'], 'native_manifest_sha256': c.tick.digest(OUT / 'native_manifest.json')})
    payload['execution_lease.json'] = (OUT / 'execution_lease.json').read_bytes()
    static = c.save('static_review.json', {'observed_at': c.now(), 'changed_files': changed,
        'all_python_ast_valid': True, 'worker_unchanged_from_r2': worker == (ROOT / 'pipeline/diagnostic_bundles/tick_3259705f/worker.py').read_bytes(),
        'fps_partitioner_function_text_unchanged': True,
        'contact_exchange_function_text_unchanged': True,
        'threshold_precision_and_attention_formula_unchanged': True,
        'candidate_source_hashes': manifest['candidate_source_hashes']})
    encoded = {name: base64.b64encode(value).decode('ascii') for name, value in payload.items()}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()}
    code = '''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE)
stage.mkdir(parents=False,exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'stage':str(stage),'files':len(PAYLOAD),'hashes':HASHES}))
'''
    observation = c.remote('STAGE=' + repr(c.STAGE) + '\nPAYLOAD=' + repr(encoded) + '\nHASHES=' + repr(hashes) + '\n' + code)
    staged = c.save('staging.json', observation)
    c.advance([OUT / 'native_manifest.json', OUT / 'worker.py', static, staged, Path(__file__)],
        'Run frozen R3 combined native graph/operator/full-source/backward/resources; preserve failures and no further local implementation revision.')
    assert observation['returncode'] == 0
    print(json.dumps({'staged': c.STAGE, 'files': len(payload), 'production_deployment': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('probe', 'prepare', 'combined', 'champion'))
    args = parser.parse_args()
    if args.operation == 'probe':
        c.probe()
    elif args.operation == 'prepare':
        prepare()
    elif args.operation == 'champion':
        c.run('resources', 'champion')
    else:
        c.run('combined', 'candidate')
