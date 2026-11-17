"""Hash- and lease-bound read-only evidence of exclusive GPU occupation."""
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shlex

MAX_AGE_SECONDS = 300


def _gpu_ids(values):
    if (not isinstance(values, list) or not values
            or any(type(v) is not int or v < 0 for v in values)
            or len(values) != len(set(values))):
        raise ValueError('Occupation evidence needs an explicit GPU whitelist')
    return set(values)


def _time(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('Occupation timestamp needs a timezone')
    return parsed


def _raw_state(proof, allowed, queue, name):
    queries = proof['queries']
    for key in ('hostname', 'gpu', 'compute'):
        if type(queries[key].get('rc')) is not int or queries[key]['rc'] != 0:
            raise ValueError('GPU observation query failed: ' + key)
        if not isinstance(queries[key].get('stdout'), str):
            raise ValueError('GPU observation query output unavailable')
    inventory, uuids = {}, set()
    for row in csv.reader(io.StringIO(queries['gpu']['stdout'])):
        if len(row) != 5:
            raise ValueError('Malformed GPU inventory')
        index = int(row[0].strip())
        uuid = row[1].strip()
        util, used, total = [float(v.strip()) for v in row[2:]]
        if (index < 0 or index in inventory or not uuid or uuid in uuids
                or not all(math.isfinite(v) for v in (util, used, total))
                or not 0 <= util <= 100 or not 0 <= used <= total or total <= 0):
            raise ValueError('Unknown, duplicate or invalid GPU inventory fields')
        inventory[index] = dict(uuid=uuid, utilization=util, memory_used=used, memory_total=total)
        uuids.add(uuid)
    if not allowed.issubset(inventory):
        raise ValueError('Authorized device missing from current GPU inventory')
    compute = {}
    for row in csv.reader(io.StringIO(queries['compute']['stdout'])):
        if len(row) != 2 or not row[0].strip():
            raise ValueError('Malformed compute process observation')
        pid = int(row[1].strip())
        if pid <= 0:
            raise ValueError('Invalid compute PID')
        compute.setdefault(row[0].strip(), []).append(pid)
    # Reservations come only from the real canonical queue, never proof summaries.
    reserved = set()
    for task in queue.get('gpu_queues', {}).get(name, []):
        if task.get('status') in ('running', 'claiming') and task.get('gpu') is not None:
            try:
                gpu = int(task['gpu'])
            except (TypeError, ValueError):
                continue
            if gpu in allowed:
                reserved.add(gpu)
    busy, idle = [], []
    for gpu in sorted(allowed):
        row = inventory[gpu]
        unavailable = (gpu in reserved or bool(compute.get(row['uuid']))
                       or row['utilization'] >= 10 or row['memory_used'] >= 1024)
        (busy if unavailable else idle).append(gpu)
    return dict(busy_gpu_ids=busy, idle_gpu_ids=idle, inventory=inventory,
                compute_pids=compute, reserved_gpu_ids=sorted(reserved))


def validated_state(root, context, candidate, server, queue, now=None):
    """Recompute availability from raw queries after validating every binding."""
    import closure
    import yaml

    root = Path(root)
    entry = candidate.get('occupation_evidence')
    if not isinstance(entry, dict) or entry not in candidate.get('evidence', []):
        raise ValueError('Current occupation evidence is not bound to this candidate')
    proof = closure.read(closure.artifact(root, entry), {})
    candidate_ids = proof.get('candidate_ids')
    if (proof.get('schema_version') != 1 or proof.get('kind') != 'exclusive_gpu_occupation'
            or proof.get('complete') is not True or proof.get('read_only') is not True
            or proof.get('project') != root.name or not isinstance(candidate_ids, list)
            or not candidate_ids or any(not isinstance(cid, str) or not cid for cid in candidate_ids)
            or len(candidate_ids) != len(set(candidate_ids))):
        raise ValueError('Unrecognized or incomplete live occupation evidence')
    raw_entry = proof.get('raw_log')
    if not isinstance(raw_entry, dict) or raw_entry not in candidate.get('evidence', []):
        raise ValueError('Raw occupation query log is not bound to the candidate')
    if closure.read(closure.artifact(root, raw_entry), {}) != proof.get('queries'):
        raise ValueError('Occupation queries differ from the original raw observation')
    headless = root / 'pipeline/headless'
    owner = closure.read(headless / '.foreground.lockdir/owner.json', {})
    snapshot = headless / '.tick_context.json'
    if (not owner.get('token') or proof.get('token') != owner['token']
            or owner.get('generated_at') != context.get('generated_at')
            or proof.get('snapshot_generated_at') != context.get('generated_at')
            or not owner.get('context_sha256')
            or proof.get('snapshot_sha256') != owner['context_sha256']
            or closure.digest(snapshot) != owner['context_sha256']):
        raise ValueError('Occupation evidence belongs to a different lease or snapshot')
    current = now or datetime.now(timezone.utc)
    observed = _time(proof['observed_at'])
    since = _time(context['generated_at'])
    if (observed < since or observed > current + timedelta(seconds=5)
            or (current - observed).total_seconds() > MAX_AGE_SECONDS
            or observed > _time(context['deadline_at'])):
        raise ValueError('Occupation evidence is stale, future-dated or outside this tick')
    settings_path = root / 'SERVERS.yaml'
    if proof.get('servers_sha256') != closure.digest(settings_path):
        raise ValueError('GPU server configuration changed since observation')
    settings = yaml.safe_load(settings_path.read_text(encoding='utf-8'))['servers'][server['name']]
    allowed = _gpu_ids(server['allowed_gpus'])
    scope = proof['scope']
    if (settings.get('role') != 'gpu_server'
            or _gpu_ids(settings.get('allowed_gpus')) != allowed
            or _gpu_ids(scope.get('allowed_gpus')) != allowed
            or settings.get('max_tasks_per_gpu', 1) != 1
            or scope.get('max_tasks_per_gpu') != 1
            or server.get('max_tasks_per_gpu', 1) != 1
            or scope.get('server') != candidate.get('required_server')
            or scope.get('server') != server['name']
            or scope.get('host') != settings['host']
            or scope.get('user') != settings['user']
            or candidate['id'] not in proof.get('candidate_ids', [])):
        raise ValueError('Occupation scope does not match the candidate and authorized server')
    state = _raw_state(proof, allowed, queue, server['name'])
    hostname = proof['queries']['hostname']['stdout'].strip()
    if not hostname or (settings.get('expected_hostname')
                        and hostname != settings['expected_hostname']):
        raise ValueError('Observed GPU server hostname does not match its identity')
    return state


def validate_block(root, context, candidate, server, queue):
    try:
        state = validated_state(root, context, candidate, server, queue)
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise ValueError('Live GPU occupation evidence invalid: ' + str(error)) from None
    if state['idle_gpu_ids']:
        raise ValueError('Live observation shows an authorized idle GPU; preserve executable work')
    return state


def collect(project, token, server_name, label=None):
    """Read-only remote query, then persist only matching resource dispositions."""
    import foreground_tick as tick
    import pipeline_monitor as monitor

    root = Path(project)
    headless = root / 'pipeline/headless'
    owner = tick.load(headless / '.foreground.lockdir/owner.json')
    if owner['token'] != token or owner['thread_id'] != os.environ.get('CODEX_THREAD_ID'):
        raise ValueError('Not the owning foreground lease')
    if (_time(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds() < 90:
        raise ValueError('Insufficient foreground time for a fresh resource observation')
    for name, key in (('.tick_context.json', 'context_sha256'),
                      ('.tick_context_state.next.json', 'pending_sha256')):
        if tick.digest(headless / name) != owner[key]:
            raise ValueError('Foreground snapshot or pending state changed')
    context = tick.load(headless / '.tick_context.json')
    server = monitor.load_servers(str(root))[server_name]
    snapshot_server = next(s for s in context['queue']['servers'] if s['name'] == server_name)
    _gpu_ids(server['allowed_gpus'])
    if server['max_tasks_per_gpu'] != 1:
        raise ValueError('Exclusive occupation collector requires one task per GPU')
    lock = monitor.acquire_lock(str(root))
    if lock is None:
        raise ValueError('Project writer is busy')
    try:
        work = tick.load(root / 'pipeline/research_work.json')
        candidates = [c for c in work['candidates'] if c.get('stage') == 'blocked'
                      and c.get('blocker_kind') == 'exclusive_gpu_slot'
                      and c.get('required_server') == server_name]
        if not candidates:
            raise ValueError('No matching blocked exclusive GPU work to observe')
        if label is not None and not re.fullmatch(r'[a-zA-Z0-9_-]{1,32}', label):
            raise ValueError('Invalid observation label')
        suffix = server_name + ('_' + label if label else '') + '_' + token
        output = root / ('pipeline/checks/gpu_occupation_' + suffix + '.json')
        log = output.with_suffix('.log')
        if output.exists() or log.exists():
            raise ValueError('Occupation observations are immutable; choose a new label')
        output.parent.mkdir(parents=True, exist_ok=True)
        commands = dict(hostname=['hostname'],
            gpu=['nvidia-smi', '--query-gpu=index,uuid,utilization.gpu,memory.used,memory.total',
                 '--format=csv,noheader,nounits'],
            compute=['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'])
        program = "import json,subprocess\ncommands=" + repr(commands) + "\nqueries={}\n" + (
            "for key,command in commands.items():\n"
            " r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)\n"
            " queries[key]=dict(rc=r.returncode,stdout=r.stdout,stderr=r.stderr,command=command)\n"
            "print(json.dumps(queries))\n")
        raw = monitor.ssh(server['host'], server['user'],
                          shlex.quote(server.get('python') or 'python3') + ' -B -c ' + shlex.quote(program), timeout=75)
        log.write_text(raw, encoding='utf-8')
        queries = json.loads(raw)
        observed = datetime.now(timezone.utc)
        proof = dict(schema_version=1, kind='exclusive_gpu_occupation',
            complete=all(q.get('rc') == 0 for q in queries.values()), read_only=True,
            project=root.name, token=token, snapshot_generated_at=context['generated_at'],
            snapshot_sha256=owner['context_sha256'], servers_sha256=tick.digest(root/'SERVERS.yaml'),
            observed_at=observed.isoformat(), candidate_ids=[c['id'] for c in candidates],
            scope=dict(server=server_name, host=server['host'], user=server['user'],
                       allowed_gpus=server['allowed_gpus'], max_tasks_per_gpu=1), queries=queries,
            command='python -B '+shlex.quote(str(Path(__file__).resolve()))+' '+root.name+
                    ' --token '+token+' --server '+server_name+(' --label '+label if label else ''),
            raw_log=dict(path=log.relative_to(root).as_posix(), sha256=tick.digest(log)))
        tick.save(output, proof)
        entry = dict(path=output.relative_to(root).as_posix(), sha256=tick.digest(output))
        queue = monitor.load_queue(str(root))
        staged = dict(candidates[0], occupation_evidence=entry,
                      evidence=candidates[0]['evidence']+[entry, proof['raw_log']])
        state = validated_state(root, context, staged, snapshot_server, queue)
        for candidate in candidates:
            candidate['occupation_evidence'] = entry
            candidate['last_resource_check_at'] = observed.isoformat()
            for evidence in (entry, proof['raw_log']):
                if evidence not in candidate['evidence']:
                    candidate['evidence'].append(evidence)
            if state['idle_gpu_ids']:
                candidate['stage'] = candidate.get('blocked_from_stage', 'validation')
                for key in ('blocker', 'blocker_kind', 'blocked_from_stage', 'retry_after', 'unblock_condition'):
                    candidate.pop(key, None)
            else:
                candidate['retry_after'] = (observed + timedelta(hours=1)).isoformat()
        if context.get('experiment_first', {}).get('enabled'):
            work['tick_attempt'] = dict(tick_started_at=context['generated_at'], candidate_id=candidates[0]['id'],
                kind='resource_check', result='passed' if state['idle_gpu_ids'] else 'blocked',
                command=proof['command'], observation='Fresh authorized GPU inventory and all compute PIDs observed; no task launch or efficacy claim.',
                evidence=[entry])
        tick.save(root/'pipeline/research_work.json', work)
        return dict(evidence=entry, server=server_name, state=state, candidate_ids=proof['candidate_ids'])
    finally:
        lock.close()


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    parser.add_argument('--token', required=True)
    parser.add_argument('--server', required=True)
    parser.add_argument('--label')
    args=parser.parse_args()
    root=Path(os.environ.get('PROJECT_ROOT','D:/project'))/args.project
    print(json.dumps(collect(root,args.token,args.server,args.label),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
