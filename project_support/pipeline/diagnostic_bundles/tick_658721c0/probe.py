"""Stage this tick's diagnostic files and run a finite remote CPU/source probe."""
import base64
import json
from pathlib import Path
from ops import ROOT, OUT, ID, TOKEN, guard, evidence, remote, save, tick

guard(600)
stage = '/data/songcl/Project/Cluster_project/pipeline/contact_658721c0'
payload = {name: base64.b64encode((OUT / name).read_bytes()).decode()
           for name in ('contact_exchange.py', 'cpu_contact_task.py')}
source_hashes = {name: tick.digest(OUT / name) for name in payload}
manifest = tick.load(ROOT / 'pipeline/diagnostic_bundles/tick_c121c67d/native_relabel/native_manifest.json')
code = '''
import base64,fcntl,hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
stage=Path(STAGE)
stage.mkdir(exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 path.write_bytes(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
fle=Path(FLE)
assert hashlib.sha256(fle.read_bytes()).hexdigest()==FLE_SHA
cards={}
for index,uuid in ((0,'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),(1,'GPU-7f82edb9-f620-8045-caea-a75232265cd1')):
 row=subprocess.check_output(['nvidia-smi','-i',str(index),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 assert [s.strip() for s in row.split(',')][:2]==[str(index),uuid]
 contexts=subprocess.check_output(['nvidia-smi','-i',str(index),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 locks={}
 for kind in ('training','diagnostic','exclusive'):
  with open('/tmp/cluster_project_gpu'+str(index)+'_'+kind+'.lock','a+b') as handle:
   try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True
   except BlockingIOError:locks[kind]=False
 cards[str(index)]={'gpu':row,'contexts':contexts,'locks_available':locks}
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'cards':cards,'stage':str(stage),'source_hashes':HASHES}))
'''
code = ('STAGE=' + repr(stage) + '\nPAYLOAD=' + repr(payload) + '\nHASHES=' + repr(source_hashes)
    + '\nFLE=' + repr(manifest['assets']['operator_path'])
    + '\nFLE_SHA=' + repr(manifest['assets']['operator_sha256']) + '\n' + code)
observation = remote(code)
save('initial_resources.json', observation)
assert observation['returncode'] == 0, 'Stage/resource observation failed; preserve evidence'
result = remote("import subprocess,json\np=subprocess.run(['python','-B'," + repr(stage + '/cpu_contact_task.py')
    + "],capture_output=True,text=True,timeout=120)\nprint(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))", timeout=180, conda=True)
path = save('cpu_contact_observation.json', result)
assert result['returncode'] == 0 and result['data']['returncode'] == 0, 'CPU source test failed; preserve evidence'
data = json.loads(result['data']['stdout'])
source_check = save('source_distinction.json', {'observed_at': result['observed_at'], 'protocol': evidence(OUT / 'contact_protocol.json'),
    'actual_result': data, 'diagnostic_source_hashes': source_hashes,
    'frozen_fle_operator_sha256': manifest['assets']['operator_sha256'],
    'historical_boundary_scope': evidence(ROOT / 'pipeline/reports/m95_feature_boundary_prereg_20260926-1613.md'),
    'limits': 'Not native task benefit, trained efficacy or proof of publication novelty. No original failed gate is waived.'})
guard()
work = tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(c for c in work['candidates'] if c['id'] == ID)
candidate['evidence'].append(evidence(source_check))
candidate['next_action'] = 'Run frozen two-scene/eight-expression native TRAIN contact capture and matched point-feature readout; check all original numerical controls before task interpretation.'
tick.save(ROOT / 'pipeline/research_work.json', work)
print(json.dumps({'candidate_id': ID, 'source_result': data, 'resources': observation['data'], 'evidence': evidence(source_check)}, ensure_ascii=False))
