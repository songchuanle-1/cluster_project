"""One checkpoint-source control, reusing the frozen constructed CPU fixture."""
import ast
from datetime import datetime,timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick

ROOT=Path('D:/project/cluster_project')
TOKEN='1e29997a8967493c85410db3d0ee54b6'
BUNDLE=Path(__file__).resolve().parent
OLD=ROOT/'pipeline/diagnostic_bundles/hier_feature_73d9f276d8ba41fe96f1176fb84e9ef4'
GOAL='6a11a897c8378c48934590d7603b5cbd18cac2d43da40690e0a7c72080f5478c'

def guard():
    owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    assert tick.digest(ROOT/'pipeline/goal.json')==GOAL
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>180

def build():
    candidate=tick.query_candidates('cluster_project','m95-hierarchical-mask-feature-path-audit')
    old_source=OLD/'audit_feature_path.py'
    expected=next(item['sha256'] for item in candidate['evidence'] if item['path']==old_source.relative_to(ROOT).as_posix())
    assert tick.digest(old_source)==expected
    spec=importlib.util.spec_from_file_location('frozen_feature_fixture',old_source)
    prior=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    original=ast.parse(prior.REMOTE)
    start=next(i for i,n in enumerate(original.body) if isinstance(n,ast.Import) and any(a.name=='torch' for a in n.names))
    body=original.body[start:]
    prefix=ast.parse('''
import ast,copy,datetime,hashlib,importlib.util,json,os,pathlib,subprocess,sys,types
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1')
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
path=root/'framework/model/Quard_model'/MODEL/'hier_postprocess.py'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
sys.path.insert(0,str(root))
resource={'fresh_this_tick':False,'scope':'No resource recheck; keep prior observation timestamp16:24:50+08 and retry17:46:54+08. No allocation permission.'}
''').body
    intervention=ast.parse('''
checkpoint=root.parent/'Cluster_checkpoints'/MODEL/'20260815_101011/best.pth'
checkpoint_expected='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
h=hashlib.sha256()
with checkpoint.open('rb') as handle:
    for block in iter(lambda:handle.read(8*1024*1024),b''):h.update(block)
assert h.hexdigest()==checkpoint_expected
rng_before=torch.get_rng_state().clone()
saved=torch.load(checkpoint,map_location='cpu',weights_only=False,mmap=True)
prefix_key='dec.cluster_att.'
weights={key[len(prefix_key):]:value for key,value in saved['model'].items() if key.startswith(prefix_key)}
assert weights
incompatible=model.load_state_dict(weights,strict=True)
assert not incompatible.missing_keys and not incompatible.unexpected_keys
module_state_count=len(weights)
del saved,weights
assert torch.equal(rng_before,torch.get_rng_state()),'Weight source must not change fixture RNG'
''').body
    positions=[i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='model' for t in n.targets)]
    assert len(positions)==1
    body[positions[0]+1:positions[0]+1]=intervention
    sample_edits=overall_edits=0
    for node in ast.walk(ast.Module(body=body,type_ignores=[])):
        if not isinstance(node,ast.Dict):continue
        for i,key in enumerate(node.keys):
            if isinstance(key,ast.Constant) and key.value=='sample_scope':
                node.values[i]=ast.Constant('One constructed CPU fixture, unchanged seed1999/constructor/input RNG, exact frozen M95 cluster-module weights. NOT native TRAIN features or network capture.')
                node.keys.extend([ast.Constant('checkpoint_sha256'),ast.Constant('module_state_count'),ast.Constant('fixture_rng_unchanged')])
                node.values.extend([ast.Name(id='checkpoint_expected',ctx=ast.Load()),ast.Name(id='module_state_count',ctx=ast.Load()),ast.Constant(True)])
                sample_edits+=1
            elif isinstance(key,ast.Constant) and key.value=='overall_control_status':
                node.values[i]=ast.parse("'PASS_CURRENT_FIXTURE_ONLY' if all(checks.values()) else 'FAIL_CURRENT_STRICT_CROSS_SHAPE_CONTROL'",mode='eval').body
                overall_edits+=1
    assert sample_edits==overall_edits==1
    program=ast.unparse(ast.fix_missing_locations(ast.Module(body=prefix+body,type_ignores=[])))+'\n'
    assert 'nvidia-smi' not in program and 'fcntl.flock' not in program
    ast.parse(program)
    return program

def main():
    guard()
    program=build()
    path=BUNDLE/'remote_checkpoint_fixture.py'
    assert not path.exists()
    path.write_text(program,encoding='utf-8')
    run=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12','server-4','/home/songcl/.conda/envs/project_cluster/bin/python','-B','-'],input=program,text=True,encoding='utf-8',capture_output=True,timeout=120)
    guard()
    tick.save(BUNDLE/'attempt.json',{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),'script_sha256':tick.digest(path),'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
    if run.returncode:
        print(run.stderr[-5000:])
        raise SystemExit(run.returncode)
    result=json.loads(run.stdout)
    assert not result['cuda_initialized'] and result['gpu_tests']==result['optimizer_steps']==0
    assert result['checkpoint_sha256']=='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
    tick.save(BUNDLE/'result.json',{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),**result})
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
