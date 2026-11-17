"""Run local mocks with an audit fence; never call production transport/prepare."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

OUT = Path(__file__).resolve().parent
ORIGIN = OUT.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True)
parser.add_argument('--suite', choices=['remote', 'all'], default='all')
args = parser.parse_args()
target = (OUT / args.output).resolve()
assert target.parent == OUT and not target.exists(), 'Exclusive new result path required'
assert 'torch' not in sys.modules
events = []


def audit(event, values):
    if event in ('subprocess.Popen', 'os.system', 'socket.connect'):
        events.append(event)
        raise AssertionError('Real process/network forbidden: ' + event)
    if event == 'open' and isinstance(values[0], (str, bytes)):
        path, mode, flags = values[:3]
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags, int) and flags & (1 | 2 | 64 | 512 | 1024))
        if writing:
            assert Path(path).resolve().is_relative_to(OUT), 'Write outside offline fixture subtree'
    if event in ('os.remove', 'os.rmdir', 'os.mkdir'):
        assert Path(values[0]).resolve().is_relative_to(OUT), 'Mutation outside offline fixture subtree'


sys.addaudithook(audit)
names = ['adapter.py', 'remote_ops.py', 'offline_tests/test_remote_ops_offline.py',
         'offline_tests/' + Path(__file__).name]
if args.suite == 'all':
    names += ['release_template.json', 'native/preparation.json', 'native/manifest_template.json',
              'offline_tests/test_adapter_review.py', 'offline_tests/test_core_port.py']


def hashes():
    return {n: hashlib.sha256((ORIGIN / n).read_bytes()).hexdigest() for n in names}


before = hashes()
import test_remote_ops_offline
modules = [test_remote_ops_offline]
if args.suite == 'all':
    import test_adapter_review
    import test_core_port
    modules += [test_adapter_review, test_core_port]


class Result(unittest.TextTestResult):
    def __init__(self, *arguments, **kwargs):
        super().__init__(*arguments, **kwargs)
        self.items = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.items.append({'test': test.id(), 'status': 'PASS'})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.items.append({'test': test.id(), 'status': 'FAIL',
                           'detail': self._exc_info_to_string(error, test)})

    def addError(self, test, error):
        super().addError(test, error)
        self.items.append({'test': test.id(), 'status': 'ERROR',
                           'detail': self._exc_info_to_string(error, test)})


suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in modules)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Result).run(suite)
assert 'torch' not in sys.modules
unchanged = before == hashes()
payload = {'generated_at': datetime.now(timezone.utc).isoformat(),
           'result_kind': 'ACTUAL_OFFLINE_MOCK_EXECUTION_ONLY', 'suite': args.suite,
           'source_hashes': before, 'tests_run': result.testsRun,
           'failures': len(result.failures), 'errors': len(result.errors),
           'successful': result.wasSuccessful() and unchanged,
           'source_unchanged_during_run': unchanged, 'real_process_or_network_audit_events': events,
           'torch_imported': False, 'production_static_release_exists': (ORIGIN / 'adapter_release.json').exists(),
           'simulated_material_scope': 'Disposable fixture projects inside offline_tests only',
           'native_execution': 'NOT_RUN', 'gpu_execution': 'NOT_RUN', 'transport_execution': 'MOCK_ONLY',
           'cases': result.items, 'stdout': stream.getvalue()}
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', 'utf-8')
print(json.dumps({k: payload[k] for k in ['suite', 'tests_run', 'failures', 'errors', 'successful',
                                       'source_unchanged_during_run', 'production_static_release_exists']}))
print('result_sha256=' + hashlib.sha256(target.read_bytes()).hexdigest())
sys.exit(0 if payload['successful'] else 1)
