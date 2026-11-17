"""Lease-bound orchestration of one isolated server-4 CPU diagnostic."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
ROOT = Path('D:/project/cluster_project')
TOKEN = 'e90e90d5415549a4a85c0650ddf62a88'
BUNDLE = Path(__file__).resolve().parent
OLD = ROOT / 'pipeline/diagnostic_bundles/hier_support_5df76ddd906e4741b57970488d4b33bd'


def guard():
    owner = tick.load(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN and owner['thread_id'] == os.environ['CODEX_THREAD_ID']
    assert tick.digest(ROOT / 'pipeline/goal.json') == '6a11a897c8378c48934590d7603b5cbd18cac2d43da40690e0a7c72080f5478c'
    assert (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds() > 180


def main():
    guard()
    assert not (BUNDLE / 'attempt.json').exists()
    sources = {'PROTOTYPE': OLD / 'hier_support.py',
        'FROZEN_TEST_SOURCE': OLD / 'test_cpu.py', 'DIAGNOSTIC': BUNDLE / 'numeric_cpu.py'}
    expected = {'PROTOTYPE': 'caf8767e1cfb8b78d3e8030ca0c2a3932e8b0be4f75f819563ccec93bb76b9e3',
        'FROZEN_TEST_SOURCE': 'a05a91b87ab0d8a823c86254bb42dd0feaa9125dc6d9dce07a65e016ca5230bd'}
    for name, digest in expected.items():
        assert tick.digest(sources[name]) == digest
    texts = {name: p.read_text(encoding='utf-8') for name, p in sources.items()}
    for name, text in texts.items():
        compile(text, str(sources[name]), 'exec')
    program = '\n'.join(name + '=' + repr(text) for name, text in texts.items()) + '''
import hashlib,os,pathlib,subprocess,sys,types
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
source=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/hier_postprocess.py')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
module=types.ModuleType('hier_support')
sys.modules['hier_support']=module
exec(compile(PROTOTYPE,'<unchanged-frozen-prototype>','exec'),module.__dict__)
exec(compile(DIAGNOSTIC,'<preregistered-numerical-localization>','exec'),{'FROZEN_TEST_SOURCE':FROZEN_TEST_SOURCE,'__name__':'__main__'})
'''
    remote = BUNDLE / 'remote_numeric.py'
    assert not remote.exists()
    remote.write_text(program, encoding='utf-8')
    tick.save(BUNDLE / 'frozen_sources.json', {'token': TOKEN,
        'frozen_at': datetime.now(timezone.utc).isoformat(),
        'files': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': tick.digest(p)}
            for p in [*sources.values(), BUNDLE / 'prereg.md', Path(__file__).resolve()]]})
    execution = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
        '-o', 'ConnectTimeout=12', 'server-4',
        '/home/songcl/.conda/envs/project_cluster/bin/python', '-B', '-'],
        input=program, text=True, encoding='utf-8', capture_output=True, timeout=240)
    guard()
    tick.save(BUNDLE / 'attempt.json', {'token': TOKEN,
        'recorded_at': datetime.now(timezone.utc).isoformat(), 'returncode': execution.returncode,
        'stdout': execution.stdout, 'stderr': execution.stderr, 'program_sha256': tick.digest(remote)})
    lines = [line for line in execution.stdout.splitlines() if line.startswith('HIER_NUMERIC_JSON=')]
    if not lines:
        print(execution.stderr[-6000:])
        raise SystemExit(execution.returncode or 2)
    result = {'token': TOKEN, 'observed_at': datetime.now(timezone.utc).isoformat(),
              **json.loads(lines[-1].split('=', 1)[1])}
    tick.save(BUNDLE / 'result.json', result)
    print(json.dumps(result, indent=2))
    raise SystemExit(execution.returncode)


if __name__ == '__main__':
    main()
