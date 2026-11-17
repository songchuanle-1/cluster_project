"""Offline AST/immutable-byte/subprocess refusal tests. No prepared model import."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

HERE=Path(__file__).resolve().parent
PROJECT=Path('D:/project/cluster_project')
OLD=PROJECT/'pipeline/diagnostic_bundles/tick_8fafa3d4/psbr_native_prepare'
SOURCE=PROJECT/'pipeline/diagnostic_bundles/tick_e2742b06/psnc_prepare'

def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def parse(f):return ast.parse(f.read_text(encoding='utf-8'))
def function(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def nested(tree,outer,name):return next(n for n in function(tree,outer).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
def dump(n):return ast.dump(n,include_attributes=False)

class StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oldw=parse(OLD/'worker.py');cls.w=parse(HERE/'worker.py');cls.oldr=parse(OLD/'native_runtime.py');cls.r=parse(HERE/'native_runtime.py')
        cls.t=json.loads((HERE/'manifest_template.json').read_text(encoding='utf-8'))
    def test_compile_all_drafts_and_frozen_copies(self):
        files=[HERE/'worker.py',HERE/'native_runtime.py',HERE/'adapter_draft.py',*sorted((HERE/'candidate_model').glob('*.py'))]
        self.assertEqual(len(files),11)
        for f in files:compile(f.read_text(encoding='utf-8'),str(f),'exec')
    def test_source_prepare_anchor_and_all_hashes(self):
        self.assertEqual(sha(SOURCE/'preparation.json'),'302432f1e2ba136576c4eb8a814a7ab3fb9596272304924b2a9db356074b49de')
        p=json.loads((SOURCE/'preparation.json').read_text(encoding='utf-8'))
        for name,value in p['prepared_file_hashes'].items():self.assertEqual(sha(SOURCE/name),value,name)
        for name,value in p['source_files'].items():
            f=HERE/'candidate.yaml' if name.endswith('.yaml') else HERE/'candidate_model'/Path(name).name
            self.assertEqual(sha(f),value,name)
    def test_manifest_draft_unbound_and_null_commit(self):
        self.assertIsNone(self.t['code_commit']);self.assertTrue(self.t['draft_execution_disabled'])
        for k in ('runtime_code_commit','current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256'):self.assertIsNone(self.t[k],k)
        self.assertEqual(self.t['base_reference_commit'],'74fcd21df0af9a971792038ffe251af1ffea2604')
    def test_manifest_assets_and_all_diagnostic_hashes(self):
        self.assertEqual(len(self.t['candidate_source_hashes']),8)
        for n,h in self.t['candidate_source_hashes'].items():self.assertEqual(sha(HERE/'candidate_model'/n),h)
        for n,h in self.t['diagnostic_files'].items():self.assertEqual(sha(HERE/n),h)
        self.assertEqual(self.t['assets'],json.loads((OLD/'manifest_template.json').read_text(encoding='utf-8'))['assets'])
    def test_original_resource_function_exact_AST(self):self.assertEqual(dump(function(self.w,'resources')),dump(function(self.oldw,'resources')))
    def test_original_json_safety_exact_AST(self):self.assertEqual(dump(function(self.w,'json_safe')),dump(function(self.oldw,'json_safe')))
    def test_original_runtime_seven_guard_functions_exact_AST(self):
        for name in ('sha','verify','observe','acquire','release','fingerprint','save'):self.assertEqual(dump(function(self.r,name)),dump(function(self.oldr,name)),name)
    def test_original_native_two_batches_and_optimizer_hooks(self):
        for name in ('TwoNativeBatches','before_step','after_step'):self.assertEqual(dump(nested(self.w,'smoke',name)),dump(nested(self.oldw,'smoke',name)),name)
        calls=[n for n in ast.walk(function(self.w,'smoke')) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and ast.unparse(n.func)=='train.train']
        self.assertEqual(len(calls),1);self.assertEqual(ast.unparse(calls[0]),'train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)')
    def test_original_setup_only_common_readout_and_labels_changed(self):
        a=copy.deepcopy(function(self.w,'setup'));b=copy.deepcopy(function(self.oldw,'setup'))
        def strip(n):
            n.body=[x for x in n.body if not (isinstance(x,ast.If) and ast.unparse(x.test)=="mode == 'smoke'")]
            for x in ast.walk(n):
                if isinstance(x,ast.Constant) and isinstance(x.value,str):x.value=x.value.replace('PSBR','PSNC')
            return n
        self.assertEqual(dump(strip(a)),dump(strip(b)))
    def test_no_auxiliary_backward_or_autograd_grad(self):
        for n in ast.walk(self.w):
            if isinstance(n,ast.Call):self.assertNotIn(ast.unparse(n.func),('torch.autograd.grad','loss.backward','model.backward'))
    def test_no_stale_RNN_claims(self):
        s=(HERE/'worker.py').read_text(encoding='utf-8')
        for text in ('PSBR','_psbr','middle_recurrence','262656','Wx','Wh','Wo'):self.assertNotIn(text,s)
    def test_f0_native_sentinel_gradient_is_record_only(self):
        s=(HERE/'worker.py').read_text(encoding='utf-8');self.assertIn("gradient[:, -1:, :]",s)
        f=nested(self.w,'smoke','ffn_hook');self.assertNotIn('.backward(',ast.unparse(f));self.assertNotIn('autograd.grad',ast.unparse(f))
        self.assertIn("Zero sentinel-row gradients can be a real cancellation",s)
    def test_runtime_barrier_precedes_manifest_fcntl_and_any_ops(self):
        source=(HERE/'native_runtime.py').read_text(encoding='utf-8')
        barrier=source.index('require_promoted_version()\n');self.assertLess(barrier,source.index('import fcntl'));self.assertLess(barrier,source.index("MANIFEST = json.loads"))
        for disabled,commit in ((True,None),(True,'a'*40),(False,None),(False,'74f'),(False,'')):
            ns={'DRAFT_EXECUTION_DISABLED':disabled,'CANDIDATE_COMMIT':commit,'re':re}
            exec(compile(ast.Module(body=[function(self.r,'require_promoted_version')],type_ignores=[]),'<guard-only>','exec'),ns)
            with self.assertRaises(RuntimeError):ns['require_promoted_version']()
    def test_actual_worker_entry_refuses_before_optional_imports(self):
        code="""import runpy,sys,json
