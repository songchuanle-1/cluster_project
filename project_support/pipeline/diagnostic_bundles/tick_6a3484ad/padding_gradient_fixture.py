"""Exact-source CPU derivative fixtures; no native backward or CUDA."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace, MethodType
import torch

p = argparse.ArgumentParser()
p.add_argument('--manifests', nargs=2, required=True)
a = p.parse_args()
assert not torch.cuda.is_initialized()
torch.set_num_threads(1)
rows = []
for manifest_path in a.manifests:
    manifest = json.loads(Path(manifest_path).read_text())
    source = Path(manifest['root'])/'framework/model/Quard_model'/manifest['name']/'hier_postprocess.py'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == manifest['assets']['source_hashes']['hier_postprocess.py']
    tree = ast.parse(source.read_text())
    method = next(f for c in tree.body if isinstance(c, ast.ClassDef) and c.name == 'C2F_ClusterAttn_CTF_HCG'
                  for f in c.body if isinstance(f, ast.FunctionDef) and f.name == '_cluster_to_points')
    scope = {'torch': torch}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), scope)
    uses_fine = any(x.arg == 'fine_message' for x in method.args.args)
    torch.manual_seed(1999)
    module = SimpleNamespace(num_scales=3, level_gate=torch.nn.Linear(512, 3).double(),
        point_out_proj=torch.nn.Linear(256, 256).double(), dropout=torch.nn.Identity())
    gather = MethodType(scope['_cluster_to_points'], module)
    tokens = [torch.randn(1, n, 256, dtype=torch.float64) for n in (2, 1, 1)]
    ids = [[torch.tensor([0, 0, 1, 1])], [torch.tensor([0, 0])], [torch.tensor([0])]]
    mask = torch.tensor([[False, False, False, False, True, True]])
    features = torch.randn(1, 6, 256, dtype=torch.float64)
    fine = torch.randn_like(features)
    cases = []
    for null in (False, True):
        x = features.clone().requires_grad_(True)
        t = [torch.zeros_like(v) for v in tokens] if null else tokens
        kwargs = {'fine_message': torch.zeros_like(fine) if null else fine} if uses_fine else {}
        value = gather(x, t, ids, mask, **kwargs)
        loss = value[~mask].square().mean()
        gradient, = torch.autograd.grad(loss, x)
        masked = float(gradient[mask].abs().max())
        valid = float(gradient[~mask].abs().max())
        if null: assert masked <= 1e-12 and valid <= 1e-12
        else: assert masked > 1e-12 and valid > 1e-12
        cases.append({'zero_scale_null': null, 'masked_gradient_max': masked, 'valid_gradient_max': valid})
    rows.append({'model': manifest['name'], 'source_sha256': digest, 'cases': cases})
result = {'passed': True, 'cases': rows, 'synthetic_cpu_backward_calls': 4,
          'native_backwards': 0, 'cuda_initialized': torch.cuda.is_initialized(),
          'scope': 'synthetic exactsource derivatives,not trained/native backward or efficacy'}
with (Path(__file__).parent/'padding_gradient_result.json').open('x') as stream:
    json.dump(result, stream, indent=2, allow_nan=False)
print(json.dumps(result))
