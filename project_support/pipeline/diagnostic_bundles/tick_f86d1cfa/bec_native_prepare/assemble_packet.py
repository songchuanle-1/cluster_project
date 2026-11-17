"""Static packet assembly only; does not create execution materials or authorize run."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_6bdbcf77/new_candidate_prepare'
REFERENCE=ROOT/'pipeline/diagnostic_bundles/tick_4694ba96/cts_native_prepare'
SOURCE_PREP='2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d'
CID='hierarchy-cross-level-bipartite-edge-composition'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):
    p=HERE/name
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    assert sha(SOURCE/'preparation.json')==SOURCE_PREP
    source=json.loads((SOURCE/'preparation.json').read_text())
    hashes={p.name:sha(p) for p in sorted((HERE/'candidate_model').glob('*.py'))}
    assert len(hashes)==8
    for name,h in hashes.items():assert h==sha(SOURCE/'staged_repository/framework/model/Quard_model'/source['model_name']/name)
    assert sha(HERE/'candidate.yaml')==sha(SOURCE/'staged_repository'/source['config'])
    version={'schema_version':1,'candidate_id':CID,'experiment_id':'M215-BEC','code_commit':None,'parent_commit':None,
      'candidate_source_hashes':hashes,'candidate_config_sha256':sha(HERE/'candidate.yaml'),'source_files':{row['path']:row['sha256'] for row in source['source_files']},
      'original_source_preparation_sha256':SOURCE_PREP,'base_reference_commit':source['base_reference_commit'],
      'future_version_parent':None,'isolated_source_version':None,
      'verification_scope':'Frozen unversioned BEC source bytes only; no actual Git commit/parent or native execution evidence. Base reference is not a future-version parent.'}
    save('source_version_binding.json',version)
    m=json.loads((REFERENCE/'manifest_template.json').read_text())
    m.update(candidate_id=CID,experiment_id='M215-BEC',candidate_name=source['model_name'],config=source['config'],
      code_commit=None,source_version_commit=None,source_parent_commit=None,candidate_source_hashes=hashes,
      source_preparation_sha256=SOURCE_PREP,source_version_binding_sha256=sha(HERE/'source_version_binding.json'),
      base_reference_commit=source['base_reference_commit'],future_version_parent=None,draft_execution_disabled=True,
      protocol='Execution-disabled unversioned BEC preparation only. Original native TRAIN2 and resources NOT_RUN. Future actual source commit/parent, independently reviewed new operational bundle, current owner/context/deadline, selected authorized idle GPU, assets, locks, manifest and lease remain mandatory. Base reference is not a source parent; no adapter included.')
    diag=['native_runtime.py','worker.py','candidate.yaml','source_version_binding.json']+['candidate_model/'+n for n in hashes]
    m['diagnostic_files']={n:sha(HERE/n) for n in diag}
    save('manifest_template.json',m)
    print(json.dumps({'manifest_sha256':sha(HERE/'manifest_template.json'),'diagnostic_count':len(diag),'binding_sha256':sha(HERE/'source_version_binding.json')}))
if __name__=='__main__':main()
