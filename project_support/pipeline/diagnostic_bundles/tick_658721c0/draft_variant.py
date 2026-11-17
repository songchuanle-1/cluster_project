"""Copy only frozen parent sources into a new independent, unadmitted draft."""
import base64
import json
from pathlib import Path
from ops import ROOT, OUT, ID, NAME, guard, evidence, remote, save, tick, now

guard(500)
manifest = tick.load(OUT / 'native_manifest.json')
assets = manifest['assets']
new_name = NAME + '_pce'
directory = ROOT / 'Cluster/framework/model/Quard_model' / new_name
config = ROOT / 'Cluster/configs/Quard/ctf_hcg_csort_pce' / (new_name + '.yaml')
assert directory.resolve().is_relative_to((ROOT / 'Cluster/framework/model/Quard_model').resolve())
assert not directory.exists() and not config.exists()
assert not list((ROOT / 'Cluster/configs').rglob(new_name + '.yaml'))
code = '''
import base64,hashlib,json
from pathlib import Path
directory=Path(ROOT)/'framework/model/Quard_model'/NAME
sources={}
for name,expected in HASHES.items():
 data=(directory/name).read_bytes()
 assert hashlib.sha256(data).hexdigest()==expected
 sources[name]=base64.b64encode(data).decode()
data=Path(CONFIG).read_bytes()
assert hashlib.sha256(data).hexdigest()==CONFIG_SHA
print(json.dumps({'sources':sources,'config':base64.b64encode(data).decode()}))
'''
observed = remote('ROOT=' + repr(manifest['root']) + '\nNAME=' + repr(NAME)
    + '\nHASHES=' + repr(assets['source_hashes']) + '\nCONFIG=' + repr(assets['config_path'])
    + '\nCONFIG_SHA=' + repr(assets['config_sha256']) + '\n' + code)
assert observed['returncode'] == 0
guard()
directory.mkdir()
for name, encoded in observed['data']['sources'].items():
    assert Path(name).name == name
    path = directory / name
    path.write_bytes(base64.b64decode(encoded))
    assert tick.digest(path) == assets['source_hashes'][name]
(directory / 'contact_exchange.py').write_bytes((OUT / 'contact_exchange.py').read_bytes())
config.parent.mkdir(exist_ok=True)
config.write_bytes(base64.b64decode(observed['data']['config']))
assert tick.digest(config) == assets['config_sha256']
path = save('independent_draft_initial.json', {'created_at': now(), 'candidate_id': ID,
    'model_name': new_name, 'model_path': directory.relative_to(ROOT).as_posix(),
    'config_path': config.relative_to(ROOT).as_posix(), 'parent_source_hashes': assets['source_hashes'],
    'parent_config_sha256': assets['config_sha256'],
    'state': 'Fresh physical copy before contact integration; not deployable or admitted yet.',
    'preserved': 'All existing local dirty/source files, old models and frozen remote parent untouched. No commit, push, safe-sync, queue or training.'})
work = tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(c for c in work['candidates'] if c['id'] == ID)
candidate['evidence'].append(evidence(path))
candidate['draft_model_path'] = directory.relative_to(ROOT).as_posix()
candidate['draft_config_path'] = config.relative_to(ROOT).as_posix()
candidate['next_action'] = 'Integrate physical contact graph and fine readback only in the independent draft, statically test the full inference/training wiring, then verify the standalone native model and remaining original gates. Draft copy alone is not a model change or admission.'
tick.save(ROOT / 'pipeline/research_work.json', work)
print(json.dumps({'model': str(directory), 'config': str(config), 'frozen_files': len(assets['source_hashes']), 'admitted': False, 'evidence': evidence(path)}))
