"""One current-lease actual task-loss matched diagnostic, no training dispatch."""
import copy
from datetime import datetime, timezone
import shlex
import shutil
from ops import (guard, save, run, ssh, advance, evidence, tick, OUT, PREV,
                 RUNTIME, TOKEN, THREAD, STAGE, HOST, SSH)

owner = guard(600)
ssh('import json\nprint(json.dumps({"hostname":socket.gethostname()}))')
label = 'task_suffix'
local = OUT / label
local.mkdir(exist_ok=False)
for src in (RUNTIME, OUT / 'native_task_suffix.py'):
    shutil.copyfile(src, local / src.name)
manifest = copy.deepcopy(tick.load(PREV / 'channel_null/native_manifest.json'))
stage = STAGE + '/' + label
manifest.update(stage=stage, task_suffix_preregistration=evidence(OUT / 'task_suffix_prereg.md'),
                original_null_failure=evidence(PREV / 'channel_null/native_channel_null_result.json'))
manifest['diagnostic_files'] = {name: tick.digest(local / name) for name in ('native_runtime.py', 'native_task_suffix.py')}
save(label + '/native_manifest.json', manifest)
save(label + '/execution_lease.json', {'project': 'cluster_project', 'thread_id': THREAD,
     'token': TOKEN, 'deadline_at': owner['deadline_at'],
     'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
advance([OUT / 'task_suffix_prereg.md', local / 'native_manifest.json',
         local / 'native_task_suffix.py', OUT / 'run_task_suffix.py'],
        next_action='Execute original native TRAIN forward/backward and exact matched task suffix on all24 frozen readouts;retain all null1e-6 failures and actual loss deltas,not efficacy.')
ssh('from pathlib import Path\nimport json\nPath(' + repr(stage) +
    ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
result = run(['scp', *SSH, *[str(local / name) for name in
             (*manifest['diagnostic_files'], 'native_manifest.json', 'execution_lease.json')],
             'songcl@' + HOST + ':' + stage + '/'])
assert result.returncode == 0, result.stderr
guard(500)
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
           'conda activate project_cluster && python -B ' + shlex.quote(stage + '/native_task_suffix.py') +
           ' --lease ' + shlex.quote(stage + '/execution_lease.json'))
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
result = run(['ssh', *SSH, 'songcl@' + HOST, shlex.join(['bash', '-lc', command])],
             min(900, int(remaining) - 120))
save(label + '_execution.json', {'returncode': result.returncode, 'stdout': result.stdout,
     'stderr': result.stderr, 'finished_at': datetime.now(timezone.utc).isoformat()})
result = run(['scp', *SSH, 'songcl@' + HOST + ':' + stage + '/native_task_suffix_result.json',
              str(local / 'native_task_suffix_result.json')])
assert result.returncode == 0, result.stderr
value = tick.load(local / 'native_task_suffix_result.json')
advance([local / 'native_task_suffix_result.json', OUT / (label + '_execution.json')],
        failure_scope='inconclusive',
        gate_result='Actual task-suffix recording complete=' + str(value.get('execution_completed')) +
                    ';native reconstruction controls=' + str(value.get('controls_passed')) +
                    ';original strict null failures preserved;not efficacy/admission.')
print({k: v for k, v in value.items() if k not in ('records', 'before', 'after', 'baseline_components')})
