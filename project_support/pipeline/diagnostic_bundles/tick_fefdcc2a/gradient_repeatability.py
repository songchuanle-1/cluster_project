"""Discriminate operator changes from original gather-gradient variability."""
from pathlib import Path
import control as c

c.guard(700)
base = c.OUT
protocol = c.save('gradient_repeatability_protocol.json', {
    'preregistered_at': c.now(), 'candidate_id': c.CID,
    'question': 'Do repeated original and revised operator backwards vary on identical native feature pointers, or is the revised derivative systematically different?',
    'sample': 'First expression of each of the two already-frozen scenes: indices0 and4; no selection by error magnitude.',
    'test': 'Three backward evaluations per operator/input with same x storage and deterministic fixed linear probe. No optimizer, precision/operator/dtype or tolerance change.',
    'readout': 'Exact output repeat and each operator self-gradient variation, plus original/revised gradient max and L2 differences.',
    'decision': 'An empirical self-repeat envelope is diagnostic evidence only. It never rewrites the original1e-6 gate or marks the failed revision passed.'})
original_sha = c.tick.load(base / 'implementation_revision1.json')['original_source']['sha256']
stage = '/data/songcl/Project/Cluster_project/pipeline/pce_fefdcc2a/implementation_r1'
code = '''
import importlib.util,json,sys
from pathlib import Path
sys.path.insert(0,STAGE)
from native_runtime import acquire,release,save,sha,observe
r={'execution_completed':False,'optimizer_steps':0,'scientific_admission':False,'records':[],'original_tolerance':1e-6,'failed_gates_waived':False}
try:
 r['before']=acquire(str(Path(STAGE)/'execution_lease.json'))
 import torch
 torch.set_num_threads(1)
 torch.cuda.set_per_process_memory_fraction(.75,0)
 fixture_path=Path('/data/songcl/Project/Cluster_project/pipeline/contact_658721c0/native_contact_fixture.pt')
 assert sha(fixture_path)=='93a4c4ef26668ffdf2c37141b1667906456142ee853b8459e110d91879d59a7b'
 fixture=torch.load(fixture_path,map_location='cpu',weights_only=False)
 paths={'original':Path('/data/songcl/Project/Cluster_project/pipeline/pce_fefdcc2a/candidate_model/contact_exchange.py'),'revised':Path(STAGE)/'candidate_model/contact_exchange.py'}
 assert sha(paths['original'])==ORIGINAL_SHA
 modules={}
 for label,path in paths.items():
  spec=importlib.util.spec_from_file_location('gradient_'+label,path)
  module=importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  modules[label]=module
 for b in (0,4):
  ids=fixture['fine_ids'][b]
  n=len(ids)
  x=fixture['features'][b,:n].cuda().detach().clone().requires_grad_()
  xyz=fixture['positions'][b,:n].numpy()
  fallback=fixture['refined_banks'][0][b,ids.long()].cuda()
  edges=fixture['physical_edges'][b//4]
  probe=torch.linspace(-1,1,x.numel(),device=x.device).reshape_as(x)
  gradients={}
  outputs={}
  for label,module in modules.items():
   gs,ys=[],[]
   for repeat in range(3):
    y,_=module.exchange(x,xyz,ids.numpy(),edges,fallback,heads=8)
    gs.append(torch.autograd.grad((y*probe).sum(),x)[0].detach())
    ys.append(y.detach())
   gradients[label]=gs
   outputs[label]=ys
  def maximum(a,b):return float((a-b).abs().max().cpu())
  rec={'expression':b,'same_input_pointer':int(x.data_ptr()),'supports':n,
   'original_self_gradient_max_abs':max(maximum(gradients['original'][0],v) for v in gradients['original'][1:]),
   'revised_self_gradient_max_abs':max(maximum(gradients['revised'][0],v) for v in gradients['revised'][1:]),
   'cross_operator_gradient_max_abs':maximum(gradients['original'][0],gradients['revised'][0]),
   'cross_operator_gradient_l2':float((gradients['original'][0]-gradients['revised'][0]).norm().cpu()),
   'original_gradient_l2':float(gradients['original'][0].norm().cpu()),
   'cross_operator_output_max_abs':maximum(outputs['original'][0],outputs['revised'][0]),
   'all_gradients_finite':all(bool(torch.isfinite(v).all()) for gs in gradients.values() for v in gs)}
  r['records'].append(rec)
 r.update(execution_completed=True,after=observe(),interpretation='Repeatability diagnostic only; neither numerical threshold nor scientific admission changed.')
except BaseException as error:
 r.update(error_type=type(error).__name__,error=str(error))
 raise
finally:
 try:save('gradient_repeatability_result.json',r)
 finally:release()
print(json.dumps(r))
'''
observed = c.remote('STAGE=' + repr(stage) + '\nORIGINAL_SHA=' + repr(original_sha) + '\n' + code,
    timeout=500, conda=True)
observation = c.save('gradient_repeatability_execution.json', observed)
assert observed['returncode'] == 0, 'Preserve observer failure; do not blindly replay.'
result = c.save('gradient_repeatability_result.json', observed['data'])
c.advance([protocol, observation, result, Path(__file__)],
    'Inspect original/revised self-gradient variation alongside preserved1e-6 failures; do not convert a repeat envelope into scientific PASS.')
print(observed['data'])
