"""Read-only readiness of explicitly named M95 assets on the authorized host."""
import json
from pathlib import Path
import subprocess
from audit_feature_path import BUNDLE, MODEL, TOKEN, guard, tick

guard()
program = '''
import datetime,hashlib,json,pathlib,subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
root=pathlib.Path('/data/songcl/Project/Cluster_project')
checkpoint=root/'pipeline/scm_admission_20260914/best.pth'
population=root/'pipeline/point_detail_population_20261009/result.manifest.json'
folder=root/'Cluster_checkpoints'/MODEL
def record(p):
    return {'path':str(p),'exists':p.exists(),'bytes':p.stat().st_size if p.is_file() else None}
result={'observed_at':datetime.datetime.now().astimezone().isoformat(),
        'm95_frozen_checkpoint':record(checkpoint),'existing_32group_population':record(population),
        'current_model_checkpoint_folder':record(folder),
        'bounded_exact_model_best_paths':[record(p) for p in sorted(folder.glob('*/best.pth'))[:4]],
        'dataset_root_exists':pathlib.Path('/home/songcl/data/data').is_dir(),
        'frozen_capture_groups':[0,60,101,124],
        'selection_scope':'Previously used fixed TRAIN group IDs; not selected by current predictions. Exact denominator to be observed, not assumed.',
        'gpu_calls':0,'writes':0}
if checkpoint.is_file():
    h=hashlib.sha256()
    with checkpoint.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    result['m95_frozen_checkpoint']['sha256']=h.hexdigest()
print(json.dumps(result))
'''
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12','server-4','/home/songcl/.conda/envs/project_cluster/bin/python','-B','-'],input='MODEL='+repr(MODEL)+'\n'+program,text=True,encoding='utf-8',capture_output=True,timeout=90)
guard()
tick.save(BUNDLE/'native_asset_probe_attempt.json',{'token':TOKEN,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
if result.returncode:
    raise RuntimeError(result.stderr)
observed=json.loads(result.stdout)
tick.save(BUNDLE/'native_asset_probe.json',{'token':TOKEN,**observed})
print(json.dumps(observed,indent=2))
