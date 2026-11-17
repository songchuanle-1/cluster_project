"""Freeze and execute one current-lease native diagnostic, not training."""
import copy
from datetime import datetime, timezone
import shutil
from ops import *

owner = guard(600)
ssh('import json\nprint(json.dumps({"hostname":socket.gethostname()}))')
label = 'moment'
local = OUT / label
local.mkdir(exist_ok=False)
runtime = ROOT / 'pipeline/diagnostic_bundles/tick_ce9bc689/trace_m95_1/native_runtime.py'
for src in (runtime, OUT / 'native_moment.py'):
    shutil.copyfile(src, local / src.name)
manifest = copy.deepcopy(tick.load(ROOT / 'pipeline/diagnostic_bundles/tick_819a58d8/task_suffix/native_manifest.json'))
stage = STAGE + '/' + label
manifest.update(candidate_id=CID, stage=stage, protocol=evidence(OUT/'protocol.json'))
manifest['diagnostic_files'] = {name:tick.digest(local/name) for name in ('native_runtime.py','native_moment.py')}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,
     'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'source_control.json',local/'native_manifest.json',local/'native_moment.py',OUT/'run_native.py'],
        next_action='Execute frozen native TRAIN forward/backward and paired point-vs-hierarchy moment permutation controls')
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
result=run(['scp',*SSH,*[str(local/name) for name in (*manifest['diagnostic_files'],'native_manifest.json','execution_lease.json')],
            'songcl@192.168.1.115:'+stage+'/'])
assert result.returncode==0,result.stderr
guard(500)
command=('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+
         shlex.quote(stage+'/native_moment.py')+' --lease '+shlex.quote(stage+'/execution_lease.json'))
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(900,int(remaining)-120))
save('native_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
pulled=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/native_moment_result.json',str(local/'native_moment_result.json')])
assert pulled.returncode==0,pulled.stderr
value=tick.load(local/'native_moment_result.json')
advance([local/'native_moment_result.json',OUT/'native_execution.json'],failure_scope='inconclusive',
        gate_result='Native moment recording complete='+str(value.get('execution_completed'))+';identity controls='+str(value.get('controls_passed'))+';task deficit/admission not established')
print(json.dumps({k:v for k,v in value.items() if k not in ('before','after')},ensure_ascii=False))
