"""Register the independent finite hypothesis before executing its test."""
from datetime import datetime, timezone
import copy
import json
import shlex
import shutil
from ops import guard, save, run, ssh, add, evidence, ROOT, OUT, TOKEN, THREAD
import foreground_tick as tick

owner = guard(650)
cid = 'hierarchical-padding-context-invariance-audit'
work = tick.load(ROOT / 'pipeline/research_work.json')
assert not any(c['id'] == cid for c in work['candidates']), 'Do not reopen or rename existing work'
candidate = {'id': cid, 'stage': 'diagnosis', 'hypothesis_id': 'hierarchical_fusion_masked_padding_invariance',
    'hypothesis': 'Masking appended points should preserve identical valid hierarchy messages;global_mean may violate this invariant.',
    'matched_control': 'Sameweights/validpoints/tokens/IDs;identityreplay+zeroscalenull;only appendedmaskedpositions vary.',
    'next_action': 'Execute preregistered first2frozenTRAINscenes;native reconstruction then7/Nmaskedzero andNmaskedone gather/suffix controls.',
    'gate_result': 'NOT_RUN', 'failure_scope': 'inconclusive', 'evidence': [evidence(OUT / 'padding_prereg.md')]}
work['candidates'].append(candidate)
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
local = OUT / 'padding_native'
local.mkdir(exist_ok=False)
shutil.copyfile(OUT / 'native_qf/native_runtime.py', local / 'native_runtime.py')
shutil.copyfile(OUT / 'native_padding.py', local / 'native_padding.py')
manifest = copy.deepcopy(tick.load(OUT / 'native_qf/native_manifest.json'))
stage = '/data/songcl/Project/Cluster_project/pipeline/fle_padding_invariance_6a3484ad'
manifest.update(candidate_id=cid, stage=stage)
manifest['diagnostic_files'] = {n: tick.digest(local / n) for n in ('native_runtime.py', 'native_padding.py')}
manifest['padding_preregistration'] = evidence(OUT / 'padding_prereg.md')
save('padding_native/native_manifest.json', manifest)
save('padding_native/execution_lease.json', {'project': 'cluster_project', 'thread_id': THREAD, 'token': TOKEN,
    'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(local / 'native_manifest.json')})
candidate.update(stage='validation', gate_result='Protocol/source frozen;nativeNOT_RUN')
add(candidate, [local / 'native_manifest.json', local / 'native_padding.py'])
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
save('padding_stage.json', ssh('from pathlib import Path\nimport json\nPath(' + repr(stage) + ').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))'))
files = [str(local / n) for n in (*manifest['diagnostic_files'], 'native_manifest.json', 'execution_lease.json')]
upload = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', *files, 'songcl@192.168.1.115:' + stage + '/'])
save('padding_upload.json', {'returncode': upload.returncode, 'stderr': upload.stderr})
assert upload.returncode == 0
guard(500)
command = ('source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '
           'python -B ' + shlex.quote(stage + '/native_padding.py') + ' --lease ' + shlex.quote(stage + '/execution_lease.json'))
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
response = run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ServerAliveInterval=15',
                '-o', 'ServerAliveCountMax=3', 'songcl@192.168.1.115', shlex.join(['bash', '-lc', command])], min(700, int(remaining) - 120))
save('padding_execution.json', {'returncode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr,
                             'finished_at': datetime.now(timezone.utc).isoformat()})
fetch = run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
             'songcl@192.168.1.115:' + stage + '/native_padding_result.json', str(local / 'native_padding_result.json')])
save('padding_fetch.json', {'returncode': fetch.returncode, 'stderr': fetch.stderr})
assert fetch.returncode == 0, response.stderr
r = tick.load(local / 'native_padding_result.json')
print(json.dumps({'passed': r['passed'], 'native_forwards': r['native_forwards'], 'suffix_replays': r['suffix_replays'],
    'padding_invariance_pass': r.get('padding_invariance_pass'),
    'cases': [{'scene': s['scene'], 'case': c['case'], 'gather': c['valid_gather_max_change'],
               'message': c['valid_message_max_change'], 'mask': c['mask_logits_max_change']} for s in r['scenes'] for c in s['cases']],
    'error': r.get('error'), 'stderr_tail': response.stderr[-1800:] if response.returncode else None}))
