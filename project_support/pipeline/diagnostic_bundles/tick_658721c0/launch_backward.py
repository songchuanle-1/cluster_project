"""One token-bound, synchronous matched native backward diagnostic."""
import ast
import base64
import copy
import json
from pathlib import Path
from ops import ROOT, OUT, ID, TOKEN, THREAD, guard, evidence, remote, save, tick, now

owner, _ = guard(750)
local = OUT / 'backward_runtime'
local.mkdir(exist_ok=False)
for name in ('native_runtime.py', 'native_backward_task.py', 'contact_exchange.py'):
    data = (OUT / name).read_bytes()
    ast.parse(data, filename=name)
    (local / name).write_bytes(data)
manifest = copy.deepcopy(tick.load(OUT / 'native_manifest.json'))
stage = '/data/songcl/Project/Cluster_project/pipeline/contact_backward_658721c0'
protocol = save('native_backward_preregistration.json', {'preregistered_at': now(), 'candidate_id': ID,
    'test': 'Same frozen two TRAIN scenes/eight expressions, original native criterion. Baseline and contact arms each restore exact model state and seed1999; one native loss forward/backward each, zero optimizer steps.',
    'controls': 'Original targets, schedule50/70, checkpoint, precision, native operators and per-arm model state preserved. Observe loss and all parameter/message gradients; finite and nonzero new-message gradients are feasibility, not trained gain.',
    'resources': 'Measure same-process native batch2 single forward/backward allocated/reserved peaks and elapsed time for both arms. This is not bs1 warmup20/repeat100, full optimizer peak, standard FLOPs or resource admission.',
    'limits': 'Instrumented prototype only; no independent package/config, queue, model commit or training launch. Full-source numerical and permutation gates remain unproved.'})
manifest.update(stage=stage, protocol=evidence(protocol), diagnostic_files={name: tick.digest(local / name)
    for name in ('native_runtime.py', 'native_backward_task.py', 'contact_exchange.py')})
tick.save(local / 'native_manifest.json', manifest)
tick.save(local / 'native_lease.json', {'project': 'cluster_project', 'thread_id': THREAD, 'token': TOKEN,
    'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
files = ('native_runtime.py', 'native_backward_task.py', 'contact_exchange.py', 'native_manifest.json', 'native_lease.json')
payload = {name: base64.b64encode((local / name).read_bytes()).decode() for name in files}
hashes = {name: tick.digest(local / name) for name in files}
code = '''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE)
stage.mkdir(exist_ok=False)
for name,value in PAYLOAD.items():
 assert Path(name).name==name
 path=stage/name
 path.write_bytes(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'stage':str(stage),'hashes':HASHES}))
'''
staged = remote('STAGE=' + repr(stage) + '\nPAYLOAD=' + repr(payload) + '\nHASHES=' + repr(hashes) + '\n' + code)
save('backward_stage_observation.json', staged)
assert staged['returncode'] == 0
guard(700)
code = '''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
process=subprocess.run([sys.executable,'-B',str(stage/'native_backward_task.py'),'--lease',str(stage/'native_lease.json')],capture_output=True,text=True,timeout=660)
value={'returncode':process.returncode,'stdout':process.stdout[-8000:],'stderr':process.stderr[-10000:]}
result=stage/'native_backward_result.json'
if result.exists():value['native_result']=json.loads(result.read_text())
print(json.dumps(value))
'''
observed = remote('STAGE=' + repr(stage) + '\n' + code, timeout=720, conda=True)
observation_path = save('native_backward_observation.json', observed)
assert observed['returncode'] == 0
native = observed['data'].get('native_result', {})
native_path = save('native_backward_result.json', native)
work = tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(c for c in work['candidates'] if c['id'] == ID)
candidate['evidence'].extend([evidence(protocol), evidence(native_path), evidence(observation_path)])
candidate['stage'] = 'implementation'
candidate['next_action'] = 'Preserve the observed native contact controls/backward and honest scene uncertainty; integrate an independent model/config only after checking exact historical and literature differences, then test affected uniform efficiency/full-source gates. No training admission yet.'
tick.save(ROOT / 'pipeline/research_work.json', work)
print(json.dumps({'candidate_id': ID, 'returncode': observed['data']['returncode'], 'native_result': native, 'evidence': evidence(native_path)}, ensure_ascii=False))
