"""Run one saved deployment/diagnostic program under the current owned lease."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import yaml

sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
ROOT = Path('D:/project/cluster_project')
BUNDLE = Path(__file__).resolve().parent
TOKEN = 'abdff23d5e2e40c3aadcde78f6b4fea9'


def guard():
    owner = tick.load(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN and owner['thread_id'] == os.environ['CODEX_THREAD_ID']
    assert owner['deadline_at'] == '2026-10-16T01:02:48.026347+00:00'
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds() > 120
    allocation = tick.load(BUNDLE / 'allocation.json')
    assert tick.digest(ROOT / 'pipeline/goal.json') == allocation['goal_sha256']
    servers = yaml.safe_load((ROOT / 'SERVERS.yaml').read_text(encoding='utf-8'))['servers']
    assert servers['server-3']['allowed_gpus'] == [1] and servers['server-3']['dispatch_enabled']
    assert servers['server-4']['allowed_gpus'] == [] and not servers['server-4']['dispatch_enabled']
    return owner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('--python', default='/home/songcl/.conda/envs/3d-stmn/bin/python')
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--attempt-tag', default='')
    parser.add_argument('args', nargs='*')
    options = parser.parse_args()
    owner = guard()
    assert options.name in ('deploy_server3', 'native_capture_server3', 'compatibility_probe_server3', 'extension_build_server3', 'extension_build_distutils_server3', 'postverify_server3', 'native_capture_analysis_server3', 'capture_metadata_server3', 'native_capture_analysis_server3_v2')
    source = BUNDLE / (options.name + '.py')
    compile(source.read_text(encoding='utf-8'), str(source), 'exec')
    label = options.name + ('_prepare' if '--prepare-only' in options.args else '')
    assert all(c.isalnum() or c in '_-' for c in options.attempt_tag)
    if options.attempt_tag: label += '_' + options.attempt_tag
    attempt = BUNDLE / (label + '_attempt.json')
    assert not attempt.exists(), 'Keep previous attempts; do not overwrite.'
    command = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
               '-o','ConnectTimeout=8','server-3',options.python,'-B','-',*options.args]
    timeout = min(options.timeout, int((datetime.fromisoformat(owner['deadline_at'])-
                   datetime.now(timezone.utc)).total_seconds())-120)
    assert timeout > 10
    run = subprocess.run(command, input=source.read_text(encoding='utf-8'),
                         text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    guard()
    tick.save(attempt, {'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'source_sha256':tick.digest(source),'returncode':run.returncode,
        'stdout':run.stdout,'stderr':run.stderr})
    print(run.stdout[-16000:])
    print(run.stderr[-6000:])
    print('returncode='+str(run.returncode))
    raise SystemExit(run.returncode)


if __name__ == '__main__':
    main()
