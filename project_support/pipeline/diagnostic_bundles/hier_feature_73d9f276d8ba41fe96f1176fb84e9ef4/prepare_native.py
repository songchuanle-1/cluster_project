"""Run only the CPU prepare branch of the future native capture adapter."""
import ast
import json
import subprocess
from audit_feature_path import BUNDLE,TOKEN,guard,tick
guard()
path=BUNDLE/'native_feature_capture.py'
source=path.read_text(encoding='utf-8')
ast.parse(source)
run=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12','server-4','/home/songcl/.conda/envs/project_cluster/bin/python','-B','-','--prepare-only','--token',TOKEN],input=source,text=True,encoding='utf-8',capture_output=True,timeout=180)
guard()
tick.save(BUNDLE/'native_prepare_attempt.json',{'token':TOKEN,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'adapter_sha256':tick.digest(path)})
if run.returncode:
    print(run.stderr[-5000:])
    raise SystemExit(run.returncode)
records=[line.removeprefix('FEATURE_NATIVE_PREPARE_JSON=') for line in run.stdout.splitlines() if line.startswith('FEATURE_NATIVE_PREPARE_JSON=')]
assert len(records)==1
record=json.loads(records[0])
tick.save(BUNDLE/'native_preparation.json',record)
print(json.dumps(record,indent=2))
