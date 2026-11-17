"""Stage and execute one preregistered natural batch2 diagnostic."""
from datetime import datetime, timezone
import copy
import json
import shlex
import shutil
from ops import guard, save, run, ssh, add, evidence, ROOT, OUT, TOKEN, THREAD
import foreground_tick as tick

owner = guard(500)
previous = tick.load(OUT / 'padding_native/native_padding_result.json')
assert previous['passed'] and previous['padding_invariance_pass'] is False
cid = 'hierarchical-padding-context-invariance-audit'
work = tick.load(ROOT / 'pipeline/research_work.json')
c = next(c for c in work['candidates'] if c['id'] == cid)
c.update(stage='validation', failure_scope='inconclusive',
         gate_result='2TRAINsceneinterface controlsPASSbutmaskedpaddingchangesvalidmessages/masks;naturalbatch2incidenceNOT_RUN.',
         next_action='One originalbatch2 nativeforward,compare actualpaddedgather to samevalid-rowcropped sourcecalls;retain1e-6controls,no productionfix/training.')
add(c, [OUT / 'padding_native/native_padding_result.json', OUT / 'padding_execution.json', OUT / 'native_batch2_prereg.md'])
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
local = OUT / 'batch2_native'
local.mkdir(exist_ok=False)
shutil.copyfile(OUT / 'native_qf/native_runtime.py', local / 'native_runtime.py')
shutil.copyfile(OUT / 'native_batch2.py', local / 'native_batch2.py')
manifest = copy.deepcopy(tick.load(OUT / 'padding_native/native_manifest.json'))
stage = '/data/songcl/Project/Cluster_project/pipeline/fle_native_batch2_6a3484ad'
manifest['stage'] = stage
manifest['diagnostic_files'] = {n: tick.digest(local / n) for n in ('native_runtime.py', 'native_batch2.py')}
manifest['batch2_preregistration'] = evidence(OUT / 'native_batch2_prereg.md')
save('batch2_native/native_manifest.json', manifest)
save('batch2_native/execution_lease.json', {'project': 'cluster_project', 'thread_id': THREAD, 'token': TOKEN,
    'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
add(c, [local / 'native_manifest.json', local / 'native_batch2.py'])
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
save('batch2_stage.json', ssh('from pathlib import Path\nimport json\nPath(' + repr(stage) + ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files = [str(local / n) for n in (*manifest['diagnostic_files'], 'native_manifest.json', 'execution_lease.json')]
upload = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', *files, 'songcl@192.168.1.115:' + stage + '/'])
save('batch2_upload.json', {'returncode': upload.returncode, 'stderr': upload.stderr})
assert upload.returncode == 0
guard(400)
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
           'python -B ' + shlex.quote(stage + '/native_batch2.py') + ' --lease ' + shlex.quote(stage + '/execution_lease.json'))
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
response = run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ServerAliveInterval=15',
                '-o', 'ServerAliveCountMax=3', 'songcl@192.168.1.115', shlex.join(['bash', '-lc', command])], min(650, int(remaining) - 120))
save('batch2_execution.json', {'returncode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr,
                            'finished_at': datetime.now(timezone.utc).isoformat()})
fetch = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
             'songcl@192.168.1.115:' + stage + '/native_batch2_result.json', str(local / 'native_batch2_result.json')])
save('batch2_fetch.json', {'returncode': fetch.returncode, 'stderr': fetch.stderr})
assert fetch.returncode == 0, response.stderr
r = tick.load(local / 'native_batch2_result.json')
print(json.dumps({'passed': r['passed'], 'native_forwards': r['native_forwards'], 'suffix_replays': r['suffix_replays'],
    'padding_invariance_pass': r.get('padding_invariance_pass'), 'rows': r.get('rows'), 'controls': r.get('controls'),
    'valid_message_max_change': r.get('valid_message_max_change'), 'mask_logits_max_change': r.get('final_mask_logits_max_change'),
    'error': r.get('error'), 'stderr_tail': response.stderr[-1800:] if response.returncode else None}))
