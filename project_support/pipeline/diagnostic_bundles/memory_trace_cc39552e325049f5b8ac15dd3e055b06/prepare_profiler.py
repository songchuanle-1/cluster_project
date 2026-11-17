"""Install pinned profiler-only dependencies into the diagnostic artifact tree."""
from datetime import datetime,timezone
import json
import subprocess
from run import BUNDLE,TOKEN,guard,tick
from independent_native import REMOTE

guard()
path=BUNDLE/'profiler_dependencies.json'
assert not path.exists()
payload='DIAGNOSTIC_ROOT='+repr(REMOTE)+'\n'+'''
import os,sys,subprocess,json,hashlib
from pathlib import Path
import importlib.metadata as metadata
assert subprocess.check_output(['hostname'],text=True).strip()=='sysu311-MS-7C59'
root=Path(DIAGNOSTIC_ROOT)
assert root.resolve().parent==Path('/sdc1/songcl/Project/Cluster_project/pipeline').resolve()
target=root/'profiler_dependencies'
assert not target.exists()
temporary=root/'pip_tmp'
temporary.mkdir()
before={name:metadata.version(name) for name in ('torch','transformers','numpy')}
versions=['fvcore==0.1.5.post20221221','iopath==0.1.10','yacs==0.1.8',
          'termcolor==2.4.0','tabulate==0.9.0','portalocker==2.8.2']
environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(temporary),CUDA_VISIBLE_DEVICES='')
command=[sys.executable,'-B','-m','pip','install','--index-url','https://pypi.org/simple',
         '--disable-pip-version-check','--no-cache-dir','--no-deps','--no-build-isolation',
         '--no-compile','--timeout','8','--retries','1','--target',str(target)]+versions
process=subprocess.run(command,text=True,capture_output=True,env=environment,timeout=150)
record={'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr,
        'target':str(target),'pinned_versions':versions,'base_versions_before':before,
        'project_local_only':True,'gpu_allocations':0}
record['base_versions_after']={name:metadata.version(name) for name in before}
assert record['base_versions_after']==before
if process.returncode==0:
 sys.path.insert(0,str(target))
 try:
  import fvcore
  from fvcore.nn import FlopCountAnalysis
  record['import_passed']=True
  record['fvcore_version']=fvcore.__version__
  record['critical_file_sha256']={str(path.relative_to(target)):hashlib.sha256(path.read_bytes()).hexdigest()
    for path in (target/'fvcore/nn/flop_count.py',target/'fvcore/nn/jit_analysis.py',target/'fvcore/nn/jit_handles.py')}
 except Exception as exc:
  record.update(import_passed=False,import_error=type(exc).__name__+': '+str(exc))
print('PROFILER_SETUP='+json.dumps(record))
'''
process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
    'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=payload,
    text=True,encoding='utf-8',capture_output=True,timeout=175)
guard()
record={'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'runner_sha256':tick.digest(BUNDLE/'prepare_profiler.py'),'returncode':process.returncode,
    'stdout':process.stdout,'stderr':process.stderr}
rows=[json.loads(line.split('=',1)[1]) for line in process.stdout.splitlines() if line.startswith('PROFILER_SETUP=')]
if rows:
    assert len(rows)==1
    record['result']=rows[0]
tick.save(path,record)
if rows:print(json.dumps({k:v for k,v in rows[0].items() if k not in ('stdout','stderr')},ensure_ascii=False))
else:print(process.stdout[-5000:])
print(process.stderr[-5000:])
assert process.returncode==0 and rows and rows[0].get('import_passed'),record
