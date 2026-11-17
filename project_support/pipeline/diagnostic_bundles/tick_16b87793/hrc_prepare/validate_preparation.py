"""Static HRC configuration, isolation and graph contract; never imports the model."""
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import yaml

PROJECT = Path('D:/project/cluster_project')
REPO = PROJECT / 'Cluster'
OUT = Path(__file__).resolve().parent
TOKEN = '16b87793a9414372a17cfa776ccdd8c9'
assert os.environ.get('CODEX_THREAD_ID') == '01a159c5-29ab-7a22-ba7f-e79174757253'
owner = json.loads((PROJECT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
assert owner['token'] == TOKEN
assert dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(owner['deadline_at'])

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tree(path):
    text = path.read_text(encoding='utf-8')
    node = ast.parse(text, filename=str(path), feature_version=(3, 10))
    compile(node, str(path), 'exec')
    return node

def find_class(node, name):
    return next(n for n in node.body if isinstance(n, ast.ClassDef) and n.name == name)

def method(node, name):
    return next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == name)

def equivalent(a, b):
    return ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)

manifest = json.loads((OUT/'preparation.json').read_text(encoding='utf-8'))
assert manifest['token'] == TOKEN and manifest['goal_sha256'] == digest(PROJECT/'pipeline/goal.json')
assert manifest['context_sha256'] == owner['context_sha256']
assert manifest['pending_sha256'] == owner['pending_sha256']
paths = list(manifest['source_hashes'])
assert len(paths) == 9 and sum(p.endswith('.py') for p in paths) == 8
for name, expected in manifest['source_hashes'].items():
    assert digest(REPO/name) == expected, name
for name, expected in manifest['original_control_hashes'].items():
    assert digest(REPO/name) == expected, name
new_dir = REPO/'framework/model/Quard_model'/manifest['new_package']
old_dir = REPO/'framework/model/Quard_model'/manifest['control_package']
trees = {p.name:tree(p) for p in new_dir.glob('*.py')}
assert len(trees) == 8
for name in ['__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py']:
    assert (new_dir/name).read_bytes() == (old_dir/name).read_bytes(), name
new_hier, old_hier = trees['hier_postprocess.py'], tree(old_dir/'hier_postprocess.py')
unchanged = ['PointCloudPartitioner','SharedClusterBank','C2F_ClusterAttn_CTF_HCG','C2F_ClusterAttn_CTF_HCG_CSORT']
for name in unchanged:
    assert equivalent(find_class(new_hier,name),find_class(old_hier,name)), name
new_ctf, old_ctf = find_class(new_hier,'C2F_ClusterAttn_CTF'), find_class(old_hier,'C2F_ClusterAttn_CTF')
assert equivalent(method(new_ctf,'__init__'),method(old_ctf,'__init__'))
forward = method(new_ctf,'forward')
calls = [ast.unparse(n.func) for n in ast.walk(forward) if isinstance(n, ast.Call)]
assert calls.count('refined_parent_mean') == 1
assert calls.count('self.cluster_ffn[lvl]') == 1
assert calls.count('self._cluster_to_points') == 1
assert calls.count('self.message_norm') == 1
assert not any(isinstance(n,ast.Call) and ast.unparse(n.func).endswith('detach') for n in ast.walk(forward))
pool = method(trees['refined_composition.py'],'refined_parent_mean')
source = ast.unparse(pool)
assert 'child_feats[batch_index, :child_count]' in source
assert 'scatter_mean(child, parent_ids, dim=0, dim_size=parent_count)' in source
assert 'parent_count = parent_template.shape[1]' in source
assert not any(isinstance(n,ast.Call) and ast.unparse(n.func).endswith('detach') for n in ast.walk(pool))
assert not any(isinstance(n,ast.ClassDef) for n in ast.walk(trees['refined_composition.py']))
configs = [p for p in paths if p.endswith('.yaml')]
cfg = REPO/configs[0]
control_cfg = REPO/'configs/Quard/ctf_hcg_csort'/f"{manifest['control_package']}.yaml"
assert cfg.stem == new_dir.name
assert cfg.read_bytes() == control_cfg.read_bytes()
assert yaml.safe_load(cfg.read_text(encoding='utf-8')) == yaml.safe_load(control_cfg.read_text(encoding='utf-8'))
loader = (REPO/'framework/__init__.py').read_text(encoding='utf-8')
assert "module_path = f'framework.model.Quard_model.{basename}'" in loader
protected = json.loads((OUT.parent/'protected_worktree_before.json').read_text(encoding='utf-8'))
for entry in protected['protected_existing_worktree']:
    assert digest(REPO/entry['path']) == entry['sha256'], entry['path']
assert not subprocess.check_output(['git','-C',str(REPO),'diff','--cached','--name-only'])
assert 'torch' not in sys.modules
result = {'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),'candidate_id':manifest['candidate_id'],
    'experiment_id':manifest['experiment_id'],'tick_token':TOKEN,'command':['python','-B',str(Path(__file__).resolve())],
    'result':'passed_static_only','source_hashes':manifest['source_hashes'],
    'checks':{'eight_python_ast_compile':True,'nine_prepared_hashes':True,'six_original_copies_equal':True,
      'raw_partition_bank_HCG_CSORT_ast_equal':True,'three_original_FFN_constructor_unchanged':True,
      'refined_child_prefix_to_fixed_mean_to_next_FFN_present':True,'single_HCG_readback':True,
      'native_YAML_equal_and_basename_import_mapping':True,'all_28_protected_files_unchanged':True,
      'index_empty':True,'local_torch_not_imported':True},
    'native_data_backward':'NOT_RUN','measured_resources':'NOT_RUN','efficacy':'UNKNOWN',
    'limitation':'AST/config isolation checks certify the prepared source contract only; native tensor behavior, gradients, runtime and training efficacy remain unmeasured.'}
path = OUT/'static_validation.json'
with path.open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2)
print(json.dumps({'path':str(path),'sha256':digest(path),'result':result['result'],'source_files':len(paths),'protected_files':len(protected['protected_existing_worktree'])}))
