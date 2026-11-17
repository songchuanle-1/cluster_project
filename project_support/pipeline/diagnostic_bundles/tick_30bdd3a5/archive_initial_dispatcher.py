"""Preserve the initial dispatcher byte identity after adding measurement modes."""
from gpu1_ops import *
import hashlib
guard(180)
path=OUT/'run_native.py';text=path.read_text(encoding='utf-8')
text=text.replace("choices=['scale','expression','scale_fix','expression_fix']","choices=['scale','expression']")
assert text.count("args.label.startswith('scale')")==2
text=text.replace("args.label.startswith('scale')","args.label=='scale'")
marker="'entry_byte_identical_to_frozen_plan':not bool(manifest.get('measurement_revision')),'measurement_revision':manifest.get('measurement_revision'),'production_model_config_unchanged':True"
assert text.count(marker)==1
text=text.replace(marker,"'entry_byte_identical_to_frozen_plan':True")
work=tick.load(ROOT/'pipeline/research_work.json');relative=path.relative_to(ROOT).as_posix()
current=tick.digest(path)
old_refs=[e for c in work['candidates'] if c['id'] in ('m95-scale-specific-boundary-responsibility','m95-expression-specific-point-message') for e in c['evidence'] if e['path']==relative and e['sha256']!=current]
assert old_refs
expected={e['sha256'] for e in old_refs};assert len(expected)==1
variants=[text.encode('utf-8'),text.replace('\n','\r\n').encode('utf-8')]
payload=next(value for value in variants if hashlib.sha256(value).hexdigest() in expected)
archive=OUT/'run_native_initial_frozen.py';archive.write_bytes(payload)
assert tick.digest(archive)==next(iter(expected))
changed=0
for c in work['candidates']:
 if c['id'] not in ('m95-scale-specific-boundary-responsibility','m95-expression-specific-point-message'):continue
 for e in c['evidence']:
  if e['path']==relative and e['sha256'] in expected:
   e['original_path']=e['path'];e['path']=archive.relative_to(ROOT).as_posix();changed+=1
save('dispatcher_source_relocation.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'reason':'Dispatcher CLI gained preregistered measurement modes after initialattempts. Preserve initialexactbytes/hash at immutablearchive;relocateONLYoriginaldispatcherevidencepaths,notresult/negativeevidence orscientifichistory. Currentmodifieddispatcherretainedatcurrenthashandwillnotbeeditedagain.','original_path':relative,'initial_sha256':next(iter(expected)),'archived_identical_source':evidence(archive),'current_dispatcher':evidence(path),'relocated_references':changed,'result_evidence_unchanged':True})
for c in work['candidates']:
 if c['id'] in ('m95-scale-specific-boundary-responsibility','m95-expression-specific-point-message'):c['evidence'].append(evidence(OUT/'dispatcher_source_relocation.json'))
guard();tick.save(ROOT/'pipeline/research_work.json',work)
print(json.dumps({'initial_source_hash_preserved':True,'relocated_source_references':changed,'negative_results_unchanged':True},ensure_ascii=True))
