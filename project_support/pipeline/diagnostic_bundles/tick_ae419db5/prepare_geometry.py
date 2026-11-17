"""Freeze exact installed native FPS binding and runnable geometry protocol."""
import ast
import json
import shutil
from ops import ROOT, OUT, CID, guard, remote, save, evidence, tick, now

guard(300)
source_program = r'''
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1')
import hashlib,importlib,json,re,sys
from pathlib import Path
import torch
root=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
sys.path[:0]=[str(root),str(root/'framework/lib')]
from tools import train
wrapper=importlib.import_module('pointnet2.pointnet2_utils')
backend=importlib.import_module('pointnet2._ext')
package=Path(wrapper.__file__).parent
paths=[package/'_ext_src/src/sampling_gpu.cu',package/'_ext_src/src/sampling.cpp']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
sources=[]
for path in paths:
 text=path.read_text()
 lines=text.splitlines()
 selected=set()
 for index,line in enumerate(lines):
  if re.search(r'\bold\s*=\s*0\b|idxs\[0\]|furthest_point_sampling_kernel|furthest_point_sampling\(',line):
   selected.update(range(max(0,index-2),min(len(lines),index+4)))
 sources.append({'path':str(path),'sha256':sha(path),'source_excerpt':'\n'.join(str(index+1)+':'+lines[index] for index in sorted(selected)),
                 'literal_old_zero_present':bool(re.search(r'\bold\s*=\s*0\s*;',text))})
assert not torch.cuda.is_initialized()
print(json.dumps({'wrapper_path':str(Path(wrapper.__file__).resolve()),'wrapper_sha256':sha(wrapper.__file__),
 'binary_path':str(Path(backend.__file__).resolve()),'binary_sha256':sha(backend.__file__),
 'native_sources':sources,'cuda_initialized':False,'source_binary_correspondence_proved':False,
 'scope':'Freeze actual native import binding and provided source;compiled behavior still requires actual GPU execution.'}))
'''
binding = remote(source_program, timeout=120, conda=True)
binding_path = save('native_backend_binding.json', {'observed_at': now(), **binding})
payload = tick.load(OUT / 'native_geometry.json')
source_witness = []
for row in payload['cohort']:
    source_witness.append({'scene_id': row['scene_id'], 'physical_row0': row['coordinates'][0],
        'physical_row0_after_reversal': row['coordinates'][-1],
        'physical_row0_changes': row['coordinates'][0] != row['coordinates'][-1],
        'scope': 'Source-literal first-index witness only if supplied CUDA source starts at0;not a measured compiled FPS result or task deficit.'})
witness_path = save('source_first_index_witness.json', {'observed_at': now(),
    'source_old_zero_present': any(row['literal_old_zero_present'] for row in binding['native_sources']),
    'records': source_witness, 'compiled_behavior': None, 'physical_hierarchy_effect': None,
    'cuda_initialized': False, 'backend_binding': evidence(binding_path)})
runtime = OUT / 'native_runtime.py'
shutil.copyfile(ROOT / 'pipeline/diagnostic_bundles/tick_30bdd3a5/expression_fix/native_runtime.py', runtime)
ast.parse((OUT / 'native_geometry_probe.py').read_text(encoding='utf-8'))
ast.parse(runtime.read_text(encoding='utf-8'))
prior = tick.load(ROOT / 'pipeline/diagnostic_bundles/tick_30bdd3a5/expression_fix/native_manifest.json')
manifest = {key: prior[key] for key in ('schema_version', 'root', 'name', 'assets', 'expected_epoch', 'tolerance')}
manifest.update(candidate_id=CID, stage='/data/songcl/Project/Cluster_project/pipeline/relabel_geometry_ae419db5',
    geometry_sha256=tick.digest(OUT / 'native_geometry.json'), backend_binding=binding,
    protocol=evidence(OUT / 'relabeling_protocol.json'), physical_gpu=1,
    gpu_uuid='GPU-7f82edb9-f620-8045-caea-a75232265cd1', scientific_admission=False,
    diagnostic_files={name: tick.digest(OUT / name) for name in ('native_runtime.py', 'native_geometry_probe.py')})
manifest_path = save('native_manifest.json', manifest)
readiness = save('native_readiness.json', {'observed_at': now(), 'manifest': evidence(manifest_path),
    'geometry': evidence(OUT / 'native_geometry.json'), 'source_witness': evidence(witness_path),
    'syntax_checked': True, 'native_gpu_executions': 0, 'mask_readouts': 0, 'backward_runs': 0,
    'scope': 'Actual nonGPU preparation;no GPU controlPASS/admission/training,not a GPU lease or claim of idleness.'})
work = tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(row for row in work['candidates'] if row['id'] == CID)
candidate['evidence'].extend([evidence(binding_path), evidence(witness_path), evidence(manifest_path),
    evidence(readiness), evidence(OUT / 'native_geometry_probe.py'), evidence(runtime),
    evidence(ROOT / 'pipeline/reviews/motivation_review_20261020_ae419db5.md'),
    evidence(ROOT / 'pipeline/designs/exp_design_20261020_ae419db5.md')])
candidate.update(updated_at=now(), non_gpu_preparation_completed=True,
    next_action='Run frozen original native FPS/composed-hierarchy geometry test under a NEW current-tick execution lease only after fresh authorizedGPU1UUID/idleness/all3locks. Preserve identity failures and distinguish label renumbering from physical support changes;mask/task benefit remains a separate future test.')
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
print(json.dumps({'backend': {key:value for key,value in binding.items() if key!='native_sources'},
    'native_sources':binding['native_sources'],'source_witnesses':source_witness,
    'readiness':evidence(readiness),'native_gpu_executions':0}, indent=2))
