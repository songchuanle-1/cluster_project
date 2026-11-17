"""Static preparation verification only. Never imports prepared model or torch."""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
import test_math_reference

ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
BASE=ROOT/'Cluster/framework/model/Quard_model'/NAME
PREP=HERE/'staged_repository/framework/model/Quard_model'/(NAME+'_psnc')

def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def node(tree,cls,method=None):
    x=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==cls)
    return next(v for v in x.body if isinstance(v,ast.FunctionDef) and v.name==method) if method else x

def dump(x):return ast.dump(x,include_attributes=False)

def main():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8-sig'))
    assert owner['token']=='e2742b06404240e398267db352a2b91a' and owner['context_sha256']=='e7ff3c372b926c73d0d14a457a19bec07c75dc5cd311cad755d52c8fe79554a1' and owner['pending_sha256']=='f2b0fa3a75f5626e1357fcefe68e88bea02110f132e93bcbb6051012701ddec6'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    checks={};sources=sorted(PREP.glob('*.py'));checks['eight_independent_sources']=len(sources)==8
    for f in sources:compile(f.read_text(encoding='utf-8'),str(f),'exec')
    checks['all_eight_AST_compile']=True
    originals=sorted(BASE.glob('*.py'));checks['five_other_sources_byte_identical']=all(sha(PREP/f.name)==sha(f) for f in originals if f.name not in ('dec.py','hier_postprocess.py'))
    a=ast.parse((BASE/'hier_postprocess.py').read_text(encoding='utf-8'));b=ast.parse((PREP/'hier_postprocess.py').read_text(encoding='utf-8'))
    for cls in ('PointCloudPartitioner','SharedClusterBank','C2F_ClusterAttn_CTF','C2F_ClusterAttn_CTF_HCG_CSORT'):
        checks[cls+'_constructor_exact_AST']=dump(node(a,cls,'__init__'))==dump(node(b,cls,'__init__'))
    for cls in ('C2F_ClusterAttn_CTF_HCG','C2F_ClusterAttn_CTF_HCG_CSORT'):
        checks[cls+'_complete_class_exact_AST']=dump(node(a,cls))==dump(node(b,cls))
    checks['raw_cluster_build_exact_AST']=dump(node(a,'SharedClusterBank','build_cluster_feats'))==dump(node(b,'SharedClusterBank','build_cluster_feats'))
    def constructors(tree):
        return [(x.name, dump(v)) for x in ast.walk(tree) if isinstance(x,ast.ClassDef) for v in x.body if isinstance(v,ast.FunctionDef) and v.name=='__init__']
    checks['all_hierarchical_constructors_exact_AST']=constructors(a)==constructors(b)
    checks['all_decoder_constructors_exact_AST']=constructors(ast.parse((BASE/'dec.py').read_text(encoding='utf-8')))==constructors(ast.parse((PREP/'dec.py').read_text(encoding='utf-8')))
    checks['original_FPS_and_partition_methods_exact_AST']=all(dump(node(a,'PointCloudPartitioner',m))==dump(node(b,'PointCloudPartitioner',m)) for m in ('cluster_layer','partition_points'))
    ha=ast.parse((PREP/'parent_spectral.py').read_text(encoding='utf-8'))
    checks['helper_no_class_parameter_buffer_or_rng_registration']=not any(isinstance(x,ast.ClassDef) for x in ast.walk(ha)) and not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ('register_buffer','register_parameter','Parameter','manual_seed','rand','randn','seed') for x in ast.walk(ha))
    f=next(x for x in ha.body if isinstance(x,ast.FunctionDef) and x.name=='parent_spectral_delta')
    ffns=[x for x in ast.walk(f) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='ffn']
    checks['two_FFN_call_sites_mutually_exclusive_by_early_return']=len(ffns)==2 and any(isinstance(x,ast.If) and ast.unparse(x.test)=='not has_mixed_group' and len(x.body)==1 and isinstance(x.body[0],ast.Return) and 'ffn(norm(cf))' in ast.unparse(x.body[0]) for x in f.body)
    checks['f0_has_real_graph_no_detach']=not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='detach' and ast.unparse(x.func.value) not in ('ids2','positions') for x in ast.walk(ha))
    checks['no_DCT_or_geometry_registration_in_state_dict']=all(s not in (PREP/'parent_spectral.py').read_text(encoding='utf-8') for s in ('register_buffer(', 'register_parameter(', 'nn.Linear(', 'nn.Parameter('))
    cfg=HERE/'staged_repository/configs/Quard/ctf_hcg_csort_psnc'/(NAME+'_psnc.yaml');orig=ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml')
    checks['native_YAML_byte_identical']=cfg.read_bytes()==orig.read_bytes()
    import yaml
    config=yaml.safe_load(cfg.read_text(encoding='utf-8'));checks['seed1999_schedule50_70_dropout0_original']=config['train']['seed']==1999 and config['train']['epochs']==50 and config['lr_scheduler']['max_iters']==70 and config['model']['dec']['dropout']==0.0
    before=json.loads((HERE/'source_before.json').read_text(encoding='utf-8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT/'Cluster',text=True).strip();status=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=ROOT/'Cluster',text=True)
    checks['Cluster_HEAD_and_status_exact_before_after']=head==before['head'] and status==before['status_porcelain_v1']
    checks['original_seven_source_bytes_unchanged']=all(sha(BASE/n)==h for n,h in before['source_hashes'].items())
    checks['no_torch_import_or_model_execution']='torch' not in sys.modules
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_math_reference));checks['stdlib_reference_tests_passed']=tests.wasSuccessful()
    report={'status':'PREPARED_STATIC_ONLY_UNEXECUTED','recorded_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'all_static_checks_passed':all(checks.values()),'stdlib_reference_tests':{'count':tests.testsRun,'failures':len(tests.failures),'errors':len(tests.errors),'output':stream.getvalue(),'scope':'Python float64-like math real-number reference only; not torch/FP32/autograd/native evidence'},'source_hashes':{f.relative_to(HERE/'staged_repository').as_posix():sha(f) for f in sources+[cfg]},'baseline_HEAD_unchanged':head,'original_dirty_status_lines':len(status.splitlines()),'native':'NOT_RUN','resources':'NOT_RUN','registered_parameter_inventory':'NOT_RUN; constructors unchanged by AST','new_declared_parameters_buffers':0,'actual_GEMM_RNG_batch_pairing':'NOT_RUN','future_lease_or_execution_binding_created':False}
    (HERE/'static_validation.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'all_static_checks_passed':all(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],'math_tests':tests.testsRun,'status':report['status']}))
    return 0 if all(checks.values()) else 2

if __name__=='__main__':raise SystemExit(main())
