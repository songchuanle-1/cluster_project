"""Read-only local preparation validation: no model import, SSH or GPU calls."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
CODE = ROOT / 'Cluster'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
m = json.loads((OUT/'manifest_template.json').read_text(encoding='utf-8'))
checks = {}
for path in sorted(OUT.rglob('*.py')):
    source = path.read_bytes()
    ast.parse(source, filename=str(path)); compile(source, str(path), 'exec')
checks['all_prepared_python_ast_and_compile'] = True
for name, expected in m['diagnostic_files'].items():
    path = (OUT/name).resolve()
    assert path.is_relative_to(OUT.resolve()) and sha(path)==expected, name
checks['all_staged_diagnostic_hashes_match'] = True
assert len(m['candidate_source_hashes'])==8
for name, expected in m['candidate_source_hashes'].items():
    relative = 'framework/model/Quard_model/'+m['candidate_name']+'/'+name
    content = subprocess.check_output(['git','-C',str(CODE),'show',m['code_commit']+':'+relative])
    assert hashlib.sha256(content).hexdigest()==expected==sha(OUT/'candidate_model'/name), name
relative=m['config']
content=subprocess.check_output(['git','-C',str(CODE),'show',m['code_commit']+':'+relative])
assert hashlib.sha256(content).hexdigest()==m['candidate_config_sha256']==sha(OUT/'candidate.yaml')
checks['nine_assets_equal_committed_hrc'] = True
for name, expected in m['assets']['source_hashes'].items():
    assert sha(CODE/'framework/model/Quard_model'/m['name']/name)==expected
assert sha(CODE/'tools/train.py')==m['assets']['native_train_source_sha256']
assert sha(CODE/'framework/dataset/scannetv2.py')==m['assets']['dataset_source_sha256']
control_yaml=CODE/'configs/Quard/ctf_hcg_csort'/(m['name']+'.yaml')
assert control_yaml.read_bytes()==(OUT/'candidate.yaml').read_bytes()
assert yaml.safe_load(control_yaml.read_text(encoding='utf-8'))==yaml.safe_load((OUT/'candidate.yaml').read_text(encoding='utf-8'))
checks['local_native_control_sources_and_yaml_unchanged'] = True
oldpath=ROOT/'pipeline/diagnostic_bundles/tick_008137b4/hap_prepare/worker_v2.py'
assert sha(oldpath)=='ffb2e09a53f3e860b398b435674ca0800b9641f5e48391d1af0d3098b8698a73'
old=ast.parse(oldpath.read_bytes()); new=ast.parse((OUT/'worker.py').read_bytes())
function=lambda tree,name:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
assert ast.dump(function(old,'resources'))==ast.dump(function(new,'resources'))
checks['resources_function_ast_identical_to_reviewed_worker'] = True
worker=(OUT/'worker.py').read_text(encoding='utf-8')
assert '_hap' not in worker and 'affine_prolongation' not in worker and 'pinv' not in worker
assert "network.__module__ == qualified + '.network'" in worker
assert "cfg.model.dec.cluster_att_num_layers == 1" in worker
assert "train.train(1, model, TwoNativeBatches(loader), optimizer, scheduler, cfg, logger, writer)" in worker
assert worker.count('gorilla.load_checkpoint(model, str(pretrain), strict=False, map_location=\'cpu\')')==1
assert 'torch.load(' not in worker
assert "'maps_unchanged_after_full_forward'" in worker
checks['native_setup_train_resolver_and_observer_static_contracts'] = True
receive=next(n for n in ast.walk(new) if isinstance(n,ast.FunctionDef) and n.name=='receive')
assert isinstance(receive.body[0],ast.If) and 'probe_active' in ast.unparse(receive.body[0].test)
assert isinstance(receive.body[0].body[0],ast.Return)
probe=next(n for n in ast.walk(new) if isinstance(n,ast.FunctionDef) and n.name=='dependency_probe')
probe_text=ast.unparse(probe)
assert 'torch.autograd.grad' in probe_text and 'retain_graph=True' in probe_text and 'allow_unused=True' in probe_text
assert 'ids2[ids1[ids0]]' in probe_text and '.backward(' not in probe_text and '.step(' not in probe_text
assert all(k in probe_text for k in ['parameter_grad_state_unchanged','optimizer_state_unchanged','scheduler_state_unchanged','cpu_rng_unchanged','cuda_rng_unchanged'])
checks['probe_gradient_rng_optimizer_isolation_static_contracts'] = True
runtime=(OUT/'native_runtime.py').read_text(encoding='utf-8')
rt=ast.parse(runtime)
assert 'setup' not in {n.name for n in rt.body if isinstance(n,ast.FunctionDef)}
assert 'torch.load' not in runtime and 'import torch' not in runtime
assert "for kind in ('training', 'diagnostic', 'exclusive')" in runtime
assert "300 < remaining <= 3600" in runtime
assert "CUDA_VISIBLE_DEVICES=GPU_UUIDS[PHYSICAL_GPU]" in runtime
assert 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in runtime and 'GPU-7f82edb9-f620-8045-caea-a75232265cd1' in runtime
for key in ['current_token','tick_generated_at','deadline_at','stage','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']:
    assert m[key] is None, key
assert not (OUT/'execution_lease.json').exists() and not (OUT/'native_manifest.json').exists()
checks['fresh_binding_missing_and_runtime_fail_closed_static_contracts'] = True
assert 'torch' not in sys.modules
checks['no_torch_imported_during_static_validation'] = True
print(json.dumps({'status':'STATIC_PASS_NOT_EXECUTED','checks':checks,
    'native_smoke':'NOT_RUN','resources':'NOT_RUN','pure_train_memory':'UNKNOWN_SUPPORT_ONLY',
    'execution_lease_created':False,'execution_manifest_created':False},sort_keys=True))
