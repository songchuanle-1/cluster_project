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

REFERENCE = Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_41eb62fa/bcr_operational_prepare')
BASE_HASHES = {'adapter.py':'85eecbe1910956bd65d2d662d777a011c930c865f0ec0a39eae69e2aa06ec996',
               'remote_ops.py':'805afced11566bf300f6bf65090f80d605fc0b3d59fce8aee541a7773c3497d4'}


def translated(data):
    changes=[(b'tick_41eb62fa/bcr_operational_prepare/native',b'manual_gpu1_20261025/bcr_gpu1_operational_prepare/native'),
             (b'a7ba73ba7610fa3e0dbac6f4a496f1657e8cf09f725d2b88f24df1d97ecff604',adapter.PREPARATION_SHA.encode()),
             (b'9be089d9434749ef6e5b2f95b80bd07307f416e63ec93a3455e28789b6e7e31a',adapter.TEMPLATE_SHA.encode()),
             (b'gpu == 0',b'gpu == 1'),(b'gpu==0',b'gpu==1'),(b"['physical_gpu']==0",b"['physical_gpu']==1"),
             (b'GPU0',b'GPU1'),(b'physical0',b'physical1'),(b'choices=[0]',b'choices=[1]'),
             (b"'bcr_execution'",b"'bcr_gpu1_execution'"),(b"'/bcr_'",b"'/bcr_gpu1_'"),(b"('bcr_'+",b"('bcr_gpu1_'+")]
    for old,new in changes:data=data.replace(old,new)
    return data


class PortTests(unittest.TestCase):
    def test_origin_and_promoted_native_maps_remain_source_bound(self):
        native = ORIGIN / 'native'
        origin = ORIGIN.parent / 'bcr_gpu1_native_prepare'
        self.assertEqual(adapter.sha(origin / 'preparation.json'), 'cc8b4b16f8a81a1f560a53da8cf988ae7548ead07d471b198709d02337042c7f')
        for directory in [origin, native]:
            prep = adapter.read(directory / 'preparation.json')
            self.assertEqual(len(prep['prepared_file_hashes']), 17)
            self.assertEqual(prep['source_commit'], adapter.COMMIT)
            for name, expected in prep['prepared_file_hashes'].items():
                self.assertEqual(adapter.sha(directory / name), expected, name)
            manifest = adapter.read(directory / 'manifest_template.json')
            self.assertEqual(len(manifest['diagnostic_files']), 12)
            for name, expected in manifest['diagnostic_files'].items():
                self.assertEqual(adapter.sha(directory / name), expected, name)
            for key in ['current_token', 'stage', 'tick_generated_at', 'deadline_at', 'physical_gpu',
                        'gpu_uuid', 'allowed_gpus', 'context_sha256', 'pending_sha256', 'runtime_code_commit']:
                self.assertIsNone(manifest[key])
        self.assertEqual((native / 'source_version_binding.json').read_bytes(),
                         (origin / 'source_version_binding.json').read_bytes())
        proof = adapter.read(native / 'source_version_binding.json')
        self.assertEqual(proof['parent_commit'], '00e2b18c6b8d568a64edb496e6979d766440883c')
        self.assertEqual(len(proof['source_files']), 9)

    def test_runtime_has_only_authorized_draft_literal_change(self):
        origin = ORIGIN.parent / 'bcr_gpu1_native_prepare'
        before = (origin / 'native_runtime.py').read_bytes()
        after = (ORIGIN / 'native/native_runtime.py').read_bytes()
        self.assertEqual(before.count(b'DRAFT_EXECUTION_DISABLED = True'), 1)
        self.assertEqual(after, before.replace(b'DRAFT_EXECUTION_DISABLED = True', b'DRAFT_EXECUTION_DISABLED = False'))
        before_ast = ast.parse(before.decode())
        after_ast = ast.parse(after.decode())
        for tree in [before_ast, after_ast]:
            node = next(n for n in tree.body if isinstance(n, ast.Assign) and
                        any(isinstance(t, ast.Name) and t.id == 'DRAFT_EXECUTION_DISABLED' for t in n.targets))
            node.value = ast.Constant(value=False)
        self.assertEqual(ast.dump(before_ast, include_attributes=False), ast.dump(after_ast, include_attributes=False))
        self.assertEqual((origin / 'worker.py').read_bytes(), (ORIGIN / 'native/worker.py').read_bytes())

    def test_original_standard_resource_function_AST_is_unchanged(self):
        before = ast.parse((REFERENCE / 'native/worker.py').read_text('utf-8'))
        after = ast.parse((ORIGIN / 'native/worker.py').read_text('utf-8'))
        get = lambda tree: next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'resources')
        self.assertEqual(ast.dump(get(before), include_attributes=False), ast.dump(get(after), include_attributes=False))

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
        self.assertNotIn('7526f819f16e4f688566119d347cd198', source)
        self.assertNotIn('torch', sys.modules)
        self.assertEqual(adapter.CANDIDATE, 'hierarchy-parent-bidirectional-complement-recurrence')
        self.assertEqual(adapter.COMMIT, '11a811618179ab1ddc0cee299194667413b7fdb9')

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
        self.assertIn('bcr_remote_ops', kwargs['input'])

    def test_API_and_no_automatic_production_execution_artifacts(self):
        for name in ['guard', 'probe', 'prepare', 'stage', 'run', 'pair', 'run_pair', 'status', 'reconcile']:
            self.assertTrue(callable(getattr(adapter.Adapter, name)))
        for name in ['adapter_release.json', 'execution_binding.json', 'native_manifest.json', 'execution_lease.json']:
            self.assertFalse((ORIGIN / name).exists(), name)
