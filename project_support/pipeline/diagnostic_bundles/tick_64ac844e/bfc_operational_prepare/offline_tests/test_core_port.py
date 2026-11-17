"""Declared narrow port, native unchanged protocol and command mock checks."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ORIGIN=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ORIGIN))
import adapter
REFERENCE=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/manual_gpu1_20261025/bcr_gpu1_operational_prepare')
NATIVE_ORIGIN=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_ab7e46d4/bfc_native_prepare')
BASE_HASHES={'adapter.py':'a7fbbdf1781a8d403eba004bedc0927d667d73a38ad38f7441bd3db1ba723037','remote_ops.py':'5bba6f0325092a4cb789029e9cd3f716eabc585edf7c96dc153e302ca0755fde'}

def translated(text):
    for old,new in adapter.read(ORIGIN/'port_provenance.json')['declared_ordered_text_transformations']:
        text=text.replace(old,new)
    return text

class PortTests(unittest.TestCase):
    def test_origin_and_promoted_native_maps_remain_source_bound(self):
        self.assertEqual(adapter.sha(NATIVE_ORIGIN/'preparation.json'),'727b89a23dedd97f152a557755133c73ce338c311689a716cc32c336e39259f4')
        for directory in [NATIVE_ORIGIN,ORIGIN/'native']:
            prep=adapter.read(directory/'preparation.json');self.assertEqual(len(prep['prepared_file_hashes']),14)
            self.assertEqual(prep['source_commit'],adapter.COMMIT)
            for name,h in prep['prepared_file_hashes'].items():self.assertEqual(adapter.sha(directory/name),h,name)
            manifest=adapter.read(directory/'manifest_template.json');self.assertEqual(len(manifest['diagnostic_files']),12)
            for name,h in manifest['diagnostic_files'].items():self.assertEqual(adapter.sha(directory/name),h,name)
            for key in ['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']:self.assertIsNone(manifest[key])
        self.assertEqual((ORIGIN/'native/source_version_binding.json').read_bytes(),(NATIVE_ORIGIN/'source_version_binding.json').read_bytes())
        proof=adapter.read(ORIGIN/'native/source_version_binding.json');self.assertEqual(proof['parent_commit'],'11a811618179ab1ddc0cee299194667413b7fdb9');self.assertEqual(proof['code_commit'],adapter.COMMIT);self.assertEqual(len(proof['source_files']),9)

    def test_runtime_has_only_authorized_draft_literal_change(self):
        before=(NATIVE_ORIGIN/'native_runtime.py').read_bytes();after=(ORIGIN/'native/native_runtime.py').read_bytes()
        self.assertEqual(before.count(b'DRAFT_EXECUTION_DISABLED = True'),1)
        self.assertEqual(after,before.replace(b'DRAFT_EXECUTION_DISABLED = True',b'DRAFT_EXECUTION_DISABLED = False'))
        self.assertEqual((NATIVE_ORIGIN/'worker.py').read_bytes(),(ORIGIN/'native/worker.py').read_bytes())
        self.assertEqual(adapter.sha(ORIGIN/'native/worker.py'),'8839251920577921493b0b663df123c330b850b08779c9841d1d98bbe26e813e')

    def test_original_standard_resource_function_AST_is_unchanged(self):
        get=lambda p:next(n for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='resources')
        self.assertEqual(ast.dump(get(REFERENCE/'native/worker.py'),include_attributes=False),ast.dump(get(ORIGIN/'native/worker.py'),include_attributes=False))

    def test_exact_full_source_declared_port(self):
        for name,h in BASE_HASHES.items():
            self.assertEqual(adapter.sha(REFERENCE/name),h)
            self.assertEqual((ORIGIN/name).read_text(encoding='utf-8'),translated((REFERENCE/name).read_text(encoding='utf-8')),name)

    def test_full_AST_declared_port(self):
        for name in BASE_HASHES:
            expected=ast.parse(translated((REFERENCE/name).read_text(encoding='utf-8')));actual=ast.parse((ORIGIN/name).read_text(encoding='utf-8'))
            self.assertEqual(ast.dump(expected,include_attributes=False),ast.dump(actual,include_attributes=False),name)

    def test_current_dependency_hash_constants_are_final(self):
        for value in [adapter.PREPARATION_SHA,adapter.TEMPLATE_SHA]:self.assertRegex(value,r'^[0-9a-f]{64}$')
        self.assertEqual(adapter.sha(adapter.FROZEN/'preparation.json'),adapter.PREPARATION_SHA)
        self.assertEqual(adapter.sha(adapter.FROZEN/'manifest_template.json'),adapter.TEMPLATE_SHA)
        release=adapter.read(ORIGIN/'release_template.json');self.assertEqual(release['source_hashes'],{n:adapter.sha(ORIGIN/n) for n in BASE_HASHES});self.assertEqual(release['native_preparation_sha256'],adapter.PREPARATION_SHA)

    def test_import_does_not_bind_static_preparation_owner_or_torch(self):
        source=(ORIGIN/'adapter.py').read_text(encoding='utf-8');self.assertNotIn('64ac844e35434422a64b1eea3d01cfa8',source);self.assertNotIn('torch',sys.modules)
        self.assertEqual(adapter.CANDIDATE,'hierarchy-parent-butterfly-token-composition');self.assertEqual(adapter.COMMIT,'48fc302c3c02ffef0b241be3593c386b6b65a72e')

    def test_pinned_transport_command_constructed_only_with_mock(self):
        class Completed:
            returncode=0;stdout=json.dumps({'mock_only':True});stderr=''
        server={'host':'192.168.1.115','user':'songcl','conda_source':'/mock/conda.sh','conda_env':'mock_env'}
        with patch.object(adapter.subprocess,'run',return_value=Completed()) as run:result=adapter.SSHTransport(ORIGIN).call('probe',{'physical_gpu':0},server,timeout=1)
        self.assertEqual(result,{'mock_only':True});args,kwargs=run.call_args;command=args[0]
        self.assertEqual(command[:7],['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10']);self.assertEqual(command[7],'songcl@192.168.1.115');self.assertIn('/usr/bin/python3 -B -',command[8]);self.assertIn("socket.gethostname()=='dl04-MS-7E06'",kwargs['input']);self.assertIn('bfc_remote_ops',kwargs['input'])

    def test_API_and_no_automatic_production_execution_artifacts(self):
        for name in ['guard','probe','prepare','stage','run','pair','run_pair','status','reconcile']:self.assertTrue(callable(getattr(adapter.Adapter,name)))
        for name in ['adapter_release.json','execution_binding.json','native_manifest.json','execution_lease.json']:self.assertFalse((ORIGIN/name).exists(),name)

    def test_native_selected_card_formula_and_worker_quadrants_unchanged(self):
        runtime=(ORIGIN/'native/native_runtime.py').read_text(encoding='utf-8');self.assertIn("'bfc_' + MANIFEST['current_token'][:8] + '_gpu' + str(MANIFEST['physical_gpu'])",runtime);self.assertIn('PHYSICAL_GPU in GPU_UUIDS',runtime)
        self.assertEqual((ORIGIN/'native/worker.py').read_bytes(),(NATIVE_ORIGIN/'worker.py').read_bytes())
