"""One frozen coherent-field matched diagnostic, no scientific gate changes."""
import copy
from datetime import datetime, timezone
import shlex
import shutil
from ops import (guard, save, run, ssh, advance, evidence, tick, OUT, PREV,
                 RUNTIME, TOKEN, THREAD, STAGE, HOST, SSH)

owner = guard(600)
ssh('import json\nprint(json.dumps({"hostname":socket.gethostname()}))')
label = 'coherent_channel'
local = OUT / label
local.mkdir(exist_ok=False)
for src, name in [(RUNTIME, 'native_runtime.py'),
                  (OUT / 'native_task_suffix.py', 'task_template.py'),
                  (OUT / 'native_coherent_channel.py', 'native_coherent_channel.py')]:
    shutil.copyfile(src, local / name)
manifest = copy.deepcopy(tick.load(PREV / 'channel_null/native_manifest.json'))
stage = STAGE + '/' + label
manifest.update(stage=stage, coherent_preregistration=evidence(OUT / 'coherent_channel_prereg.md'),
                task_template_evidence=evidence(OUT / 'native_task_suffix.py'),
                original_null_failure=evidence(PREV / 'channel_null/native_channel_null_result.json'))
manifest['diagnostic_files'] = {name: tick.digest(local / name) for name in
    ('native_runtime.py', 'task_template.py', 'native_coherent_channel.py')}
save(label + '/native_manifest.json', manifest)
save(label + '/execution_lease.json', {'project': 'cluster_project', 'thread_id': THREAD,
     'token': TOKEN, 'deadline_at': owner['deadline_at'],
     'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
advance([OUT / 'coherent_channel_prereg.md', local / 'native_manifest.json',
         local / 'native_coherent_channel.py', OUT / 'run_coherent_channel.py'],
        next_action='Execute same fixed24readouts with coherent outside-coarse sender field and receiver-only native suffix;match row/null input energy,retain strict failures and actual task loss.')
ssh('from pathlib import Path\nimport json\nPath(' + repr(stage) +
    ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
result = run(['scp', *SSH, *[str(local / name) for name in
             (*manifest['diagnostic_files'], 'native_manifest.json', 'execution_lease.json')],
             'songcl@' + HOST + ':' + stage + '/'])
assert result.returncode == 0, result.stderr
guard(500)
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
           'conda activate project_cluster && python -B ' + shlex.quote(stage + '/native_coherent_channel.py') +
           ' --lease ' + shlex.quote(stage + '/execution_lease.json'))
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
result = run(['ssh', *SSH, 'songcl@' + HOST, shlex.join(['bash', '-lc', command])],
             min(900, int(remaining) - 120))
save(label + '_execution.json', {'returncode': result.returncode, 'stdout': result.stdout,
     'stderr': result.stderr, 'finished_at': datetime.now(timezone.utc).isoformat()})
result = run(['scp', *SSH, 'songcl@' + HOST + ':' + stage + '/native_coherent_channel_result.json',
              str(local / 'native_coherent_channel_result.json')])
assert result.returncode == 0, result.stderr
value = tick.load(local / 'native_coherent_channel_result.json')
advance([local / 'native_coherent_channel_result.json', OUT / (label + '_execution.json')],
        failure_scope='inconclusive',
        gate_result='Coherent-field task-suffix complete=' + str(value.get('execution_completed')) +
                    ';exact reconstruction=' + str(value.get('controls_passed')) +
                    ';native null failures retained,not novel model or efficacy/admission.')
print({k: v for k, v in value.items() if k not in ('records', 'before', 'after', 'baseline_components')})
