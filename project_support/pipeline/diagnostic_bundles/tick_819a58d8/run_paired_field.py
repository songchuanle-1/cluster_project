"""One same-prefix paired scope control under this owning foreground lease."""
import copy
from datetime import datetime, timezone
import shlex
import shutil
from ops import (guard, save, run, ssh, advance, evidence, tick, OUT, PREV,
                 RUNTIME, TOKEN, THREAD, STAGE, HOST, SSH)

owner = guard(600)
ssh('import json\nprint(json.dumps({"hostname":socket.gethostname()}))')
label = 'paired_field'
local = OUT / label
local.mkdir(exist_ok=False)
for src, name in [(RUNTIME, 'native_runtime.py'),
                  (OUT / 'native_task_suffix.py', 'task_template.py'),
                  (OUT / 'native_paired_field.py', 'native_paired_field.py')]:
    shutil.copyfile(src, local / name)
manifest = copy.deepcopy(tick.load(PREV / 'channel_null/native_manifest.json'))
stage = STAGE + '/' + label
manifest.update(stage=stage, paired_preregistration=evidence(OUT / 'paired_field_prereg.md'),
                task_template_evidence=evidence(OUT / 'native_task_suffix.py'))
manifest['diagnostic_files'] = {name: tick.digest(local / name) for name in
    ('native_runtime.py', 'task_template.py', 'native_paired_field.py')}
save(label + '/native_manifest.json', manifest)
save(label + '/execution_lease.json', {'project': 'cluster_project', 'thread_id': THREAD,
     'token': TOKEN, 'deadline_at': owner['deadline_at'],
     'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
advance([OUT / 'paired_field_prereg.md', local / 'native_manifest.json',
         local / 'native_paired_field.py', OUT / 'run_paired_field.py'],
        next_action='Run ONE same-native-prefix paired single/coherent scope diagnostic;preserve original null failures,quantify actual loss without trained-gain claims.')
ssh('from pathlib import Path\nimport json\nPath(' + repr(stage) +
    ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
result = run(['scp', *SSH, *[str(local / name) for name in
             (*manifest['diagnostic_files'], 'native_manifest.json', 'execution_lease.json')],
             'songcl@' + HOST + ':' + stage + '/'])
assert result.returncode == 0, result.stderr
guard(500)
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
           'conda activate project_cluster && python -B ' + shlex.quote(stage + '/native_paired_field.py') +
           ' --lease ' + shlex.quote(stage + '/execution_lease.json'))
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
result = run(['ssh', *SSH, 'songcl@' + HOST, shlex.join(['bash', '-lc', command])],
             min(900, int(remaining) - 120))
save(label + '_execution.json', {'returncode': result.returncode, 'stdout': result.stdout,
     'stderr': result.stderr, 'finished_at': datetime.now(timezone.utc).isoformat()})
result = run(['scp', *SSH, 'songcl@' + HOST + ':' + stage + '/native_paired_field_result.json',
              str(local / 'native_paired_field_result.json')])
assert result.returncode == 0, result.stderr
value = tick.load(local / 'native_paired_field_result.json')
advance([local / 'native_paired_field_result.json', OUT / (label + '_execution.json')],
        failure_scope='inconclusive',
        gate_result='Shared-prefix paired control completed=' + str(value.get('execution_completed')) +
                    ';exact reconstruction=' + str(value.get('controls_passed')) +
                    ';null failures retained,not trained efficacy/new-model admission.')
print({k: v for k, v in value.items() if k not in ('records', 'before', 'after', 'baseline_components')})
