"""BEC exact source/version/guard port tests. No model or transport execution."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

ORIGIN=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ORIGIN))
import adapter
REFERENCE=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_6bdbcf77/cts_operational_prepare')
NATIVE_ORIGIN=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_prepare')
SOURCE=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_6bdbcf77/new_candidate_prepare')
PARENT='48fc302c3c02ffef0b241be3593c386b6b65a72e'
COMMIT='9b6782f44ca7f2c8ac35baea01dfd070314b5701'
ACTIVE=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')


def translate(text):
    for old,new in adapter.read(ORIGIN/'port_provenance.json')['declared_ordered_text_transformations']:
        text=text.replace(old,new)
    return text


def expected_adapter():
    return translate((REFERENCE/'adapter.py').read_text(encoding='utf-8'))


def function(source,name):
    return next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)


class PortTests(unittest.TestCase):
    def test_exact_full_declared_adapter_remote_source_port(self):
        self.assertEqual((ORIGIN/'adapter.py').read_text(encoding='utf-8'),expected_adapter())
        self.assertEqual((ORIGIN/'remote_ops.py').read_text(encoding='utf-8'),translate((REFERENCE/'remote_ops.py').read_text(encoding='utf-8')))

    def test_runtime_only_explicit_version_capability_and_runtime_assertion_changes(self):
        before=(NATIVE_ORIGIN/'native_runtime.py').read_text(encoding='utf-8')
        prep=adapter.read(ORIGIN/'native/preparation.json')
        for old,new in prep['runtime_declared_ordered_text_transformations']:
            self.assertEqual(before.count(old),1);before=before.replace(old,new,1)
        self.assertEqual(before,(ORIGIN/'native/native_runtime.py').read_text(encoding='utf-8'))
        # All inherited runtime guard/function bodies remain exact.
        oldtree=ast.parse((NATIVE_ORIGIN/'native_runtime.py').read_text(encoding='utf-8'))
        newtree=ast.parse(before)
        funcs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(funcs(oldtree),funcs(newtree))

    def test_original_worker_and_full_resource_AST_unchanged(self):
        old=(NATIVE_ORIGIN/'worker.py').read_bytes();new=(ORIGIN/'native/worker.py').read_bytes()
        self.assertEqual(old,new)
        self.assertEqual(hashlib.sha256(new).hexdigest(),'7e5d0f5b109e85d0d2f0bb7f2f806dd9db73fb7885add5abc372ce244ee753e3')
        f=lambda p:ast.dump(function(p.read_text(encoding='utf-8'),'resources'),include_attributes=False)
        self.assertEqual(f(NATIVE_ORIGIN/'worker.py'),f(ORIGIN/'native/worker.py'))
        self.assertEqual(f(REFERENCE/'native/worker.py'),f(ORIGIN/'native/worker.py'))

    def test_source_and_original_disabled_packet_remain_null_and_immutable(self):
        self.assertEqual(adapter.sha(NATIVE_ORIGIN/'preparation.json'),'322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff')
        source=adapter.read(SOURCE/'preparation.json')
        self.assertTrue(all(source[k] is None for k in ('code_commit','source_commit','future_version_parent')))
        old=adapter.read(NATIVE_ORIGIN/'manifest_template.json')
        self.assertTrue(old['draft_execution_disabled']);self.assertIsNone(old['code_commit'])
        for name,h in adapter.read(NATIVE_ORIGIN/'preparation.json')['prepared_file_hashes'].items():
            self.assertEqual(adapter.sha(NATIVE_ORIGIN/name),h,name)

    def test_version_bound_native14_diag12_maps_and_ten_active_null(self):
        p=adapter.read(ORIGIN/'native/preparation.json');m=adapter.read(ORIGIN/'native/manifest_template.json')
        self.assertEqual(len(p['prepared_file_hashes']),14);self.assertEqual(len(m['diagnostic_files']),12)
        self.assertEqual(p['source_commit'],COMMIT);self.assertEqual(p['source_parent_commit'],PARENT)
        for name,h in p['prepared_file_hashes'].items():self.assertEqual(adapter.sha(ORIGIN/'native'/name),h,name)
        for name,h in m['diagnostic_files'].items():self.assertEqual(adapter.sha(ORIGIN/'native'/name),h,name)
        for k in ACTIVE:self.assertIsNone(m[k]);self.assertIsNone(p['manifest_execution_fields'][k])
        self.assertEqual(m['runtime_expected_commit'],PARENT);self.assertFalse(m['draft_execution_disabled'])

    def test_actual_version_proof_not_old_null_declaration(self):
        v=adapter.read(ORIGIN/'native/source_version_binding.json')
        self.assertEqual(v['code_commit'],COMMIT);self.assertEqual(v['parent_commit'],PARENT)
        self.assertEqual(v['future_version_parent'],PARENT)
        proof=adapter.read(adapter.PROJECT_ROOT/v['isolated_source_version']['path'])
        self.assertEqual(adapter.sha(adapter.PROJECT_ROOT/v['isolated_source_version']['path']),v['isolated_source_version']['sha256'])
        self.assertEqual(proof['committed_blob_sha256'],v['source_files']);self.assertEqual(len(v['source_files']),9)
        self.assertEqual(proof['code_commit'],COMMIT);self.assertEqual(proof['parent_commit'],PARENT)
        self.assertEqual(v['original_source_preparation_sha256'],'2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d')
        for n,h in v['candidate_source_hashes'].items():self.assertEqual(adapter.sha(ORIGIN/'native/candidate_model'/n),h)
        self.assertEqual(v['source_files'],{n.removeprefix('staged_repository/'):h for n,h in adapter.read(SOURCE/'preparation.json')['prepared_file_hashes'].items() if n.startswith('staged_repository/')})

    def test_static_catalog_current_source_hashes_no_active_release(self):
        self.assertEqual(adapter.sha(adapter.FROZEN/'preparation.json'),adapter.PREPARATION_SHA)
        self.assertEqual(adapter.sha(adapter.FROZEN/'manifest_template.json'),adapter.TEMPLATE_SHA)
        r=adapter.read(ORIGIN/'release_template.json')
        self.assertEqual(r['source_hashes'],{n:adapter.sha(ORIGIN/n) for n in ('adapter.py','remote_ops.py')})
        self.assertEqual(r['native_preparation_sha256'],adapter.PREPARATION_SHA)
        self.assertEqual(adapter.CANDIDATE,'hierarchy-cross-level-bipartite-edge-composition')
        self.assertEqual(adapter.COMMIT,COMMIT);self.assertEqual(adapter.RUNTIME_EXPECTED_COMMIT,PARENT)
        for name in ('adapter_release.json','execution_binding.json','native_manifest.json','execution_lease.json'):
            self.assertFalse((ORIGIN/name).exists(),name);self.assertFalse((ORIGIN/'native'/name).exists(),name)
        self.assertNotIn('torch',sys.modules)

    def test_runtime_parent_mismatch_refuses_without_binding_or_transport(self):
        a=adapter.Adapter()
        good=dict(server_id='server-4',hostname='dl04-MS-7E06',root=adapter.REMOTE_ROOT,
            physical_gpu=0,gpu_uuid=adapter.GPU_UUIDS[0],runtime_code_commit=PARENT,
            idle=True,contexts=[],memory_used_mib=0,utilization_percent=0,
            locks={k:'available' for k in ('training','diagnostic','exclusive')})
        a._check_probe(good,0)
        for commit in (COMMIT,'a'*40,'11a811618179ab1ddc0cee299194667413b7fdb9','',None):
            with self.subTest(commit=commit),self.assertRaises((adapter.Refused,TypeError)):
                a._check_probe(dict(good,runtime_code_commit=commit),0)

    def test_pinned_transport_command_is_constructed_only_with_mock(self):
        class Completed:returncode=0;stdout=json.dumps({'mock_only':True});stderr=''
        server={'host':'192.168.1.115','user':'songcl','conda_source':'/mock/conda.sh','conda_env':'mock_env'}
        with patch.object(adapter.subprocess,'run',return_value=Completed()) as run:
            self.assertEqual(adapter.SSHTransport(ORIGIN).call('probe',{'physical_gpu':1},server,timeout=1),{'mock_only':True})
        args,kwargs=run.call_args;command=args[0]
        self.assertEqual(command[:7],['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10'])
        self.assertEqual(command[7],'songcl@192.168.1.115')
        self.assertIn("socket.gethostname()=='dl04-MS-7E06'",kwargs['input']);self.assertIn('bec_remote_ops',kwargs['input'])

    def test_no_old_preparation_token_and_stage_selected_card_formula(self):
        s=(ORIGIN/'adapter.py').read_text(encoding='utf-8')
        self.assertNotIn('521a6f59f2a74a69b41144aa6a8b6153',s)
        self.assertIn("'/bec_'".strip("'"),s)
        runtime=(ORIGIN/'native/native_runtime.py').read_text(encoding='utf-8')
        self.assertIn("'bec_' + MANIFEST['current_token'][:8] + '_gpu' + str(MANIFEST['physical_gpu'])",runtime)
        self.assertIn("CUDA_VISIBLE_DEVICES=GPU_UUIDS[PHYSICAL_GPU]",runtime)
        self.assertIn("assert MANIFEST['runtime_code_commit'] == RUNTIME_EXPECTED_COMMIT",runtime)

