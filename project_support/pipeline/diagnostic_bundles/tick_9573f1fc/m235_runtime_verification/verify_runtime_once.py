"""Default NOP. Root-only one read-only SSH verification; never sync or launch."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
KEYS = ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')
SOURCE = 'b1e639b3ceb14bb5c65d9f81a084d41c834b951c'
RUNTIME = '/data/songcl/Project/Cluster_project/Cluster_nsd_20261107'
GIT = 'C:/Program Files (x86)/Git/cmd/git.exe'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2); stream.write('\n')

def git(path,*args):
    return subprocess.check_output([GIT,'--no-optional-locks','-c','core.fsmonitor=false','-C',str(path),*args],
                                   env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),timeout=25)

def guard(args):
    assert sys.dont_write_bytecode and not sys.flags.optimize and sys.flags.utf8_mode
    assert os.environ.get('GIT_OPTIONAL_LOCKS') == '0'
    baseline = read(HERE/'baseline.json'); owner = baseline['owner']
    assert os.environ.get('CODEX_THREAD_ID') == owner['thread_id']
    live = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert {key:live[key] for key in KEYS} == owner
    assert owner['token'] == '9573f1fc8cad435fb47660949b563298'
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds() > 180
    assert read(ROOT/'pipeline/execution_mode.json') == {'mode':'foreground','target_thread_id':owner['thread_id']}
    for name,key in (('.tick_context.json','context_sha256'),('.tick_context_state.next.json','pending_sha256')):
        assert sha(ROOT/'pipeline/headless'/name) == owner[key]
    frozen = read(HERE/'FROZEN.json')
    assert frozen['owner'] == owner and frozen['source_commit'] == SOURCE
    assert all(sha(HERE/name) == expected for name,expected in frozen['files'].items())
    assert sha(ROOT/'SERVERS.yaml') == baseline['SERVERS_sha256']
    assert sha(ROOT/'pipeline/goal.json') == baseline['goal_sha256']
    history = baseline['historical_canonical_sync']
    assert sha(ROOT/history['path']) == history['sha256']
    history_actual = read(ROOT/history['path'])
    assert history_actual['passed'] and history_actual['canonical_safe_sync'] and history_actual['source_commit'] == SOURCE
    main = ROOT/'Cluster'
    assert git(main,'rev-parse','HEAD').decode().strip() == baseline['main_HEAD']
    index = Path(git(main,'rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute(): index = main/index
    assert sha(index) == baseline['real_index_sha256']
    assert hashlib.sha256(git(main,'ls-files','--stage','-z')).hexdigest() == baseline['real_index_entries_sha256']
    for name,expected in {**baseline['dirty_files_exact28'],**baseline['working_tree_r0_files_exact9']}.items():
        assert sha(main/name) == expected, name
    detached = ROOT/'pipeline/isolated_versions/m235_sinc_79656807'
    assert git(detached,'rev-parse','HEAD').decode().strip() == SOURCE
    assert git(detached,'status','--porcelain=v1','--untracked-files=all','-z') == b''
    assert all(sha(detached/name) == expected for name,expected in baseline['source_files_exact9'].items())
    review_path = Path(args.review).resolve()
    assert review_path.is_relative_to(HERE.parent) and sha(review_path) == args.review_sha256
    peer = read(review_path)
    assert peer['owner'] == owner and peer['passed'] is True and peer['material_concerns'] == []
    assert peer['FROZEN_sha256'] == sha(HERE/'FROZEN.json')
    assert peer['reviewer_thread_id'] not in (owner['thread_id'],'/root','/root/sinc_runtime','/root/sinc_prod')
    assert peer['runtime_source_transport_review_passed'] is True
    return baseline,owner

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root',action='store_true')
    parser.add_argument('--review'); parser.add_argument('--review-sha256')
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({'status':'DEFAULT_NOP_NO_SSH_OR_MUTATION'})); return
    assert args.review and args.review_sha256
    baseline,owner = guard(args)
    intent,actual_path = HERE/'runtime_verification.intent.json',HERE/'runtime_verification.actual.json'
    assert not intent.exists() and not actual_path.exists(), 'Existing/uncertain read: preserve; no automatic replay'
    save(intent,{'owner':owner,'kind':'READ_ONLY_RUNTIME_SOURCE_VERIFICATION','recorded_at':datetime.now(timezone.utc).isoformat(),
                 'FROZEN_sha256':sha(HERE/'FROZEN.json'),'review_sha256':args.review_sha256,
                 'new_sync_performed':False,'no_replay':True})
    remote = (HERE/'remote_verify.py.txt').read_text(encoding='utf-8')
    command = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
               '-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no','songcl@192.168.1.115',
               "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -B -c "+shlex.quote(remote)]
    record = {'owner':owner,'kind':'READ_ONLY_RUNTIME_SOURCE_VERIFICATION','passed':False,'certainty':'uncertain',
              'source_commit':SOURCE,'runtime_root':RUNTIME,'new_sync_performed':False,
              'historical_canonical_sync':baseline['historical_canonical_sync'],'training_started':False,
              'GPU_compute':False,'signals_sent':False,'remote_mutations':False,'automatic_retry':False,
              'intent_sha256':sha(intent),'FROZEN_sha256':sha(HERE/'FROZEN.json'),'review_sha256':args.review_sha256}
    outpath,errpath = HERE/'transport.stdout.partial',HERE/'transport.stderr.partial'
    try:
        with outpath.open('x+b') as outfile, errpath.open('x+b') as errfile:
            process = subprocess.Popen(command,stdin=subprocess.PIPE,stdout=outfile,stderr=errfile)
            record['local_ssh_pid'] = process.pid
            try:
                process.communicate(json.dumps({'owner':owner,'baseline':baseline,'read_only':True}).encode(),timeout=150)
            except subprocess.TimeoutExpired:
                record['reason'] = 'Read-only transport uncertain; no signals, cleanup or replay'
                save(actual_path,record); raise SystemExit(75)
        assert outpath.stat().st_size <= 1048576 and errpath.stat().st_size <= 65536
        stdout,stderr = outpath.read_text(encoding='utf-8'),errpath.read_text(encoding='utf-8',errors='replace')
        record.update(ssh_returncode=process.returncode,stderr=stderr,transport_stdout_sha256=sha(outpath))
        assert process.returncode == 0, 'Read-only verification failed; preserve actual outcome'
        observation = json.loads(stdout)
        assert observation['owner'] == owner and observation['source_integrity_before_after'] is True
        a = observation['actual']
        assert a['hostname'] == 'dl04-MS-7E06' and a['uid'] == 1001 and a['runtime_HEAD'] == SOURCE
        assert a['runtime_root'] == RUNTIME and a['new_stage_absent'] and a['markers_absent']
        record.update(actual=a,runtime_code_commit=SOURCE,source_verified=True,source_integrity_before_after=True,
                      source_files_exact9=baseline['source_files_exact9'],observed_at=observation['observed_at'])
        guard(args)
        record.update(passed=True,certainty='terminal',completed_at=datetime.now(timezone.utc).isoformat())
    except Exception as error:
        record.update(error_type=type(error).__name__,error=str(error),completed_at=datetime.now(timezone.utc).isoformat())
        if not actual_path.exists(): save(actual_path,record)
        raise
    save(actual_path,record)
    print(json.dumps({'path':str(actual_path),'sha256':sha(actual_path),'passed':True,'new_sync_performed':False}))

if __name__ == '__main__':
    main()
