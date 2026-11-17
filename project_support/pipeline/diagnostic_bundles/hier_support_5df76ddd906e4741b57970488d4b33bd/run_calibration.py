from datetime import datetime, timezone
import json
import subprocess
from run_cpu import BUNDLE, ROOT, TOKEN, guard, tick

guard()
prototype = (BUNDLE/'hier_support.py').read_text(encoding='utf-8')
tests = (BUNDLE/'test_cpu.py').read_text(encoding='utf-8')
calibration = (BUNDLE/'calibration.py').read_text(encoding='utf-8')
program = 'PROTOTYPE='+repr(prototype)+'\nFROZEN_TEST_SOURCE='+repr(tests)+'\nCALIBRATION='+repr(calibration)+'\n'+'''
import os,sys,subprocess,types
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
module=types.ModuleType('hier_support')
sys.modules['hier_support']=module
exec(compile(PROTOTYPE,'<unchanged-prototype>','exec'),module.__dict__)
exec(compile(CALIBRATION,'<diagnostic-only-calibration>','exec'),globals())
'''
run = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
    'server-4','/home/songcl/.conda/envs/project_cluster/bin/python','-B','-'],
    input=program,text=True,encoding='utf-8',capture_output=True,timeout=180)
guard()
tick.save(BUNDLE/'calibration_attempt.json',{'token':TOKEN,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,
    'recorded_at':datetime.now(timezone.utc).isoformat()})
lines = [line for line in run.stdout.splitlines() if line.startswith('HIER_CALIBRATION_JSON=')]
if not lines:
    print(run.stderr[-5000:])
    raise SystemExit(run.returncode or 2)
result = {'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),**json.loads(lines[-1].split('=',1)[1])}
tick.save(BUNDLE/'calibration_result.json',result)
print(json.dumps(result,indent=2))
raise SystemExit(run.returncode)
