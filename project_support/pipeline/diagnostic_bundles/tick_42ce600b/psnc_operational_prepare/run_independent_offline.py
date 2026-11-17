"""Run only the local mocked review suite and retain exact source-bound results."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

OUT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
args = parser.parse_args()
target = (OUT / args.output).resolve()
assert target.parent == OUT and not target.exists(), 'New local result filename required'
assert 'torch' not in sys.modules
events = []


def audit(event, values):
    if event in ('subprocess.Popen', 'os.system', 'socket.connect'):
        events.append(event)
        raise AssertionError('Real process/network action forbidden in offline review: ' + event)
    if event == 'open' and isinstance(values[0], (str, bytes)):
        path, mode, flags = values[:3]
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags, int) and flags & (1 | 2 | 64 | 512 | 1024))
        if writing:
            assert Path(path).resolve().is_relative_to(OUT), 'Write outside review fixture tree'
    if event in ('os.remove', 'os.rmdir', 'os.mkdir'):
        assert Path(values[0]).resolve().is_relative_to(OUT), 'Mutation outside review fixture tree'


sys.addaudithook(audit)
names = ('adapter.py', 'remote_ops.py', 'release_template.json',
    'native/preparation.json', 'native/manifest_template.json',
    'test_adapter_review.py', 'test_remote_ops_offline.py', Path(__file__).name)
hashes = {n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in names}
import test_adapter_review
import test_remote_ops_offline


class Result(unittest.TextTestResult):
    def __init__(self, *arguments, **kwargs):
        super().__init__(*arguments, **kwargs)
        self.items = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.items.append({'test':test.id(), 'status':'PASS'})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.items.append({'test':test.id(), 'status':'FAIL', 'detail':self._exc_info_to_string(error, test)})

    def addError(self, test, error):
        super().addError(test, error)
        self.items.append({'test':test.id(), 'status':'ERROR', 'detail':self._exc_info_to_string(error, test)})


suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)
    for m in (test_adapter_review, test_remote_ops_offline))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Result).run(suite)
assert 'torch' not in sys.modules
unchanged = hashes == {n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in names}
payload = dict(generated_at=datetime.now(timezone.utc).isoformat(),
    result_kind='ACTUAL_OFFLINE_MOCK_EXECUTION_ONLY', source_hashes=hashes,
    tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
    successful=result.wasSuccessful() and unchanged, source_unchanged_during_run=unchanged,
    real_process_or_network_audit_events=events, torch_imported=False,
    production_static_release_exists=(OUT/'adapter_release.json').exists(),
    simulated_material_scope='Disposable temporary fixture projects below this directory only',
    native_execution='NOT_RUN', gpu_execution='NOT_RUN', transport_execution='MOCK_ONLY',
    cases=result.items, stdout=stream.getvalue())
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k:payload[k] for k in ('tests_run','failures','errors','successful',
    'source_unchanged_during_run','production_static_release_exists')}))
print('result_sha256=' + hashlib.sha256(target.read_bytes()).hexdigest())
sys.exit(0 if payload['successful'] else 1)
