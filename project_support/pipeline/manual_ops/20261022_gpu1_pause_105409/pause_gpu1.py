"""One explicit-user manual pause; exact pidfd stop, no automatic resume."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import yaml

ROOT = Path('D:/project/cluster_project')
P = ROOT / 'pipeline'
OUT = Path(__file__).resolve().parent
RID = OUT.name
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
REQUEST = 'GPU1可以先暂停训练了  给别人腾出来一张卡'
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0, str(SKILL))
import pipeline_monitor as pm


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def save(path, value, exclusive=False):
    if exclusive:
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        return
    temporary = path.with_name(path.name + '.' + RID + '.tmp')
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def guard():
    assert os.environ['CODEX_THREAD_ID'] == THREAD
    assert load(P / 'execution_mode.json') == dict(mode='foreground', target_thread_id=THREAD)
    assert not (P / 'headless/.foreground.lockdir').exists()
    assert sha(P / 'goal.json') == '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'


def remote(script, output, params=None, conda=False, timeout=60):
    guard()
    payload = ('PARAMS=' + repr(params) + '\n' if params is not None else '') + (OUT / script).read_text(encoding='utf-8')
    command = '/usr/bin/python3 -B -'
    if conda:
        command = shlex.join(['bash', '-lc', 'source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B -'])
    completed = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10', 'songcl@192.168.1.115', command], input=payload, text=True, encoding='utf-8', capture_output=True, timeout=timeout)
    record = dict(observed_at=now(), command='strict known-host SSH; python -B stdin', remote_script=script,
        remote_script_sha256=hashlib.sha256(payload.encode()).hexdigest(), returncode=completed.returncode,
        stdout=completed.stdout, stderr=completed.stderr)
    if completed.returncode == 0:
        record['data'] = json.loads(completed.stdout)
    save(OUT / output, record, exclusive=True)
    assert completed.returncode == 0, completed.stderr[-2500:]
    return record['data']


def main():
    guard()
    lock = pm.acquire_lock(str(ROOT))
    assert lock is not None, 'Another project writer is active; no manual mutation performed'
    try:
        guard()
        relative_files = ['SERVERS.yaml', 'pipeline/queue.json', 'pipeline/running.json', 'pipeline/experiments/M206-CGCA.json', 'pipeline/research_work.json', 'pipeline/codex_memory.md']
        for relative in relative_files:
            with (OUT / ('before_' + relative.replace('/', '__'))).open('xb') as stream:
                stream.write((ROOT / relative).read_bytes())
        q = load(P / 'queue.json')
        task = next(t for t in q['gpu_queues']['server-4'] if t['id'] == 'M206-CGCA')
        protected_task = copy.deepcopy(next(t for t in q['gpu_queues']['server-4'] if t['id'] == 'M207-HAP'))
        assert task['status'] == 'running' and task['pid'] == 732137 and str(task['gpu']) == '1'
        assert protected_task['status'] == 'running' and protected_task['pid'] == 979955 and str(protected_task['gpu']) == '0'
        original_task = copy.deepcopy(task)
        resource_path = P / 'authorizations' / ('server4_gpu0_only_' + RID + '.json')
        save(resource_path, dict(schema_version=1, purpose='cluster_resource_authorization', source='human',
            authorization_granted=True, recorded_at=now(), human_request=REQUEST, owning_thread_id=THREAD,
            project='cluster_project', server='server-4', host='192.168.1.115', expected_hostname='dl04-MS-7E06',
            allowed_gpus=[0], max_tasks_per_gpu=1,
            expected_gpu_uuids={'0':'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c','1':'GPU-7f82edb9-f620-8045-caea-a75232265cd1'},
            scope='Pause current GPU1 M206, preserve saved complete checkpoint, release GPU1 to others. GPU0 HAP continues. No automatic migration, resume or cold start; GPU1 requires later explicit reauthorization.',
            supersedes='Latest prior GPU1 reenable grant for all future cluster_project work on GPU1 only', human_request_evidence=evidence(OUT / 'human_request.json')), exclusive=True)
        servers_path = ROOT / 'SERVERS.yaml'
        original_servers = servers_path.read_text(encoding='utf-8')
        start = original_servers.index('  server-4:')
        end = original_servers.index('  server-6:', start)
        block = original_servers[start:end]
        new_block, count = re.subn(r'^    allowed_gpus: \[0, 1\].*$', '    allowed_gpus: [0]   # User 2026-10-22 pauses GPU1 and releases it to others.', block, flags=re.MULTILINE)
        assert count == 1
        updated_servers = original_servers[:start] + new_block + original_servers[end:]
        before_parsed, after_parsed = yaml.safe_load(original_servers), yaml.safe_load(updated_servers)
        expected = copy.deepcopy(before_parsed)
        expected['servers']['server-4']['allowed_gpus'] = [0]
        assert expected == after_parsed
        temporary = servers_path.with_name('SERVERS.' + RID + '.tmp')
        with temporary.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(updated_servers)
        os.replace(temporary, servers_path)
        task['dispatch_hold'] = 'User pause in progress: GPU1 released to others; never relaunch, migrate or cold-start automatically.'
        task['dispatch_phase'] = 'user_pause_stop_pending'
        task['pause_request'] = evidence(OUT / 'human_request.json')
        save(P / 'queue.json', q)
        print('GPU1 excluded from dispatch; checking current exact process and checkpoint.', flush=True)
        initial = remote('preflight_remote.py', 'initial_preflight.json')
        captured = remote('checkpoint_remote.py', 'checkpoint_capture.json', dict(source_checkpoint=initial['source_checkpoint'], operation_id=RID), conda=True, timeout=180)
        print('Stable full checkpoint CPU-verified at epoch ' + str(captured['cpu_inspection']['meta']['epoch']) + '; stopping only exact M206 processes.', flush=True)
        params = dict(target=initial['target'], protected=initial['protected'], snapshot=captured['resume_from'], checkpoint_sha256=captured['checkpoint_sha256'], operation_id=RID)
        save(OUT / 'stop_intent.json', dict(recorded_at=now(), params=params, checkpoint_capture=evidence(OUT / 'checkpoint_capture.json')), exclusive=True)
        stopped = remote('stop_remote.py', 'stop_confirmation.json', params, timeout=70)
        assert stopped['stop_confirmed'] and stopped['target_GPU_context_absent'] and stopped['protected_identity_unchanged']
        checkpoint_path = OUT / 'checkpoint_evidence.json'
        save(checkpoint_path, dict(schema_version=1, purpose='cluster_native_resume', id='M206-CGCA', config=task['config'],
            code_commit=task['code_commit'], server='server-4', gpu='1', remote_code_root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1',
            resume_from=captured['resume_from'], checkpoint_sha256=captured['checkpoint_sha256'],
            cpu_inspection=captured['cpu_inspection'], source_checkpoint=captured['source'], frozen_checkpoint_bytes=captured['bytes'],
            admitted_code_commit=task['code_commit'], actual_runtime_HEAD_at_pause=initial['runtime_HEAD'],
            historical_and_runtime_HEAD_difference_disclosed=True, original_run_log=original_task['log'],
            original_pid=original_task['pid'], original_starttime='21298582',
            capture=evidence(OUT / 'checkpoint_capture.json'), original_task=evidence(OUT / 'before_pipeline__queue.json'),
            stop_confirmation=evidence(OUT / 'stop_confirmation.json'),
            resume_authorized=False, source_revalidation_required_before_any_resume=True, partial_current_epoch_saved=False), exclusive=True)
        prior_pause = copy.deepcopy(task.get('paused_run'))
        if prior_pause:
            task.setdefault('pause_history', []).append(prior_pause)
        paused = {k:original_task.get(k) for k in ['pid','gpu','log','launched','launch_verified','launch_verification','claimed_gpu','resume_from','resume_authorization','resume_checkpoint_evidence']}
        paused.update(paused_at=now(), reason=REQUEST, starttime='21298582', checkpoint=captured['resume_from'],
            checkpoint_sha256=captured['checkpoint_sha256'], meta=captured['cpu_inspection']['meta'],
            stop_confirmation=evidence(OUT / 'stop_confirmation.json'))
        task.update(status='waiting', training_status='paused_by_user', dispatch_phase='user_paused',
            dispatch_hold='User paused M206 to release GPU1 to others. No automatic resume or GPU0 migration; wait for explicit resume instruction and full source/checkpoint/resource validation.',
            paused_run=paused, paused_at=now(), resume_from=captured['resume_from'],
            resume_checkpoint_evidence=evidence(checkpoint_path), launch_verified=False, launch_verification='user_paused',
            resume_authorized=False, resource_authorization=evidence(resource_path),
            note='Paused, not terminal and not ready waiting. Latest complete epoch checkpoint preserved; no automatic replay/cold start.')
        for key in ['pid', 'log', 'launched', 'claimed_gpu', 'resume_authorization', 'resume_validation', 'resume_validated_at']:
            task.pop(key, None)
        assert next(t for t in q['gpu_queues']['server-4'] if t['id']=='M207-HAP') == protected_task
        save(P / 'queue.json', q)
        running = load(P / 'running.json')
        assert running['server-4']['1']=='M206-CGCA' and running['server-4']['0']=='M207-HAP'
        del running['server-4']['1']
        save(P / 'running.json', running)
        exp_path = P / 'experiments/M206-CGCA.json'
        exp = load(exp_path)
        exp.update(status='waiting', training_status='paused_by_user', gpu='1', paused_run=paused,
            dispatch_hold=task['dispatch_hold'], resume_from=captured['resume_from'],
            resume_checkpoint_evidence=evidence(checkpoint_path), resume_authorized=False,
            launch_verified=False, launch_verification='user_paused')
        for key in ['pid','log','launched','resume_authorization']:
            exp.pop(key, None)
        exp.setdefault('history', []).append(dict(ts=now(), action='user_paused_GPU1_release_to_others',
            checkpoint_meta=captured['cpu_inspection']['meta'], checkpoint=evidence(checkpoint_path),
            stop_confirmation=evidence(OUT / 'stop_confirmation.json'), no_auto_resume=True))
        save(exp_path, exp)
        work = load(P / 'research_work.json')
        cgca = next(c for c in work['candidates'] if c['id']=='hierarchy-coarse-conditioned-fine-channel-attention')
        cgca.update(training_status='paused_by_user', human_hold=True, resume_authorized=False,
            next_action='Latest human paused GPU1 to release it to others. Preserve exact admitted M206/source898 and latest full checkpoint. Do not resume on any GPU or cold-start without later explicit instruction and exact source/full-state/current resource validation; GPU0 HAP continues.')
        for path in [resource_path, checkpoint_path, OUT / 'stop_confirmation.json', OUT / 'human_request.json']:
            cgca['evidence'].append(evidence(path))
        for c in work['candidates']:
            if c['id'] in ['hierarchy-bottom-up-refined-token-composition','hierarchy-parent-segmented-bidirectional-token-state']:
                c['required_gpu']='0'
                c['blocker']='Latest human reserves only server4GPU0 for project use; GPU0 HAP remains running. GPU1 is released to others and unauthorized for native diagnostics/training.'
                c['unblock_condition']='Fresh real authorized server4GPU0 opening, current policy/UUID/owner/exclusive checks. GPU1 becoming physically idle does not authorize use.'
                c['next_action']='GPU0 only: preserve HAP until natural completion; then verify exact prepared worker/adapter external anchors and fresh current binding for actual native/resource checks. Do not use GPU1 or auto-resume M206. ' + c['next_action']
                c['evidence'].append(evidence(resource_path))
        work['latest_resource_authorization']=evidence(resource_path)
        work['next_action']='Respect new server4GPU0-only scope; preserve running HAP. M206 is user-paused with full checkpoint, not terminal or auto-runnable; GPU1 belongs to others until explicit reauthorization. HRC/PSBR can continue authorized local preparation and wait for actual GPU0 opening.'
        work['updated_at']=now()
        save(P / 'research_work.json', work)
        summary = dict(recorded_at=now(), status='USER_PAUSED_GPU1_RELEASED', id='M206-CGCA',
            stopped_pid=732137, checkpoint_meta=captured['cpu_inspection']['meta'], checkpoint=evidence(checkpoint_path),
            frozen_remote_checkpoint=captured['resume_from'], gpu1_empty_at_check=stopped['gpu1_empty_at_check'],
            gpu1_project_context_released=True, protected_gpu0_HAP_unchanged=True,
            allowed_gpus=[0], queue_state='waiting_with_user_pause_hold_not_runnable', no_auto_resume=True,
            no_scheduler_or_goal_or_source_change=True, resource_authorization=evidence(resource_path),
            stop_confirmation=evidence(OUT / 'stop_confirmation.json'))
        save(OUT / 'operation_summary.json', summary, exclusive=True)
        print(json.dumps(summary, ensure_ascii=False), flush=True)
    finally:
        lock.close()


if __name__ == '__main__':
    main()
