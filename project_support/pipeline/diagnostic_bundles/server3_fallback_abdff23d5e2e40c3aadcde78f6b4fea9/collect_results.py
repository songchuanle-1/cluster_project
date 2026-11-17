"""Extract structured receipts, preserving every full attempt unchanged."""
from datetime import datetime, timezone
import json
from pathlib import Path
from run_remote import BUNDLE, TOKEN, guard, tick

guard()
markers=('SERVER3_DEPLOY_JSON=', 'FEATURE_NATIVE_PREPARE_JSON=',
    'FEATURE_NATIVE_CAPTURE_JSON=', 'SERVER3_COMPATIBILITY_JSON=',
    'SERVER3_EXTENSION_BUILD_JSON=', 'SERVER3_POSTVERIFY_JSON=', 'SERVER3_CAPTURE_ANALYSIS_JSON=', 'SERVER3_CAPTURE_METADATA_JSON=')
records=[]
for path in sorted(BUNDLE.glob('*_attempt.json')):
    attempt=tick.load(path)
    results=[]
    for line in attempt.get('stdout','').splitlines():
        if any(line.startswith(marker) for marker in markers):
            results.append(json.loads(line.split('=',1)[1]))
    result_path=path.with_name(path.name.replace('_attempt.json','_result.json'))
    result={'token':TOKEN,'attempt':{'path':path.relative_to(tick.paths('cluster_project')[0].parent).as_posix(),
        'sha256':tick.digest(path)},'returncode':attempt['returncode'],'results':results}
    if not results:
        result['failure_excerpt']=attempt.get('stderr','')[-5000:]
    if result_path.exists():assert tick.load(result_path)==result
    else:tick.save(result_path,result)
    records.append({'name':result_path.name,'returncode':attempt['returncode'],
        'structured_results':len(results),'sha256':tick.digest(result_path)})
print(json.dumps({'token':TOKEN,'results':records},indent=2))
