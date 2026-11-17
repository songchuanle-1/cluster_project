"""Fresh foreground lease, exact frozen PCE revision2 revalidation only."""
import argparse
import hashlib
import importlib.util
import shutil
from pathlib import Path

ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_fefdcc2a'
spec = importlib.util.spec_from_file_location('pce_leased_ops', OLD / 'control.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
c.TOKEN = '3259705f09e24e0b90718a29a9015c27'
c.OUT = OUT
c.STAGE = '/data/songcl/Project/Cluster_project/pipeline/pce_3259705f'


def prepare():
    c.guard(1200)
    package = ROOT / 'Cluster/framework/model/Quard_model' / (c.NAME + '_pce')
    expected = c.tick.load(OLD / 'implementation_r2/native_manifest.json')['candidate_source_hashes']
    actual = {path.name: c.tick.digest(path) for path in package.glob('*.py')}
    assert actual == expected, 'Frozen revision2 source changed'
    source = OLD / 'implementation_r2/worker.py'
    shutil.copyfile(source, OUT / 'worker.py')
    receipt = c.save('continuation.json', {'recorded_at': c.now(), 'candidate_id': c.CID,
        'previous_tick': 'fefdcc2a82294674927257b9c68f7b47',
        'previous_tick_status': 'INCOMPLETE/aborted; owned lease and pending absence verified14:56:19Shanghai',
        'revision': 2, 'implementation_changed': False, 'source_sha256': actual,
        'frozen_worker': c.evidence(source), 'operations': 'Exact existing graph/operator/resources/full-source/native-backward tests; no third implementation revision or gate waiver.'})
    c.stage()
    c.advance([receipt, Path(__file__)], 'Run exact frozen revision2 combined checks on fresh current lease; preserve original andR1 failures and prior INCOMPLETE tick.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('probe', 'prepare', 'combined'))
    args = parser.parse_args()
    if args.operation == 'probe':
        c.probe()
    elif args.operation == 'prepare':
        prepare()
    else:
        c.run('combined', 'candidate')
