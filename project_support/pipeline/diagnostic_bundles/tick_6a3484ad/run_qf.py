"""Freeze and run one current-lease native diagnostic, preserving old stages."""
from datetime import datetime, timezone
import copy
import json
import shlex
import shutil
from ops import guard, save, run, ssh, add, evidence, ROOT, OUT, OLD, TOKEN, THREAD, CID, STAGE
import foreground_tick as tick

owner = guard(1000)
local = OUT / 'native_qf'
for name in ('native_runtime.py', 'neighbor_content.py'):
    target = local / name
    assert not target.exists()
    shutil.copyfile(OLD / 'terminal_content' / name, target)
    assert tick.digest(target) == tick.digest(OLD / 'terminal_content' / name)
manifest = copy.deepcopy(tick.load(OLD / 'terminal_content/native_manifest.json'))
manifest['stage'] = STAGE
manifest['diagnostic_files'] = {name: tick.digest(local / name) for name in
                               ('native_runtime.py', 'native_diagnostic.py', 'neighbor_content.py')}
manifest['qf_preregistration'] = evidence(OUT / 'qf_native_prereg.md')
save('native_qf/native_manifest.json', manifest)
save('native_qf/execution_lease.json', {'project': 'cluster_project', 'thread_id': THREAD, 'token': TOKEN,
     'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
work = tick.load(ROOT / 'pipeline/research_work.json')
c = next(c for c in work['candidates'] if c['id'] == CID)
c.update(stage='validation', next_action='Execute frozen native Q/F32TRAIN factorial attribution;first native1e-6reconstruction,null/helper2controls,then originalqueryindexPiou/BCE. No training/VAL/arithmeticrevision3.')
add(c, [OUT / 'qf_native_prereg.md', local / 'native_manifest.json', local / 'native_diagnostic.py'])
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
save('remote_stage.json', ssh('from pathlib import Path\nimport json\nPath(' + repr(STAGE) + ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files = [str(local / name) for name in (*manifest['diagnostic_files'], 'native_manifest.json', 'execution_lease.json')]
upload = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', *files, 'songcl@192.168.1.115:' + STAGE + '/'])
save('upload.json', {'returncode': upload.returncode, 'stderr': upload.stderr})
assert upload.returncode == 0
guard(900)
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
           'python -B ' + shlex.quote(STAGE + '/native_diagnostic.py') + ' --lease ' + shlex.quote(STAGE + '/execution_lease.json'))
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
response = run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ServerAliveInterval=15',
                '-o', 'ServerAliveCountMax=3', 'songcl@192.168.1.115', shlex.join(['bash', '-lc', command])], min(1250, int(remaining) - 120))
save('native_execution.json', {'returncode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr,
                              'finished_at': datetime.now(timezone.utc).isoformat()})
fetch = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
             'songcl@192.168.1.115:' + STAGE + '/native_diagnostic_result.json', str(local / 'native_diagnostic_result.json')])
save('fetch.json', {'returncode': fetch.returncode, 'stderr': fetch.stderr})
assert fetch.returncode == 0, response.stderr
r = tick.load(local / 'native_diagnostic_result.json')
print(json.dumps({'passed': r['passed'], 'native_forwards': r['native_forwards'], 'suffix_replays': r['suffix_replays'],
                  'scenes': len(r['scenes']), 'task_readouts': r.get('task_readouts'),
                  'contrasts': r.get('paired_scene_contrasts'), 'error_type': r.get('error_type'),
                  'error': r.get('error'), 'stderr_tail': response.stderr[-1600:] if response.returncode else None}))
