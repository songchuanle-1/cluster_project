"""Verify frozen existing M95 assets, then one matched native batch2 test."""
from datetime import datetime, timezone
import copy
import json
import shlex
import shutil
from ops import guard, save, run, ssh, add, evidence, ROOT, OUT, TOKEN, THREAD
import foreground_tick as tick

owner = guard(600)
name = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
manifest = copy.deepcopy(tick.load(OUT / 'shape_native/native_manifest.json'))
assets = manifest['assets']
root = manifest['root']
checkpoint = '/data/songcl/Project/Cluster_project/pipeline/hds_server4_3c22e34d/frozen_m95.pth'
expected = 'fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
config = root + '/configs/Quard/ctf_hcg_csort/' + name + '.yaml'
program = 'from pathlib import Path\nimport hashlib,json\ndef sha(p):\n h=hashlib.sha256()\n with Path(p).open("rb") as f:\n  for b in iter(lambda:f.read(8388608),b""):h.update(b)\n return h.hexdigest()\n'
program += 'd=Path(' + repr(root + '/framework/model/Quard_model/' + name) + ')\n'
program += 'sources={p.name:sha(p) for p in d.glob("*.py")}\n'
program += 'print(json.dumps({"source_hashes":sources,"checkpoint_sha256":sha(' + repr(checkpoint) + '),"config_sha256":sha(' + repr(config) + ')}))'
asset_probe = ssh(program, timeout=90)
save('m95_assets.json', asset_probe)
assert asset_probe['checkpoint_sha256'] == expected
for filename, digest in asset_probe['source_hashes'].items():
    assert tick.digest(ROOT / 'Cluster/framework/model/Quard_model' / name / filename) == digest
assets.update(source_hashes=asset_probe['source_hashes'], checkpoint=checkpoint, checkpoint_sha256=expected,
              config_path=config, config_sha256=asset_probe['config_sha256'], selection='ExistingavailableM95epoch16,notverifiedhistoricalchampion')
manifest['name'] = name
stage = '/data/songcl/Project/Cluster_project/pipeline/m95_padding_control_6a3484ad'
manifest['stage'] = stage
manifest['m95_padding_preregistration'] = evidence(OUT / 'm95_padding_prereg.md')
local = OUT / 'm95_native'
local.mkdir(exist_ok=False)
shutil.copyfile(OUT / 'native_qf/native_runtime.py', local / 'native_runtime.py')
shutil.copyfile(OUT / 'native_m95_padding.py', local / 'native_batch2.py')
manifest['diagnostic_files'] = {n: tick.digest(local / n) for n in ('native_runtime.py', 'native_batch2.py')}
save('m95_native/native_manifest.json', manifest)
save('m95_native/execution_lease.json', {'project': 'cluster_project', 'thread_id': THREAD, 'token': TOKEN,
    'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
work = tick.load(ROOT / 'pipeline/research_work.json')
c = next(c for c in work['candidates'] if c['id'] == 'hierarchical-padding-context-invariance-audit')
c.update(stage='validation', next_action='Execute exactavailableM95epoch16 counterpart on sameTRAINbatch2 with sameidentity/zero/nonpadded controls;no baselinepatch/training/VAL.')
add(c, [OUT / 'shape_native/native_batch2_result.json', OUT / 'm95_padding_prereg.md', OUT / 'm95_assets.json', local / 'native_manifest.json'])
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
save('m95_stage.json', ssh('from pathlib import Path\nimport json\nPath(' + repr(stage) + ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files = [str(local / n) for n in (*manifest['diagnostic_files'], 'native_manifest.json', 'execution_lease.json')]
upload = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', *files, 'songcl@192.168.1.115:' + stage + '/'])
save('m95_upload.json', {'returncode': upload.returncode, 'stderr': upload.stderr})
assert upload.returncode == 0
guard(450)
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
           'python -B ' + shlex.quote(stage + '/native_batch2.py') + ' --lease ' + shlex.quote(stage + '/execution_lease.json'))
remaining = (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
response = run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ServerAliveInterval=15',
                '-o', 'ServerAliveCountMax=3', 'songcl@192.168.1.115', shlex.join(['bash', '-lc', command])], min(600, int(remaining)-120))
save('m95_execution.json', {'returncode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr,
                          'finished_at': datetime.now(timezone.utc).isoformat()})
fetch = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
             'songcl@192.168.1.115:' + stage + '/native_batch2_result.json', str(local / 'native_batch2_result.json')])
save('m95_fetch.json', {'returncode': fetch.returncode, 'stderr': fetch.stderr})
assert fetch.returncode == 0, response.stderr
r = tick.load(local / 'native_batch2_result.json')
print(json.dumps({'passed': r['passed'], 'native_forwards': r['native_forwards'], 'suffix_replays': r['suffix_replays'],
    'controls': r.get('controls'), 'same_shape_cases': r.get('same_shape_cases'),
    'padding_invariance_pass': r.get('same_shape_padding_invariance_pass'), 'error': r.get('error'),
    'stderr_tail': response.stderr[-1500:] if response.returncode else None}))
