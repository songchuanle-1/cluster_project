"""Exact source-port and command-construction checks; no tensor/native model."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ORIGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ORIGIN))
import adapter

REFERENCE = Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_42ce600b/psnc_operational_prepare')
BASE_HASHES = {'adapter.py': '95d6788db45eb014cfc6bb354bac346874f8db6bc1d6536e06e500249ea4f682',
               'remote_ops.py': '46c2843636baf06ce6b8bac43e47828277aaa3c6363e875a46b59a7aba09247a'}


def translated(data):
    replacements = [(b'hierarchy-parent-spectral-nonlinear-token-coupling',
                     b'hierarchy-parent-binary-tree-complement-composition'),
                    (b'43dce016c1a1713c2a5dab7061810dc2efde8954',
                     b'00e2b18c6b8d568a64edb496e6979d766440883c'),
                    (b'tick_42ce600b', b'tick_7dcc29e8'),
                    (b'M210-PSNC', b'M211-BTC'), (b'PSNC', b'BTC'), (b'psnc', b'btc'),
                    (b'eebd34a6d2123cc8728d5e2dd6ebc8d055473e5bbf8da1fd33f909ae4e1c77d6',
                     adapter.PREPARATION_SHA.encode()),
                    (b'd55848c32d8e95a3d4d34dc1a339050fb9f8b2d96b2bc74fe18c3a138bb63bd4',
                     adapter.TEMPLATE_SHA.encode())]
    for old, new in replacements:
        data = data.replace(old, new)
    return data


class PortTests(unittest.TestCase):
    def test_exact_full_source_literal_port_no_guard_logic_change(self):
        for name, expected_hash in BASE_HASHES.items():
            original = (REFERENCE / name).read_bytes()
            self.assertEqual(hashlib.sha256(original).hexdigest(), expected_hash)
            self.assertEqual((ORIGIN / name).read_bytes(), translated(original), name)

    def test_full_AST_literal_port(self):
        for name in BASE_HASHES:
            expected = ast.parse(translated((REFERENCE / name).read_bytes()).decode())
            actual = ast.parse((ORIGIN / name).read_text('utf-8'))
            self.assertEqual(ast.dump(expected, include_attributes=False),
                             ast.dump(actual, include_attributes=False), name)

    def test_current_dependency_hash_constants_are_final(self):
        for value in [adapter.PREPARATION_SHA, adapter.TEMPLATE_SHA]:
            self.assertRegex(value, r'^[0-9a-f]{64}$')
        self.assertEqual(adapter.sha(adapter.FROZEN / 'preparation.json'), adapter.PREPARATION_SHA)
        self.assertEqual(adapter.sha(adapter.FROZEN / 'manifest_template.json'), adapter.TEMPLATE_SHA)

    def test_import_does_not_bind_current_preparation_tick_or_torch(self):
        source = (ORIGIN / 'adapter.py').read_text('utf-8')
        self.assertNotIn('7dcc29e8844245ec87b6d58eee6ec966', source)
        self.assertNotIn('torch', sys.modules)
        self.assertEqual(adapter.CANDIDATE, 'hierarchy-parent-binary-tree-complement-composition')
        self.assertEqual(adapter.COMMIT, '00e2b18c6b8d568a64edb496e6979d766440883c')

    def test_pinned_transport_command_constructed_only_with_mock(self):
        class Completed:
            returncode = 0
            stdout = json.dumps({'mock_only': True})
            stderr = ''
        server = {'host': '192.168.1.115', 'user': 'songcl',
                  'conda_source': '/mock/conda.sh', 'conda_env': 'mock_env'}
        with patch.object(adapter.subprocess, 'run', return_value=Completed()) as run:
            result = adapter.SSHTransport(ORIGIN).call('probe', {'physical_gpu': 0}, server, timeout=1)
        self.assertEqual(result, {'mock_only': True})
        args, kwargs = run.call_args
        command = args[0]
        self.assertEqual(command[:7], ['ssh', '-o', 'BatchMode=yes', '-o',
                                      'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10'])
        self.assertEqual(command[7], 'songcl@192.168.1.115')
        self.assertIn('/usr/bin/python3 -B -', command[8])
        self.assertIn("socket.gethostname()=='dl04-MS-7E06'", kwargs['input'])
        self.assertIn('btc_remote_ops', kwargs['input'])

    def test_API_and_no_automatic_production_execution_artifacts(self):
        for name in ['guard', 'probe', 'prepare', 'stage', 'run', 'pair', 'run_pair', 'status', 'reconcile']:
            self.assertTrue(callable(getattr(adapter.Adapter, name)))
        for name in ['adapter_release.json', 'execution_binding.json', 'native_manifest.json', 'execution_lease.json']:
            self.assertFalse((ORIGIN / name).exists(), name)
