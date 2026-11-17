"""One bounded replication, no retry-until-success or numerical repair."""
from datetime import datetime, timezone
import copy
import json
import shlex
import shutil
from ops import guard, save, run, ssh, add, evidence, ROOT, OUT, TOKEN, THREAD, CID
import foreground_tick as tick

owner = guard(900)
first = tick.load(OUT / 'native_qf/native_diagnostic_result.json')
assert not first['passed'] and first['native_forwards'] == 9 and len(first['scenes']) == 8
assert 'Fixed64bisections exhausted' in first['error']
save('initial_qf_failure.json', {'observed_at': datetime.now(timezone.utc).isoformat(), 'passed': False,
     'native_forwards': first['native_forwards'], 'suffix_replays': first['suffix_replays'],
     'completed_scenes': len(first['scenes']), 'failure_scope': 'implementation',
     'scientific_result': '32sceneQFattributionNOT_ESTABLISHED;not mechanismfalsification',
     'error': first['error'], 'evidence': [evidence(OUT / 'native_qf/native_diagnostic_result.json')]})
local = OUT / 'capture_repeat'
local.mkdir(exist_ok=False)
for name in ('native_runtime.py', 'neighbor_content.py', 'native_diagnostic.py'):
    shutil.copyfile(OUT / 'native_qf' / name, local / name)
    assert tick.digest(local / name) == tick.digest(OUT / 'native_qf' / name)
shutil.copyfile(OUT / 'capture_launcher.py', local / 'capture_launcher.py')
stage = '/data/songcl/Project/Cluster_project/pipeline/fle_qf_capture_6a3484ad'
manifest = copy.deepcopy(tick.load(OUT / 'native_qf/native_manifest.json'))
manifest['stage'] = stage
manifest['diagnostic_files']['capture_launcher.py'] = tick.digest(local / 'capture_launcher.py')
manifest['replication_preregistration'] = evidence(OUT / 'repeat_capture_prereg.md')
save('capture_repeat/native_manifest.json', manifest)
save('capture_repeat/execution_lease.json', {'project': 'cluster_project', 'thread_id': THREAD, 'token': TOKEN,
     'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
work = tick.load(ROOT / 'pipeline/research_work.json')
c = next(c for c in work['candidates'] if c['id'] == CID)
c.update(stage='validation', failure_scope='implementation',
         gate_result='FirstnativeQFfailsoriginalrevision2normcontrolatscene9;8completedscenesonly;no native32sceneQFPASS,no arithmeticrevision3.',
         next_action='One exactsource replication with exception-only operandcapture;allcontrols unchanged. Preserve bothoutcomes;diagnose originalsolver,not repair or training.')
add(c, [OUT / 'initial_qf_failure.json', OUT / 'native_qf/native_diagnostic_result.json',
        OUT / 'native_execution.json', OUT / 'repeat_capture_prereg.md', local / 'native_manifest.json'])
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
save('capture_stage.json', ssh('from pathlib import Path\nimport json\nPath(' + repr(stage) + ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files = [str(local / name) for name in (*manifest['diagnostic_files'], 'native_manifest.json', 'execution_lease.json')]
upload = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', *files, 'songcl@192.168.1.115:' + stage + '/'])
save('capture_upload.json', {'returncode': upload.returncode, 'stderr': upload.stderr})
assert upload.returncode == 0
guard(900)
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
           'python -B ' + shlex.quote(stage + '/capture_launcher.py') + ' --lease ' + shlex.quote(stage + '/execution_lease.json'))
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
response = run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ServerAliveInterval=15',
                '-o', 'ServerAliveCountMax=3', 'songcl@192.168.1.115', shlex.join(['bash', '-lc', command])], min(1250, int(remaining) - 120))
save('capture_execution.json', {'returncode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr,
                              'finished_at': datetime.now(timezone.utc).isoformat()})
fetch = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
             'songcl@192.168.1.115:' + stage + '/native_diagnostic_result.json', str(local / 'native_diagnostic_result.json')])
save('capture_fetch.json', {'returncode': fetch.returncode, 'stderr': fetch.stderr})
assert fetch.returncode == 0, response.stderr
r = tick.load(local / 'native_diagnostic_result.json')
if not r['passed']:
    for name in ('failed_norm_operands.npz', 'failed_norm_context.json'):
        copied = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                      'songcl@192.168.1.115:' + stage + '/' + name, str(local / name)])
        save('capture_' + name.replace('.', '_') + '_fetch.json', {'returncode': copied.returncode, 'stderr': copied.stderr})
print(json.dumps({'passed': r['passed'], 'native_forwards': r['native_forwards'], 'suffix_replays': r['suffix_replays'],
                  'scenes': len(r['scenes']), 'task_readouts': r.get('task_readouts'),
                  'contrasts': r.get('paired_scene_contrasts'), 'error_type': r.get('error_type'),
                  'error': r.get('error'), 'captured_operands': (local / 'failed_norm_operands.npz').exists()}))
