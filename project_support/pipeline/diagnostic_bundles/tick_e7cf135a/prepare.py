"""Freeze a prediction-blind TRAIN cohort and stage a native diagnostic."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import register

c = register.c
OUT, ROOT = register.OUT, register.ROOT


def metadata():
    code = '''
import hashlib,json
from pathlib import Path
assert hashlib.sha256(Path(ANNOTATION).read_bytes()).hexdigest()==ANNOTATION_SHA
assert hashlib.sha256(Path(SOURCE).read_bytes()).hexdigest()==SOURCE_SHA
rows=json.loads(Path(ANNOTATION).read_text());rows.sort(key=lambda row:row['scene_id'])
groups=[];current=[];scene=''
for row in rows:
 if row['scene_id']!=scene:
  if current:groups.append(current)
  scene=row['scene_id'];current=[]
 if len(current)>=4:groups.append(current);current=[]
 current.append(row)
groups.append(current)
seen=set();cohort=[]
for index,group in enumerate(groups):
 scene=group[0]['scene_id']
 if scene in seen:continue
 seen.add(scene)
 cohort.append({'scene_id':scene,'group_index':index,'expression_ids':[{'object_id':str(row['object_id']),'ann_id':str(row['ann_id'])} for row in group]})
 if len(cohort)==8:break
assert len(cohort)==8
print(json.dumps({'cohort':cohort,'cuda_initialized':False,'selection':'first8distinctTRAINscenes/firstlanguagegroup; no predictions inspected','metadata_method':'Mirror hashed native dataset stable annotation sort/group-of4 only; worker must verify exact native dataset.scene_inputs before predictions'}))
'''
    frozen = c.tick.load(ROOT / 'pipeline/diagnostic_bundles/tick_658721c0/native_manifest.json')
    assets = frozen['assets']
    observation = c.remote('ANNOTATION='+repr(assets['annotation_path'])+'\nANNOTATION_SHA='+repr(assets['annotation_sha256'])+'\nSOURCE='+repr(frozen['root']+'/framework/dataset/scannetv2.py')+'\nSOURCE_SHA='+repr(assets['dataset_source_sha256'])+'\n'+code,timeout=60)
    path = c.save('cohort_metadata_observation_cpu.json', observation)
    assert observation['returncode'] == 0
    c.save('cohort.json', observation['data'])
    c.advance([path, OUT / 'cohort.json'], 'Execute prediction-blind fixed8scene native capture and preregistered scale interventions; no structural model or training.')
    print(json.dumps(observation['data'], ensure_ascii=False))


def stage():
    owner, _ = c.guard(1200)
    supplement = c.save('matched_correspondence_preregistration.json', {
        'preregistered_at': c.now(), 'candidate_id': c.CID,
        'primary_protocol_unchanged': c.evidence(OUT / 'preregistration.json'),
        'reason': 'Omission removes message energy and bank-token rotation changes point-level multiplicities when cluster sizes differ. Add separate distribution-preserving correspondence controls before observing outcomes; do not replace or select the primary tests.',
        'arms': ['middle_point_message_cycle', 'coarse_point_message_cycle', 'middle_and_coarse_same_point_message_cycle'],
        'permutation': 'One fixed one-position cycle of valid point rows in xyz lexicographic order per expression; padding unchanged. Use identical donor permutation for middle+coarse to preserve their joint point-message pairing. No alternative permutation selection.',
        'invariants': 'Each scale point-message multiset exactly preserved, fine messages/query/weights/formula/precision/GT unchanged.',
        'readout': 'Report all-arm valid/foreground/non-target MAE and native-query mask change, plus MC-M-C interaction on scene means; sensitivity alone does not establish benefit, complementarity or a new architecture.',
        'training': 0})
    frozen = c.tick.load(ROOT / 'pipeline/diagnostic_bundles/tick_658721c0/native_manifest.json')
    runtime = (ROOT / 'pipeline/diagnostic_bundles/tick_658721c0/native_runtime.py').read_text(encoding='utf-8')
    runtime = runtime.replace('658721c071ae487ea47224e55d51abde', c.TOKEN).replace('01a04987-fdbe-7301-b2f0-f9b6ab60f74c', c.THREAD)
    payload = {'native_runtime.py': runtime.encode('utf-8'), 'worker.py': (OUT / 'worker.py').read_bytes()}
    manifest = copy.deepcopy(frozen)
    manifest.update(stage=c.STAGE, current_token=c.TOKEN, candidate_id=c.CID,
        protocol=c.evidence(OUT / 'preregistration.json'),
        matched_correspondence_protocol=c.evidence(supplement),
        cohort=c.tick.load(OUT / 'cohort.json')['cohort'])
    manifest['diagnostic_files'] = {name: hashlib.sha256(value).hexdigest() for name,value in payload.items()}
    c.save('native_manifest.json', manifest)
    payload['native_manifest.json'] = (OUT / 'native_manifest.json').read_bytes()
    c.save('execution_lease.json', {'token': c.TOKEN,'thread_id':c.THREAD,'project':'cluster_project',
        'deadline_at':owner['deadline_at'],'native_manifest_sha256':c.tick.digest(OUT / 'native_manifest.json')})
    payload['execution_lease.json'] = (OUT / 'execution_lease.json').read_bytes()
    encoded = {name:base64.b64encode(value).decode('ascii') for name,value in payload.items()}
    hashes = {name:hashlib.sha256(value).hexdigest() for name,value in payload.items()}
    code='''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE);stage.mkdir(exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 with path.open('xb') as stream:stream.write(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'staged':str(stage),'files':len(PAYLOAD)}))
'''
    observed=c.save('staging.json',c.remote('STAGE='+repr(c.STAGE)+'\nPAYLOAD='+repr(encoded)+'\nHASHES='+repr(hashes)+'\n'+code))
    assert c.tick.load(observed)['returncode']==0
    c.advance([supplement,OUT/'native_manifest.json',OUT/'worker.py',observed,Path(__file__)],
        'Execute frozen native scale diagnosis; labels are readouts only, no PCE edits or training.')
    print(json.dumps({'staged':c.STAGE,'files':len(payload)}))


def run():
    c.guard(1200)
    code='''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
process=subprocess.run([sys.executable,'-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json')],capture_output=True,text=True,timeout=580)
result={'returncode':process.returncode,'stdout':process.stdout[-8000:],'stderr':process.stderr[-14000:]}
path=stage/'native_scale_result.json'
if path.exists():result['result']=json.loads(path.read_text())
print(json.dumps(result))
'''
    observation=c.remote('STAGE='+repr(c.STAGE)+'\n'+code,timeout=620,conda=True)
    execution=c.save('native_execution.json',observation)
    assert observation['returncode']==0,'Observer failed; reconcile without blind retry'
    result=observation['data'].get('result',{})
    path=c.save('native_scale_result.json',result)
    c.advance([execution,path],'Analyze all frozen8scene scale effects and controls before choosing any structural mechanism; no training admission.')
    print(json.dumps({'returncode':observation['data']['returncode'],
        'execution_completed':result.get('execution_completed'),'error':result.get('error'),
        'scenes_completed':len(result.get('batches',[]))*2,
        'summary':result.get('summary')},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('probe','metadata','stage','run'))
    args=parser.parse_args()
    if args.operation=='probe':c.probe()
    elif args.operation=='metadata':metadata()
    elif args.operation=='stage':stage()
    else:run()
