"""One observational native matching audit of the shared-prefix task protocol."""
import copy
from datetime import datetime, timezone
import shlex
import shutil
from ops import (guard, save, run, ssh, advance, evidence, tick, OUT, PREV,
                 RUNTIME, TOKEN, THREAD, STAGE, HOST, SSH)

owner = guard(600)
ssh('import json\nprint(json.dumps({"hostname":socket.gethostname()}))')
label = 'matched_pair'
local = OUT / label
local.mkdir(exist_ok=False)
for src, name in [(RUNTIME, 'native_runtime.py'),
                  (OUT / 'native_task_suffix.py', 'task_template.py'),
                  (OUT / 'native_paired_field.py', 'pair_template.py'),
                  (OUT / 'native_matched_pair.py', 'native_matched_pair.py')]:
    shutil.copyfile(src, local / name)
manifest = copy.deepcopy(tick.load(PREV / 'channel_null/native_manifest.json'))
stage = STAGE + '/' + label
manifest.update(stage=stage, matching_preregistration=evidence(OUT / 'matched_pair_prereg.md'))
manifest['diagnostic_files'] = {name: tick.digest(local / name) for name in
    ('native_runtime.py', 'task_template.py', 'pair_template.py', 'native_matched_pair.py')}
save(label + '/native_manifest.json', manifest)
save(label + '/execution_lease.json', {'project': 'cluster_project', 'thread_id': THREAD,
     'token': TOKEN, 'deadline_at': owner['deadline_at'],
     'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
advance([OUT / 'matched_pair_prereg.md', local / 'native_manifest.json',
         local / 'native_matched_pair.py', OUT / 'run_matched_pair.py'],
        next_action='Run finite actual criterion mask-target/matching fingerprint check on unchanged paired scopes;stop with partial evidence on matching change,no numerical retry loop.')
ssh('from pathlib import Path\nimport json\nPath(' + repr(stage) +
    ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
result = run(['scp', *SSH, *[str(local / name) for name in
             (*manifest['diagnostic_files'], 'native_manifest.json', 'execution_lease.json')],
             'songcl@' + HOST + ':' + stage + '/'])
assert result.returncode == 0, result.stderr
guard(500)
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && '
           'conda activate project_cluster && python -B ' + shlex.quote(stage + '/native_matched_pair.py') +
           ' --lease ' + shlex.quote(stage + '/execution_lease.json'))
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
result = run(['ssh', *SSH, 'songcl@' + HOST, shlex.join(['bash', '-lc', command])],
             min(900, int(remaining) - 120))
save(label + '_execution.json', {'returncode': result.returncode, 'stdout': result.stdout,
     'stderr': result.stderr, 'finished_at': datetime.now(timezone.utc).isoformat()})
result = run(['scp', *SSH, 'songcl@' + HOST + ':' + stage + '/native_matched_pair_result.json',
              str(local / 'native_matched_pair_result.json')])
assert result.returncode == 0, result.stderr
value = tick.load(local / 'native_matched_pair_result.json')
advance([local / 'native_matched_pair_result.json', OUT / (label + '_execution.json')],
        failure_scope='inconclusive',
        gate_result='Finite native matching audit completed=' + str(value.get('execution_completed')) +
                    ';identity matching=' + str(value.get('identity_matching_identical')) +
                    ';retain all failures and measured loss drift;not efficacy/admission.')
print({k: v for k, v in value.items() if k not in ('records', 'before', 'after',
      'baseline_components', 'native_match_signature', 'baseline_match_signature')})
