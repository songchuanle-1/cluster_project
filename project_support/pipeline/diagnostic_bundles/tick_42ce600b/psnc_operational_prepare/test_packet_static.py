"""Additional version/packet/command construction checks, no SSH/model imports."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import adapter

HERE=Path(__file__).resolve().parent
NATIVE=HERE/'native'
OLD=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_d6b400e3/psnc_native_prepare')

def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def read(f):return json.loads(f.read_text(encoding='utf-8'))
def fun(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def dump(x):return ast.dump(x,include_attributes=False)

class PacketTests(unittest.TestCase):
    def test_compile_without_importing_native(self):
        for f in [HERE/'adapter.py',HERE/'remote_ops.py',NATIVE/'native_runtime.py',NATIVE/'worker.py',*list((NATIVE/'candidate_model').glob('*.py'))]:compile(f.read_text(encoding='utf-8'),str(f),'exec')
    def test_worker_entire_file_unchanged(self):self.assertEqual(sha(NATIVE/'worker.py'),'69e2f096475fb31d533d0c701a15cf9c08dc7e5d9e85d6ba58d953af50eafcdd')
    def test_native_prep_all14_hashes(self):
        p=read(NATIVE/'preparation.json');self.assertEqual(p['source_commit'],adapter.COMMIT);self.assertEqual(len(p['prepared_file_hashes']),14)
        for n,h in p['prepared_file_hashes'].items():self.assertEqual(sha(NATIVE/n),h,n)
    def test_version43_exact9_candidate_bytes(self):
        p=read(NATIVE/'source_version_binding.json');self.assertEqual(p['code_commit'],adapter.COMMIT);self.assertEqual(p['parent_commit'],'74fcd21df0af9a971792038ffe251af1ffea2604');self.assertEqual(len(p['source_files']),9)
        for n,h in p['source_files'].items():self.assertEqual(sha(NATIVE/'candidate.yaml' if n.endswith('.yaml') else NATIVE/'candidate_model'/Path(n).name),h,n)
    def test_manifest12_files_and_no_execution_binding(self):
        p=read(NATIVE/'manifest_template.json');self.assertEqual(len(p['diagnostic_files']),12)
        for n,h in p['diagnostic_files'].items():self.assertEqual(sha(NATIVE/n),h,n)
        for k in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit'):self.assertIsNone(p[k],k)
        for path in (HERE,NATIVE):
            for n in ('adapter_release.json','native_manifest.json','execution_lease.json','execution_binding.json'):self.assertFalse((path/n).exists(),n)
    def test_runtime_version_verify_positive_and_mismatches(self):
        function=fun(ast.parse((NATIVE/'native_runtime.py').read_text(encoding='utf-8')),'verify_source_version')
        with tempfile.TemporaryDirectory() as temp:
            stage=Path(temp);p=read(NATIVE/'source_version_binding.json');f=stage/'source_version_binding.json';f.write_text(json.dumps(p),encoding='utf-8')
            manifest=read(NATIVE/'manifest_template.json');manifest['source_version_binding_sha256']=sha(f)
            ns={'STAGE':stage,'MANIFEST':manifest,'CANDIDATE_COMMIT':adapter.COMMIT,'sha':sha,'json':json}
            exec(compile(ast.Module(body=[function],type_ignores=[]),'<version-check-only>','exec'),ns);ns['verify_source_version']()
            p['code_commit']='0'*40;f.write_text(json.dumps(p),encoding='utf-8');manifest['source_version_binding_sha256']=sha(f)
            with self.assertRaises(AssertionError):ns['verify_source_version']()
    def test_resource_function_AST_unchanged(self):
        a=ast.parse((NATIVE/'worker.py').read_text(encoding='utf-8'));b=ast.parse((OLD/'worker.py').read_text(encoding='utf-8'));self.assertEqual(dump(fun(a,'resources')),dump(fun(b,'resources')))
    def test_runtime_guards_preserved_plus_version_prefix(self):
        a=ast.parse((NATIVE/'native_runtime.py').read_text(encoding='utf-8'));b=ast.parse((OLD/'native_runtime.py').read_text(encoding='utf-8'))
        for name in ('sha','observe','acquire','release','fingerprint','save','require_promoted_version'):self.assertEqual(dump(fun(a,name)),dump(fun(b,name)),name)
        v=fun(a,'verify');self.assertEqual(ast.unparse(v.body[0]),'verify_source_version()');v.body=v.body[1:];self.assertEqual(dump(v),dump(fun(b,'verify')))
    def test_static_release_has_no_token_or_lease(self):
        r=read(HERE/'release_template.json');self.assertEqual(r['code_commit'],adapter.COMMIT)
        self.assertNotIn('token',r);self.assertNotIn('deadline_at',r);self.assertNotIn('physical_gpu',r)
        for n,h in r['source_hashes'].items():self.assertEqual(sha(HERE/n),h)
    def test_transport_command_pinned_without_execution(self):
        server={'user':'songcl','host':'192.168.1.115','conda_source':'/safe/conda.sh','conda_env':'original_env'}
        for conda in (False,True):
            with patch.object(adapter.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='{}',stderr='')) as called:
                adapter.SSHTransport(HERE).call('probe',{'physical_gpu':0},server,timeout=30,conda=conda)
                argv=called.call_args.args[0];wire=called.call_args.kwargs['input']
                self.assertEqual(argv[0],'ssh');self.assertEqual(argv[-2],'songcl@192.168.1.115');self.assertIn('StrictHostKeyChecking=yes',argv);self.assertIn('BatchMode=yes',argv)
                self.assertIn("socket.gethostname()=='dl04-MS-7E06'",wire)
                self.assertIn('python -B -' if conda else '/usr/bin/python3 -B -',argv[-1])
    def test_module_import_does_not_import_torch(self):
        import sys
        self.assertNotIn('torch',sys.modules)

if __name__=='__main__':unittest.main()