sys.path.insert(0,sys.argv[1])
try:runpy.run_path(sys.argv[1]+'/worker.py',run_name='__main__')
except RuntimeError as e:
 print(json.dumps({'error':str(e),'torch_imported':'torch' in sys.modules,'fcntl_imported':'fcntl' in sys.modules,'numpy_imported':'numpy' in sys.modules}));sys.exit(3)
"""
        before={x.name for x in HERE.iterdir()};r=subprocess.run([sys.executable,'-B','-X','utf8','-c',code,str(HERE)],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,3,r.stderr);x=json.loads(r.stdout);self.assertIn('draft is unversioned',x['error']);self.assertFalse(x['torch_imported']);self.assertFalse(x['fcntl_imported']);self.assertFalse(x['numpy_imported']);self.assertEqual(before,{x.name for x in HERE.iterdir()})
    def test_all_adapter_operations_refuse_without_transport_or_files(self):
        before={x.name for x in HERE.iterdir()}
        for op in ('probe','prepare','stage','run','pair','status','reconcile'):
            r=subprocess.run([sys.executable,'-B','-X','utf8',str(HERE/'adapter_draft.py'),op],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,2,r.stderr);x=json.loads(r.stdout);self.assertFalse(x['transport_attempted']);self.assertFalse(x['transport_implemented']);self.assertIsNone(x['code_commit'])
        self.assertEqual(before,{x.name for x in HERE.iterdir()})
    def test_describe_is_only_local_draft_metadata(self):
        r=subprocess.run([sys.executable,'-B',str(HERE/'adapter_draft.py'),'describe'],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr);x=json.loads(r.stdout);self.assertEqual(x['status'],'DRAFT_EXECUTION_DISABLED');self.assertFalse(x['transport_implemented'])
    def test_no_execution_or_receipt_artifacts(self):
        for name in ('native_manifest.json','execution_lease.json','execution_binding.json','adapter_release.json','native_smoke.json','admission.json'):self.assertFalse((HERE/name).exists(),name)

if __name__=='__main__':unittest.main()
